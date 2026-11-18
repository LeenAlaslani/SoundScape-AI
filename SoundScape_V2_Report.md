# SoundScape V2: findings and execution guide

## Scope and preservation

The supplied teammate notebook was confirmed as the original. The original copy is byte-identical to the supplied file (SHA-256 `398bb3fc5e673b9e0fde2226d3fbe07d9cb583e1de27219e91a77a836624d0b7`). All 93 original cells, source, comments, saved outputs and metadata are unchanged in V2; the V2 experiment is appended. The original interactive input loop must be skipped to reach the new section.

## Evidence from the original experiment

The notebook records AudioLDM 2 generation and two 150-step LoRA training runs, with 192 adapted layers and 1,585,152 trainable parameters. The saved output reports validation denoising loss decreasing from 0.0526 to 0.0506 for both runs. The original model and intensity adapter each produced the expected heavy-versus-light proxy direction in 4/5 categories for one seed. This does not demonstrate improved intensity or comfort. The saved adapter checkpoint was not embedded in the notebook; retraining or the trusted checkpoint is needed to run adapter inference again.

Intensity labels are class-wise RMS terciles, vulnerable to recording gain and mic distance; comfort labels are generated from brightness, crest factor and dynamic-range ranks rather than listener judgments. The original thresholds use all splits, leaking held-out distribution information into labels. Captions cannot guarantee sound-category or comfort fidelity. AudioLDM 2 is a 16 kHz model and can exhibit bandwidth limits; specific causes of audible defects require listening and comparison, not inference from these numbers alone. Repetition of a 10-second source is an established limitation of the original long-form exports.

## Checks performed

- All six saved original-versus-LoRA comparison WAVs and five existing 60-second exports were read. All are mono 16 kHz, with durations of 10 and 60 seconds respectively. No sample reached absolute 0.999 and no 100 ms RMS frame was below 0.001 in these files. The 60-second output RMS ranged from -28.02 to -21.05 dBFS. These checks do not establish realism or absence of audible artifacts.
- Three existing saved 10-second files for `heavy and strong rain` are supplied for listening. They come from the teammate's earlier run, not from V2 inference.
- The real comparison endpoint returned valid WAV data, the correct `audio/wav` MIME type and a working HTTP byte-range response. A browser `0:00` failure was not reproduced or diagnosed. Notebook players embed data URLs; no external file URL is needed for those saved outputs. Client/CSP or renderer issues remain possible, not proven.
- The ONNX scene model ran on the bundled forest example and returned `forest` with score 0.9985. One example is not a generalization test. Its six scene classes omit weather and its configured threshold is 0.0; the score should not be treated as evidence of weather or an out-of-distribution guarantee. No vision model was retrained.
- Twenty-two API, cloud-vision, remote bridge, playback and signal-quality tests passed. Synthetic arrays in tests are fixtures, not generated audio.

## What remains unverified

No new generative inference, alternative-model comparison, human listening study, revised LoRA training, or end-to-end GPU service test was completed in this environment. The host has 16 GB shared memory and the previously installed PyTorch reported CUDA and MPS unavailable; model weights and LoRA checkpoint were not cached. Network access and model access may differ in Colab. Better quality is a hypothesis, not an observed outcome. GPU memory for the alternative model and the full V2 notebook has not been measured.

## Running V2 in Colab

1. Upload the V2 notebook, choose a GPU runtime, and run the original cells in order through section 17. Skip the interactive prompt loop in original cell 89. If only the original model is needed, adapter training may be skipped, but initialize the adapter helpers and `adapter_states` used by V2.
2. Inspect original examples and confirm model/adapter licenses. Optionally enable `RUN_TRAIN_ONLY_PROXY_EXPERIMENT` to train a separate diagnostic adapter with train-derived thresholds. This does not validate the proxy labels. Turn on `RUN_V2_GRID` for matched baseline and available adapter comparisons; duration, prompt, seed and settings are recorded. The default grid is expensive. Inspect technical measurements and use blinded listening with multiple raters and seeds.
3. Optionally accept the access terms for Stable Audio Open and enable its pilot. Unload or restart between models if GPU memory is insufficient. The notebook records the downloaded revision. Compare paired prompts, not identical noise across different architectures.
4. Only after selecting a candidate by listening, enable `RUN_LONG_FORM`. Seven separately generated segments are crossfaded and trimmed to 60 seconds. Review every transition, overall dynamics and boundary; crossfading does not guarantee seamlessness. The manifest records seeds, settings, provenance, sample rate, format and SHA-256.
5. Reopen exported WAVs and independently confirm duration, levels, clipping and subjective quality before use. Record all listening outcomes and failures rather than assuming they pass.

## Platform contract and licensing

The existing web app automatically analyzes a supported scene, composes an artistic sound request and mixes saved layers. When generation is configured, the updated image flow also calls the existing local or remote GPU generation endpoint and exposes its returned WAV; the generated result remains unverified until the service actually runs. Scene classification does not detect weather. Users can select a desired sound, including rain or wind, but that selection is not presented as an observation. If generation is unavailable, the saved WAV preview remains usable.

The AudioLDM 2 checkpoint is [CC BY-NC-SA 4.0](https://huggingface.co/cvssp/audioldm2); [Stable Audio Open](https://huggingface.co/stabilityai/stable-audio-open-1.0) has its own access and commercial terms. Check all applicable model and source-audio licenses before deploying or redistributing generated material. Neither model is approved here for commercial use.
