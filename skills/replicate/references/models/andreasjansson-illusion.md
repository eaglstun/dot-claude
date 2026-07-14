# andreasjansson/illusion

Model page: <https://replicate.com/andreasjansson/illusion>

> **Pinned version required.** The bare `andreasjansson/illusion` slug returns a **404** on `POST /v1/predictions` — this model is an older community upload without a "latest version" alias. You must pass a pinned version hash (e.g. `andreasjansson/illusion:75d51a73...`) or use the `"version": "<id>"` field. Grab the current version hash from the API tab on the model page. The `run_model.py` helper handles this automatically for most models, but for this one double-check that a version is resolved before the POST.

Optical-illusion / hidden-image generation. This is the original "spiral illusion" / "hidden QR code art" model — the one that went viral in 2023 for images that look like normal scenes but resolve into a scannable QR code (or logo, word, or high-contrast pattern) when you blur, squint, or step back. It stacks **Monster Labs' `control_v1p_sd15_qrcode_monster` ControlNet** on top of **Stable Diffusion 1.5 + Realistic Vision 5.1**, which is the specific recipe tuned for the illusion effect. GitHub: <https://github.com/andreasjansson/cog-qrcode>.

## When to pick this over alternatives

- **Pick it over generic SD+ControlNet (canny/depth/scribble)** when you want the illusion effect specifically — generic ControlNets reproduce the input pattern too literally and don't "hide" it. The qrcode-monster checkpoint was trained to produce images where the pattern _emerges_ rather than dominates.
- **Pick it over later SDXL illusion models** when you need a scannable QR code output (SD 1.5 + this ControlNet is still the gold standard for actually-works-when-scanned QRs) or when you want fast, cheap iteration.
- **Either supply your own control `image`** (logo, word-as-image, dense high-contrast pattern) **or let the model generate a QR code for you** by passing only `qr_code_content`. `qr_code_content` is required in the schema even when you supply an `image` — pass an empty string `""` in that case.
- **Skip it** if the control shape is low-contrast, subtle grayscale, or a thin line drawing — the illusion needs dense dark/light regions to latch onto.

## Input schema

| Field                           | Type         | Required | Default                                         | Description                                                                                                                                                                                |
| ------------------------------- | ------------ | -------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `prompt`                        | string       | yes      | —                                               | Text prompt guiding the surface image. Abstract/natural scenes (forests, clouds, oil paintings, cobblestones) hide patterns better than portraits or busy subjects.                        |
| `qr_code_content`               | string       | yes      | —                                               | URL / text the QR code should point to. **Required even when you supply a custom `image`** — pass `""` in that case. If non-empty and no `image` is supplied, a QR code is auto-generated. |
| `image`                         | string (URI) |          | —                                               | Optional custom control image (logo, word-as-image, silhouette, dense pattern). Overrides QR code generation. Local paths are auto-uploaded by `run_model.py`.                             |
| `negative_prompt`               | string       |          | `"ugly, disfigured, low quality, blurry, nsfw"` | Content to exclude from the output.                                                                                                                                                        |
| `num_inference_steps`           | integer      |          | `40`                                            | Diffusion steps. Range `20–100`. 40 is the sweet spot; above 60 rarely helps.                                                                                                              |
| `guidance_scale`                | number       |          | `7.5`                                           | Classifier-free guidance. Range `0.1–30`. Higher = more prompt-literal; lower = more room for the ControlNet to impose the pattern.                                                        |
| `controlnet_conditioning_scale` | number       |          | `2.2`                                           | **The main tuning knob.** Range `0–4`. Higher = illusion is stronger/more scannable but output looks more "pattern-forced"; lower = prettier image but illusion may not read. See below.   |
| `seed`                          | integer      |          | `-1`                                            | `-1` = random. Set for reproducibility.                                                                                                                                                    |
| `width`                         | integer      |          | `768`                                           | Output width. Keep square for QR codes; match control image aspect ratio for custom `image`.                                                                                               |
| `height`                        | integer      |          | `768`                                           | Output height.                                                                                                                                                                             |
| `num_outputs`                   | integer      |          | `1`                                             | Range `1–4`. Cheap way to get variations at one seed sweep.                                                                                                                                |
| `border`                        | integer      |          | `1`                                             | QR code border (quiet zone) size. Range `0–4`. Bigger border = easier to scan but smaller code area inside the image.                                                                      |
| `qrcode_background`             | enum         |          | `"gray"`                                        | Background fill for the raw QR code before ControlNet sees it. Typical values `"gray"` / `"white"`. Gray tends to blend better; white gives sharper illusion contrast.                     |

Local file paths for `image` are auto-uploaded by `run_model.py`.

## Output

An **array of image URIs** (PNG). With default `num_outputs: 1` you get a one-element list. Saved as `andreasjansson_illusion_0.png` (and `_1.png`, `_2.png`, ... when `num_outputs > 1`).

## Pricing

**~$0.0033 per run** on Nvidia L40S — roughly **303 runs per $1**. Predictions typically complete in **~4 seconds**. Cheap enough to do large seed sweeps and conditioning-scale ladders without worrying about cost.

