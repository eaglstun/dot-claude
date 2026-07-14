# black-forest-labs/flux-canny-pro

Model page: <https://replicate.com/black-forest-labs/flux-canny-pro>

**Flux.1 Pro with Canny-edge ControlNet.** Takes an input image, extracts its Canny edges internally, and generates a new image whose structure/outlines match those edges while content and style are driven by a text prompt. The edge extraction is baked in — you supply the source image and the model derives the control signal; there are no exposed `canny_low` / `canny_high` threshold knobs. Sweet spot: keep the **exact composition, silhouettes, and line work** of a reference while changing style, colors, materials, or subject matter (e.g. architectural photo -> oil painting of the same building, line-art sketch -> photoreal render, product photo -> different colorway with identical form).

## When to pick this over sibling models

- **`black-forest-labs/flux-depth-pro`** — controls with a depth map instead of edges. Pick depth when you care about **spatial/scene preservation** (relative distance, volume, 3D layout) more than exact outlines. Flux-canny is strict about silhouettes; flux-depth lets details within a surface drift.
- **`black-forest-labs/flux-canny-dev`** — the open-weights Dev version of the same idea. Cheaper per run and runnable locally, but lower fidelity and less adherence than Pro. Pick Dev for volume/iteration, Pro for hero shots.
- **`black-forest-labs/flux-redux-pro`** — image variations **without** a control signal. Pick Redux when you want "more like this" loose variants, not "same shape, new style."
- **`black-forest-labs/flux-fill-pro`** — inpainting/outpainting with a mask. Different job: edit part of an image, don't restyle the whole thing.

## Input schema

