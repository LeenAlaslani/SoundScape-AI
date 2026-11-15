# Connect your CV checkpoint, then enable real GPU generation

## CV: no retraining required if your checkpoint exists
1. Open `notebooks/SoundScape_Connect_CV_To_Render.ipynb` in Colab. Run it on CPU; upload the genuine `scene_mobilenetv3.pt` or your saved `SoundScape_CV_Final_Artifacts.zip`. This file was produced by your own completed notebook, not from the PDF report.
2. The notebook converts it to ONNX, **compares logits** against PyTorch, and downloads `SoundScape_CV_Render_Files.zip`.
3. Unzip `SoundScape_CV_Render_Files.zip` on your Mac. Copy the contained `models/` directory into the **root of your local Git clone**, e.g. `~/Desktop/SoundScape_Deploy/models/`.
4. From your clone, `git add models && git commit -m "Connect trained scene classifier" && git push origin main`. Render auto-deploys.
5. Open `https://soundscape-ai-studio.onrender.com/api/status`. The `vision` field must be `onnx_trained_cpu_model_ready`. At the site, upload a forest/sea image and click **Analyze**.

Do not upload personal training datasets; keep checkpoint `.pt` local (the web server only needs `.onnx` and `.json`). On your public GitHub repository, exported model weights are public. Respect photo/audio/model licensing.

## GPU generation: deploy separate Hugging Face ZeroGPU Space
1. Create a **new Hugging Face account/Space** if needed. The free ZeroGPU hosting eligibility requires a verified account in good standing older than 30 days; check current Hugging Face documentation. **Do not assume this is instantly free on a new account.**
2. Create a **Gradio Space**, then upload the *contents* of `hf_zerogpu_space/` to that Space's root and select ZeroGPU hardware in its Settings. This code is a prepared starter, **not yet executed on real ZeroGPU hardware**. The first model download is several GB and version compatibility must be tested.
3. Confirm the Space itself generates a WAV with `Original AudioLDM 2`. Save the exact `username/space-name`.
4. In the Render service's **Environment** settings, add `SOUNDSCAPE_GRADIO_SPACE=username/space-name` and redeploy. You can then use Generate from SoundScape after the Space is reachable. The public site proxies the request without hosting PyTorch.
5. This starter **does not** include Athir's `lora_adapters.pt`; the Intensity and Comfort choices remain disabled. To activate those models you need the actual adapter weights and a separately tested LoRA inference integration.

**Do not expose Hugging Face tokens in the public GitHub repository or frontend JS.** Limit public access while experimenting because ZeroGPU uses per-user quota and can queue requests.
