# lucataco/realistic-vision-v5.1

Model page: https://replicate.com/lucataco/realistic-vision-v5.1

A cog-packaged implementation of **Realistic Vision v5.1** (with baked-in VAE) — one of the most popular photoreal **SD 1.5** community fine-tunes. Cheap, fast (~2s predict on an A40 at 512×728), and still very strong for portraits, skin, and natural lighting. It is, however, **dated**: SD1.5-era resolution limits, no native prompt-weighting syntax beyond the legacy `(token:1.4)` form, no text-in-image, no multilingual, no built-in img2img on this endpoint.

## When to pick v5.1 over alternatives

- **Pick it over Flux-dev / SDXL** when you want a **cheap, sub-3-second** portrait or natural-skin photo and you don't need >768px fidelity, text rendering, or strong prompt-following for complex scenes. v5.1's skin/face aesthetic is still loved.
- **Pick Flux-dev / Flux.1.1-pro / SDXL-based photoreal checkpoints (Juggernaut, RealVisXL) instead** when you need ≥1024px coherence, legible text in image, complex multi-subject scenes, modern prompt understanding, or wide-aspect / high-aspect compositions.
- **Pick newer photoreal offerings (Flux-dev-lora, ideogram-v3, recraft-v3)** when rights-cleanliness, typography, or very high fidelity matter more than speed/cost.

Treat this model as the **"quick portrait draft"** tier in your toolbox.

## Input schema

| Field             | Type    | Required | Default                                                                                                                           | Description                                                                                         |
| ----------------- | ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `prompt`          | string  |          | `"RAW photo, a portrait photo of a latina woman in casual clothes, natural skin, 8k uhd, high quality, film grain, Fujifilm XT3"` | Positive prompt. Legacy SD1.5 `(token:weight)` syntax is honored.                                   |
| `negative_prompt` | string  |          | long SD1.5 boilerplate (see Gotchas — ships with a thorough default)                                                              | Content to exclude. **v5.1 is strongly negative-prompt-dependent** — keep the default or extend it. |
| `steps`           | integer |          | `20`                                                                                                                              | `num_inference_steps`. Range: 0–100. 20–30 is the sweet spot; >30 rarely helps on SD1.5.            |
| `guidance`        | number  |          | `5`                                                                                                                               | CFG / guidance scale. Described range **3.5–7**. Too high → burnt, over-saturated, plastic skin.    |
| `scheduler`       | enum    |          | `"EulerA"`                                                                                                                        | One of `"EulerA"`, `"MultistepDPM-Solver"`. Only two choices on this endpoint (see Gotchas).        |
| `width`           | integer |          | `512`                                                                                                                             | Output width in px. Range: 0–1920. **Keep at 512–768 for best coherence** (SD1.5 native is 512).    |
| `height`          | integer |          | `728`                                                                                                                             | Output height in px. Range: 0–1920. Portrait 512×728 is the default and plays to v5.1's strengths.  |
| `seed`            | integer |          | `0`                                                                                                                               | `0` = random. Max `2147483647`. Set for reproducible generation.                                    |

Note the field is `guidance`, **not** `guidance_scale`. No `init_image` / `strength` / `num_outputs` — this endpoint is txt2img single-image only; loop `run_model.py` if you need a batch.

## Output

A **single URI string** to the generated **PNG** (not an array). Saved as `lucataco_realistic-vision-v5.1_0.png`.

## Pricing

Not published as a fixed per-run price on the model page — billed **per runtime** on Replicate GPU (the cog config targets Nvidia A40). Default example completed in **~2 seconds** of predict time (~3.3s total). On the A40 tier this puts a typical single-image run in the **~$0.001–0.003** range — essentially free for iteration. Confirm in the playground estimator at https://replicate.com/lucataco/realistic-vision-v5.1 for a specific resolution/steps config.

## Examples

**Portrait (where this model shines) — minimal args, rely on the excellent default negative prompt:**

```bash
python scripts/run_model.py lucataco/realistic-vision-v5.1 \
    --input '{
      "prompt": "RAW photo, close-up portrait of a 30-year-old fisherman at dawn, weathered skin, salt-and-pepper stubble, wool sweater, soft golden window light, shallow depth of field, 85mm f/1.4, natural skin texture, film grain, Kodak Portra 400",
      "width": 512,
      "height": 768,
      "steps": 25,
      "guidance": 5,
      "scheduler": "EulerA"
    }' \
    --output ./out/
```

**Explicit negative-prompt example** (the widely-circulated v5.1 "bad anatomy" template — extend for your subject):

```bash
python scripts/run_model.py lucataco/realistic-vision-v5.1 \
    --input '{
      "prompt": "RAW photo, a woman standing in a sunlit kitchen, natural skin, freckles, soft morning light, 8k uhd, high quality, film grain, Fujifilm XT3",
      "negative_prompt": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, plastic skin, airbrushed, overexposed",
      "width": 512,
      "height": 768,
      "steps": 30,
      "guidance": 4.5,
      "scheduler": "MultistepDPM-Solver",
      "seed": 42
    }' \
    --output ./out/
```

**Full-body / scene at the upper edge of comfortable SD1.5 resolution:**

```bash
python scripts/run_model.py lucataco/realistic-vision-v5.1 \
    --input '{
      "prompt": "RAW photo, full body shot of a hiker on a rocky ridge at sunset, backpack, wind-tousled hair, warm orange side light, crisp air, dramatic mountain backdrop, 35mm lens, natural skin, film grain",
      "width": 640,
      "height": 960,
      "steps": 28,
      "guidance": 5.5,
      "scheduler": "EulerA"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- **Portraits, faces, natural skin** — the whole reason v5.1 is still used.
- Speed: ~2s predict at 512×728 on A40.
- Cost: cents per hundred images; ideal for iteration/grids.
- Responds well to film-emulation prompts ("Kodak Portra 400", "Fujifilm XT3", "film grain").

**Gotchas:**

- **SD1.5 resolution ceiling.** Stay in **512–768px** on the short edge. Going much past 768×1024 produces doubled heads, cloned limbs, and texture smearing (no built-in hires-fix on this endpoint — if you need ≥1024, upscale afterwards with a separate model like `philz1337x/clarity-upscaler` or `nightmareai/real-esrgan`).
- **Negative-prompt dependency.** v5.1 without a strong negative prompt looks noticeably worse — leave the default negative_prompt in place unless you know what you're replacing it with.
- **Scheduler choice is limited here.** This endpoint exposes only `EulerA` and `MultistepDPM-Solver`. The community consensus favorite **"DPM++ 2M Karras"** is NOT available on this wrapper — for that you'd need a different cog. `MultistepDPM-Solver` is the closest in spirit; try it when `EulerA` gives you soft/washed-out results. Stick with `EulerA` as the safe default.
- **Field name is `guidance`, not `guidance_scale`** — passing `guidance_scale` will be silently ignored and the default used.
- **No text-in-image.** Any requested signs, captions, or labels will render as illegible glyph-soup. Use Ideogram / Flux-dev for typography.
- **Not multilingual.** English prompts only; other languages degrade fast.
- **Prompt-following is SD1.5-era.** Multi-subject scenes ("a man AND a woman, each wearing X"), complex spatial relations, and counting all fail more than they succeed — reach for Flux-dev for that.
- **Output is PNG.** Expect ~0.5–1.5 MB per image at default sizes.
- `seed: 0` means random, not "use seed 0". To actually pin seed 0, pass `1` (or any value ≥1).
- Implementation source: https://github.com/lucataco/cog-realistic-vision-v5.1
