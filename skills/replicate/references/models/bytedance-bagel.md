# bytedance/bagel

Model page: <https://replicate.com/bytedance/bagel>

GitHub (Cog wrapper): <https://github.com/zsxkib/cog-bagel>

BAGEL is ByteDance Seed's **unified multimodal model** — a single 7B-parameter endpoint that does text-to-image generation, instruction-based image editing, **and** visual understanding/reasoning (VQA). One model, three modes, one API. The trade-off is a more complex input surface: a `task` selector plus mode-dependent fields, versus specialist endpoints like `bria/fibo` (pure T2I) or `flux-kontext-apps/multi-image-kontext-max` (pure edit). The unusual capability here is **image understanding** — ask it questions about an image and it answers in natural language. That's rare among Replicate image models (most are pure generators), and it makes BAGEL useful as a cheap captioner / VQA layer in a pipeline that also does generation, without having to route to a separate vision model.

Chain-of-thought reasoning is available via `enable_thinking: true` for any of the three modes, producing more deliberate outputs at the cost of extra latency.

## Modes (selected via `task` enum)

| Mode                    | `task` value            | Required inputs      | Returns                                           |
| ----------------------- | ----------------------- | -------------------- | ------------------------------------------------- |
| **Text-to-image**       | `"text-to-image"`       | `prompt`             | Generated `image` URI. `text` is null.            |
| **Image editing**       | `"image-editing"`       | `prompt` + `image`   | Edited `image` URI. `text` is null.               |
| **Image understanding** | `"image-understanding"` | `prompt` + `image`   | `text` answer string. `image` is null.            |

The output object is always `{ "text": str | null, "image": URI | null }` — which field is populated depends on the mode.

## Input schema

| Field                 | Type         | Required | Default           | Description                                                                                                           |
| --------------------- | ------------ | -------- | ----------------- | --------------------------------------------------------------------------------------------------------------------- |
| `prompt`              | string       | ✅       | —                 | Text prompt. Generation prompt, edit instruction, or question depending on `task`.                                   |
| `image`               | string (URI) | ✱        | —                 | Input image. Required for `image-editing` and `image-understanding`; ignored for `text-to-image`. Local paths auto-upload via `run_model.py`. |
| `task`                | enum         |          | `"text-to-image"` | One of `text-to-image`, `image-editing`, `image-understanding`.                                                        |
| `enable_thinking`     | boolean      |          | `false`           | Chain-of-thought reasoning before answering/generating. Improves complex results; adds latency.                       |
| `cfg_text_scale`      | number       |          | `4`               | Text guidance scale. How closely to follow the prompt. Range **1–20**.                                                |
| `cfg_img_scale`       | number       |          | `1.5`             | Image guidance scale for preserving input image details (editing mode). Range **1–10**.                               |
| `num_inference_steps` | integer      |          | `50`              | Denoising steps. Range **1–100**.                                                                                     |
| `timestep_shift`      | number       |          | `3`               | Distribution of denoising steps between composition and details. Range **1–10**.                                     |
| `cfg_renorm_type`     | enum         |          | `"global"`        | CFG renormalization method. One of `global`, `local`, `text_channel`. The official default example uses `text_channel` for editing. |
| `cfg_renorm_min`      | number       |          | `1`               | Minimum CFG renorm value. Range **0–1**.                                                                              |
| `seed`                | integer      |          | random            | Seed for reproducible output.                                                                                         |
| `output_format`       | enum         |          | `"webp"`          | One of `webp`, `jpg`, `png`. Image-bearing modes only.                                                                |
| `output_quality`      | integer      |          | `90`              | Compression quality for lossy formats (webp/jpg). Range **1–100**.                                                    |

✱ `image` is required for `image-editing` and `image-understanding`, not for `text-to-image`.

## Output

```json
{
  "text":  "<string or null>",
  "image": "<URI or null>"
}
```

