from io import BytesIO
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app import vision

client=TestClient(app)

def test_cloud_manual_mode_when_no_export(monkeypatch, tmp_path):
    monkeypatch.setattr(vision,'ONNX_FILE',tmp_path/'missing.onnx')
    monkeypatch.setattr(vision,'META_FILE',tmp_path/'missing.json')
    assert vision.model_status().startswith('manual_scene')
    img=BytesIO();Image.new('RGB',(64,64),'green').save(img,format='PNG')
    resp=client.post('/api/analyze',files={'image':('forest.png',img.getvalue(),'image/png')})
    assert resp.status_code==503
    assert 'manually' in resp.json()['detail'].lower()


def test_cloud_onnx_inference_contract(monkeypatch):
    class FakeInput:
        name='pixel_values'
    class FakeSession:
        def get_inputs(self):return [FakeInput()]
        def run(self, outputs,inputs):
            assert list(inputs.values())[0].shape==(1,3,224,224)
            return [np.array([[0,6,0,0,1,0]], dtype=np.float32)]
    labels=['buildings','forest','glacier','mountain','sea','street']
    monkeypatch.setattr(vision,'_load',lambda:(FakeSession(),{'classes':labels,'temperature':1.0,'accept_threshold':0.5}))
    out=vision.analyze(Image.new('RGB',(450,300),'green'))
    assert out['scene']=='forest'
    assert out['model']=='mobilenet_finetuned_onnx'
    assert out['accepted']
    assert len(out['candidates'])==4
