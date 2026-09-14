# prunaai/p-image-edit

Model page: <https://replicate.com/prunaai/p-image-edit>
Companion model: <https://replicate.com/prunaai/p-image> (for generation from scratch)

Pruna's **production-grade multi-image editor** — sub-1-second, ~$0.01/run, with a baked-in **20-task preset enum** covering the vast majority of common edit operations (relight, style transfer, character consistency, upscale, and more). The headline feature is cost/speed: **27M+ runs** on Replicate at the time of writing makes this one of the most-used image models on the platform, period. Latest version: `05a6b136...` (2026-03-17).

## When to pick this over alternatives

- **Pick it over `black-forest-labs/flux-2-pro` (edit mode)** when cost and speed dominate — Pruna is ~$0.01 vs Flux-2-Pro's ~$0.04–0.08 and runs in <1 s vs 5–15 s. Quality is still high for presettable edit tasks.
- **Pick it over `flux-kontext-apps/multi-image-kontext-max`** when one of the 20 preset `replicate_weights` tasks matches your need — the purpose-tuned weights produce more consistent output than open-ended prompting on a general editor.
- **Pick it over `fofr/kontext-make-person-real`** for *generic* plastic-skin fixes — Pruna has `anything_to_real` which handles AI-look → real-look across more than just skin. (For skin specifically, `fofr/kontext-make-person-real` is the specialist.)
- **Skip it** for novel edit tasks not covered by the 20 presets — use Flux-2-Pro or Kontext Max for freeform work. Also skip for the highest-quality hero renders where the cost difference is worth it.

## Input schema

| Field                    | Type         | Required | Default              | Description                                                                                                                                                           |
| ------------------------ | ------------ | -------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                 | string       | yes      | —                    | Edit instruction. Reference inputs as `image 1`, `image 2`, etc. when you have multiple.                                                                              |
| `images`                 | array[URI]   |          | `[]`                 | Reference images. **First image is treated as the main subject** for editing tasks.                                                                                   |
| `replicate_weights`      | enum         |          | `"default"`          | **The 20-task preset enum** — see table below. Picks a task-specific weight set. `"default"` = open-ended editing.                                                     |
| `aspect_ratio`           | enum         |          | `"match_input_image"` | `match_input_image`, `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`. `match_input_image` = match the first image's aspect.                                         |
| `turbo`                  | boolean      |          | `true`               | Extra speed optimizations. **Leave on** for most work; turn off only for complex edits where quality loss shows.                                                       |
| `seed`                   | integer      |          | random               | Set for reproducibility.                                                                                                                                              |
| `disable_safety_checker` | boolean      |          | `false`              | Keep off for user-facing; flip only for trusted internal pipelines.                                                                                                   |

### The 20-task `replicate_weights` enum — the whole reason to pick this model

