# Relaxation soundscape research

## Evidence and limits

SoundScape is a vision-guided audio system, not a medical intervention or a single vision-language model. Its intended experience is ASMR-inspired ambience; no generated file has been shown to induce ASMR or treat a condition.

- [Fan and Baharum (2024)](https://pubmed.ncbi.nlm.nih.gov/39285764/) systematically reviewed natural sound exposure versus quiet. Physiological outcomes differed for some measures, but perceived stress did not show a significant difference; results were inconsistent. These population-level findings do not validate this product or identify a universally relaxing waveform.
- [Zhu et al. (2024)](https://pubmed.ncbi.nlm.nih.gov/38373459/) reviewed natural sound exposure and health recovery. The range of contexts and measures limits direct transfer to synthetic audio delivered through unknown devices.
- [Poerio et al. (2018)](https://pubmed.ncbi.nlm.nih.gov/29924796/) studied ASMR experiences through online and laboratory experiments. ASMR responses vary between individuals; reported changes do not mean every listener or natural recording produces tingles or relaxation.
- [Saskovets et al. (2025)](https://mental.jmir.org/2025/1/e69120) reviewed 34 studies of sound interventions. Individual preferences, delivery and context mattered, and some studies found adverse responses; nonmusical sound evidence remains limited.
- [Hozaki et al. (2025)](https://pubmed.ncbi.nlm.nih.gov/40342555/) compared ASMR and nature videos. Both reduced pulse rate relative to rest in one experiment, but audiovisual conditions and individual differences prevent treating it as proof that generated nature audio is therapeutic.

## Engineering implications and tests

1. **Listener choice:** offer independently adjustable layers, presets, volume and stop controls. A preset is a starting point, not a clinical prescription. Test that controls change the requested mix and that zero-valued layers are absent.
2. **Avoid abrupt artifacts:** screen samples for clipping, short-window level jumps and join discontinuities. Ask listeners whether transients are distracting; no single threshold guarantees comfort. Test crossfades with both correlated and unrelated signals.
3. **Preserve dynamics:** avoid global loudness inflation or aggressive denoising. Comfort mode lowers preview gain and alters the generation request; this is an engineering choice, not evidence of perceived comfort. Compare level-matched and user-adjustable A/B samples before claiming benefit.
4. **Continuity:** create independent segments where model resources allow; do not label repeated audio as fresh generation. Record segment seeds, overlap, length and transitions, and rate repetition in long listening tests.
5. **Spectral quality:** inspect spectrograms and listen for tonal or metallic artifacts. Spectral centroid is descriptive, not a validated universal harshness or comfort score. Do not remove high frequencies automatically.
6. **Spatial audio:** stereo or binaural rendering is an optional hypothesis. Compare on appropriate playback devices and test mono compatibility before recommending it. The existing AudioLDM 2 export is mono.
7. **Blinded evaluation:** use paired prompts and seeds within the same model, randomize presentation order and hide model identity. Collect naturalness, category match, comfort, artifact and continuity ratings from multiple listeners; predefine exclusions and report uncertainty. Do not use objective metrics or denoising loss as a substitute.

## Current evidence

The preserved notebook records a single-seed comparison in which the intensity adapter and original each matched the intended direction in four of five categories. The feature-derived labels are not human comfort or intensity annotations. No V2 listening study, alternative-model comparison, or new GPU inference has been completed; no model is selected as perceptually superior.
