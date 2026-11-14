# SoundScape AI: Nature Generator

This notebook audits ESC-50 and configures pretrained AudioLDM 2 for text-to-audio inference, candidate review, looping, and PCM WAV export. It is a research prototype. It has not been demonstrated to produce acceptable soundscapes in the current environment.

## Run on Google Colab

1. Upload `SoundScape_Nature_Production.ipynb` to Google Colab and select Runtime > Change runtime type > GPU (a high-memory GPU is recommended).
2. Run cells in order. The first cell installs dependencies; restart the runtime and rerun if Colab reports an import conflict. The notebook downloads ESC-50 and the pinned AudioLDM 2 checkpoint. The checkpoint is several gigabytes; allow sufficient disk, memory, and download time.
3. Listen to references and every generated candidate. Set `REVIEWED_SEEDS` before rerunning the export cells. Technical ranking is only a fallback, not a quality judgment. Inspect repeated joins, comfort, naturalness, and category accuracy before using any output.
4. Download `soundscape_nature_platform_export.zip`. Record listening decisions and runtime outputs separately; the manifest conservatively marks listening review as not recorded.

## Integration contract

`generate_nature_audio(category, duration_seconds, seed=None)` requires the loaded pipeline and accepts `rain`, `sea_waves`, `wind`, `pouring_water`, or `thunderstorm`; supported call duration is 1-10 seconds. It returns `(waveform, metadata)`: a mono float32 NumPy array at 16 kHz and a dictionary of generation parameters. It performs real model inference and may fail for missing memory, dependencies, weights, or network access. A fixed seed does not guarantee identical audio across hardware and library versions.

The batch export writes 60-second, mono, 16 kHz PCM16 WAV files, a JSON manifest with relative WAV paths and model provenance, and CSV quality reports. Each layer is created by processing and repeating a short generated clip; this does not generate new audio content. Treat its loop quality as unverified until heard. Apply independent linear gains to each layer, allow headroom, and avoid clipping the sum. Peak control on the sum can alter relative overall loudness. RMS dBFS is not integrated LUFS. Retain the manifest alongside the files and validate the files before ingesting them.

## Results recorded locally

- The ESC-50 metadata contained 200 selected clips, 40 per class, and 145 distinct source identifiers; no identifier crossed the dataset folds. Metadata checks do not establish absence of near duplicates or pretraining leakage.
- All 200 original WAV files were read: all were mono 44.1 kHz PCM16 and five seconds long. All file hashes were unique. Thirty-three contained at least one sample at or above 0.999 full scale; that flags review and does not prove audible clipping. No file had overall RMS below 0.001. These checks do not establish perceptual quality.
- Four signal-processing tests passed using synthetic test fixtures, including a WAV round trip. No generated audio is implied by those tests.
- Local real model inference, generated WAVs, perceptual listening, and fine-tuning are not verified. The host has an Apple GPU but no CUDA GPU; pretrained weights were not available locally. Dependency and model downloads are required. The Colab workflow is provided for that execution and has not been verified end to end here.

## Licensing and model choice

The selected [AudioLDM 2 checkpoint](https://huggingface.co/cvssp/audioldm2) is CC BY-NC-SA 4.0, a significant restriction for commercial use. [ESC-50](https://github.com/karolpiczak/ESC-50) is generally CC BY-NC, with an identified CC BY subset; review attribution and individual source terms. FSD50K is a possible larger source, but it has not been acquired or assessed here. Dataset and checkpoint licenses must be reviewed before use or distribution.

The notebook uses pretrained inference. There is no training or fine-tuning result. A useful adaptation experiment requires suitable licensed audio with captions, a source-disjoint validation and test set, adequate GPU resources, and a comparison against the frozen baseline using blinded listening. No evidence currently shows that fine-tuning would improve this task.

## Tests

Run `python test_notebook.py` with NumPy installed. These tests exercise notebook-defined mastering, loop and mixer validation functions and the standard-library WAV reader. The notebook contains additional checks that run in Colab; passing tests do not establish audio quality.
