"""Optional GPU inference for Athir's exact AudioLDM 2 + plain-PyTorch LoRA format.

This module deliberately loads no diffusion dependencies on import.  The five
60-second WAV exports and A/B previews work on CPU without a model download.
"""
from __future__ import annotations
from pathlib import Path
from io import BytesIO
from threading import Lock
import importlib.util
import os
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / 'models' / 'audio' / 'lora_adapters.pt'
MODEL_ID = 'cvssp/audioldm2'
MODEL_REVISION = 'c8e7e189d324425c05c4c2f81214041ef4107983'
NEGATIVE = 'music, speech, voice, singing, siren, alarm, explosion, gunshot, distortion, harsh noise, loud crack, abrupt impact, clipping'
LOCK = Lock()
_ENGINE = None


def generation_status() -> dict:
    """Report prerequisites accurately; never imply a loaded/working model."""
    enabled = os.environ.get('SOUNDSCAPE_ENABLE_GPU_AUDIO', '0') == '1'
    adapters_present = ADAPTER_PATH.is_file()
    deps = all(importlib.util.find_spec(p) is not None for p in ('diffusers', 'transformers', 'torch'))
    cuda = False
    if deps:
        try:
            import torch
            cuda = bool(torch.cuda.is_available())
        except Exception:
            pass
    return {
        'available': bool(enabled and deps and cuda),
        'enabled': enabled,
        'cuda': cuda,
        'dependencies_available': deps,
        'adapter_checkpoint_present': adapters_present,
        'available_models': ['original'] + (['intensity','comfort'] if adapters_present else []),
        'loaded': _ENGINE is not None,
        'message': ('GPU audio generation can be launched on first use.' if enabled and deps and cuda
                    else 'CPU playback and mixer ready; new diffusion inference needs a CUDA GPU and optional model dependencies.'),
    }


class LoRALinear:
    """Construct only at runtime to keep the base app CPU-light."""
    @staticmethod
    def build(torch, nn, base_layer, rank=8, alpha=8):
        class AdapterLinear(nn.Module):
            def __init__(self):
                super().__init__()
                self.base = base_layer
                self.scale = alpha / rank
                self.enabled = False
                self.lora_A = nn.Parameter(torch.zeros(rank, base_layer.in_features, dtype=torch.float32, device=base_layer.weight.device),requires_grad=False)
                self.lora_B = nn.Parameter(torch.zeros(base_layer.out_features, rank, dtype=torch.float32, device=base_layer.weight.device),requires_grad=False)
            @property
            def weight(self): return self.base.weight
            @property
            def bias(self): return self.base.bias
            @property
            def in_features(self): return self.base.in_features
            @property
            def out_features(self): return self.base.out_features
            def forward(self, x):
                y = self.base(x)
                if self.enabled:
                    correction = (x.float() @ self.lora_A.t()) @ self.lora_B.t()
                    y = y + (correction * self.scale).to(y.dtype)
                return y
        return AdapterLinear()


