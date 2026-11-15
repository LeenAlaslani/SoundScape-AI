"""Smoke test for final notebook checkpoint format, without internet downloads."""
import torch
from PIL import Image
from torchvision.models import mobilenet_v3_small
from app import vision_torch as vision

def test_exported_checkpoint_loads_and_predicts(tmp_path,monkeypatch):
    path=tmp_path/'scene_mobilenetv3.pt'
    model=mobilenet_v3_small(weights=None)
    model.classifier[3]=torch.nn.Linear(model.classifier[3].in_features,6)
    torch.save({
      'state_dict':model.state_dict(),
      'classes':['buildings','forest','glacier','mountain','sea','street'],
      'training_phase':'finetune','dataset_id':'mock','seed':42,
      'trained_samples':100,'temperature':1.3,'accept_threshold':0.95,
      'target_accept_accuracy':0.9,'target_met_on_validation':True,
      'vision_to_scene':{'forest':'forest','sea':'coast','mountain':'mountain',
          'glacier':'mountain','street':'unknown','buildings':'unknown'},
      'version':'soundscape-cv-1.0',
    },path)
    monkeypatch.setattr(vision,'CHECKPOINT',path)
    det=vision.SceneDetector();det.device='cpu'
    result=det.predict(Image.new('RGB',(224,224),(30,150,60)))
    assert result['model']=='mobilenet_finetuned'
    assert result['version']=='soundscape-cv-1.0'
    assert result['raw_label'] in ['buildings','forest','glacier','mountain','sea','street']
    assert result['scene']=='unknown' # random initial weights should not pass 95% threshold
    assert len(result['candidates'])==4
    assert result['accept_threshold']==0.95
