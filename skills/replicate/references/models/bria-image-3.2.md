# bria/image-3.2

Model page: https://replicate.com/bria/image-3.2

BRIA Image 3.2 — a commercial-ready, 4B-parameter text-to-image model trained **entirely on licensed data**. Positioned as the lightweight, fast, rights-clear workhorse: exceptional aesthetics and competitive text rendering at a fraction of the compute of bigger models. Bria evaluates it "on par to other leading models in the market" while remaining safe for commercial/enterprise use.

## When to pick image-3.2 over alternatives

- **Pick it over Flux / SDXL / Ideogram** when you need legally-clean output (no scraped training data) for commercial deployment. Same rights-clear pitch as `bria/fibo`.
- **Pick it over `bria/fibo`** when you want fast, simple, text-only prompting at a smaller model size (4B vs 8B). `image-3.2` is the general-purpose aesthetic generator; it has no `structured_prompt` / Inspire / Refine modes. If you just want a good-looking, commercially-safe image from a prompt, start here.
- **Pick `bria/fibo` instead of `image-3.2`** when you need structured JSON control over lighting/camera/composition, image-guided (Inspire) generation, or round-trippable refinement.
- **Pick Flux / SDXL / Ideogram instead** for LoRA ecosystems, reference-image conditioning, or higher-fidelity text-in-image rendering.

## Input schema

| Field                | Type         | Required | Default | Description                                                                                                                           |
| -------------------- | ------------ | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`             | string       | ✅       | —       | Free-text prompt for image generation.                                                                                                |
| `negative_prompt`    | string       |          | —       | Content to exclude from the image.                                                                                                    |
| `aspect_ratio`       | enum / float |          | `"1:1"` | One of `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"` — or a custom float between `0.5` and `3.0`. |
| `guidance_scale`     | number       |          | —       | Prompt adherence. **Range: 3–5** (schema enforces this — the description says "1–10" but the min/max cap is 3–5).                     |
| `prompt_enhancement` | boolean      |          | `false` | Rewrites the prompt for a more creative, expanded output before generation.                                                           |
| `enhance_image`      | boolean      |          | `false` | Post-processes the output for added detail/clarity.                                                                                   |
| `seed`               | integer      |          | random  | Random seed. Set for reproducible generation.                                                                                         |

No image inputs — this is pure text-to-image. No `structured_prompt`, no reference image, no controlnet.

## Output

An array containing a single URI to the generated **PNG**. Saved as `bria_image-3.2_0.png`.

## Pricing

**Not published on the model page.** Check the playground estimator at https://replicate.com/bria/image-3.2 before running a batch. The default-example run completed in ~8.7 seconds (a typical sub-10s single-image run at 4B params), so cost should be in the cheap-image-model range, but confirm in the playground before large batches.

## Examples

**Basic text-to-image:**

```bash
python scripts/run_model.py bria/image-3.2 \
    --input '{
      "prompt": "Praying mantis perched on a wet leaf, macro photography, shallow depth of field, morning dew",
      "aspect_ratio": "1:1"
    }' \
    --output ./out/
```

**Portrait with prompt enhancement and a fixed seed (reproducible):**

```bash
python scripts/run_model.py bria/image-3.2 \
    --input '{
      "prompt": "editorial portrait of an elderly fisherman at golden hour, windswept hair, cinematic",
      "aspect_ratio": "3:4",
      "guidance_scale": 4,
      "prompt_enhancement": true,
      "seed": 42
    }' \
    --output ./out/
```

**Wide landscape, negative prompt, extra detail pass:**

```bash
python scripts/run_model.py bria/image-3.2 \
    --input '{
      "prompt": "a misty mountain valley at dawn with a lone wooden cabin beside a still lake",
      "negative_prompt": "text, watermark, people, deformed, blurry",
      "aspect_ratio": "16:9",
      "guidance_scale": 5,
      "enhance_image": true
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Rights-clear, commercially-safe output (100% licensed training data).
- Strong aesthetic defaults out of a very small (4B) model — fast and cheap per image.
- Competitive text rendering per Bria's own evals (better than most sub-10B models).
- Wide enumerated aspect-ratio support plus arbitrary float ratios in `[0.5, 3.0]`.

**Gotchas:**

- `guidance_scale` is **capped at 3–5** in the schema despite the "1–10" description — values outside will 422. Safe to omit (lets the model default).
- `aspect_ratio` accepts the listed enum strings _or_ floats in `[0.5, 3.0]`; arbitrary ratio strings outside the enum will reject.
- No image/reference inputs — if you need image-guided generation, use `bria/fibo` (Inspire mode) or a Flux variant instead.
- No `structured_prompt` support — for structured JSON control, use `bria/fibo` instead.
- `prompt_enhancement` rewrites your prompt before generation; if you want exact prompt fidelity, leave it `false`.
- Output is PNG (not WebP/JPEG). Expect ~1–1.5 MB per image at default sizes.
- Bria's commercial license terms apply — verify your usage is within the published license before production deployment.
