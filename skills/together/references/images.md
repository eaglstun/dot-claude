# Together — image generation

> **Script:** `scripts/images.py "prompt" -o out.png [--model --width --height]` wraps this endpoint (downloads + embeds provenance).

Endpoint: `POST https://api.together.ai/v1/images/generations`. Pricing is per megapixel of output unless noted.

```bash
curl -sS https://api.together.ai/v1/images/generations \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "black-forest-labs/FLUX.1-schnell",
    "prompt": "A serene mountain landscape at sunset",
    "width": 1024, "height": 1024, "steps": 4, "n": 1
  }' | jq -r '.data[0].url'
```

Response gives an image URL (default) or base64 if `response_format: "base64"`.

## Serverless models

| Model                                      | $/MP    | Notes                                                              |
| ------------------------------------------ | ------- | ------------------------------------------------------------------ |
| `black-forest-labs/FLUX.1-schnell`         | $0.0027 | **Default** — 4-step, fastest+cheapest FLUX, fine for most prompts |
| `black-forest-labs/FLUX.2-dev`             | $0.0154 | Newer FLUX.2 family, dev tier                                      |
| `black-forest-labs/FLUX.1.1-pro`           | $0.04   | Higher quality, slower                                             |
| `black-forest-labs/FLUX.1-kontext-pro`     | $0.04   | Editing — takes `image_url` for img2img / edits                    |
| `black-forest-labs/FLUX.1-kontext-max`     | $0.08   | Editing, highest quality tier                                      |
| `black-forest-labs/FLUX.2-max`             | $0.07   | Highest-quality FLUX.2                                             |
| `Qwen/Qwen-Image`                          | $0.0058 | Cheap alt, decent for prompts with text rendering                  |
| `ByteDance-Seed/Seedream-3.0`              | $0.018  | Strong on photoreal/stylized                                       |
| `google/imagen-4.0-fast`                   | $0.02   | Google's fast tier                                                 |
| `google/imagen-4.0-preview`                | $0.04   | Google's standard tier                                             |
| `stabilityai/stable-diffusion-xl-base-1.0` | $0.0019 | Classic SDXL — cheapest serious option                             |
| `Rundiffusion/Juggernaut-Lightning-Flux`   | $0.0017 | Cheapest FLUX-derived, lightning-tuned                             |

## Parameters

- `prompt` (required) — text description
- `width`, `height` — output size in pixels
- `n` — number of images (1–4)
- `steps` — diffusion steps (FLUX.1-schnell is fixed at 4; others 20–50)
- `seed` — int for reproducibility
- `negative_prompt` — string of things to avoid
- `guidance` — classifier-free guidance scale
- `response_format` — `"url"` (default) or `"base64"`
- `image_url` — input image for edit-capable models (FLUX.1-kontext-\*)
