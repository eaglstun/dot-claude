# bria/fibo

Model page: https://replicate.com/bria/fibo

BRIA FIBO — an 8B open-source text-to-image model trained exclusively on **licensed data**, designed for enterprise/agentic workflows that need rights-clear output, repeatability, and structured control. The headline feature is **structured JSON prompting**: you can pass a long-form JSON spec (up to ~1,000+ words) with explicit controls for lighting, camera, composition, depth of field, etc., alongside or instead of a free-text prompt.

## When to pick FIBO over alternatives

- **Pick it over Flux / SDXL / Ideogram** when you need legally-clean output (no scraped training data) for commercial/enterprise use, or when you need fine-grained structured control over composition.
- **Pick it over Flux** when you want deterministic iterative refinement — structured prompts are round-trippable: the API response includes a `structured_prompt` you can edit and pass back for precise tweaks.
- **Pick Flux / SDXL / Ideogram instead** for pure text-only prompting, faster iteration, well-known LoRA ecosystems, or text-in-image rendering (FIBO's text rendering isn't the selling point).

## Modes (inferred from which inputs are set)

| Mode         | How to trigger                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------------------ |
| **Generate** | Pass `prompt` (and optionally `aspect_ratio`, `guidance_scale`, `negative_prompt`).                    |
| **Refine**   | Pass `prompt` + `structured_prompt` (JSON string from a prior response) to iteratively adjust details. |
| **Inspire**  | Pass `prompt` + `image` to generate variants inspired by a reference image.                            |

## Input schema

| Field               | Type          | Required | Default | Description                                                                                                                                                                                                                                                                                       |
| ------------------- | ------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`            | string        | ✅       | —       | Free-text prompt for image generation.                                                                                                                                                                                                                                                            |
| `image`             | string (URI)  |          | —       | Optional reference image (Inspire mode). Local paths are auto-uploaded by `run_model.py`.                                                                                                                                                                                                         |
| `structured_prompt` | string (JSON) |          | `""`    | Structured JSON prompt for precise control (lighting, camera, composition, depth of field, etc.). Pass a `structured_prompt` from a previous generation's response, or generate one via the `/v2/structured_prompt/generate` endpoint.                                                            |
| `negative_prompt`   | string        |          | —       | Content to exclude from the image.                                                                                                                                                                                                                                                                |
| `guidance_scale`    | integer       |          | —       | Prompt adherence. **Range: 3–5** (schema enforces this — the description says "1–10" but the min/max cap is 3–5).                                                                                                                                                                                 |
| `aspect_ratio`      | enum / float  |          | `"1:1"` | One of `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"` — OR a custom float between `0.5` and `3.0`. (Alternatively supply `canvas_size` with `original_image_size` / `location`, but those fields aren't first-class in this schema — use the enum/float path.) |
| `seed`              | integer       |          | random  | Random seed. Set for reproducible generation.                                                                                                                                                                                                                                                     |

Local file paths for `image` are auto-uploaded by `run_model.py`.

## Output

A single URI to the generated **PNG**. Saved as `bria_fibo_0.png`.

## Pricing

**Not published on the model page.** Check the playground price estimator at https://replicate.com/bria/fibo before running a batch. Runtime for the default example was ~15 seconds (a typical sub-minute single-image run), so cost should be in the usual cheap-image-model range, but don't assume — confirm in the playground.

## Examples

**Basic text-to-image (Generate mode):**

```bash
python scripts/run_model.py bria/fibo \
    --input '{
      "prompt": "A hyper-detailed, ultra-fluffy owl sitting in the trees at night, looking directly at the camera with wide, adorable, expressive eyes. Soft moonlight, silver highlights, whimsical storybook mood.",
      "aspect_ratio": "3:4",
      "guidance_scale": 5
    }' \
    --output ./out/
```

**Inspire mode** (image-guided generation):

```bash
python scripts/run_model.py bria/fibo \
    --input '{
      "prompt": "same subject and mood, but at golden hour instead of night",
      "image": "./reference.jpg",
      "aspect_ratio": "16:9"
    }' \
    --output ./out/
```

**Refine mode** (structured JSON for precise control) — the JSON is passed as a stringified value:

```bash
python scripts/run_model.py bria/fibo \
    --input '{
      "prompt": "editorial product shot of a ceramic teapot",
      "structured_prompt": "{\"subject\": \"matte black ceramic teapot with gold rim\", \"composition\": \"centered, rule-of-thirds\", \"lighting\": \"soft diffused key from upper-left, subtle rim light\", \"camera\": {\"angle\": \"slight high angle\", \"focal_length_mm\": 85, \"depth_of_field\": \"shallow, f/2.8\"}, \"mood\": \"minimalist editorial\", \"background\": \"seamless warm beige paper\"}",
      "aspect_ratio": "4:5",
      "guidance_scale": 4
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Rights-clear, commercially-safe output (100% licensed training data — the enterprise pitch).
- Structured JSON control over lighting, camera, composition, depth of field in one prompt.
- Repeatable/iterative refinement via round-tripped `structured_prompt` (Refine mode).
- Image-guided variants (Inspire mode) alongside pure text generation.

**Gotchas:**

- `guidance_scale` is **capped at 3–5** in the schema despite the "1–10" description — values outside will 422. Default behavior if omitted seems to be fine; only set it within 3–5.
- `structured_prompt` is a **JSON string**, not a nested object — double-escape the quotes inside your outer JSON input, or use a Python dict with `json.dumps()` before passing.
- `aspect_ratio` accepts enum strings _or_ floats in `[0.5, 3.0]`, but not arbitrary ratio strings outside the enum — stick to the listed set unless passing a numeric value.
- Default example logs showed `"Warning: Moderation check failed"` but still produced output — the model runs an internal moderation pass that may log warnings without blocking; expect occasional noise in logs.
- No text-in-image rendering claim — if you need legible signs/captions inside the image, use Ideogram instead.
- Output is PNG (not WebP/JPEG). Expect ~1–2 MB per image at default sizes.
- GitHub / license: https://github.com/Bria-AI/FIBO — verify your usage is within the published license before commercial deployment.
