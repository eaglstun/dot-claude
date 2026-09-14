# black-forest-labs/flux-dev-lora

Model page: https://replicate.com/black-forest-labs/flux-dev-lora

FLUX.1 [dev] — Black Forest Labs' 12B-parameter transformer — with **full LoRA support baked into the official endpoint**. Accepts LoRAs from Replicate, Hugging Face, Civitai, or any `.safetensors` URL, and can stack **two** LoRAs via `lora_weights` + `extra_lora`.

Use this when you want high-quality Flux-Dev outputs and need a specific LoRA style/subject. See `references/loras.md` for broader LoRA concepts; this file covers the exact schema of _this_ model.

## Input schema

### Core

| Field                 | Type    | Required | Default | Description                                                                            |
| --------------------- | ------- | -------- | ------- | -------------------------------------------------------------------------------------- |
| `prompt`              | string  | ✅       | —       | Image description. Must include your LoRA's trigger word(s) for the style to activate. |
| `aspect_ratio`        | enum    |          | `"1:1"` | `1:1`, `16:9`, `21:9`, `3:2`, `2:3`, `4:5`, `5:4`, `3:4`, `4:3`, `9:16`, `9:21`.       |
| `num_outputs`         | integer |          | `1`     | 1–4.                                                                                   |
| `num_inference_steps` | integer |          | `28`    | 1–50. 28 is the default sweet spot; 40–50 for hero renders.                            |
| `guidance`            | number  |          | `3`     | 0–10. Classifier-free guidance. Flux Dev likes lower guidance (2–4) than SDXL.         |
| `megapixels`          | enum    |          | `"1"`   | `"1"` or `"0.25"`. Passed as a string.                                                 |
| `seed`                | integer |          | random  | For reproducibility — but see `go_fast` gotcha below.                                  |

### LoRAs

| Field               | Type            | Required | Default | Description                                                                                                                                                                               |
| ------------------- | --------------- | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lora_weights`      | string          |          | —       | Primary LoRA. Accepts Replicate slug `owner/name[:version]`, `huggingface.co/<owner>/<model>[/<file>.safetensors]`, `civitai.com/models/<id>[/<name>]`, or any direct `.safetensors` URL. |
| `lora_scale`        | number          |          | `1`     | -1 to 3. Sane range 0–1 for base mode; `go_fast` auto-applies a 1.5× multiplier internally.                                                                                               |
| `extra_lora`        | string          |          | —       | Second LoRA to stack. Same URL formats as `lora_weights`.                                                                                                                                 |
| `extra_lora_scale`  | number          |          | `1`     | Same range/behavior as `lora_scale`.                                                                                                                                                      |
| `hf_api_token`      | string (secret) |          | —       | For authenticated HuggingFace LoRAs.                                                                                                                                                      |
| `civitai_api_token` | string (secret) |          | —       | For authenticated Civitai LoRAs.                                                                                                                                                          |

### img2img

| Field             | Type         | Required | Default | Description                                                                                         |
| ----------------- | ------------ | -------- | ------- | --------------------------------------------------------------------------------------------------- |
| `image`           | string (URI) |          | —       | Input image for img2img. If set, output aspect ratio matches this image (overrides `aspect_ratio`). |
| `prompt_strength` | number       |          | `0.8`   | 0–1. 1.0 = fully re-generate; lower = preserve more of the input.                                   |

### Output / safety

| Field                    | Type    | Required | Default  | Description                   |
| ------------------------ | ------- | -------- | -------- | ----------------------------- |
| `output_format`          | enum    |          | `"webp"` | `webp`, `jpg`, `png`.         |
| `output_quality`         | integer |          | `80`     | 0–100. Ignored for `.png`.    |
| `disable_safety_checker` | boolean |          | `false`  | Standard default (filter on). |

### Perf

| Field     | Type    | Required | Default    | Description                                                                                                                                         |
| --------- | ------- | -------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `go_fast` | boolean |          | **`true`** | fp8 quantization + optimized attention + LoRA weight fusion. ⚠ Outputs become **non-deterministic even with `seed`**. Turn off for reproducibility. |

Local `image` path auto-uploaded by `run_model.py`.

## Output

An **array** of URIs (one per output, up to 4 depending on `num_outputs`). `run_model.py` saves each as `black-forest-labs_flux-dev-lora_0.webp`, `_1.webp`, etc.

## LoRA source formats

All valid for `lora_weights` and `extra_lora`:

| Source                     | Format                                                        | Example                                               |
| -------------------------- | ------------------------------------------------------------- | ----------------------------------------------------- |
| Replicate trained model    | `owner/name` or `owner/name:version_id`                       | `fofr/flux-pixar-cars`                                |
| Hugging Face               | `huggingface.co/<owner>/<repo>`                               | `huggingface.co/alvdansen/flux-koda`                  |
| Hugging Face specific file | `huggingface.co/<owner>/<repo>/<file>.safetensors`            | `huggingface.co/alvdansen/flux-koda/koda.safetensors` |
| Civitai                    | `civitai.com/models/<id>` or `civitai.com/models/<id>/<slug>` | `civitai.com/models/123456/my-lora`                   |
| Direct URL                 | Any signed or public `.safetensors` URL                       | `https://example.com/path/to/model.safetensors`       |

