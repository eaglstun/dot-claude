# levelsio/lomography

Model page: <https://replicate.com/levelsio/lomography>

**Lomography film-effect stylization** — a Flux-dev LoRA fine-tune by Pieter Levels (`levelsio`, the solo-dev "shipper" behind Nomad List / PhotoAI) that applies the analog Lomo aesthetic: saturated colors, heavy vignetting, light leaks, cross-processed color shifts, soft focus, high contrast, and the occasional fisheye distortion. It's a thin, single-purpose LoRA wrapper around `black-forest-labs/flux-dev` (the standard Replicate flux-lora-trainer template), not an enterprise pipeline — best understood as one tool in his own product stack that he happens to publish publicly.

## When to pick it over alternatives

- **Pick it over a Photoshop / VSCO / Lightroom Lomo preset** when you want the AI to _reinterpret_ the scene — re-lighting, adding plausible film grain texture, exaggerating bokeh — rather than a deterministic LUT/curve overlay. Trade-off: AI may shift fine details you wanted preserved.
- **Pick it over rolling your own LoRA on `black-forest-labs/flux-dev-lora`** when you don't want to source weights, hunt for a trigger word, or pick `lora_scale` defaults — this model has all of that baked in (trigger word `TOK lomography` from the original training run).
- **Pick `fofr/kontext-ps1` instead** for a different nostalgic aesthetic — PS1 is low-poly 90s 3D-game look (chunky textures, vertex jitter); `lomography` is analog-film toy-camera look (light leaks, saturated grain). Different decades, different mediums.
- **Sweet spot:** batch-styling a photo library or product shots with a consistent retro-film look, or quick single-image stylization for social posts. Less ideal when you need pixel-faithful output of the input — this is a generative re-render, not a filter pass.

## Input schema

This is a fully-loaded Flux-dev LoRA inference template — every Flux-LoRA knob is exposed.

| Field                    | Type         | Required | Default  | Description                                                                                                                                                                              |
| ------------------------ | ------------ | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                 | string       | yes      | —        | Text prompt. **Include the trigger phrase `TOK lomography`** to activate the trained style (see Gotchas).                                                                                |
| `image`                  | string (URI) |          | —        | Input image for img2img / stylization. If omitted, runs in pure txt2img mode (generates a Lomo-style image from the prompt). Local paths are auto-uploaded by `run_model.py`.            |
| `mask`                   | string (URI) |          | —        | Inpainting mask. White areas regenerated, black preserved. Requires `image`. Disables `aspect_ratio` / `width` / `height`.                                                               |
| `aspect_ratio`           | enum         |          | `"1:1"`  | One of the standard Flux ratios (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`, etc.) or `"custom"` to use `width`/`height`. Ignored when `image` is set.                                  |
| `height`                 | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest multiple of 16. Incompatible with `go_fast`.                                                                        |
| `width`                  | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest multiple of 16. Incompatible with `go_fast`.                                                                        |
| `prompt_strength`        | number       |          | `0.8`    | **The img2img tuning knob.** 0.0 = preserve input exactly (no effect), 1.0 = full destruction of input information. `0.7–0.85` is the Lomo sweet spot.                                   |
| `model`                  | enum         |          | `"dev"`  | `"dev"` (28 steps, best quality) or `"schnell"` (4 steps, fast/cheap).                                                                                                                   |
| `num_outputs`            | integer      |          | `1`      | 1–4. Cheap way to grab variations at one seed.                                                                                                                                           |
| `num_inference_steps`    | integer      |          | `28`     | 1–50. 28 is right for `dev`; drop to 4 for `schnell`.                                                                                                                                    |
| `guidance_scale`         | number       |          | `3`      | 0–10. Flux likes low values — 2.5–3.5 is the band. Higher = more prompt-literal but less photographic.                                                                                   |
| `seed`                   | integer      |          | random   | Set for reproducibility.                                                                                                                                                                 |
| `output_format`          | enum         |          | `"webp"` | `"webp"`, `"jpg"`, or `"png"`.                                                                                                                                                           |
| `output_quality`         | integer      |          | `80`     | 0–100. Ignored for PNG.                                                                                                                                                                  |
| `disable_safety_checker` | boolean      |          | `false`  | Disable NSFW filter.                                                                                                                                                                     |
| `go_fast`                | boolean      |          | `false`  | fp8-quantized fast path. Faster + cheaper, slight quality loss. Incompatible with custom `width`/`height`.                                                                               |
| `megapixels`             | enum         |          | `"1"`    | Approximate output size — `"1"` (~1MP) or `"0.25"` (~0.25MP). Ignored when `width`/`height` set or `image` provided.                                                                     |
| `lora_scale`             | number       |          | `1`      | -1 to 3. **The effect-strength knob.** How strongly the Lomo LoRA is applied. 0 = none, 1 = trained strength, >1 = exaggerated. With `go_fast` Replicate auto-applies a 1.5x multiplier. |
| `replicate_weights`      | string       |          | —        | Override the main LoRA. Rarely useful here — the whole point of this model is its baked-in weights.                                                                                      |
| `extra_lora`             | string       |          | —        | Stack a second LoRA on top (Replicate slug, HuggingFace URL, CivitAI URL, or `.safetensors` URL). E.g. add a face LoRA for portraits.                                                    |
| `extra_lora_scale`       | number       |          | `1`      | -1 to 3. Strength of the stacked LoRA.                                                                                                                                                   |

## Output

An **array of URI strings** (length = `num_outputs`). With the default `num_outputs: 1` you get a one-element list. `run_model.py` saves them as `levelsio_lomography_0.<ext>` (and `_1.<ext>`, `_2.<ext>`, ... when `num_outputs > 1`). Extension follows `output_format` — default `.webp`.

## Pricing

**~$0.029 per run** on Nvidia H100 — roughly **34 runs per $1**. Predictions typically complete in **~19 seconds** at default settings. Drop to `model: "schnell"` + `go_fast: true` for cheaper/faster iteration; bump `num_inference_steps` and use `dev` for final renders.

## Examples

**Portrait → Lomo stylization** (img2img on an existing photo). Note the trigger phrase `TOK lomography` in the prompt:

```bash
python scripts/run_model.py levelsio/lomography \
    --input '{
      "prompt": "Portrait of a woman in a vintage cafe, in the style of TOK lomography, saturated colors, vignette, light leaks, soft focus, analog film grain",
      "image": "./portrait.jpg",
      "prompt_strength": 0.75,
      "lora_scale": 1.0,
      "guidance_scale": 3.0,
      "num_inference_steps": 28,
      "output_format": "jpg",
      "output_quality": 90
    }' \
    --output ./out/
