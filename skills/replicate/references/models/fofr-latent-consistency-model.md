# fofr/latent-consistency-model

Model page: <https://replicate.com/fofr/latent-consistency-model>

A cog-packaged **Latent Consistency Model (LCM)** — a distilled Stable Diffusion 1.5 variant that generates high-quality images in **1–8 denoising steps** instead of the usual 20–50, roughly **10× faster** per image. Self-described as "super-fast, 0.6s per image." Supports txt2img, img2img, large batching (up to 50 images per call), and Canny ControlNet in a single endpoint. Runs on A100 (80GB).

## When to pick LCM over alternatives

- **Pick LCM over full SD1.5 (`lucataco/realistic-vision-v5.1`)** when you want throughput / real-time-feel iteration and can accept slightly less refined output. Same SD1.5-era aesthetic family, but ~5–10× fewer steps per image.
- **Pick LCM over SD-turbo / SDXL-turbo** when you're already anchored to the SD1.5 community/LoRA aesthetic and want batching + ControlNet in one endpoint. Turbo models are a different family (ADD distillation, not consistency distillation) targeting the same speed goal — test both for your subject.
- **Pick LCM over Flux-schnell** when cost matters more than prompt-following or modern fidelity. Flux-schnell is a stronger modern model; LCM is cheaper per image and supports batching + ControlNet out of the box.
- **Pick Flux-dev / SDXL / Flux-schnell instead** when you need ≥1024px coherence, text-in-image, complex multi-subject scenes, or modern prompt understanding. LCM inherits SD1.5's ceiling.

Sweet spot: **real-time-ish generation, large batch jobs, grids/variations, and anywhere speed/cost > peak quality.**

## Input schema

| Field                           | Type         | Required | Default                      | Description                                                                                                                                      |
| ------------------------------- | ------------ | -------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `prompt`                        | string       |          | cyborg self-portrait example | Positive prompt. **Multiple prompts: one per line** — the model batches across lines.                                                            |
| `width`                         | integer      |          | `768`                        | Output width. Lower if OOM. SD1.5 lineage — stay 512–768 on the short edge.                                                                      |
| `height`                        | integer      |          | `768`                        | Output height. Same caveat as width.                                                                                                             |
| `sizing_strategy`               | enum         |          | `"width/height"`             | `"width/height"` (use the fields), or resize based on input image / control image.                                                               |
| `image`                         | string (URI) |          | —                            | Input image for **img2img** mode. Local paths are auto-uploaded by `run_model.py`.                                                               |
| `prompt_strength`               | number       |          | `0.8`                        | img2img strength. `0` = keep input, `1` = full destruction of input info. Range 0–1.                                                             |
| `num_images`                    | integer      |          | `1`                          | Images per prompt. **Range 1–50** — this is the batching lever; LCM's whole pitch is cheap large batches.                                        |
| `num_inference_steps`           | integer      |          | `8`                          | Denoising steps. **Range 1–50, but recommend 1–8.** This is LCM's headline feature — defaults here are _much lower_ than normal SD. See gotchas. |
| `guidance_scale`                | number       |          | `8`                          | CFG. **Schema range 1–20, but LCM-native sweet spot is ~1–2.** The `8` default is SD-ish, not LCM-ish — reduce it. See gotchas.                  |
| `lcm_origin_steps`              | integer      |          | `50`                         | Internal LCM schedule anchor. Leave at default unless you know what you're doing.                                                                |
| `seed`                          | integer      |          | random                       | Leave blank to randomize.                                                                                                                        |
| `control_image`                 | string (URI) |          | —                            | Image for **Canny ControlNet** conditioning.                                                                                                     |
| `controlnet_conditioning_scale` | number       |          | `2`                          | ControlNet strength. Range 0.1–4.                                                                                                                |
| `control_guidance_start`        | number       |          | `0`                          | When (0–1 of schedule) ControlNet starts influencing.                                                                                            |
| `control_guidance_end`          | number       |          | `1`                          | When (0–1 of schedule) ControlNet stops influencing.                                                                                             |
| `canny_low_threshold`           | number       |          | `100`                        | Canny edge detector low threshold (1–255).                                                                                                       |
| `canny_high_threshold`          | number       |          | `200`                        | Canny edge detector high threshold (1–255).                                                                                                      |
| `archive_outputs`               | boolean      |          | `false`                      | If true, outputs are bundled into an archive. Leave off for normal use.                                                                          |
| `disable_safety_checker`        | boolean      |          | `false`                      | API-only. Disables NSFW check.                                                                                                                   |