class GenerationEngine:
    def __init__(self):
        import torch
        from torch import nn
        from transformers import GPT2LMHeadModel
        from diffusers import AudioLDM2Pipeline
        if not torch.cuda.is_available():
            raise RuntimeError('AudioLDM 2 GPU inference is not enabled on this machine.')
        self.torch = torch
        self.nn = nn
        self.device = 'cuda'
        self.dtype = torch.float16
        self.pipe = AudioLDM2Pipeline.from_pretrained(MODEL_ID, revision=MODEL_REVISION, torch_dtype=self.dtype).to(self.device)
        if type(self.pipe.language_model).__name__ == 'GPT2Model':
            old = self.pipe.language_model
            new = GPT2LMHeadModel(old.config)
            new.transformer.load_state_dict(old.state_dict(), strict=True)
            new = new.to(device=next(old.parameters()).device, dtype=next(old.parameters()).dtype).eval()
            self.pipe.register_modules(language_model=new)
            del old
        if not hasattr(self.pipe.language_model, '_update_model_kwargs_for_generation'):
            raise RuntimeError('Transformers GPT-2 generation interface is incompatible with this checkpoint')
        self.rate = int(getattr(self.pipe.vocoder.config,'sampling_rate',16000))
        self.layers = {}
        self.adapters = {}
        if ADAPTER_PATH.is_file():
            # The file must come from your own trusted Colab execution; never load arbitrary weights.
            data = torch.load(ADAPTER_PATH, map_location='cpu', weights_only=True)
            if not isinstance(data, dict) or not {'intensity','comfort'}.intersection(data):
                raise ValueError('Adapter checkpoint must contain the named intensity / comfort adapters')
            names=[]
            for name,mod in self.pipe.unet.named_modules():
                if ('attn2' in name.split('.')) and isinstance(mod, nn.Linear) and name.endswith(('to_q','to_k','to_v','to_out.0')):
                    names.append(name)
            if not names:
                raise ValueError('Could not find expected AudioLDM 2 cross-attention layers')
            for name in names:
                parent,child=name.rsplit('.',1)
                module=self.pipe.unet.get_submodule(parent)
                wrapper=LoRALinear.build(torch,nn,getattr(module,child),rank=8,alpha=8)
                setattr(module,child,wrapper)
                self.layers[name]=wrapper
            if len(self.layers)!=192:
                raise ValueError(f'Adapter layout mismatch: expected 192 layers, found {len(self.layers)}')
            for label,weights in data.items():
                if not isinstance(weights,dict) or set(weights)!=set(self.layers):
                    raise ValueError(f'Unexpected LoRA layer list for {label}')
                for name,(a,b) in weights.items():
                    layer=self.layers[name]
                    if a.shape != layer.lora_A.shape or b.shape != layer.lora_B.shape:
                        raise ValueError(f'LoRA shape mismatch for {label}/{name}')
                self.adapters[label]=weights
        self.pipe.unet.eval()

    def _activate(self, label):
        if label == 'original':
            for layer in self.layers.values(): layer.enabled=False
            return
        if label not in self.adapters:
            raise ValueError(f'Adapter {label!r} unavailable; export models/audio/lora_adapters.pt from Colab')
        with self.torch.no_grad():
            for name,(a,b) in self.adapters[label].items():
                layer=self.layers[name]
                layer.lora_A.copy_(a.to(layer.lora_A.device))
                layer.lora_B.copy_(b.to(layer.lora_B.device))
                layer.enabled=True

    def generate(self,prompt,adapter,seconds,seed):
        torch=self.torch
        self._activate(adapter)
        try:
            with torch.inference_mode():
                result=self.pipe(prompt=prompt,negative_prompt=NEGATIVE,audio_length_in_s=float(seconds),
                         num_inference_steps=50,guidance_scale=3.5,generator=torch.Generator(device=self.device).manual_seed(seed))
            y=np.asarray(result.audios[0],dtype=np.float32).reshape(-1)
            if not len(y) or not np.isfinite(y).all():raise RuntimeError('Model returned invalid audio')
            peak=np.max(np.abs(y))
            if peak>0.95:y=y*(0.95/peak)
            out=BytesIO();sf.write(out,y,self.rate,format='WAV',subtype='PCM_16')
            return out.getvalue()
        finally:
            self._activate('original')


def generate_wav(prompt: str,adapter: str,seconds: int,seed: int) -> bytes:
    global _ENGINE
    if not generation_status()['available']:
        raise RuntimeError('GPU generation is not available. Existing WAV previews and mixing still work.')
    if adapter not in ('original','intensity','comfort'):
        raise ValueError('Adapter must be original, intensity, or comfort')
    if not 5 <= seconds <= 10:
        raise ValueError('Diffusion output must be 5–10 seconds')
    if not 0 <= seed <= 2**32-1:
        raise ValueError('Seed out of range')
    if not prompt.strip() or len(prompt)>400:
        raise ValueError('Prompt must be 1–400 characters')
    # One request at a time: switching an adapter changes the shared U-Net weights.
    with LOCK:
        if _ENGINE is None:_ENGINE=GenerationEngine()
        return _ENGINE.generate(prompt,adapter,seconds,seed)
