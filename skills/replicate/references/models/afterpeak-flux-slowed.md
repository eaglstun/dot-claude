# afterpeak/flux-slowed

Model page: <https://replicate.com/afterpeak/flux-slowed>

**"Slowed + reverb" cover-art aesthetic** — a Flux-dev LoRA by `afterpeak` that reproduces the specific visual look used as thumbnail art on slowed/reverb/nightcore song edits flooding YouTube and TikTok: soft-lit, shallow-DoF, lightly-stylized portraits of attractive women, usually against plain walls or minimal backgrounds, with flattering skin, neutral-to-warm color grading, subtle film softness, and zero visible branding — the "aesthetic girl" selfie template that anonymous audio-only uploads use as a placeholder image. Despite the name, this is **not** a vaporwave / purple-tint / heavy-blur filter; the cover image and default example show a polished-but-plain portrait of a woman in a black top on a white wall, exactly the TikTok-audio-cover-art template. Trained on ~80 images at 512×512 (per the model page), heavily skewed toward female portraits, and the author's own note says the LoRA "performs best when generating women."

It's a thin, single-purpose LoRA wrapper around `black-forest-labs/flux-dev` — no novel pipeline, no README beyond the one-line description (which is typo'd: "arworks used for sowed versions of a song"). Treat it as a cosmetic / meme-adjacent tool, not a serious design primitive.

## When to pick it over alternatives

- **Pick it over generic Flux** when you specifically want the "anonymous slowed-song YouTube thumbnail" look — generic prompt-stuffing on `flux-dev` can get close but doesn't reproduce the particular flatness / framing / soft-portrait bias this LoRA bakes in.
- **Pick `levelsio/lomography` instead** if what you actually want is an obvious analog-film overlay (saturation, vignette, light leaks). `flux-slowed` is much more subtle — the stylization reads as "influencer selfie," not "filter was applied."
- **Pick `fofr/kontext-ps1` or similar** for overt, loud nostalgia aesthetics. `flux-slowed` is understated.
- **Pick a vaporwave-specific LoRA** (search CivitAI) if you want the purple-tinted-grid-sunset look commonly associated — misleadingly — with "slowed + reverb" music. This model is **not** that.
- **Sweet spot:** mock slowed-audio YouTube thumbnails, TikTok audio-visualizer placeholder art, meme covers for playlist edits, social posts parodying the genre's visual tropes. Niche, aesthetic-specific, mildly meme-coded.

## Input schema

Standard fully-loaded Flux-dev-LoRA inference template — every Flux-LoRA knob exposed.

