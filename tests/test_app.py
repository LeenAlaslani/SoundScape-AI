from io import BytesIO
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app import audio
import soundfile as sf

client = TestClient(app)

def test_status():
    d = client.get('/api/status')
    assert d.status_code == 200
    assert 'vision' in d.json() and d.json()['audio'] == 'generated_library_ready'
    assert len(d.json()['available_layers']) == 5
    assert 'generation' in d.json()

def test_compose():
    r = client.post('/api/compose', json={'scene':'forest','sound':'rain','intensity':'gentle','comfort_mode':True})
    assert r.status_code == 200
    assert 'forest' in r.json()['prompt'] and 'rain' in r.json()['prompt']
    assert r.json()['settings']['sound'] == 'rain'

def test_bad_compose():
    assert client.post('/api/compose',json={'scene':'no-such-place'}).status_code == 422

def test_weather_is_a_user_preference_and_comfort_changes_request():
    base={'scene':'forest','sound':'rain','weather':'fog'}
    gentle=client.post('/api/compose',json={**base,'comfort_mode':True}).json()
    natural=client.post('/api/compose',json={**base,'comfort_mode':False}).json()
    assert 'listener imagines fog' in gentle['prompt']
    assert gentle['prompt'] != natural['prompt']
    assert client.post('/api/compose',json={**base,'weather':'hail'}).status_code == 422

def test_image_validation():
    r = client.post('/api/analyze',files={'image':('bad.txt',b'not image','text/plain')})
    assert r.status_code == 415
    r = client.post('/api/analyze',files={'image':('bad.png',b'not image','image/png')})
    assert r.status_code == 400

def test_analysis_mock_does_not_download_models(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main, 'analyze', lambda img: {'scene':'forest','model':'test','score':0.7})
    bio = BytesIO();Image.new('RGB',(32,32),(42,115,74)).save(bio,format='PNG')
    r=client.post('/api/analyze',files={'image':('forest.png',bio.getvalue(),'image/png')})
    assert r.status_code == 200 and r.json()['scene'] == 'forest'

def test_mixer_missing_file(tmp_path,monkeypatch):
    monkeypatch.setattr(audio,"BASE",tmp_path)
    r=client.post('/api/mix',json={'seconds':5,'levels':{'thunderstorm':100}})
    assert r.status_code == 409 and 'Missing' in r.json()['detail']

def test_mixer_generated_test_tone_is_not_in_distribution(tmp_path,monkeypatch):
    monkeypatch.setattr(audio,'BASE',tmp_path)
    sr=8000
    samples=np.sin(2*np.pi*440*np.arange(sr,dtype=np.float32)/sr)*.1
    sf.write(tmp_path/'rain_ambient_60s.wav',samples,sr)
    r=client.post('/api/mix',json={'seconds':5,'levels':{'rain':60}})
    assert r.status_code==200 and r.headers['content-type'].startswith('audio/wav')
    wav,output_sr=sf.read(BytesIO(r.content))
    assert output_sr==16000 and len(wav)==5*16000
    assert float(np.max(np.abs(wav)))>0.01


def test_real_audio_files_and_preview_endpoints():
    for cat in ('rain','sea_waves','wind','pouring_water','thunderstorm'):
        r=client.get('/api/preview/'+cat)
        assert r.status_code==200 and r.content[:4]==b'RIFF'
        data,rate=sf.read(BytesIO(r.content))
        assert rate==16000 and len(data)==60*16000
        assert np.isfinite(data).all()
        assert float(np.max(np.abs(data)))>0.03
    assert client.get('/api/preview/../../../etc/passwd').status_code in (400,404)


def test_finetuned_comparison_samples():
    for prompt in ('heavy_rain','rain_nice_sound'):
        for model in ('original','intensity','comfort'):
            response=client.get(f'/api/compare/{prompt}/{model}')
            assert response.status_code==200
            data,rate=sf.read(BytesIO(response.content))
            assert rate==16000 and len(data)==160000
    assert client.get('/api/compare/invalid/comfort').status_code==404
    assert client.get('/api/compare/heavy_rain/bogus').status_code==404


def test_generate_gate(monkeypatch):
    import app.main as m
    monkeypatch.setattr(m,'generation_status',lambda:{'available':False})
    response=client.post('/api/generate',json={'prompt':'gentle rain','adapter':'intensity','seconds':10})
    assert response.status_code==503
    assert client.post('/api/generate',json={'prompt':'rain','seconds':30}).status_code==422


def test_generate_route_with_model_mock(monkeypatch):
    import app.main as m
    monkeypatch.setattr(m,'generation_status',lambda:{'available':True})
    mock=BytesIO();sf.write(mock,np.zeros(16000,dtype=np.float32),16000,format='WAV',subtype='PCM_16')
    monkeypatch.setattr(m,'generate_wav',lambda prompt,adapter,seconds,seed:mock.getvalue())
    response=client.post('/api/generate',json={'prompt':'gentle forest rain','adapter':'original','seconds':10,'seed':42})
    assert response.status_code==200 and response.content[:4]==b'RIFF'


def test_lora_layer_wrapper_reproduces_base_without_adapter():
    import torch
    from torch import nn
    from app.audio_generation import LoRALinear
    base=nn.Linear(5,3)
    adapter=LoRALinear.build(torch,nn,base)
    x=torch.randn(2,5)
    assert torch.allclose(adapter(x),base(x))
    with torch.no_grad():
        adapter.lora_A.fill_(.1);adapter.lora_B.fill_(.2)
    adapter.enabled=True
    assert not torch.allclose(adapter(x),base(x))
