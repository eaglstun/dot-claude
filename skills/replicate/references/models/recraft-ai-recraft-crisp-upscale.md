# recraft-ai/recraft-crisp-upscale

Model page: <https://replicate.com/recraft-ai/recraft-crisp-upscale>

Recraft's **"crisp" upscaler** — a single-shot endpoint that sharpens and cleans an image while resizing, **without hallucinating detail**. This is the **faithful / pixel-preserving** half of Recraft's two-upscaler pair: it makes existing pixels bigger and cleaner, rather than re-painting textures. Recraft's own framing: "make images sharper and cleaner, [...] suitable for web use or print-ready materials."

## Crisp vs. Creative — pick the right sibling

| Want                                                           | Use                             |
| -------------------------------------------------------------- | ------------------------------- |
| Bigger, sharper pixels. Don't touch what's there.              | **`recraft-crisp-upscale`** (this model) |
| Add detail, re-paint texture, fill in missing micro-structure. | `recraft-ai/recraft-creative-upscale` |

They share the **exact same API surface** (one input: `image`, no knobs). The only difference is behaviour: crisp preserves, creative invents. If identity / source fidelity matters — real people, product shots, client deliverables, typography, logos — pick crisp. If the source is small generative art and you want it to look "shot at resolution," pick creative.

## When to pick recraft-crisp-upscale over alternatives

- **Pick it over `recraft-ai/recraft-creative-upscale`** when **pixel fidelity matters**. Crisp won't re-dream skin pores or morph faces; creative will. Rule of thumb: anything with a real human, text, or a client brand identity goes through crisp.
- **Pick it over `topazlabs/image-upscale`** when you want a **zero-config, single-call** faithful upscale. Topaz is the other end of the spectrum — five model variants (`Standard V2`, `High Fidelity V2`, `CGI`, `Text Refine`, `Low Resolution V2`), `2x`/`4x`/`6x` factor, face-enhancement pass, subject detection. More control, more decisions, commercial-grade. Recraft's crisp upscaler is "just give me the cleaner version" — no knobs to tune.
- **Pick Topaz instead** when you need a specific upscale factor (Recraft hides it), need output format control (Recraft returns WebP), want tuned variants for documents/text/CGI, or need to hit print-MP targets predictably.
- **Pick it over classical Real-ESRGAN / SeeSR** when your source is already clean (Recraft-native art, flux/sdxl renders, phone photos) and you want a polished "larger & crisper" pass. Use SeeSR / Real-ESRGAN when the source is severely degraded (old photos, heavy JPEG artifacts) and needs restoration, not just enlargement.

## Input schema

| Field   | Type         | Required | Default | Description                                                        |
| ------- | ------------ | -------- | ------- | ------------------------------------------------------------------ |
| `image` | string (URI) | Yes      | —       | Image to upscale. Local paths are auto-uploaded by `run_model.py`. |

That's the entire schema — **one input, zero knobs.** Same shape as `recraft-creative-upscale`: no upscale-factor selector, no fidelity dial, no output-format choice, no seed. Recraft picked defaults and hid them.

## Output

A single URI to the upscaled image — returned as a **WebP** (confirmed from the default example: `tmpo2nljpw_.webp`). Saved by `run_model.py` as `recraft-ai_recraft-crisp-upscale_0.webp`.

Runtime on the default example was **~9 seconds of predict time** for a 191 KB input producing a 1.84 MB output — roughly **5× faster than the creative variant** (~47 s in its default example). The speed gap makes sense: crisp is a cleanup/sharpening pass, creative is a diffusion-style re-paint.

## Pricing

**Not published as a flat per-run number on the model page.** Recraft API models on Replicate are typically priced per output image in the **~$0.04–0.06 range** (for reference, `recraft-ai/recraft-v3` is $0.04/image). The crisp upscaler is usually cheaper than the creative one — the model page at <https://replicate.com/recraft-ai/recraft-crisp-upscale> shows the current per-image price in the playground estimator. Check there before running a batch; don't assume.

## Examples

**Basic crisp upscale of a phone photo** (the identity-safe case — pick this over creative when the subject is a real person):

```bash
python scripts/run_model.py recraft-ai/recraft-crisp-upscale \
    --input '{
      "image": "./portrait.jpg"
    }' \
    --output ./out/
```

**Clean up a product shot for web** (exact colours / texture matter — crisp will not re-paint the label):

```bash
python scripts/run_model.py recraft-ai/recraft-crisp-upscale \
    --input-file input.json \
    --output ./out/
```

...where `input.json` is:

```json
{
  "image": "./product_hero.png"
}
```

**Upscale a remote image by URL** (skip local upload):

```bash
python scripts/run_model.py recraft-ai/recraft-crisp-upscale \
    --input '{
      "image": "https://example.com/my_artwork.png"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- **Pixel-faithful upscales.** No hallucinated skin pores, no morphed facial features, no re-painted textures. Safe for identity-sensitive work, product shots, and typography.
- **Recraft-native art workflows.** If you generated vector-ish / illustration art in Recraft and want a print-ready version **without** stylistic drift, this is the matching upscaler from the same vendor.
- **Fast.** ~9 s predict time in the default example — roughly 5× quicker than the creative sibling. Practical for small batches.
- **Zero-configuration.** One input. Ship it.

**Gotchas:**

- **No upscale-factor knob.** The model decides the output size from the input — you can't force 2× vs 4×. Pre-resize the source if you need a specific target resolution, or use `topazlabs/image-upscale` where `upscale_factor` is explicit.
- **Output is WebP,** not PNG/JPG. If the downstream pipeline expects PNG, add a conversion step. Not configurable via the API.
- **Won't rescue severely degraded sources.** Crisp sharpens and cleans; it doesn't restore. Heavy JPEG artifacts, extreme blur, or tiny thumbnails are better served by `topazlabs/image-upscale` with `Low Resolution V2`, by SeeSR, or by the creative sibling (which *will* invent what's missing, for better or worse).
- **Tuned for Recraft-style generative art first.** It handles photos fine, but the cleanup style is most at-home on illustration / stylised renders. Photo grain and film texture may be slightly smoothed.
- **No face-enhancement pass, no subject detection, no text-aware mode.** If the portrait needs a dedicated face pass or the image is a document/screenshot, reach for `topazlabs/image-upscale` (`face_enhancement`, `Text Refine`).
- **No GitHub / paper / license URL** published on the model page — it's a closed API wrapping Recraft's hosted service. Verify commercial usage terms with Recraft directly before shipping client work.
