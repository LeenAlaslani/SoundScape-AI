# Review of Athir's `SoundScape_AI_Project(1).ipynb`

## Verified from executed notebook

1. ESC-50 reference dataset: 200 examples across 5 classes (40 each), group splits 120 training, 40 validation, 40 held-out test. Features and EDA include RMS, centroid, crest factor, dynamic range, padding and clipping checks.
2. Pretrained model `cvssp/audioldm2`, pinned revision `c8e7e189d324425c05c4c2f81214041ef4107983`; AudioLDM2 pipeline runs on Colab's 14.56GiB T4. The notebook fixed the GPT2Model vs GPT2LMHeadModel interface mismatch in its pipeline.
3. Genuine generation of 10 10-second candidates, with two per category, and export of five 60-second looped WAVs, plus a demo mixer. These outputs are embedded in the notebook and shipped here.
4. Two separate plain-PyTorch LoRA adapters, named `intensity` and `comfort`. Cross-attention (`attn2`) on 192 Linear layers, rank 8, **1,585,152 trainable parameters**. Trained 150 gradient steps each. Training captions and target labels were **heuristically auto-labeled from ESC-50 audio properties**, not hand-validated perceptual labels.
5. Held-out denoising MSE improved after LoRA: intensity 0.0552 → 0.0526 (−4.54%), comfort 0.0548 → 0.0527 (−3.96%). No user listening evaluation was recorded.
6. 'Heavy minus light' generated loudness moves in intended direction for 4/5 classes with Intensity LoRA **and** 4/5 with original: no aggregate directional gain. Thunderstorm LoRA reverses the expected sign. One seed was used in the reported generation tests.
7. The Comfort LoRA `calm` average surrogate harshness is **0.59** and its `harsh` average is **0.53**; original calm **0.51** and harsh **0.48**. That surrogate does not demonstrate that calm prompts sound more comfortable than harsh prompts. Objective metrics alone cannot establish human comfort.
8. Section 17 writes `soundscape_export/extra/lora_adapters.pt` (12.91MB), but the checkpoint file itself is **not embedded** in the uploaded notebook. All six A/B sample WAVs were embedded and extracted for this platform.

## Honest deployment decision

**Integrate previews and layering now** because they are real outputs and functioning assets. **Offer experimental LoRA generation only after the actual adapter weights are exported and CUDA inference is set up**. Do not call the fine-tuned models "better" in UI without stronger multi-seed listening and model-evaluation evidence. For a scientific report, also assess the heuristic auto-label validity: recording amplitude is not the same physical thing as sound intensity at the source, and a bright/spiky sound is not necessarily uncomfortable.

## Embedded audio extraction provenance

- Five final WAVs: notebook **cell 47** (players 1,3,5,7,9), from Section 9 generated ambient layer export (cell 44).
- Two original-vs-LoRA comparisons: notebook **cell 88** (outputs 1,3,5) prompt `heavy and strong rain`; **cell 89** (outputs 1,3,5) prompt `rain nice sound`.
- All sound files validated as mono PCM WAV at 16kHz and expected sample counts.
