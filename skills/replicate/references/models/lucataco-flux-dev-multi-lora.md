# lucataco/flux-dev-multi-lora

Model page: https://replicate.com/lucataco/flux-dev-multi-lora

Community Flux-Dev variant that stacks **up to 20 LoRAs at once** (vs. 2 on the official `black-forest-labs/flux-dev-lora`). Use this when you need to combine more than character+style — e.g. subject + style + film-emulation + aspect-ratio-fix LoRAs in a single generation.

**Cheap and fast:** ~$0.029/run, ~20s on H100. ~34 runs per dollar.

## Relationship to other Flux LoRA models

| Model                             | Max LoRAs | Go-Fast? | Best for                                     |
| --------------------------------- | --------- | -------- | -------------------------------------------- |
| `black-forest-labs/flux-dev-lora` | 2         | yes      | Official path, fp8 speed, two-LoRA workflows |
| `lucataco/flux-dev-multi-lora`    | **20**    | no       | Heavy stacking, LoRA-blending experiments    |
| `prunaai/flux.1-dev-lora`         | varies    | —        | 3× speed-up via Pruna optimization           |

See `references/loras.md` for LoRA fundamentals; this file only covers this model's specific schema and quirks.

## Input schema

### LoRAs (the whole point of this model)

| Field         | Type             | Required | Default   | Description                                                                    |
| ------------- | ---------------- | -------- | --------- | ------------------------------------------------------------------------------ |
| `hf_loras`    | array of strings |          | —         | Up to 20 LoRA sources. See formats below.                                      |
| `lora_scales` | array of numbers |          | all `0.8` | One scale **per LoRA, in the same order**. If you pass N LoRAs, pass N scales. |

**Ordering matters.** `lora_scales[i]` applies to `hf_loras[i]`. Miscounted arrays silently misapply scales — double-check length parity.

LoRA sources accepted (same as other Flux LoRA models):

- Replicate slug: `owner/name` or `owner/name:version_id`
- Hugging Face path: `alvdansen/frosting_lane_flux` (bare path works) or `huggingface.co/<owner>/<repo>`
- Civitai URL: `civitai.com/models/<id>`, or with token for gated: `https://civitai.com/api/download/models/<id>?token=<YOUR_CIVITAI_TOKEN>`
- Direct `.safetensors` URL

**No separate auth-token input.** For gated Civitai LoRAs, append `&token=<YOUR_CIVITAI_TOKEN>` to the URL. Gated HF repos similarly need the token embedded in the URL or require a public mirror.

### Core generation

| Field                 | Type    | Required | Default | Description                                                                                   |
| --------------------- | ------- | -------- | ------- | --------------------------------------------------------------------------------------------- |
| `prompt`              | string  | ✅       | —       | Must include **trigger words for every active LoRA** — e.g. `"a photo of TOK, sftsrv style"`. |
| `aspect_ratio`        | enum    |          | `"1:1"` | `1:1`, `16:9`, `21:9`, `3:2`, `2:3`, `4:5`, `5:4`, `3:4`, `4:3`, `9:16`, `9:21`.              |
| `num_outputs`         | integer |          | `1`     | 1–4.                                                                                          |
| `num_inference_steps` | integer |          | `28`    | 1–50.                                                                                         |
| `guidance_scale`      | number  |          | `3.5`   | 0–10. Note: **`guidance_scale`**, not `guidance` like BFL's model.                            |
| `seed`                | integer |          | random  | For reproducibility.                                                                          |

### img2img

| Field             | Type         | Required | Default | Description                                                      |
| ----------------- | ------------ | -------- | ------- | ---------------------------------------------------------------- |
| `image`           | string (URI) |          | —       | Input image for img2img. Output aspect ratio matches this image. |
| `prompt_strength` | number       |          | `0.8`   | 0–1. 1.0 = fully re-generate.                                    |

### Output / safety

| Field                    | Type    | Required | Default  | Description           |
| ------------------------ | ------- | -------- | -------- | --------------------- |
| `output_format`          | enum    |          | `"webp"` | `webp`, `jpg`, `png`. |
| `output_quality`         | integer |          | `80`     | 0–100.                |
| `disable_safety_checker` | boolean |          | `false`  | Standard default.     |