| Field                    | Type         | Required | Default  | Description                                                                                                                                                                            |
| ------------------------ | ------------ | -------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                 | string       | yes      | —        | Text prompt. **Include the trigger word `SLOW3D`** to activate the trained style (see Gotchas). The default example starts with `"SLOW3D. A woman posing for a photo. ..."`.           |
| `image`                  | string (URI) |          | —        | Input image for img2img / stylization. If omitted, runs in pure txt2img mode. Local paths are auto-uploaded by `run_model.py`.                                                         |
| `mask`                   | string (URI) |          | —        | Inpainting mask. White = regenerate, black = preserve. Requires `image`. Disables `aspect_ratio` / `width` / `height`.                                                                 |
| `aspect_ratio`           | enum         |          | `"1:1"`  | Standard Flux ratios (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`, etc.) or `"custom"` to use `width` / `height`. Ignored when `image` is set.                                         |
| `height`                 | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest multiple of 16. Incompatible with `go_fast`.                                                                      |
| `width`                  | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest multiple of 16. Incompatible with `go_fast`.                                                                      |
| `prompt_strength`        | number       |          | `0.8`    | img2img tuning knob. 0.0 = preserve input exactly, 1.0 = full destruction. 0.7–0.85 is the usual sweet spot for stylization.                                                           |
| `model`                  | enum         |          | `"dev"`  | `"dev"` (28 steps, best quality) or `"schnell"` (4 steps, fast / cheap).                                                                                                               |
| `num_outputs`            | integer      |          | `1`      | 1–4 outputs per call.                                                                                                                                                                  |
| `num_inference_steps`    | integer      |          | `28`     | 1–50. 28 is right for `dev`; drop to 4 for `schnell`.                                                                                                                                  |
| `guidance_scale`         | number       |          | `3`      | 0–10. Flux likes low — 2.5–3.5 is the usable band. The default example uses `3.5`.                                                                                                     |
| `seed`                   | integer      |          | random   | Set for reproducibility.                                                                                                                                                               |
| `output_format`          | enum         |          | `"webp"` | `"webp"`, `"jpg"`, or `"png"`.                                                                                                                                                         |
| `output_quality`         | integer      |          | `80`     | 0–100. Ignored for PNG.                                                                                                                                                                |
| `disable_safety_checker` | boolean      |          | `false`  | Disable NSFW filter.                                                                                                                                                                   |
| `go_fast`                | boolean      |          | `false`  | fp8-quantized fast path. Faster + cheaper, slight quality loss. Incompatible with custom `width` / `height`.                                                                           |
| `megapixels`             | enum         |          | `"1"`    | `"1"` (~1MP) or `"0.25"` (~0.25MP). Ignored when `width` / `height` set or `image` provided.                                                                                           |
| `lora_scale`             | number       |          | `1`      | -1 to 3. Main effect-strength knob. **The default example uses `0.8`** — the author's tuned value. 1.0 is training intensity. With `go_fast` Replicate auto-applies a 1.5x multiplier. |
| `replicate_weights`      | string       |          | —        | Override the main LoRA. Rarely useful — overriding defeats the point of this endpoint.                                                                                                 |
| `extra_lora`             | string       |          | —        | Stack a second LoRA on top (Replicate slug, HuggingFace URL, CivitAI URL, or `.safetensors` URL).                                                                                      |
| `extra_lora_scale`       | number       |          | `1`      | -1 to 3. Strength of stacked LoRA.                                                                                                                                                     |

## Output

An **array of URI strings** (length = `num_outputs`). With the default `num_outputs: 1` you get a one-element list. `run_model.py` saves them as `afterpeak_flux-slowed_0.<ext>` (and `_1.<ext>`, `_2.<ext>`, ... when `num_outputs > 1`). Extension follows `output_format` — default `.webp`.

## Pricing

**~$0.045 per run** on Nvidia H100 — roughly **22 runs per $1**. Typical prediction time **~23–30 seconds** at default settings. Drop to `model: "schnell"` + `go_fast: true` for cheaper iteration; keep `dev` + 28 steps for finished covers. Confirm pricing at <https://replicate.com/afterpeak/flux-slowed> before batching.

## Examples

**1. Default-style portrait** (canonical "slowed-song cover" — woman, plain background, trigger word up front, author's recommended `lora_scale: 0.8`):

```bash
python scripts/run_model.py afterpeak/flux-slowed \
    --input '{
      "prompt": "SLOW3D. A woman posing for a photo. She is smiling wearing beautiful makeup with a black top. There is a white wall in the background.",
      "aspect_ratio": "1:1",
      "lora_scale": 0.8,
      "guidance_scale": 3.5,
      "num_inference_steps": 28,
      "output_format": "webp"
    }' \
    --output ./out/
```

**2. Mock YouTube thumbnail at 16:9** (wider aspect for a thumbnail, generate 3 variations at a fixed seed base):

```bash
python scripts/run_model.py afterpeak/flux-slowed \
    --input '{
      "prompt": "SLOW3D. A woman looking out a car window at night, soft streetlight glow on her face, neutral color grading, aesthetic cover art",
      "aspect_ratio": "16:9",
      "num_outputs": 3,
      "lora_scale": 0.8,
      "guidance_scale": 3.0,
      "num_inference_steps": 28,
      "output_format": "jpg",
      "output_quality": 90
    }' \
    --output ./out/
