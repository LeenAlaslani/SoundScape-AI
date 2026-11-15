# Cloud deployment

**See [DEPLOY_RENDER.md](DEPLOY_RENDER.md)** for publishing the existing sound studio on Render with no rented GPU.

# SoundScape AI — Vision × Nature Audio Studio

An integrated, simple web studio to **upload a photo, analyze its nature scene, suggest an audio prompt, listen to real generated nature sounds, compare two fine-tuned adapters, and mix or download WAVs**. The optional CUDA server can also generate **new audio** from a prompt once the actual model checkpoints are supplied.

## What is already real and usable now

- Five actual **60-second AudioLDM 2 WAVs** (`rain`, `sea_waves`, `wind`, `pouring_water`, `thunderstorm`), reconstructed directly from Section 9 of Athir's executed Colab notebook. Each loop uses a generated 10-second seed audio segment; it is *not* 60 seconds of independently generated diffusion output.
- Six actual **10-second LoRA A/B audio recordings** from the notebook's prompt tests: two prompts (`heavy and strong rain`, `rain nice sound`) × the Original, Intensity, Comfort models. These are *previously generated examples*; playback does not run the model.
- Functional Web UI, prompt builder, audio preview, server-side mixing, download of mixed audio, upload and analysis route for user photos, and a model availability indicator.
- Ready-to-connect cloud CPU image classification (`models/scene_mobilenetv3.onnx` + metadata, exported from `models/scene_mobilenetv3.pt`) and ready-to-connect live AudioLDM2 + LoRA pipeline (`models/audio/lora_adapters.pt`), with **honest gating** if the checkpoints/GPU are absent.

## Start the studio (Mac / Windows / Linux)

From a terminal in this folder:

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000 in your browser. **Do not open `frontend/index.html` by itself**; it relies on the FastAPI backend. Mac users can double-click `start_mac.command` after granting execution permission, or run `bash start_mac.command`.

First try **Listen to the nature**: all five players should work immediately. Then compare the original and fine-tuned audio recordings, and press **Mix available WAV layers**. A forest example image is supplied. On the CPU cloud build, scene understanding uses an exported ONNX checkpoint if one is installed; otherwise choose the scene manually.

## Enable live AI generation and your trained vision model

**See [RUN_GPU.md](RUN_GPU.md).** Get `lora_adapters.pt` from Athir's Colab Section 17; it is **not embedded in the shared notebook**. Get `scene_mobilenetv3.pt` from your own Colab export for trained CV predictions. Then run the app with a CUDA GPU and the extra audio dependencies. A Colab launcher notebook is included.

## Important interpretation

The audio LoRA training is real, but the shared quantitative results **do not yet prove better audible intensity control or comfort**. The original and both adapters are available for controlled listening tests. Image classification based only on scene labels cannot prove that rain, wind or thunder actually occurs in a still picture.

## File layout

- `app/`: FastAPI endpoints, scene analysis, audio prompt builder, real audio WAV mixing, optional lazy AudioLDM2 + LoRA GPU inference.
- `frontend/`: responsive web studio, comparisons, generated audio controls, example forest image.
- `assets/audio/*.wav`: genuine 60-second export files from Athir's notebook.
- `assets/audio/comparisons/`: real original-vs-LoRA notebook samples; filenames map to known prompts.
- `models/`: checkpoint destinations for vision and audio.
- `notebooks/`: CV full training notebook and optional Colab web launcher.
- `tests/`: API, sample WAV integrity, mixing, checkpoint wrapper test.
- `AUDIO_NOTEBOOK_FINDINGS.md`: research review and adapter results.
- `RUN_GPU.md`: checkpoint retrieval and live audio inference instructions.

## Tests

```bash
python -m pip install pytest httpx
python -m pytest -q tests
node --check frontend/app.js
```

## Limits / rights

The AudioLDM2 checkpoint is reported as CC BY-NC-SA 4.0 and ESC-50 is noncommercial; do not assume this project can be monetized. Check sources and provenance before redistribution or commercial use. Uploaded screenshots and sample images are demonstration materials. The platform is a local research prototype, **not** a production cloud service with authentication or job scheduling.