Local `image` path auto-uploaded by `run_model.py`.

## Output

Array of URIs (1–4 images). `run_model.py` saves as `lucataco_flux-dev-multi-lora_0.webp`, `_1.webp`, etc.

## Examples

**Single LoRA (matches BFL's model in behavior, but cheaper):**

```bash
python scripts/run_model.py lucataco/flux-dev-multi-lora \
    --input '{
      "prompt": "frstingln illustration of a cat napping in a sunlit window",
      "hf_loras": ["alvdansen/frosting_lane_flux"],
      "lora_scales": [0.9]
    }' \
    --output ./out/
```

**Stack three LoRAs (subject + style + detail enhancer):**

```bash
python scripts/run_model.py lucataco/flux-dev-multi-lora \
    --input '{
      "prompt": "a photo of TOK, sftsrv painterly style, ultra-detailed",
      "hf_loras": [
        "ostris/tok-man-flux",
        "alvdansen/softserve_anime",
        "fofr/flux-detail-enhancer"
      ],
      "lora_scales": [1.0, 0.85, 0.5],
      "aspect_ratio": "3:4",
      "num_outputs": 4
    }' \
    --output ./out/
```

**Civitai LoRA with token for gated content:**

```bash
python scripts/run_model.py lucataco/flux-dev-multi-lora \
    --input '{
      "prompt": "a detective in film-noir lighting, smoke-filled alley",
      "hf_loras": [
        "https://civitai.com/api/download/models/123456?token=YOUR_CIVITAI_TOKEN"
      ],
      "lora_scales": [0.9]
    }' \
    --output ./out/
```

**Bigger stack (5 LoRAs blending):**

```bash
python scripts/run_model.py lucataco/flux-dev-multi-lora \
    --input '{
      "prompt": "TOK the character, hlfcel anime shading, rtrfilm grain, glwngn neon accents",
      "hf_loras": [
        "ostris/tok-man-flux",
        "alvdansen/half-cel-flux",
        "fofr/flux-retro-film",
        "community/glowing-neon-flux",
        "fofr/flux-detail-enhancer"
      ],
      "lora_scales": [1.0, 0.8, 0.6, 0.7, 0.4],
      "guidance_scale": 3,
      "num_inference_steps": 32
    }' \
    --output ./out/
```

## Stacking strategy

Combining many LoRAs is an art — a few rules that generally work:

- **Keep one LoRA at ~1.0** as the primary anchor (usually the subject/character).
- **Secondary style LoRAs at 0.7–0.9** — too high and they overpower the subject.
- **Tertiary detail/enhancer LoRAs at 0.3–0.6** — additive rather than transformative.
- **Total "LoRA budget" ~3.0–4.0 summed** as a rough ceiling. Past that, the base model's behavior gets drowned out.
- **Activate every LoRA's trigger word in the prompt.** A LoRA without its trigger in the prompt contributes less, sometimes nothing.

The docs note that `guidance_scale: 2–5` enhances artistic styles and skin quality — this is a slightly lower range than the usual Flux default.

## Gotchas

- **`hf_loras` and `lora_scales` must have the same length.** Off-by-one silently misapplies scales.
- **Default `lora_scale: 0.8`** (not `1.0` like BFL's model). A direct copy of inputs that worked elsewhere at 1.0 will be slightly under-strength here — bump to 0.9–1.0 when porting.
- **Field is `guidance_scale`, not `guidance`.** Different from BFL's official model. 422 validation errors usually trace here when porting inputs.
- **No `go_fast` flag.** Runs at full bf16; tradeoff is determinism (seed works) for speed — if you need repeatability at higher throughput, this might actually be a feature.
- **Gated LoRAs need token embedded in URL.** No `civitai_api_token` / `hf_api_token` fields like the official model.
- **Commercial use:** fine on Replicate; self-hosted has restrictions (Flux Dev license).
- **No `megapixels` option** — you're stuck at the model's default resolution. For other sizes, use a different Flux endpoint.
