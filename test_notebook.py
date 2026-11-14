import ast
import json
import tempfile
import unittest
import wave
from pathlib import Path
import numpy as np

notebook = json.loads((Path(__file__).resolve().parent / 'SoundScape_Nature_Production.ipynb').read_text())
env = {'np': np, 'SR': 16000}
for cell in notebook['cells']:
    if cell['cell_type'] != 'code':
        continue
    source = ''.join(cell['source'])
    if source.lstrip().startswith('%'):
        continue
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name in {'soft_master', 'loop_crossfade', 'mix_soundscape'}:
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<notebook>', 'exec'), env)

class SignalTests(unittest.TestCase):
    def test_loop_and_wav_roundtrip(self):
        sr = env['SR']
        audio = (0.1*np.sin(2*np.pi*220*np.arange(sr*3)/sr)).astype(np.float32)
        loop = env['loop_crossfade'](audio, seconds=5, fade_seconds=.25)
        self.assertEqual(len(loop), sr*5)
        self.assertTrue(np.isfinite(loop).all())
        self.assertAlmostEqual(float(loop[0]), float(loop[-1]), places=6)
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder)/'fixture.wav')
            with wave.open(path, 'wb') as f:
                f.setparams((1, 2, sr, 0, 'NONE', 'not compressed'))
                f.writeframes((loop*32767).astype('<i2').tobytes())
            with wave.open(path, 'rb') as f:
                self.assertEqual((f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()), (1, 2, sr, sr*5))
    def test_master_peak(self):
        out = env['soft_master'](np.array([0., 1., -1.], dtype=np.float32))
        self.assertLessEqual(float(np.max(np.abs(out))), .881)
    def test_short_loop_rejected(self):
        with self.assertRaises(ValueError):
            env['loop_crossfade'](np.zeros(20), seconds=1, fade_seconds=1)
    def test_invalid_mix_rejected(self):
        for volume in [-1, 101, float('nan')]:
            with self.assertRaises(ValueError):
                env['mix_soundscape']({'rain': volume})

if __name__ == '__main__':
    unittest.main(verbosity=2)
