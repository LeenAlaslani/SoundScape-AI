# Evaluation and release status

The historical AudioLDM 2 checkpoint and two LoRA experiments are preserved in Athir's notebook. The intensity evaluation reported matching light-to-heavy proxy direction in 4/5 classes for both the base model and intensity adapter on one seed. The training labels are automatically inferred acoustic proxies. No blinded listener results support a claim that either adapter improves relaxation or realism.

Six previously generated comparison WAVs were measured with `python scripts/evaluate_saved_audio.py` using `pyloudnorm` and four-times oversampling. See [saved_audio_metrics.csv](saved_audio_metrics.csv). The oversampled maximum is an estimate, not certified true peak. Integrated loudness and clipping checks are technical diagnostics, not human ratings.

The V2 notebook defines a paired model/seed grid, optional train-only-proxy experiment, Stable Audio Open pilot and distinct-segment assembly. Those experiments are not executed results. See [the V2 report](../../SoundScape_V2_Report.md) and [rating template](../../listening_ratings_template.csv). No new soundscape is recommended as better without blinded listening.

The UI's saved-layer previews are mixtures of existing WAVs, whose long-form sources repeat short generated material. Browser playback and comfort-gain behavior were tested locally; weather recognition and a live GPU generation request remain unverified.
