# SoundScape AI — publish online without renting a GPU

The cloud preview is the **real FastAPI app**, with 5 authentic saved AudioLDM2 WAV layers, 6 LoRA example clips, live audio mixing and WAV downloads, plus prompt composition and upload UI. It **does not** generate new diffusion sounds on the free CPU host. This is intentional: users must not confuse playback of saved clips with novel inference.

## Deploy using a private GitHub repository (recommended for the project draft)

1. Check rights and licenses of the source image, checkpoint, samples and derived audio before placing the repository or website in public. `cvssp/audioldm2` is non-commercial; do not assume commercial permission.
2. Create a new **private GitHub repository**, then upload the contents of this directory **at its repository root**, not inside an extra folder. Include the `assets/audio/` WAV files. Do **not** upload personal credentials, Hugging Face tokens, or training data.
3. Visit https://dashboard.render.com/ and sign in. Choose **New → Blueprint** and connect this GitHub repo. Render reads `render.yaml` to create the FastAPI web service. Alternatively choose **New → Web Service** with:
   - Build command: `pip install -r requirements-cloud.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Python version: `3.11.11`
   - Free plan (if available)
4. Wait for deployment to succeed in Render's logs and open its generated `https://...onrender.com` URL.
5. Test: `/api/status`, WAV players, prompt builder, and mixing. Scene selection is manual until the trained vision ONNX artifacts are deployed; the Generate button remains disabled without GPU.
6. Future code edits: work on a development branch and merge to the deployment branch when tested. Render can auto-deploy new commits. Consider disabling auto-deploy if you want manual control.

**Render Free limits:** 512 MiB RAM; can spin down when idle; limited monthly bandwidth/build minutes and other restrictions. This configuration avoids heavyweight GPU and PyTorch installs to reduce memory needs; live cloud deploy has **not** been verified here. If the free host runs out of RAM, upgrade or move to a host with more memory. The publicly visible website does not provide authenticated uploads or per-user isolation; keep the site as a demo until adding those protections.

## Add YOUR trained Computer Vision model with CPU inference

After your final Colab training, obtain your *real* `scene_mobilenetv3.pt` checkpoint. In a Python environment with `torch`, `torchvision`, and `onnx` installed, run:

```bash
python scripts/export_scene_to_onnx.py path/to/scene_mobilenetv3.pt
```

This generates `models/scene_mobilenetv3.onnx` and `models/scene_mobilenetv3_metadata.json`. Upload both to your private GitHub repo and redeploy. **You do not need a GPU for hosted ONNX inference.** It is a *six-class scene classifier* (forest, sea, mountain, glacier, buildings, street), not a rain detector. Validate export predictions on sample images before reporting comparable metrics. Large files and host memory limits might require artifact storage or a larger service.

## Add new generative audio later

The source includes an optional GPU AudioLDM 2 module, separate from this CPU deployment. For genuine new 10-second audio, configure a GPU inference endpoint (on-demand GPU service) and your trusted LoRA checkpoint. Do not set `SOUNDSCAPE_ENABLE_GPU_AUDIO=1` on the Render CPU service; it has no CUDA. The current website **does not** call an external GPU endpoint yet. Creating one and wiring it to `/api/generate` is a separate integration step. On-demand is preferable to always-on rental for intermittent usage.

## Operations and privacy

The site uses no user login. Uploaded photos are processed as API inputs and not intentionally saved, but hosting logs and provider policies still matter. Consider abuse control/rate limiting, security review, timeouts, monitoring, protected admin endpoints, copyright attribution, and a privacy statement before public launch.
