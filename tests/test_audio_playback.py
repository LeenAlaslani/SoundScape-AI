from io import BytesIO
import soundfile as sf
from fastapi.testclient import TestClient
from app.main import app


def test_comparison_audio_headers_duration_and_ranges():
    with TestClient(app) as client:
        url = '/api/compare/heavy_rain/original'
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('audio/wav')
        info = sf.info(BytesIO(response.content))
        assert info.format == 'WAV' and info.samplerate == 16000
        assert info.channels == 1 and info.frames == 160000
        partial = client.get(url, headers={'Range': 'bytes=0-99'})
        assert partial.status_code == 206
        assert partial.content == response.content[:100]
