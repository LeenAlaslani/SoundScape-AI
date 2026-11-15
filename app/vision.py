"""Lightweight, truthful cloud CV inference.

Uses the exported ONNX MobileNet checkpoint on CPU when installed.
If it is missing, the site still offers manual scene selection; no fake predictions.
The legacy PyTorch/CLIP implementation is available in vision_torch.py locally.
"""
from __future__ import annotations
import json
from pathlib import Path
from threading import Lock
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ONNX_FILE = ROOT / 'models' / 'scene_mobilenetv3.onnx'
META_FILE = ROOT / 'models' / 'scene_mobilenetv3_metadata.json'
SCENE_MAP = {'forest': 'forest', 'sea': 'coast', 'mountain': 'mountain',
             'glacier': 'mountain', 'buildings': 'unknown', 'street': 'unknown'}
_model = None
_metadata = None
_lock = Lock()


class VisionNotConfigured(RuntimeError):
    pass


def model_status():
    if ONNX_FILE.is_file() and META_FILE.is_file():
        return 'onnx_trained_cpu_model_ready'
    return 'manual_scene_selection_only_no_vision_checkpoint'


def _load():
    global _model, _metadata
    if not ONNX_FILE.is_file() or not META_FILE.is_file():
        raise VisionNotConfigured('Image AI is not connected yet. Choose the environment manually. To enable it, upload the exported ONNX checkpoint and metadata.')
    if _model is None:
        with _lock:
            if _model is None:
                import onnxruntime as ort
                metadata = json.loads(META_FILE.read_text('utf-8'))
                classes = metadata.get('classes')
                if not isinstance(classes, list) or not classes or any(not isinstance(c, str) for c in classes):
                    raise ValueError('Invalid classes in ONNX metadata')
                session = ort.InferenceSession(str(ONNX_FILE), providers=['CPUExecutionProvider'],
                                               sess_options=_session_options(ort))
                _metadata = metadata
                _model = session
    return _model, _metadata


def _session_options(ort):
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    opts.inter_op_num_threads = 1
    return opts


def _preprocess(image: Image.Image):
    # Same resize / center crop / ImageNet normalization as MobileNetV3 weights.transforms().
    im = ImageOps.exif_transpose(image).convert('RGB')
    w, h = im.size
    size = 256
    if w <= h:
        out_w, out_h = size, round(size * h / w)
    else:
        out_w, out_h = round(size * w / h), size
    im = im.resize((out_w, out_h), resample=Image.Resampling.BILINEAR)
    x0 = (out_w - 224) // 2
    y0 = (out_h - 224) // 2
    im = im.crop((x0, y0, x0 + 224, y0 + 224))
    arr = np.asarray(im, dtype=np.float32) / 255.0
    arr = (arr - np.array([.485, .456, .406], dtype=np.float32)) / np.array([.229, .224, .225], dtype=np.float32)
    return np.ascontiguousarray(arr.transpose(2, 0, 1)[None, :, :, :])


def analyze(image: Image.Image) -> dict:
    session, meta = _load()
    x = _preprocess(image)
    scores = session.run(None, {session.get_inputs()[0].name: x})[0]
    logits = np.asarray(scores, dtype=np.float64).reshape(-1)
    classes = meta['classes']
    if len(logits) != len(classes):
        raise ValueError('Model metadata classes do not match ONNX output')
    temperature = max(float(meta.get('temperature', 1.0)), 0.01)
    logits = logits / temperature
    probs = np.exp(logits - logits.max())
    probs = probs / probs.sum()
    order = np.argsort(-probs)
    chosen_id = int(order[0])
    raw_label = classes[chosen_id]
    confidence = float(probs[chosen_id])
    threshold = float(meta.get('accept_threshold', 0.0))
    accepted = confidence >= threshold
    mapping = meta.get('vision_to_scene', SCENE_MAP)
    mapped_scene = mapping.get(raw_label, 'unknown') if accepted else 'unknown'
    return {
        'scene': mapped_scene, 'raw_label': raw_label, 'score': round(confidence, 4),
        'accepted': bool(accepted), 'accept_threshold': round(threshold, 4),
        'model': 'mobilenet_finetuned_onnx', 'version': meta.get('version', 'exported'),
        'candidates': [{'label': classes[int(i)], 'score': round(float(probs[i]), 4)} for i in order[:4]],
        'caution': 'Scene labels only. Weather and audible sounds are not inferred from this image; confirm manually.'
    }