## Examples

**Hide a QR code inside an oil-painting landscape** (no custom `image` — the model generates the QR from `qr_code_content`):

```json
{
  "prompt": "an oil painting of a medieval village at dusk, winding cobblestone streets, warm lanterns, dramatic sky, highly detailed, masterpiece",
  "qr_code_content": "https://example.com",
  "negative_prompt": "blurry, low quality, text, watermark, signature",
  "num_inference_steps": 40,
  "guidance_scale": 7.5,
  "controlnet_conditioning_scale": 2.0,
  "width": 768,
  "height": 768,
  "border": 2,
  "qrcode_background": "gray",
  "num_outputs": 2,
  "seed": 42
}
```

```bash
python scripts/run_model.py andreasjansson/illusion \
    --input-file input.json \
    --output ./out/
```

**Hide a logo / word-shape inside a portrait-oriented nature scene** using a custom control image. Note `qr_code_content: ""` — required by the schema but ignored when `image` is supplied:

```json
{
  "prompt": "a lush vertical rainforest canopy seen from below, sunlight breaking through leaves, aerial perspective, photorealistic",
  "qr_code_content": "",
  "image": "./logo_high_contrast.png",
  "controlnet_conditioning_scale": 1.8,
  "guidance_scale": 8.0,
  "num_inference_steps": 50,
  "width": 640,
  "height": 896,
  "num_outputs": 3,
  "seed": -1
}
```

```bash
python scripts/run_model.py andreasjansson/illusion \
    --input-file input.json \
    --output ./out/
```

**Conditioning-scale sweep** — the recommended workflow. Run the same prompt+control at 1.4 / 1.8 / 2.2 / 2.6 and pick the sweet spot where the illusion scans but the image still looks natural:

```json
{
  "prompt": "abstract swirling clouds at sunrise, dramatic light rays, painterly, serene",
  "qr_code_content": "https://replicate.com",
  "controlnet_conditioning_scale": 1.8,
  "num_inference_steps": 40,
  "seed": 12345,
  "num_outputs": 1
}
```

```bash
for s in 1.4 1.8 2.2 2.6; do
  jq ".controlnet_conditioning_scale = $s" input.json > _tmp.json
  python scripts/run_model.py andreasjansson/illusion \
      --input-file _tmp.json \
      --output "./out/scale_${s}/"
done
```

## Strengths / gotchas

**Good at:**

- Producing scannable QR codes hidden inside a coherent image — the original viral use-case, still one of the most reliable QR-illusion recipes available.
- Fast (~4s) and cheap (~$0.003), so seed + conditioning sweeps are practically free.
- Abstract / natural / painterly prompts (forests, clouds, oil paintings, stone walls, galaxies, aurora, crowds at distance) that have lots of mid-frequency texture for the pattern to disappear into.
- Taking arbitrary custom `image` control (not just QR codes) — logos, kanji, word-as-image shapes, silhouettes all work provided they're **high-contrast black/white**.

**Gotchas:**

- **Bare slug 404s.** `andreasjansson/illusion` alone returns 404 — you must pin a version hash (`andreasjansson/illusion:75d51a73...`) or pass `version` at the top level. Pull the current hash from the model page's API tab; re-pin when it rotates.
- **`controlnet_conditioning_scale` is _the_ tuning knob.** Default `2.2` is aggressive. If output looks too much like "pretty QR code" (pattern too visible, details look grid-aligned), drop to `1.6–2.0`. If the illusion doesn't read / code doesn't scan, push to `2.4–3.0`. Above ~3.2 the output degenerates into the raw pattern with texture sprinkled on top.
- **Scannability vs beauty is a real tradeoff.** A QR that scans reliably from any angle will look more "QR-ish"; a beautiful image that only reveals the code when squinted will sometimes fail a phone scan. Sweep scales and test-scan before committing.
- **High-contrast control images only.** Subtle grayscale, thin line drawings, or low-contrast logos won't latch — binarize your control image (hard black/white) before uploading. Think stencil, not photograph.
- **Match aspect ratios.** If your custom `image` is 1:1 but you set `width=640, height=896`, the control gets stretched and the illusion smears. Keep control image aspect ratio equal to `width/height`.
- **Detailed subjects hide patterns poorly.** Portraits, product shots, architecture with strong straight lines, and busy foreground characters tend to _fight_ the pattern. Abstract / atmospheric / textural prompts work far better.
- **`qr_code_content` is required by the schema** even when you supply your own `image`. Pass `""` in that case — it will be ignored.
- **Prompt leakage:** avoid words like "QR code", "grid", "pattern", "pixelated" in the prompt — they make the illusion obvious instead of hidden. And keep `"text, watermark, signature"` in the negative prompt, since the ControlNet sometimes tries to render pattern edges as text glyphs.
- **Output is always PNG** in an array (even for `num_outputs=1`). `run_model.py` saves them as `andreasjansson_illusion_0.png`, `_1.png`, ....
- **Test the scan on a real phone**, not just by eyeballing the image — screens and cameras tolerate different levels of pattern-breakup than human vision does.
