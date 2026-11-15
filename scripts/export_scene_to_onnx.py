"""Run once in Colab or a local PyTorch environment to prepare CPU-cloud vision files.

Usage:
  pip install onnx
  python scripts/export_scene_to_onnx.py path/to/scene_mobilenetv3.pt

Copies the resulting .onnx and _metadata.json files into models/ before pushing to host.
No training performed in this script.
"""
from pathlib import Path
import json
import sys
import torch
from torchvision.models import mobilenet_v3_small

CHECKPOINT = Path(sys.argv[1] if len(sys.argv) > 1 else 'models/scene_mobilenetv3.pt')
DEST = Path(__file__).resolve().parents[1] / 'models'
DEST.mkdir(exist_ok=True)

cp = torch.load(CHECKPOINT, map_location='cpu', weights_only=True)
classes = list(cp['classes'])
net = mobilenet_v3_small(weights=None)
net.classifier[3] = torch.nn.Linear(net.classifier[3].in_features, len(classes))
net.load_state_dict(cp['state_dict'], strict=True)
net.eval()
onnx_path = DEST / 'scene_mobilenetv3.onnx'
with torch.no_grad():
    torch.onnx.export(net, torch.randn(1, 3, 224, 224), str(onnx_path),
                      input_names=['pixel_values'], output_names=['logits'],
                      dynamic_axes={'pixel_values': {0: 'batch'}, 'logits': {0: 'batch'}},
                      opset_version=17, do_constant_folding=True, dynamo=False)
metadata = {
    'classes': classes,
    'temperature': float(cp.get('temperature', 1.0)),
    'accept_threshold': float(cp.get('accept_threshold', 0.0)),
    'vision_to_scene': cp.get('vision_to_scene', {
      'forest':'forest','sea':'coast','mountain':'mountain',
      'glacier':'mountain','buildings':'unknown','street':'unknown'}),
    'version': 'soundscape_cv_onnx_cpu_v1',
    'training_phase': cp.get('training_phase', 'unknown')
}
meta_path = DEST / 'scene_mobilenetv3_metadata.json'
meta_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
print('Exported:', onnx_path, meta_path)
