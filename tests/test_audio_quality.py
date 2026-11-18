import numpy as np
import pytest
from app.audio_quality import conservative_peak, join_segments, measure


def test_quality_metrics_have_expected_units():
    x = np.full(2000, .5, dtype=np.float32)
    result = measure(x, 1000)
    assert result['duration_s'] == 2
    assert result['rms_dbfs'] == pytest.approx(-6.0206, abs=.001)
    assert result['quiet_frame_fraction'] == 0
    assert result['near_clip_fraction'] == 0


def test_crossfade_preserves_distinct_segment_endpoints_and_length():
    a, b = np.ones(20, dtype=np.float32), -np.ones(20, dtype=np.float32)
    out, joins = join_segments([a, b], 10, .5)
    assert len(out) == 35 and joins == [15]
    np.testing.assert_allclose(out[15:20], [1, .5, 0, -.5, -1])
    assert out[0] == 1 and out[-1] == -1


def test_reject_invalid_audio_and_overlaps():
    for bad in [[], [float('nan')], [[1, 2]]]:
        with pytest.raises(ValueError):
            measure(bad, 16000)
    with pytest.raises(ValueError):
        join_segments([np.ones(10), np.ones(10)], 10, 1)
    with pytest.raises(ValueError):
        join_segments([], 10, 1)


def test_peak_reduction_preserves_dynamics_and_does_not_amplify():
    np.testing.assert_allclose(conservative_peak([.25, -.5]), [.25, -.5])
    np.testing.assert_allclose(conservative_peak([1., -.5], .8), [.8, -.4])
