from __future__ import annotations
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from app.vision import analyze, model_status, VisionNotConfigured
from app.prompting import SoundSettings, build_prompt
from app.audio import mix_layers, available_layers
from app.audio_generation import generation_status, generate_wav

app = FastAPI(title='SoundScape AI — Vision Guided Sound', version='0.3.0')
FRONTEND = Path(__file__).resolve().parents[1] / 'frontend'

@app.get('/api/status')
def status():
    return {
        'vision': model_status(),
        'audio': 'generated_library_ready' if available_layers() else 'generated_library_missing',
        'available_layers': available_layers(),
        'generation': generation_status(),
        'comparison_prompts': ['heavy_rain','rain_nice_sound'],
    }

@app.post('/api/analyze')
async def analyze_image(image: UploadFile = File(...)):
    if image.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(415, 'Upload a JPEG, PNG or WebP image')
    data = await image.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, 'Image is larger than 8MB')
    try:
        pic = Image.open(BytesIO(data))
        pic.verify()
        pic = Image.open(BytesIO(data))
        if pic.width * pic.height > 25_000_000:
            raise HTTPException(413, 'Image resolution is too large')
        pic.load()
        return analyze(pic)
    except HTTPException:
        raise
    except VisionNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, 'Invalid image file') from exc
    except Exception as exc:
        raise HTTPException(503, 'Vision model could not load; check server logs and model installation') from exc

@app.post('/api/compose')
def compose(settings: SoundSettings):
    return build_prompt(settings)

class MixSettings(BaseModel):
    seconds: int = Field(default=30, ge=5, le=120)
    levels: dict[str, int] = Field(default_factory=dict)

@app.post('/api/mix')
def mix(request: MixSettings):
    try:
        wav = mix_layers(request.levels, request.seconds)
        return Response(content=wav, media_type='audio/wav', headers={
            'Content-Disposition': 'attachment; filename="soundscape_mix.wav"',
            'Cache-Control': 'no-store'
        })
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(409, str(exc)) from exc

@app.get('/api/preview/{category}')
def preview_layer(category: str):
    if category not in ('rain','sea_waves','wind','pouring_water','thunderstorm'):
        raise HTTPException(404,'Unknown audio layer')
    path=Path(__file__).resolve().parents[1] / 'assets' / 'audio' / f'{category}_ambient_60s.wav'
    if not path.is_file():
        raise HTTPException(404,'The exported audio WAV has not been added yet')
    return FileResponse(path,media_type='audio/wav',filename=path.name)

@app.get('/api/compare/{prompt_id}/{adapter}')
def preview_comparison(prompt_id: str, adapter: str):
    if prompt_id not in ('heavy_rain','rain_nice_sound') or adapter not in ('original','intensity','comfort'):
        raise HTTPException(404,'Unknown example or model')
    path=Path(__file__).resolve().parents[1] / 'assets' / 'audio' / 'comparisons' / f'{prompt_id}_{adapter}.wav'
    if not path.is_file():
        raise HTTPException(404,'Example waveform missing')
    return FileResponse(path,media_type='audio/wav',filename=path.name)

class GenerateSettings(BaseModel):
    prompt: str = Field(min_length=1,max_length=400)
    adapter: str = Field(default='original',pattern='^(original|intensity|comfort)$')
    seconds: int = Field(default=10,ge=5,le=10)
    seed: int = Field(default=42,ge=0,le=4294967295)

@app.post('/api/generate')
def generate_audio(request: GenerateSettings):
    if not generation_status()['available']:
        raise HTTPException(503,'Live generation requires a CUDA GPU and the optional AudioLDM 2 environment. The pre-generated audio library works without them.')
    try:
        wav=generate_wav(request.prompt,request.adapter,request.seconds,request.seed)
        return Response(content=wav,media_type='audio/wav',headers={'Content-Disposition':'attachment; filename="soundscape_generated.wav"','Cache-Control':'no-store'})
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(503,str(exc)) from exc

@app.get('/')
def home():
    return FileResponse(FRONTEND / 'index.html')

app.mount('/static', StaticFiles(directory=FRONTEND), name='static')
