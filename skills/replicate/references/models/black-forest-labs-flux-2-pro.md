# black-forest-labs/flux-2-pro

Model page: <https://replicate.com/black-forest-labs/flux-2-pro>

BFL's **FLUX.2 Pro** — the flagship T2I + image-editing endpoint in the FLUX.2 family, with **up to 8 input reference images** for multi-image composition, character consistency, and reference-guided generation. Handles both pure text-to-image and image-editing in the same endpoint (distinguished by whether `input_images` is empty). Latest version: `ccb5e331...` (2026-03-23). **5.6M+ runs** — one of the most-used image models on Replicate.

## When to pick this over alternatives

- **Pick it over `black-forest-labs/flux-dev-lora`** when you need the best quality FLUX output available — Flux-2-Pro is the newer, stronger model with better prompt adherence, more natural compositions, and support for reference-image conditioning natively (no LoRA needed for character consistency).
- **Pick it over `flux-kontext-apps/multi-image-kontext-max`** when you need more than 2 reference images or want to generate-from-scratch with references as style anchors (Kontext Max is edit-focused, 2-image).
- **Pick it over `bria/fibo`** when you need top-tier visual quality and aren't constrained by rights-clear training data requirements. Stick with Bria for licensed-data / enterprise compliance use cases.
- **Skip it** for cheap iteration — at premium-quality pricing, use `fofr/latent-consistency-model` or `lucataco/realistic-vision-v5.1` for drafts, then promote winners to Flux-2-Pro.

## Input schema

| Field              | Type         | Required | Default     | Description                                                                                                                                                                        |
| ------------------ | ------------ | -------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`           | string       | yes      | —           | Text description of what to generate, or edit instruction when `input_images` is provided.                                                                                         |
| `input_images`     | array[URI]   |          | `[]`        | Up to **8 reference images** (jpeg/png/gif/webp). Empty = pure T2I; 1+ images = reference-guided / edit mode.                                                                      |
| `aspect_ratio`     | enum         |          | `"1:1"`     | `match_input_image`, `custom`, `1:1`, `16:9`, `3:2`, `2:3`, `4:5`, `5:4`, `9:16`, `3:4`, `4:3`. Use `custom` to pass explicit `width`/`height`.                                    |
| `resolution`       | enum         |          | `"1 MP"`    | `0.5 MP`, `1 MP`, `2 MP`, `4 MP`, or `match_input_image`. Up to 4 MP is allowed but 2 MP or below is recommended. Max 2048 × 2048.                                                |
| `width`            | integer      |          | —           | Only used when `aspect_ratio: "custom"`. Range `256–2048`. **Must be a multiple of 16** (rounded if not).                                                                          |
| `height`           | integer      |          | —           | Same constraints as `width`.                                                                                                                                                       |
| `seed`             | integer      |          | random      | Set for reproducibility.                                                                                                                                                           |
| `output_format`    | enum         |          | `"webp"`    | `webp`, `jpg`, or `png`.                                                                                                                                                            |
| `output_quality`   | integer      |          | `80`        | `0–100`. Ignored for PNG.                                                                                                                                                           |
| `safety_tolerance` | integer      |          | `2`         | Range `1–5`. **1 = most strict, 5 = most permissive.** Tune up only for trusted internal pipelines with legitimate need for lenient filtering.                                     |

### Aspect-ratio / resolution interaction

- `resolution` is ignored when `aspect_ratio: "custom"` — use `width`/`height` instead.
- `resolution: "match_input_image"` pairs with `aspect_ratio: "match_input_image"` for round-trip edits that preserve source dimensions (clamped 0.5–4 MP).
- At high resolutions with non-1:1 aspect ratios, the 2048 × 2048 ceiling may reduce effective MP below what you requested — `4 MP` at `16:9` hits ~2048 × 1152 (2.4 MP real).

## Output

**Bare URI string** — single image. Saved as `black-forest-labs_flux-2-pro_0.{ext}` by `run_model.py`.

## Pricing and runtime

Pricing not in schema — confirm on the model page. Flux Pro tier is typically **~$0.04–0.08 per image** depending on resolution. Default example predicted in **~5.6 s**. Budget 5–15 s per image depending on resolution and image count.

## Examples

**Pure text-to-image** — no references:

```json
{
  "prompt": "A cinematic shot of a rain-slick Tokyo alley at night, neon signs reflected in puddles, a lone figure walking away from camera, 35mm film grain, Kodak Portra 400",
  "aspect_ratio": "16:9",
  "resolution": "2 MP",
  "output_format": "png"
}
```

```bash
python scripts/run_model.py black-forest-labs/flux-2-pro \
    --input-file input.json \
    --output ./out/
```

**Reference-guided generation** — use up to 8 images as composition / style / character references:

```json
{
  "prompt": "the character from the first reference image, now seated at a café table by a rain-soaked window, warm interior lighting, cinematic",
  "input_images": [
    "./char_hero.jpg",
    "./char_profile.jpg",
    "./cafe_reference.jpg"
  ],
  "aspect_ratio": "match_input_image",
  "resolution": "match_input_image"
}
```

**Custom dimensions** — precise control when the standard aspect ratios don't fit:

```json
{
  "prompt": "A sprawling hand-drawn city map, parchment texture, ink illustration",
  "aspect_ratio": "custom",
  "width": 1792,
  "height": 1024,
  "output_format": "png"
}
```

**Edit with a single reference** — treat the first input image as the source to modify:

```json
{
  "prompt": "change the jacket to navy blue suede, keep everything else identical",
  "input_images": ["./portrait.jpg"],
  "aspect_ratio": "match_input_image",
  "resolution": "match_input_image"
}
```

## Strengths / gotchas

**Good at:**

- Top-tier prompt adherence and natural scene composition
- Up to 8 reference images for **multi-subject** composition (try `multi-image-kontext-max` tops out at 2)
- Identity preservation across reference-guided generation — good for character-consistent series
- Text rendering inside images (legible signage, labels) — inherited from FLUX strength
- Flexible aspect/resolution combo including `custom` exact pixel dimensions

**Gotchas:**

- **`resolution` is a string enum** (`"1 MP"` with space) — not an integer. Quote-matters, including the space.
- **Width/height must be multiples of 16.** Non-multiples are silently rounded; pass only when you know why.
- **2048 × 2048 hard cap.** At high-MP + non-square aspects, effective resolution drops. 4 MP at 16:9 caps at ~2048 × 1152.
- **`safety_tolerance` defaults to `2` (strict).** Commercial/user-facing products should keep default or lower; push to 4–5 only for trusted internal pipelines.
- **Reference images share a lens.** Lighting, palette, and camera character tend to homogenize across refs — use more varied refs if you want varied outputs, fewer if you want tight consistency.
- **Edit mode vs generate mode is implicit.** No `mode` switch — passing any `input_images` flips behavior toward editing/reference-guided. An empty array is pure T2I.
- **Default output is webp.** Override to png for lossless if you're doing further editing downstream.
- **No `negative_prompt` field.** Shape prompts positively ("clean white background" not "no background noise").
- **Higher resolution = higher cost and slower runs** — 4 MP runs ~2–3× longer than 1 MP. Default to 1–2 MP for most work.
- **`prompt_upsampling`** appears in the default example's input JSON but is **not in the current schema** — likely a legacy / hidden field. Don't rely on it; modern calls should shape the prompt directly.
- **Version pin:** `black-forest-labs/flux-2-pro:ccb5e33141097816e6fab8c895e702fe4c619e4e07500885b71214e9f6382a5c`. Pin when doing batch runs where BFL updates mid-project would be disruptive.
