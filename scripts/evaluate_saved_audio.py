"""Measure existing teammate-generated WAVs; this does not generate or rate audio."""
import csv
from pathlib import Path
import sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.audio_quality import measure

root = Path(__file__).resolve().parents[1]
paths = sorted((root / 'assets/audio/comparisons').glob('*.wav'))
rows = []
for path in paths:
    audio, sample_rate = sf.read(path, dtype='float32')
    info = measure(audio, sample_rate)
    info['integrated_lufs'] = float(pyln.Meter(sample_rate).integrated_loudness(audio))
    info['file'] = path.name
    rows.append(info)
out = root / 'docs/results/saved_audio_metrics.csv'
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f'Wrote {len(rows)} measurements to {out}')