Note: **no `negative_prompt`** — LCM's aggressive distillation means a negative-prompt branch would double the per-step cost and defeat the purpose. If you need strong negative guidance, use full SD1.5 or SDXL instead.

## Output

An **array of image URIs** (JPG). Length equals `num_images` × (number of prompt lines). Even for `num_images: 1` with a single prompt, output is a one-element list — unwrap accordingly. `run_model.py` saves them as `fofr_latent-consistency-model_0.jpg`, `fofr_latent-consistency-model_1.jpg`, etc.

## Pricing

**~$0.039 per run** on Nvidia A100 (80GB) — roughly **25 runs per $1** per the model page. The raw image generation is ~0.6s, but end-to-end prediction time (cold start + upload) typically lands around ~28s on cold hardware, closer to 1–3s warm. Because a single "run" can emit up to **50 images** (via `num_images: 50`), per-image cost in batch mode is effectively **<$0.001 per image** — one of the cheapest image options on Replicate. Confirm at <https://replicate.com/fofr/latent-consistency-model> for your specific config.

## Examples

**(1) Text-to-image at 4 steps, LCM-native low CFG:**

```bash
python scripts/run_model.py fofr/latent-consistency-model \
    --input '{
      "prompt": "a neon-lit noodle shop at midnight, cinematic, 35mm film, shallow depth of field",
      "width": 768,
      "height": 768,
      "num_inference_steps": 4,
      "guidance_scale": 1.5,
      "num_images": 1
    }' \
    --output ./out/
```

**(2) img2img quick-variant (fast restyle of a reference photo):**

```bash
python scripts/run_model.py fofr/latent-consistency-model \
    --input '{
      "prompt": "same scene, painted in gouache with bold outlines, storybook aesthetic",
      "image": "./reference.jpg",
      "sizing_strategy": "input_image",
      "prompt_strength": 0.55,
      "num_inference_steps": 6,
      "guidance_scale": 1.8,
      "num_images": 1
    }' \
    --output ./out/
```

**(3) Low-CFG batch (4 variants of one prompt in a single call):**

```bash
python scripts/run_model.py fofr/latent-consistency-model \
    --input '{
      "prompt": "product shot of a matte-black ceramic teapot on seamless warm beige paper, soft diffused key light, editorial",
      "width": 768,
      "height": 768,
      "num_inference_steps": 4,
      "guidance_scale": 1.5,
      "num_images": 4
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- **Speed.** 0.6s per image raw; warm batches of 4–8 images complete in a couple of seconds.
- **Cheap batching.** One call can emit up to 50 images at ~flat cost — unbeatable for grids, A/B tests, thumbnailing.
- **Multi-prompt batching.** Put one prompt per line in `prompt` and LCM runs them in the same call.
- **Canny ControlNet** built into the same endpoint — pass `control_image` and you're done.

**Gotchas — read before your first run:**

- **`num_inference_steps` is 1–8, NOT 20–50.** The model's whole point is step-count distillation. **The recommended range is `1–8`; the default is `8`.** Going to 20+ is wasted compute and often _degrades_ output because the LCM schedule is tuned for short trajectories. **If you bring in SD defaults (20/30/50 steps), you will get worse results at higher cost, not better.**
- **`guidance_scale` is ~1–2, NOT 7–8.** Consistency-distilled models break down under normal CFG because the distillation folded classifier-free guidance into the student. The schema allows up to 20 and the endpoint defaults to **`8`, which is too high for LCM** — expect burnt, oversaturated, contrast-crushed output at that setting. **Use `1.0`–`2.0` for normal generation; `~1.5` is a safe default.** This is the single most common mistake with this model.
- **No `negative_prompt` field.** By design — see input schema note. If you're leaning on negative prompts for quality, you're on the wrong model; reach for `lucataco/realistic-vision-v5.1` or SDXL.
- **SD1.5 resolution ceiling.** Keep the short edge at 512–768. Past ~768×1024 expect cloned features and texture smearing, same as vanilla SD1.5.
- **Output is an array even for `num_images: 1`.** Don't assume a single string.
- **Output is JPG** (not PNG). Expect ~100–300 KB per image. Fine for web/grids; if you need PNG for compositing, convert locally or use a different model.
- **`lcm_origin_steps` (default 50) is not your normal step count** — it's an internal schedule anchor. Don't confuse it with `num_inference_steps`.
- Implementation source: <https://github.com/fofr/cog-lcm>
