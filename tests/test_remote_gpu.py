import pytest
from app.remote_gpu import remote_status, generate_remote_wav


def test_missing_space_is_not_available(monkeypatch):
    monkeypatch.delenv('SOUNDSCAPE_GRADIO_SPACE', raising=False)
    assert remote_status()['available'] is False


def test_configured_space_reports_unverified(monkeypatch):
    monkeypatch.setenv('SOUNDSCAPE_GRADIO_SPACE','sample/soundscape-audio')
    status=remote_status()
    assert status['available'] is True
    assert status['status_verified'] is False
    assert status['available_models'] == ['original']


def test_adapter_is_disabled_without_checkpoint(monkeypatch):
    monkeypatch.setenv('SOUNDSCAPE_GRADIO_SPACE','sample/soundscape-audio')
    monkeypatch.delenv('SOUNDSCAPE_REMOTE_ADAPTERS',raising=False)
    with pytest.raises(ValueError):
        generate_remote_wav('rain', 'comfort',10,42)


def test_remote_receives_exact_prompt(monkeypatch):
    from pathlib import Path
    from app import remote_gpu
    captured = []
    class FakeClient:
        def predict(self, prompt, *args, **kwargs):
            captured.append(prompt)
            return str(Path(__file__).resolve().parents[1] / 'assets/audio/comparisons/heavy_rain_original.wav')
    monkeypatch.setenv('SOUNDSCAPE_GRADIO_SPACE','sample/soundscape-audio')
    monkeypatch.setattr(remote_gpu, '_client', lambda *args: FakeClient())
    prompt = '  soft rain with distant thunder  '
    assert generate_remote_wav(prompt, 'original', 10, 42).startswith(b'RIFF')
    assert captured == [prompt]
