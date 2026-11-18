"""Technical measurements and transitions for mono float audio experiments."""
from __future__ import annotations
import numpy as np
from scipy.signal import resample_poly


def _audio(samples):
    x = np.asarray(samples, dtype=np.float32)
    if x.ndim != 1 or not x.size or not np.isfinite(x).all():
        raise ValueError('Audio must be nonempty, finite, and mono')
    return x


def measure(samples, sample_rate):
    x = _audio(samples)
    if sample_rate <= 0:
        raise ValueError('Sample rate must be positive')
    rms = float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))
    # Four-times oversampling is an estimate, not certified BS.1770 true peak.
    oversampled_peak = float(np.max(np.abs(resample_poly(x.astype(np.float64), 4, 1))))
    frame = max(1, int(sample_rate * .1))
    levels = [np.sqrt(np.mean(part.astype(np.float64) ** 2))
              for part in (x[i:i + frame] for i in range(0, len(x), frame))]
    return {'duration_s': len(x) / sample_rate, 'peak': float(np.max(np.abs(x))),
            'rms_dbfs': float(20 * np.log10(max(rms, 1e-12))),
            'near_clip_fraction': float(np.mean(np.abs(x) >= .999)),
            'quiet_frame_fraction': float(np.mean(np.array(levels) < .001)),
            'boundary_jump': float(abs(x[0] - x[-1])),
            'oversampled_peak_dbfs': float(20 * np.log10(max(oversampled_peak, 1e-12)))}


def join_segments(segments, sample_rate, overlap_seconds=1.0):
    """Crossfade distinct generated segments; returns audio and join positions."""
    clips = [_audio(segment) for segment in segments]
    if not clips or sample_rate <= 0 or not np.isfinite(overlap_seconds):
        raise ValueError('Segments and valid sample rate are required')
    n = int(round(overlap_seconds * sample_rate))
    if n < 2 or any(len(clip) <= n for clip in clips):
        raise ValueError('Overlap must be positive and shorter than each segment')
    result = clips[0].copy()
    joins = []
    fade = np.linspace(0, 1, n, dtype=np.float32)
    for clip in clips[1:]:
        joins.append(len(result) - n)
        # Complementary gains avoid a gain bump for correlated signals.
        blend = result[-n:] * (1 - fade) + clip[:n] * fade
        result = np.concatenate((result[:-n], blend, clip[n:]))
    return result, joins


def conservative_peak(samples, limit=.95):
    x = _audio(samples).copy()
    if not 0 < limit <= 1:
        raise ValueError('Peak limit must be in (0, 1]')
    peak = float(np.max(np.abs(x)))
    if peak > limit:
        x *= limit / peak
    return x
