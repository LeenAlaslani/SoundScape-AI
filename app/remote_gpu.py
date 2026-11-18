"""Optional external HF ZeroGPU / Gradio generator bridge.

This file does NOT load AudioLDM 2 in the free Render service.
Calls are server-side; keep HF_TOKEN in Render secrets, never in the browser.
A configured URL is not proof that the remote runtime has been tested or is live.
"""
from __future__ import annotations
import os
from pathlib import Path
from functools import lru_cache
import soundfile as sf


def remote_space_id() -> str:
    return os.environ.get('SOUNDSCAPE_GRADIO_SPACE', '').strip()


def remote_status() -> dict:
    space = remote_space_id()
    adapters = [x.strip() for x in os.environ.get('SOUNDSCAPE_REMOTE_ADAPTERS', 'original').split(',') if x.strip()]
    adapters = [x for x in ('original', 'intensity', 'comfort') if x in adapters]
    if not adapters:
        adapters = ['original']
    return {
        'available': bool(space),  # configured, *not* independently verified to be responding
        'enabled': bool(space),
        'cuda': False,
        'backend': 'huggingface_zerogpu_gradio' if space else 'not_configured',
        'space_configured': bool(space),
        'status_verified': False,
        'adapter_checkpoint_present': all(x in adapters for x in ('intensity','comfort')),
        'available_models': adapters,
        'message': ('Hugging Face GPU Space configured; availability and quotas are checked when a request is made.'
                    if space else 'A public HF ZeroGPU Space must be deployed to enable new audio generation.'),
    }


@lru_cache(maxsize=4)
def _client(space: str, hf_token: str):
    from gradio_client import Client
    return Client(space, token=hf_token or None, verbose=False)


def generate_remote_wav(prompt: str, adapter: str, seconds: int, seed: int) -> bytes:
    space = remote_space_id()
    if not space:
        raise RuntimeError('No external GPU Space is configured yet.')
    s=remote_status()
    if adapter not in s['available_models']:
        raise ValueError(f'Model {adapter!r} not enabled in the remote GPU Space')
    if not 5 <= int(seconds) <= 10:
        raise ValueError('Audio must be between 5 and 10 seconds')
    if not 0 <= int(seed) <= 2**32 - 1:
        raise ValueError('Seed out of range')
    if not 1 <= len(prompt.strip()) <= 400:
        raise ValueError('Prompt must contain 1–400 characters')
    try:
        result = _client(space, os.environ.get('HF_TOKEN', '')).predict(
            prompt, adapter, int(seconds), int(seed), api_name='/generate_audio'
        )
        # gr.Audio(type='filepath') returns a downloaded local filename via gradio_client.
        if isinstance(result, dict):
            result = result.get('path') or result.get('name')
        if not isinstance(result, str) or not result:
            raise RuntimeError('Unexpected Gradio audio response')
        path = Path(result)
        if not path.is_file():
            raise RuntimeError('The GPU Space did not return a locally downloaded audio file')
        if not (44 <= path.stat().st_size <= 20_000_000):
            raise RuntimeError('Audio file is missing or exceeds size limit')
        info = sf.info(str(path))
        if not info.frames or not info.samplerate or info.format != 'WAV':
            raise RuntimeError('The GPU Space returned an invalid WAV')
        return path.read_bytes()
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        raise RuntimeError('Hugging Face GPU Space request failed or its quota is exhausted; check the Space logs.') from exc