```

**3. img2img restyle** (take an existing portrait and push it toward the slowed-cover aesthetic — lower `prompt_strength` to preserve identity):

```bash
python scripts/run_model.py afterpeak/flux-slowed \
    --input '{
      "prompt": "SLOW3D. Portrait of a person, soft lighting, plain wall background, minimal styling, aesthetic cover-art framing",
      "image": "./portrait.jpg",
      "prompt_strength": 0.7,
      "lora_scale": 0.9,
      "guidance_scale": 3.0,
      "num_inference_steps": 28,
      "output_format": "png"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- One-call production of the specific "slowed-audio cover art" portrait look — soft-lit, shallow-DoF, plain background, flattering skin tones, the TikTok-visualizer template.
- Female portraits (the author explicitly notes this is where the LoRA performs best — training set skewed that way).
- Stacking with face / identity / costume LoRAs via `extra_lora` if you want specific features retained.

**Gotchas:**

- **Trigger word is `SLOW3D`** (note the `3`, not the letter E — it's the literal token `SLOW3D`). Without it the LoRA barely activates and you get plain Flux output. The default example puts it at the very start of the prompt as `"SLOW3D. ..."` — follow that pattern.
- **Not vaporwave, not "slowed + reverb" tint.** Despite the name, the actual trained aesthetic is understated portrait cover-art, not purple-haze / chopped-screw / vaporwave / dreamy-blur. If a user expects purple tint, grid sunsets, chromatic aberration, or "slowed to 80% + reverb" visual metaphors — they will be disappointed. This LoRA produces clean, polished, flatly-lit portraits that _happen_ to be the visual template used on slowed-song uploads.
- **Heavy female-portrait bias.** Trained on ~80 images at 512×512 (the defaults on the Replicate flux-lora-trainer), mostly of women. Male subjects, non-portrait compositions (landscapes, objects), and non-human subjects will activate the LoRA much more weakly or produce off-looking results. Don't use this as a general stylizer.
- **Low training resolution (512×512) on an 80-image dataset** means: narrow stylistic range, overfitting to the specific training-set composition (centered portrait, plain background), and noticeable quality drop on complex scenes or wide aspect ratios. The aesthetic is brittle — push too far outside portrait territory and the LoRA's influence fades fast.
- **`lora_scale` default is `1.0` in the schema, but the author's default example uses `0.8`.** Trust the example — 0.8 is the tuned value. 1.0 can over-apply the style and crunch features. Drop to 0.6–0.7 for subtler "hint of the aesthetic," raise to 1.0–1.1 for stronger commitment at the cost of over-smoothed skin and cookie-cutter faces.
- **Faces can drift / homogenize.** This is a cosmetic LoRA — it nudges toward a specific "look" (young, attractive, made-up, symmetric). Portrait identity is **not preserved**, and everyone tends to come out looking like the training-set average. Don't use for recognizable likenesses of named individuals.
- **`guidance_scale: 3.5` in the default example is at the high end for Flux.** 2.5–3.0 usually gives more photographic output; 3.5 pushes prompt-literalness. Experiment.
- **Max input/output resolution is 1440 on either axis** (Flux-dev limit). Chain into a dedicated upscaler (`fermatresearch/magic-image-refiner`, `topazlabs/image-upscale`) for larger outputs.
- **`go_fast: true` is incompatible with custom `width` / `height`.** If you set `aspect_ratio: "custom"`, leave `go_fast` off.
- **Output is an array**, not a single string — index `[0]` when wiring the response.
- **No README, no GitHub, no license URL on the model page.** Description is one typo'd sentence. Schema and default example are the source of truth. Afterpeak has published this and moved on.
- **Mildly meme-coded / niche.** Useful for content creators parodying or participating in the slowed-audio upload scene, and as a cosmetic primitive for social-post art. Not a serious design-workflow tool.