| Preset                   | What it does                                                                                                      |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `default`                | Open-ended edit — follows the `prompt` freely. Fallback when no preset matches.                                  |
| `multiple_angles`        | Generate additional angles of the same subject (360° / side views).                                              |
| `relight`                | Re-light the scene — change time of day, lighting direction, warmth, mood.                                       |
| `light_restoration`      | Recover proper exposure/contrast on badly-lit source.                                                             |
| `white_to_scene`         | Take a subject on a plain white background and place it in a described scene.                                    |
| `fusion`                 | Combine elements from multiple reference images into one composition.                                             |
| `add_characters`         | Add new characters to an existing scene, matching style and lighting.                                            |
| `next_scene`             | Generate the "next shot" — same subject, different pose/action/setting continuation.                              |
| `style_consistency`      | Keep visual style consistent across a series of outputs (match an image's look).                                 |
| `subject_consistency`    | Keep the subject (face/body/outfit) consistent while changing scene.                                              |
| `scene_consistency`      | Keep the scene/environment consistent while changing subjects or action.                                          |
| `to_anime`               | Convert realistic input to anime-style.                                                                           |
| `to_3dchibi`             | Convert to 3D chibi / stylized mini-character look.                                                              |
| `to_caricature`          | Exaggerated caricature rendering.                                                                                 |
| `photous`                | Stylized "Photous" signature look (Pruna preset).                                                                 |
| `extract_texture`        | Pull a texture/pattern from an image for reuse.                                                                   |
| `apply_texture`          | Apply an extracted or provided texture onto another subject.                                                      |
| `upscale`                | Upscale / enhance resolution.                                                                                     |
| `anything_to_real`       | Convert AI/illustrated/stylized input to photorealistic.                                                          |
| `white_film_to_rendering` | Take a white-film 3D / clay-render model and produce a realistic rendering.                                      |

Each preset has task-tuned weights behind the scenes — using the right preset usually beats a freeform prompt on `default` for the same job.

## Output

**Bare URI string** — single image. Saved as `prunaai_p-image-edit_0.{ext}` by `run_model.py`.

## Pricing and runtime

**~$0.01 per run** (stated in the model description). Default example ran in **0.91 s** — genuinely sub-second. This is the price/speed benchmark for multi-image editing on Replicate.

## Examples

**Default open-ended edit** (no preset) — simple wardrobe change:

```json
{
  "prompt": "The woman's dress is changed to black",
  "images": ["./portrait.jpg"],
  "aspect_ratio": "1:1"
}
```

```bash
python scripts/run_model.py prunaai/p-image-edit \
    --input-file input.json \
    --output ./out/
```

**Relight a scene** — use the `relight` preset:

```json
{
  "prompt": "warm golden-hour sunset lighting from camera left, long shadows",
  "images": ["./daytime_scene.jpg"],
  "replicate_weights": "relight"
}
```

**Subject consistency** — keep the character while changing context:

```json
{
  "prompt": "image 1 the same person, now standing in a bustling night market, neon signs, street food steam",
  "images": ["./character_hero.jpg"],
  "replicate_weights": "subject_consistency",
  "aspect_ratio": "16:9"
}
```

**Multi-image fusion** — combine subject + scene + style:

```json
{
  "prompt": "place the person from image 1 into the environment of image 2, matching the style of image 3",
  "images": [
    "./subject.jpg",
    "./scene.jpg",
    "./style_reference.jpg"
  ],
  "replicate_weights": "fusion"
}
```

**White background → scene** — for e-commerce / product photography:

```json
{
  "prompt": "a sunlit beach with gentle waves, sand, distant palm trees",
  "images": ["./product_white_bg.png"],
  "replicate_weights": "white_to_scene",
  "aspect_ratio": "1:1"
}
```

**Anything → real** — convert an AI illustration or 3D render to photoreal:

```json
{
  "prompt": "photorealistic, natural lighting, real-world texture",
  "images": ["./ai_illustration.png"],
  "replicate_weights": "anything_to_real"
}
```

**Multi-angle generation** — get additional views of one subject:

```json
{
  "prompt": "generate a 3/4 angle and a profile view of this character",
  "images": ["./character_front.jpg"],
  "replicate_weights": "multiple_angles"
}
```

## Strengths / gotchas

**Good at:**

- Sub-second, sub-cent edit operations at production quality
- Matching a specific task to one of 20 preset weight sets — dramatically better than open-ended prompting on general editors for the tasks covered
- Multi-image composition (character + scene, subject + style, fusion)
- Batch workflows where cost×volume matters (27M runs is not an accident)

**Gotchas:**

- **Pick the right `replicate_weights`.** `default` works for freeform edits but consistently loses to the task-specific preset when one fits. If your task maps to one of the 20, use it.
- **First image in `images` is the main subject.** Order matters — for "place subject into scene" workflows, pass subject first, scene references after.
- **`turbo: true` by default.** Leave on for ~95% of work; only turn off for complex multi-element composites where you see quality degradation you can't fix with a better prompt.
- **Prompt can reference images as `image 1`, `image 2`** — use this explicitly in multi-image prompts ("use the background from image 2"). Ambiguous prompts on multi-image inputs degrade quality.
- **Safety checker on by default.** Keep on for user-facing work. Disabling is for trusted pipelines only.
- **Not for generation-from-scratch.** This is an *editor* — pass at least one image. For pure T2I, use the companion `prunaai/p-image`.
- **Output quality tops out below Flux-2-Pro** on hero/portfolio work — use Pruna for volume/draft passes, promote winners to Flux-2-Pro if the final needs more polish.
- **Aspect ratio enum is shorter than Flux-2-Pro's** — no `21:9`, `9:21`, `4:5`, `5:4`, or `custom` width/height. Constrain your work to the 7 listed ratios or `match_input_image`.
- **Version pin:** `prunaai/p-image-edit:05a6b136010c1590ff0de1a473b5bc8a5aa221359229f9a69b230d093503eae0`. Pin for large batch runs since Pruna iterates frequently.
