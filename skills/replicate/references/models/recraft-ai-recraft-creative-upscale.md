# recraft-ai/recraft-creative-upscale

Model page: <https://replicate.com/recraft-ai/recraft-creative-upscale>

Recraft's **"creative" upscaler** — a single-shot endpoint that enhances details and refines complex elements while resizing. Unlike classical upscalers that preserve pixels, creative upscalers **hallucinate detail**: they re-paint textures, facial features, and fine structures so a small or soft source image looks like it was always high-res. Closest in spirit to Magnific / Clarity-upscaler style "re-imagine" passes rather than traditional super-resolution.

## When to pick recraft-creative-upscale over alternatives

- **Pick it over `topazlabs/image-upscale`** when you want the model to **add** detail and texture, not faithfully preserve pixels. Topaz is more conservative, commercial-grade, with multiple variants, face-enhancement knobs, subject detection, and tunable fidelity — Recraft's creative upscaler is one-knob (just pass the image) and deliberately re-interprets content.
- **Pick it over `cswry/seesr`** when you've generated art in Recraft or with a diffusion model at 512–1024 px and want to scale it up to print size with added texture/detail — not just semantic-aware restoration of a degraded photo. SeeSR targets severely-degraded real-world inputs; creative-upscale targets clean-but-small generative art.
- **Pick it over Magnific clones (e.g. `philz1337x/clarity-upscaler`, `batouresearch/magic-image-refiner`)** when you're already inside the Recraft stack and want a single-call upgrade with no prompt engineering, CFG knobs, or creativity dial to babysit.
- **Pick something else** (Topaz, SeeSR, Real-ESRGAN) when **identity / pixel fidelity matters** (real people, product shots, evidence, printable client deliverables where "drift from the original" is unacceptable).

## Input schema

| Field   | Type         | Required | Default | Description                                                        |
| ------- | ------------ | -------- | ------- | ------------------------------------------------------------------ |
| `image` | string (URI) | Yes      | —       | Image to upscale. Local paths are auto-uploaded by `run_model.py`. |

That's the entire schema — **one input, zero knobs.** No upscale-factor selector, no creativity/fidelity dial, no output-format choice, no seed. Recraft decided the sensible defaults and hid them.

## Output

A single URI to the upscaled image — returned as a **WebP** (confirmed from the default example: `tmps4yon7pj.webp`). Saved by `run_model.py` as `recraft-ai_recraft-creative-upscale_0.webp`.

## Pricing

**Not published as a flat per-run number on the model page.** Recraft API models on Replicate are typically priced per output image in the **~$0.04–0.06 range** (for reference, `recraft-ai/recraft-v3` is $0.04/image), and the creative upscaler is usually a **premium tier** above the base text-to-image. Check the playground price estimator at <https://replicate.com/recraft-ai/recraft-creative-upscale> before running a batch — don't assume.

Runtime on the default example was **~47 seconds of predict time** for a 160 KB input producing a 3.3 MB output — meaningfully slower than a Topaz pass, in line with diffusion-based creative upscalers.

## Examples

**Basic upscale of a small generative image** (the one-liner case — there is no other case):

```bash
python scripts/run_model.py recraft-ai/recraft-creative-upscale \
    --input '{
      "image": "./flux_render_1024.png"
    }' \
    --output ./out/
```

**Upscale a local phone photo** (also just the single input, but via a JSON file for clarity in batch pipelines):

```bash
python scripts/run_model.py recraft-ai/recraft-creative-upscale \
    --input-file input.json \
    --output ./out/
```

...where `input.json` is:

```json
{
  "image": "./photo.jpg"
}
```

**Upscale a remote image by URL** (skip local upload):

```bash
python scripts/run_model.py recraft-ai/recraft-creative-upscale \
    --input '{
      "image": "https://example.com/my_small_artwork.png"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- **Adding texture and micro-detail** — skin pores, fabric weave, foliage leaves, hair strands. The model re-paints these rather than interpolating, so upscaled images look "shot at resolution" rather than "blown up from small."
- **Recraft-native art workflows.** If you generated at 1024 px in Recraft and want a print-ready version, this is the matching upscaler from the same vendor — expect consistent aesthetics.
- **Zero-configuration.** One input. Ship it. No prompt engineering, no CFG sweep, no seed hunt.

**Gotchas:**

- **Creative upscalers change the image.** This is the critical distinction from Topaz / Real-ESRGAN. Expect re-painted skin texture, altered grain, subtly different facial features, and invented micro-detail. **Do not use this for identity-sensitive work** (real people, legal/evidence, product photography where exact colour/texture matters).
- **No creativity/fidelity knob.** You cannot dial it back toward faithful. If you need "a little detail added, mostly preserve pixels" use `topazlabs/image-upscale` with `High Fidelity V2`, or `fermatresearch/magic-image-refiner` with a low creativity setting.
- **No explicit upscale-factor.** The model decides the output size from the input. You can't force 2× vs 4× — you get whatever Recraft's default is for that input. Plan around that, or pre-resize your source if you need a specific target resolution.
- **Output is WebP,** not PNG/JPG. If your downstream pipeline expects PNG, add a conversion step. Not configurable via the API.
- **Tuned for Recraft-style generative art first.** It handles photos, but the detail-hallucination behaviour is most at-home on illustration / stylised renders. Photos can end up with "slightly too-crisp" skin or fabric that reads as AI-touched.
- **~47 s predict time per image** in the default example — slower than a classical upscaler pass. Not a real-time tool.
- **No GitHub / paper / license URL** published on the model page — it's a closed API wrapping Recraft's hosted service. Verify commercial usage terms with Recraft directly before shipping client work.