For Civitai — right-click the download link on the LoRA's page and "Copy Link Address" to get the proper URL. Gated Civitai LoRAs need `civitai_api_token`; gated HF repos need `hf_api_token`.

## Examples

**Single LoRA from Replicate:**

```bash
python scripts/run_model.py black-forest-labs/flux-dev-lora \
    --input '{
      "prompt": "a retro diner interior in pixar cars style, cinematic lighting",
      "lora_weights": "fofr/flux-pixar-cars",
      "lora_scale": 1.0,
      "aspect_ratio": "16:9",
      "num_outputs": 2
    }' \
    --output ./out/
```

**Stack two LoRAs (character + style):**

```bash
python scripts/run_model.py black-forest-labs/flux-dev-lora \
    --input '{
      "prompt": "ZIKI the man at a beach, MSMRB watercolor style",
      "lora_weights": "zeke/ziki-flux",
      "lora_scale": 1.0,
      "extra_lora": "jakedahn/flux-midsummer-blues",
      "extra_lora_scale": 1.0,
      "aspect_ratio": "3:2",
      "num_outputs": 4
    }' \
    --output ./out/
```

**Civitai LoRA via URL:**

```bash
python scripts/run_model.py black-forest-labs/flux-dev-lora \
    --input '{
      "prompt": "a noir detective in a rain-slick alley, neon signs reflecting in puddles",
      "lora_weights": "civitai.com/models/123456/noir-style-flux",
      "lora_scale": 0.9
    }' \
    --output ./out/
```

**Reproducible output (turn off go_fast, fix seed):**

```bash
python scripts/run_model.py black-forest-labs/flux-dev-lora \
    --input '{
      "prompt": "a serene lakeside temple at dawn",
      "seed": 42,
      "go_fast": false,
      "num_inference_steps": 40
    }' \
    --output ./out/
```

**img2img with a LoRA:**

```bash
python scripts/run_model.py black-forest-labs/flux-dev-lora \
    --input '{
      "prompt": "same scene but in MSMRB watercolor style",
      "image": "./photo.jpg",
      "prompt_strength": 0.65,
      "lora_weights": "jakedahn/flux-midsummer-blues",
      "lora_scale": 1.0
    }' \
    --output ./out/
```

## Tips

- **Always include the LoRA's trigger word(s)** in the prompt — each LoRA's page lists them. Without, the style may not activate.
- **Default `guidance: 3`** is right for Flux Dev. Pushing above 5 often produces "burnt" results.
- **Stacking scales:** start both at `1.0`. If the primary LoRA dominates, drop _its_ scale (not the other one's); makes balancing easier.
- **`num_inference_steps: 28`** is fine for most work. Bump to 40–50 only for a final pass on a winning seed — marginal quality gain, large time cost.
- **`megapixels`**: `"1"` (~1024×1024 equivalent) is the standard; `"0.25"` halves each side for faster iteration.
- **Cached LoRA loading**: first use of a given LoRA URL is slow (downloads weights); subsequent calls with the same LoRA are faster.

## Gotchas

- **`go_fast: true` (default) makes outputs non-deterministic even with `seed` set.** If you need reproducibility (A/B tests, retrieval), set `go_fast: false`.
- **`lora_scale` behaves differently with `go_fast`.** The internal 1.5× multiplier means a `lora_scale: 1.0` under `go_fast` is roughly equivalent to `1.5` under base inference. Experiment.
- **Flux Dev LoRAs only.** SDXL, Pony, Illustrious, etc. LoRAs won't work. If a LoRA's page says "Base: SDXL" or "Base: Pony", pick a different model.
- **Output is a list, not a single file.** If you `num_outputs: 1`, you still get a one-element array. `run_model.py` handles this correctly — saved as `_0.webp`.
- **`megapixels` is an enum of strings** — `"1"` not `1`. JSON type matters.
- **Licensing:** images generated on Replicate can be used commercially, but downloading the weights for self-host has additional restrictions. Check BFL's license.