```

**Landscape txt2img with fisheye flair** (no input image — pure generation in the Lomo style):

```bash
python scripts/run_model.py levelsio/lomography \
    --input '{
      "prompt": "Photo of a coastal cliff at golden hour, dramatic clouds, in the style of TOK lomography fisheye, heavy vignette, cross-processed colors, high contrast",
      "aspect_ratio": "16:9",
      "lora_scale": 1.1,
      "guidance_scale": 3.5,
      "num_inference_steps": 28,
      "seed": 42
    }' \
    --output ./out/
```

**Batch variant sweep** (4 outputs at one seed, fast mode for cheap iteration):

```bash
python scripts/run_model.py levelsio/lomography \
    --input '{
      "prompt": "Street market in Tokyo at night, neon reflections, in the style of TOK lomography, light leaks, motion blur, saturated reds and greens",
      "image": "./street.jpg",
      "prompt_strength": 0.8,
      "num_outputs": 4,
      "lora_scale": 1.0,
      "model": "dev",
      "go_fast": true,
      "output_format": "webp"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Saturated, contrasty, vignetted analog-film aesthetic in one call — no LoRA hunting / weight-merging required.
- Both txt2img (generate Lomo-style scenes from scratch) and img2img (stylize an existing photo) in the same endpoint.
- Stacking with a second LoRA via `extra_lora` — useful for "Lomo + face LoRA" or "Lomo + costume LoRA" combinations.
- Cheap enough (~$0.03) for batch runs over a photo library; fast enough (~19s) for interactive iteration.

**Gotchas:**

- **Trigger phrase required.** This is a `TOK`-trained Flux LoRA (the default Replicate flux-lora-trainer instance token). The default example uses `"in the style of TOK lomography fisheye"` — without `TOK lomography` (or at minimum the word `lomography`) in the prompt the LoRA barely activates and you get plain Flux output. Drop the trigger phrase _into_ a natural prompt rather than appending it as an afterthought.
- **`lora_scale` is the effect-strength knob.** Default `1.0` matches training intensity. Bump to `1.1–1.4` for more aggressive vignetting / saturation; drop to `0.6–0.8` if the look is overcooked. Above ~1.6 the image starts to fall apart (over-saturated, washed-out highlights, broken composition). With `go_fast: true`, Replicate silently multiplies your `lora_scale` by 1.5 — adjust accordingly.
- **`prompt_strength` is the second tuning knob (img2img only).** 0.6–0.7 keeps the input recognizable with a film tint; 0.8–0.9 lets the Lomo aesthetic take over and re-render textures. Above ~0.9 the model invents new content and stops resembling the input photo.
- **Faces can drift / distort.** Lomo aesthetics include heavy grain, vignette, and soft focus — combined with Flux's known face-identity instability under LoRAs, this means **portrait identity is not reliably preserved**. For "make this person look like a Lomo photo of them," lower `prompt_strength` (0.55–0.7) or stack a face/identity LoRA via `extra_lora`. Don't use this for tasks requiring strict face fidelity (ID photos, recognizable portraits of named subjects).
- **Max input/output resolution is 1440 on either axis** (Flux-dev limit). For larger outputs, run this then chain into a dedicated upscaler (`fermatresearch/magic-image-refiner`, `topazlabs/image-upscale`, etc.).
- **Output format defaults to webp.** Switch to `"jpg"` or `"png"` if your downstream tooling doesn't handle webp, or set `output_quality: 90+` for archival-quality jpg.
- **No README on the model page.** This is a `levelsio` publish-and-move-on LoRA — schema is the source of truth. Don't expect docs/changelog.
- **`go_fast: true` is incompatible with custom `width`/`height`.** If you set `aspect_ratio: "custom"`, leave `go_fast` off (or vice versa) — the runtime silently falls back otherwise.
- **Output is an array**, not a single string — index `[0]` when wiring the response.
