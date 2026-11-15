# Generate brand-new AudioLDM 2 sounds with Athir's adapter

This stage is optional. **The project already plays the five real generated 60-second WAV layers and six genuine A/B examples without a GPU**. New sound generation needs a CUDA-enabled Python process with the model downloaded, not just WAV outputs.

## A. Retrieve the actual adapter checkpoint from Colab

The uploaded `.ipynb` contains the *training code, metrics and several inline audio players*, but does **not** contain the learned 12.91 MB `lora_adapters.pt` checkpoint bytes. In **Athir's original Colab session**, after her Section 17 save cell executes:

```python
from google.colab import files
files.download('soundscape_export/extra/lora_adapters.pt')
```

Put that download at `models/audio/lora_adapters.pt` inside this project (create the `audio` folder if necessary). If the original Colab runtime was deleted and the file was not saved, the training must be run again to re-export it.

Likewise, to use your actual fine-tuned **computer vision** classifier rather than the CLIP suggestion, put your Colab export at `models/scene_mobilenetv3.pt`. No CV weights were provided in these uploaded notebooks.

## B. Start studio with actual GPU inference

On Colab or another machine with an NVIDIA CUDA GPU, from project root:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-gpu.txt
export SOUNDSCAPE_ENABLE_GPU_AUDIO=1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If pip updates packages already loaded in a live notebook runtime, restart the notebook's Python runtime once before importing the model. Colab's T4 GPU was sufficient for the teammate's AudioLDM 2 pipeline; it has **not** been verified with this separate FastAPI-serving process. An Internet connection is required to download pretrained AudioLDM 2 weights the first time.

In Colab, use the included `notebooks/Launch_Studio_Colab.ipynb` to upload the ZIP and optional checkpoints. The browser connection uses Colab's port-proxy UI, and its behavior can vary with Colab updates.

Once enabled, Studio lets the user choose `Original`, `Fine-tuned: Intensity`, or `Fine-tuned: Comfort`, and click Generate. The API loads the diffusion pipeline lazily and keeps it cached between requests; access is serialized so adapters never race.

**The adapters are alternatives, not composable**: the original notebook did not train a combined (`joint`) adapter. Selecting Comfort does not automatically apply the Intensity LoRA too.

## C. What is and is not established

Athir's notebook confirms real LoRA parameter updates (192 cross-attention layers, about 1.585M trainable parameters, 150 steps per adapter) and reduced held-out denoising MSE: **4.54% intensity**, **3.96% comfort**. However, her control-direction test improved **0 out of 5 categories** compared to the original baseline (both 4/5), and her calm-vs-harsh surrogate metric did not consistently show the desired trend. Those adapters are experimental until multiple-seed listening and objective tests establish perceptual benefit. Thus the platform exposes *which model produced each audio* rather than calling the adapter "better".

## D. Security and licensing

Use this only on trusted local/Colab workspaces. It loads checkpoint tensors with `torch.load(weights_only=True)`, but machine-learning checkpoint files are still untrusted inputs; never load an unknown file. Do not deploy the GPU endpoint publicly without authentication, request limits, job queueing, rate controls, and safeguards against huge requests. The current source model and ESC-50 have non-commercial license restrictions; verify terms before commercial use.
