# GPU inference options

Checked 18 November 2026 against provider documentation. No service was created and no paid compute was enabled.

- [Hugging Face ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu) is a shared, Gradio-only GPU option. Eligible free personal accounts may host two Spaces; access is subject to account eligibility, queueing and daily quotas. The documentation lists 5 minutes daily for free accounts and 2 minutes for unauthenticated users. Some paid tiers can automatically consume prepaid credits beyond quota, so inspect account billing settings before use. The existing Gradio bridge still needs an actual deployed Space, compatible model dependencies and an end-to-end test.
- [Hugging Face dedicated Spaces](https://huggingface.co/pricing) list T4 small at $0.40/hour and T4 medium at $0.60/hour at the time of review. These are billable; no deployment has been made.
- The notebook's Colab GPU path is suitable for a controlled research run but availability and limits vary. A notebook session is not an always-on production inference service.

The existing Render web service is configured for a free CPU runtime. No separately verified GPU endpoint or LoRA checkpoint is available to this project in the current environment. Model compatibility, capacity, audio quality, license suitability and true end-to-end generation must be verified before calling a backend production-ready.