- **Text-to-image / image-editing** — `image` populated, `text` null. Saved by `run_model.py` as `bytedance_bagel_0.webp` (or `.jpg`/`.png` per `output_format`).
- **Image understanding** — `text` populated (natural-language answer), `image` null. `run_model.py` will write the text response to `bytedance_bagel_0.txt` / print it to stdout (no image file to save).

## Pricing

**~$0.096 per run** (≈ 10 runs per $1), though cost varies with `num_inference_steps` and `enable_thinking`. Typical prediction completes in ~99 seconds on Nvidia L40S. Understanding-mode runs tend to be faster (no image diffusion), T2I and editing at default 50 steps dominate runtime. Check the playground estimator on the model page before batching.

## Examples

**Text-to-image:**

```bash
python scripts/run_model.py bytedance/bagel \
    --input '{
      "task": "text-to-image",
      "prompt": "a hyper-detailed ultra-fluffy owl perched on a mossy branch at night, silver moonlight, whimsical storybook mood",
      "cfg_text_scale": 4,
      "num_inference_steps": 50,
      "output_format": "png"
    }' \
    --output ./out/
```

**Image editing** (instruction-based; the default example's setup):

```bash
python scripts/run_model.py bytedance/bagel \
    --input '{
      "task": "image-editing",
      "image": "./portrait.jpg",
      "prompt": "She boards a modern London Tube, quietly reading a folded newspaper, wearing the same clothes",
      "cfg_img_scale": 2,
      "cfg_text_scale": 4,
      "cfg_renorm_type": "text_channel",
      "num_inference_steps": 50
    }' \
    --output ./out/
```

**Image understanding** (visual Q&A) — returns a text answer, no image:

```bash
python scripts/run_model.py bytedance/bagel \
    --input '{
      "task": "image-understanding",
      "image": "./scene.jpg",
      "prompt": "What is the person in the foreground holding, and describe the weather.",
      "enable_thinking": true
    }' \
    --output ./out/
```

**Text-to-image with chain-of-thought** (for complex compositional prompts):

```bash
python scripts/run_model.py bytedance/bagel \
    --input '{
      "task": "text-to-image",
      "prompt": "an isometric diorama of a ramen shop at dusk, steam rising from three bowls, a cat on the counter, warm paper lantern light, strict color palette of teal and orange",
      "enable_thinking": true,
      "cfg_text_scale": 5,
      "num_inference_steps": 50
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- One endpoint for three workflows — T2I, edit, VQA — handy when you want to avoid stitching together multiple models.
- Image understanding / VQA is unusual for a Replicate "image model" — use it as a cheap captioner or visual-reasoning step inside a generation pipeline.
- Instruction-following edits (the default example shows preserving subject identity across a scene change).
- `enable_thinking` helps on complex multi-element prompts or nuanced edits.

**Gotchas:**

- **Mode selection is manual**: you must set `task` explicitly. There is no auto-inference from which fields are populated — passing an `image` with `task: "text-to-image"` will silently ignore the image.
- **Output shape changes by mode.** Consumers must check both `text` and `image` fields and handle `null`. Scripts that blindly download `output.image` will break on `image-understanding` runs.
- **`image` is required** for editing and understanding; the API will error if it's missing.
- **`cfg_img_scale` only matters for editing**; for T2I, tune `cfg_text_scale` (default 4) — higher = more prompt adherence.
- **Reasoning output format for VQA is plain natural-language text**, not JSON. If you need structured output, post-process with a small LLM or prompt BAGEL explicitly for JSON in the `prompt` — the model doesn't guarantee a schema.
- **Specialist models often beat it per-task**: Flux / Ideogram for pure T2I quality, Flux-Kontext for precise edits, a dedicated VLM for heavy VQA. Pick BAGEL when the one-endpoint convenience or cost matters more than best-in-class per task.
- **Default runtime is slow-ish** (~99s) because of 50 diffusion steps — drop `num_inference_steps` to 20–30 for faster drafts, bump back to 50 for finals. VQA mode runs faster since it skips image diffusion.
- Watermark / licensing: check the GitHub repo and the ByteDance Seed BAGEL license before commercial use.
