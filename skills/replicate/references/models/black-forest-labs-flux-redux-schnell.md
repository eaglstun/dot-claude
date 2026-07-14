# black-forest-labs/flux-redux-schnell

Model page: <https://replicate.com/black-forest-labs/flux-redux-schnell>
License: <https://github.com/black-forest-labs/flux/blob/main/model_licenses/LICENSE-FLUX1-schnell>

BFL's **FLUX.1 Redux** variant on the fast Schnell backbone — **image-to-variation** model where the input is an image (not a text prompt) and the output is a stylistic/compositional variation of it. No prompt field at all; the source image _replaces_ the prompt. Ideal for rapid "give me more like this" iteration — explore variations of a concept, find adjacent compositions, or fan out from a single hero image. Latest version: `8a9ff6ce...` (2025-03-18). ~74k runs.

## When to pick this over alternatives

- **Pick it over `black-forest-labs/flux-2-pro`** when you have a source image you like and want variations _without_ the work of describing it in a prompt. Redux Schnell is a one-click "more like this" button.
- **Pick it over running `flux-2-pro` with the image as reference** when speed matters — Schnell is the fast variant (4 steps) and is ~3–5× faster / cheaper than Flux-2-Pro.
- **Pick it over `fofr/latent-consistency-model`** when you want quality-tier output — LCM is faster but lower quality; Redux Schnell is the sweet spot of fast + Flux-quality.
- **Skip it** when you have a specific text prompt in mind (there's no `prompt` field — you can't steer it with words). Skip also when you want to _edit_ rather than _vary_ — this is not an editor, it's a variation generator.

## Input schema

| Field                    | Type         | Required | Default  | Description                                                                                      |
| ------------------------ | ------------ | -------- | -------- | ------------------------------------------------------------------------------------------------ |
| `redux_image`            | string (URI) | yes      | —        | **The image that replaces the prompt.** Output will be a variation conditioned on this image.    |
| `aspect_ratio`           | enum         |          | `"1:1"`  | `1:1`, `16:9`, `21:9`, `3:2`, `2:3`, `4:5`, `5:4`, `3:4`, `4:3`, `9:16`, `9:21`.                 |
| `megapixels`             | enum         |          | `"1"`    | `"1"` or `"0.25"` — string enum. `"0.25"` for fast drafts.                                       |
| `num_outputs`            | integer      |          | `1`      | Range `1–4`. Generate multiple variations per call at cost multiplier.                           |
| `num_inference_steps`    | integer      |          | `4`      | Range `1–4`. **Hard-capped at 4** (it's Schnell). More steps = better quality; 4 is recommended. |
| `seed`                   | integer      |          | random   | Set for reproducibility. Same seed + same image = same variation.                                |
| `output_format`          | enum         |          | `"webp"` | `webp`, `jpg`, or `png`.                                                                         |
| `output_quality`         | integer      |          | `80`     | `0–100`. Ignored for PNG.                                                                        |
| `disable_safety_checker` | boolean      |          | `false`  | Keep off for user-facing; flip only for trusted pipelines.                                       |

Notable: **there is no `prompt` field**. The model's conditioning signal is the input image alone.

## Output

**Array of image URIs** — even for `num_outputs: 1` you get a one-element list. Saved as `black-forest-labs_flux-redux-schnell_0.webp`, `_1.webp`, ... by `run_model.py`.

## Pricing and runtime

Pricing not in schema — confirm on the model page. Flux Schnell tier is **~$0.003 per image** typically — extremely cheap. Default example predicted in **~1.4 s** — near-realtime. Ideal for rapid iteration loops.

## Examples

**Single variation** of a hero image:

```json
{
  "redux_image": "./hero_reference.png",
  "aspect_ratio": "3:2",
  "megapixels": "1",
  "num_outputs": 1
}
```

```bash
python scripts/run_model.py black-forest-labs/flux-redux-schnell \
    --input-file input.json \
    --output ./out/
```

**Variation fan-out** — 4 different variations from the same source for mood-board work:

```json
{
  "redux_image": "./concept.png",
  "num_outputs": 4,
  "aspect_ratio": "1:1",
  "megapixels": "1"
}
```

**Fast draft pass** — quarter-MP for cheap seed sweeping:

```json
{
  "redux_image": "./concept.png",
  "megapixels": "0.25",
  "num_outputs": 4
}
```

**Different aspect ratio from source** — reframe as part of variation:

```json
{
  "redux_image": "./vertical_hero.png",
  "aspect_ratio": "16:9"
}
```

## Strengths / gotchas

**Good at:**

- "More like this" one-click variation workflows
- Mood-board / concept exploration — run with `num_outputs: 4` to get a spread
- Near-realtime iteration at ~$0.003/image
- Preserving the _vibe_ of the input (palette, style, mood) while varying composition/pose/details
- Aspect-ratio remapping as a side effect of variation

**Gotchas:**

- **No `prompt` field.** Can't steer the variation with text — the source image is the only input signal. If you want to mix image + text conditioning, use `black-forest-labs/flux-2-pro` with both.
- **`num_inference_steps` caps at 4.** Schnell is explicitly 4-step — pushing to 8/20/50 like normal Flux isn't an option here. 4 is both the default and the ceiling.
- **Output is an array, not a bare URI.** Unwrap `output[0]` even for `num_outputs: 1`. `run_model.py` handles this; direct SDK/HTTP callers need to index.
- **`megapixels` is a string enum.** `"1"` or `"0.25"` — quoting matters.
- **Quality is below Flux-2-Pro.** Use Redux Schnell for _exploration_, Flux-2-Pro for hero renders. Typical workflow: generate 16 Redux Schnell variations cheaply, pick favorites, regenerate at hero quality via Flux-2-Pro using a text prompt that captures what made them work.
- **Seed stability is useful.** Same seed + same image = same variation — lock a winning variation with a seed before you lose it to a rerun.
- **Not an editor.** Can't say "make the sky cloudy" — it will produce a variation that _might_ have cloudy skies but isn't directed to. For directed edits use `flux-2-pro` or `prunaai/p-image-edit`.
- **Source image quality dominates.** Garbage in, garbage out — Redux propagates the compositional and stylistic DNA of the input, including its flaws. Use a clean hero image as the reference.
- **License:** Flux.1 Schnell license (Apache-2.0-derived, commercial-friendly) — the most permissive Flux variant.
- **Version pin:** `black-forest-labs/flux-redux-schnell:8a9ff6ce228b950c7079005fd0804f54c74c0113cda3f3c07eff10ab943f32a1`. Pin for reproducible variation fan-outs across sessions.
