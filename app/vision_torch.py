"""SoundScape image → scene inference.

The supervised MobileNet checkpoint supports six classes only; unsupported nature
classes must be selected by the user or suggested (unvalidated) by CLIP fallback.
The image never proves what audio was present when the photo was taken.
"""
from __future__ import annotations
from pathlib import Path
from threading import Lock
from PIL import Image, ImageOps
import torch

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / 'models' / 'scene_mobilenetv3.pt'

SCENE_LABELS = {
    'forest': 'forest', 'sea': 'coast', 'mountain': 'mountain',
    'glacier': 'mountain', 'buildings': 'unknown', 'street': 'unknown',
}
CLIP_CANDIDATES = {
    'a photograph of a lush green forest': 'forest',
    'a photograph of a quiet beach beside the ocean': 'coast',
    'a photograph of an open desert with sand dunes': 'desert',
    'a photograph of a flowing river or stream': 'river',
    'a photograph of a cascading waterfall': 'waterfall',
    'a photograph of a mountain landscape': 'mountain',
    'a photograph of a peaceful lake': 'lake',
    'a photograph of a modern city street': 'unknown',
    'a photograph of an indoor room': 'unknown',
    'a photograph of a closeup portrait of a person': 'unknown',
}

class SceneDetector:
    def __init__(self):
        self._model = None
        self._processor = None
        self._mode = None
        self._classes = None
        self._lock = Lock()
        self._temperature = 1.0
        self._threshold = 0.0
        self._version = 'untrained'
        self._mapping = dict(SCENE_LABELS)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def _initialize(self):
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            if CHECKPOINT.exists():
                from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
                checkpoint = torch.load(CHECKPOINT, map_location='cpu', weights_only=True)
                classes = checkpoint['classes']
                model = mobilenet_v3_small(weights=None)
                model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, len(classes))
                model.load_state_dict(checkpoint['state_dict'], strict=True)
                model.to(self.device).eval()
                self._processor = MobileNet_V3_Small_Weights.DEFAULT.transforms()
                self._classes = classes
                self._model = model
                phase = checkpoint.get('training_phase', 'finetune')
                self._mode = 'mobilenet_finetuned' if phase in ('finetune','partial_finetune') else 'mobilenet_head'
                self._temperature = max(0.01,float(checkpoint.get('temperature',1.0)))
                self._threshold = float(checkpoint.get('accept_threshold',0.0))
                self._version = checkpoint.get('version','legacy_checkpoint')
                self._mapping = checkpoint.get('vision_to_scene',dict(SCENE_LABELS))
            else:
                from transformers import pipeline
                self._model = pipeline('zero-shot-image-classification',
                    model='openai/clip-vit-base-patch32',
                    device=0 if self.device=='cuda' else -1)
                self._mode = 'clip_zero_shot'
                self._version = 'unvalidated_zero_shot_baseline'

    def predict(self,image:Image.Image) -> dict:
        self._initialize()
        image = ImageOps.exif_transpose(image).convert('RGB')
        if self._mode.startswith('mobilenet_'):
            with torch.inference_mode():
                x=self._processor(image).unsqueeze(0).to(self.device)
                logits=self._model(x).float().squeeze(0)
                probs=torch.softmax(logits/self._temperature,dim=0).cpu().tolist()
            ranked=sorted(zip(self._classes,probs),key=lambda item:item[1],reverse=True)
            raw_label,score=ranked[0]
            accepted=bool(float(score)>=self._threshold)
            scene=self._mapping.get(raw_label,'unknown') if accepted else 'unknown'
            return {'scene':scene,'raw_label':raw_label,'score':round(float(score),4),
                    'accepted':accepted,'accept_threshold':round(self._threshold,4),
                    'model':self._mode,'version':self._version,
                    'candidates':[{'label':label,'score':round(float(s),4)} for label,s in ranked[:4]],
                    'caution':'In-domain calibrated scene suggestion only; unseen scene classes and audible events are not validated. Confirm or edit.'}
        result=self._model(image,candidate_labels=list(CLIP_CANDIDATES))
        top=result[0]
        scene=CLIP_CANDIDATES[top['label']]
        if len(result)>1 and float(top['score'])-float(result[1]['score'])<0.035:
            scene='unknown'
        return {'scene':scene,'raw_label':top['label'],'score':round(float(top['score']),4),
                'accepted':scene!='unknown','model':self._mode,'version':self._version,
                'candidates':[{'label':CLIP_CANDIDATES[item['label']],'score':round(float(item['score']),4)} for item in result[:4]],
                'caution':'CLIP suggestions are not evaluated on this dataset for new classes; similarity scores are not calibrated. Confirm manually.'}

_detector=SceneDetector()
def analyze(image:Image.Image)->dict:
    return _detector.predict(image)

def model_status()->str:
    return 'trained_checkpoint_detected' if CHECKPOINT.exists() else 'unvalidated_clip_fallback_available_on_first_request'
