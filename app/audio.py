"""Optional playback mixer for real AudioLDM2 exports; no fake model inference."""
from pathlib import Path
from io import BytesIO
import math
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

BASE = Path(__file__).resolve().parents[1] / 'assets' / 'audio'
LAYERS = ('rain', 'sea_waves', 'wind', 'pouring_water', 'thunderstorm')
RATE = 16000

def available_layers() -> list[str]:
    return [name for name in LAYERS if (BASE / f'{name}_ambient_60s.wav').exists()]

def _loop(y: np.ndarray, total: int, xfade: int = 800) -> np.ndarray:
    if len(y) >= total:
        return y[:total].copy()
    if len(y) < xfade * 2:
        xfade = max(0, len(y) // 4)
    if not xfade:
        return np.resize(y, total)
    result = y.copy()
    while len(result) < total:
        t = np.linspace(0, 1, xfade, endpoint=False, dtype=np.float32)
        overlap = result[-xfade:] * (1 - t) + y[:xfade] * t
        result = np.concatenate([result[:-xfade], overlap, y[xfade:]])
    return result[:total]

def mix_layers(levels: dict[str, int], seconds: int = 30) -> bytes:
    if not 5 <= seconds <= 120:
        raise ValueError('Duration must be between 5 and 120 seconds')
    if any(name not in LAYERS for name in levels):
        raise ValueError('Unknown sound layer')
    if any(type(vol) is not int or not 0 <= vol <= 100 for vol in levels.values()):
        raise ValueError('Layer levels must be integers from 0 to 100')
    used = [(name, vol) for name, vol in levels.items() if vol > 0]
    if not used:
        raise ValueError('Choose at least one layer above 0%')
    missing = [name for name, _ in used if name not in available_layers()]
    if missing:
        raise FileNotFoundError('Missing generated audio WAV: ' + ', '.join(missing))
    mixed = np.zeros(int(RATE * seconds), dtype=np.float32)
    for name, level in used:
        data, sr = sf.read(BASE / f'{name}_ambient_60s.wav', dtype='float32', always_2d=True)
        mono = data.mean(axis=1)
        if sr != RATE:
            g = math.gcd(sr, RATE)
            mono = resample_poly(mono, RATE // g, sr // g).astype('float32')
        mixed += _loop(mono, len(mixed)) * (level / 100.0)
    peak = float(np.max(np.abs(mixed)))
    if peak > 0.95:
        mixed *= (0.95 / peak)
    output = BytesIO()
    sf.write(output, mixed, RATE, format='WAV', subtype='PCM_16')
    return output.getvalue()