| Field               | Type         | Required | Default | Description                                                                                                                                                                                       |
| ------------------- | ------------ | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`            | string       | Yes      | —       | Text prompt describing the image to generate. The edges from `control_image` enforce the structure; the prompt drives style, subject, lighting, mood.                                             |
| `control_image`     | string (URI) | Yes      | —       | Reference image whose Canny edges will be extracted and used as the structural control. Must be **jpeg, png, gif, or webp**. Local paths are auto-uploaded by `run_model.py`.                     |
| `steps`             | integer      |          | `50`    | Diffusion steps. Range **15–50**. Higher = finer details but slower. 28–50 is the typical range; the default example uses 28.                                                                     |
| `guidance`          | number       |          | `30`    | Prompt adherence. Range **1–100**. Higher = follow the prompt more literally; lower = more creative freedom. Note: Flux Pro guidance scale is **not** the familiar SD cfg-7 range — 25–35 is normal here. |
| `safety_tolerance`  | integer      |          | `2`    | BFL safety filter strictness. Range **1 (strictest) – 6 (most permissive)**. Defaults to 2. Raising it permits more latitude on NSFW / violent / sensitive content within BFL's commercial terms. |
| `prompt_upsampling` | boolean      |          | `false` | If true, the model rewrites your prompt internally to be more descriptive/creative before generation. Turn on for terse prompts; leave off when you've already written the prompt you want.       |
| `output_format`     | enum         |          | `"jpg"` | Output file format. Typical values `"jpg"` / `"png"` / `"webp"` (BFL standard set).                                                                                                               |
| `seed`              | integer      |          | random  | Random seed. Set for reproducible generation.                                                                                                                                                     |

**No exposed Canny threshold controls.** The schema does **not** include `canny_low` / `canny_high` / `low_threshold` / `high_threshold` / `preprocessed_image`. The edge map is computed internally with fixed thresholds — if you need a pre-computed or tuned edge map, you'd have to use `flux-canny-dev` or a different ControlNet pipeline.

## Output

A single URI string pointing to the generated image (not an array). Saved as `black-forest-labs_flux-canny-pro_0.<ext>` where `<ext>` matches `output_format` (default `jpg`).

## Pricing

**$0.05 per image** on the Replicate model page (flat per-run for Flux Pro tier). Typical prediction time is ~15 seconds per image. See <https://replicate.com/black-forest-labs/flux-canny-pro> for the canonical number — BFL Pro endpoints are priced per image, not per second, so step count does not change cost.

## Examples

**1. Architectural photo -> painted version** (keep the exact building outline, restyle as an oil painting):

```json
{
  "prompt": "oil painting of a brutalist concrete apartment block at dusk, warm amber light spilling from windows, thick impasto brushwork, moody sky, in the style of Edward Hopper",
  "control_image": "./photos/building_exterior.jpg",
  "steps": 40,
  "guidance": 30,
  "output_format": "jpg"
}
```

```bash
python scripts/run_model.py black-forest-labs/flux-canny-pro --input-file input.json --output ./out/
```

**2. Restyling an illustration while keeping the line art** (ink sketch -> photoreal):

```json
{
  "prompt": "photorealistic render of a robotic fox standing in a forest clearing, morning mist, cinematic lighting, shallow depth of field, 85mm lens",
  "control_image": "./sketches/fox_lineart.png",
  "steps": 50,
  "guidance": 25,
  "prompt_upsampling": false,
  "output_format": "png",
  "seed": 12345
}
```

```bash
python scripts/run_model.py black-forest-labs/flux-canny-pro --input-file input.json --output ./out/
```

**3. Product photo recolor** (same silhouette, new materials — good demo of the "edges fixed, surface free" behavior):

```json
{
  "prompt": "studio product photograph of a ceramic teapot in matte forest green with polished brass spout and handle, seamless beige backdrop, soft three-point lighting",
  "control_image": "./products/teapot_white.jpg",
  "steps": 35,
  "guidance": 35,
  "safety_tolerance": 2,
  "output_format": "jpg"
}
```

```bash
python scripts/run_model.py black-forest-labs/flux-canny-pro --input-file input.json --output ./out/
```

## Strengths / gotchas

**Good at:**

- Pixel-accurate silhouette / outline preservation across drastic style changes.
- Turning clean line art or sketches into finished renders without composition drift.
- Restyling architectural, product, and character references where the shape is sacred.
- Flux Pro-grade photoreal output quality (noticeably better than `flux-canny-dev`).

**Gotchas:**

- **Source-image quality is load-bearing.** Canny extraction is internal and uses fixed thresholds — busy backgrounds, heavy JPEG compression, low contrast, or motion blur produce **noisy edge maps** that bleed into the output as phantom lines and smudged structure. Pre-clean the source (crop tightly, boost contrast, flatten busy backgrounds) before passing it in.
- **No Canny threshold controls.** If the default thresholds miss subtle edges or pick up too much noise for your image, you cannot tune them on this endpoint — switch to `flux-canny-dev` or pre-compute edges with a separate pipeline (but note this endpoint does **not** accept a pre-extracted edge map — `control_image` is the RGB source, not the edge map).
- **`guidance` is NOT the SD cfg scale.** Default is 30 and range is 1–100. Around **25–35 is the sweet spot** for Flux Pro. Pushing past 50 tends to oversaturate and crisp-up artifacts; below 15 you lose prompt adherence. Do not port SD's "cfg=7" intuition here.
- **`steps` is capped at 50.** You cannot push higher for extra detail — invest in a better prompt or a cleaner source instead.
- **Safety tolerance defaults to 2 (fairly strict).** Raise toward 6 only if you know you need permissive output; the filter still enforces BFL's hard bans regardless.
- **`output_format` defaults to `"jpg"`.** Set `"png"` if you need lossless (e.g. for downstream compositing) — default JPG will show compression artifacts on fine line work.
- **Single output per call.** Returns one URI. Loop with different seeds for variations.
- **Commercial use:** the `-pro` Flux endpoints are licensed for commercial use via Replicate's BFL hosting; verify current BFL commercial terms at <https://blackforestlabs.ai/> before shipping generated assets. `-dev` sibling weights have different (non-commercial by default) terms — don't confuse the two.
- **Cover image on the model page** (<https://tjzk.replicate.delivery/models_models_featured_image/4c07cacc-d206-4587-9357-8e4e81cd761a/https___replicate.deli_lsMxQWe.jpg>) illustrates the canonical "same outline, new content" behavior.
