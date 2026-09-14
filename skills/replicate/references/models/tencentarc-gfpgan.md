# tencentarc/gfpgan

Model page: <https://replicate.com/tencentarc/gfpgan>

GFPGAN — **blind face restoration using a GAN prior**. Tencent ARC's classic, and one of the most-run models on Replicate (113M+ runs). It leans on a pretrained StyleGAN2 face prior to hallucinate clean face pixels from degraded inputs, with channel-split spatial feature transform layers keeping the output aligned to the original geometry. GitHub: <https://github.com/replicate/GFPGAN>.

## When to pick GFPGAN over alternatives

- **vs `sczhou/codeformer`** (the main competitor): GFPGAN tends to produce **smoother, softer** results with a characteristic "clean skin" look. CodeFormer's codebook-lookup prior often **preserves identity better at high fidelity values** but can look plastic when dialed up. GFPGAN is generally stronger on **old, grainy, film-scanned photos**; CodeFormer more often wins on **over-compressed modern selfies and badly warped AI faces**. Both have vocal fans — if one disappoints, try the other before giving up.
- **Skip it** when the input is already sharp and well-lit — the GAN prior will smooth away real skin texture and the result will look over-processed.
- **Sweet spot:** old family photos, mid-century portraits, low-res thumbnails, mild compression artifacts, AI-generated faces that need a gentle cleanup pass.

## Input schema

| Field     | Type         | Required | Default | Description                                                                                   |
| --------- | ------------ | -------- | ------- | --------------------------------------------------------------------------------------------- |
| `img`     | string (URI) | yes      | —       | Input image. Local paths are auto-uploaded by `run_model.py`.                                 |
| `version` | enum         |          | `v1.4`  | GFPGAN weights. One of `v1.2`, `v1.3`, `v1.4`, `RestoreFormer`. See below for what each does. |
| `scale`   | number       |          | `2`     | Rescaling factor for the whole image. Combines face restoration with Real-ESRGAN upscaling.   |

## Output

A single URI to the restored image (PNG). Saved as `tencentarc_gfpgan_0.png`.

## Pricing

**~$0.0027 per run** on Nvidia L40S — roughly **370 runs per $1**. Predictions typically complete in ~3 seconds. Batch-safe: one of the cheapest models on Replicate.

## Examples

**Default restoration** on an old portrait (v1.4 weights, 2x upscale):

```json
{
  "img": "./old_portrait.jpg"
}
```

```bash
python scripts/run_model.py tencentarc/gfpgan \
    --input-file input.json \
    --output ./out/
```

**Version comparison — v1.3 vs v1.4** (subtle but real differences; run both and pick):

```json
{
  "img": "./grainy_scan.jpg",
  "version": "v1.3",
  "scale": 2
}
```

```bash
python scripts/run_model.py tencentarc/gfpgan \
    --input-file input.json \
    --output ./out/
```

Swap `"version": "v1.3"` for `"v1.4"` and run again to compare. v1.3 is often **gentler and more natural-looking** on clean-ish faces; v1.4 pushes **more detail and slightly stronger identity recovery** but can over-sharpen. No single winner — depends on the input.

**Upscale-plus-restore** (small thumbnail → 4x output):

```json
{
  "img": "./tiny_thumbnail.jpg",
  "version": "v1.4",
  "scale": 4
}
```

```bash
python scripts/run_model.py tencentarc/gfpgan \
    --input-file input.json \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Old film scans, low-contrast vintage portraits, mild-to-moderate noise.
- Multi-face inputs — GFPGAN detects and restores **every** face in the frame, not just the largest one.
- Fast, cheap, predictable — no dials to tune means batch jobs "just work."

**The `version` parameter — what actually changes:**

- `v1.2` → oldest weights here; softer, more aggressive smoothing. Occasionally useful on very rough inputs where newer versions over-sharpen artifacts.
- `v1.3` → **better overall quality.** Good default for general-purpose use. More natural skin, less "AI polish."
- `v1.4` (default) → **more detail and better identity preservation.** Sharper eyes and mouth. Can over-process clean inputs.
- `RestoreFormer` → a different architecture entirely (transformer-based, from the RestoreFormer paper). Included as a sibling option; behaves more like CodeFormer. Try it if v1.3/v1.4 results look too "GAN-ish."

**Gotchas:**

- **Smoothing bias / "AI skin" look.** GFPGAN's signature failure mode: close-up portraits come back with unnaturally clean skin, reduced pores and freckles, and a slight wax-figure quality. If the client cares about skin texture, test `v1.3` (gentler) or switch to CodeFormer at high fidelity.
- **`scale` interacts with input size.** Setting `scale: 4` on a 2000px image produces an 8000px output where the background is Real-ESRGAN-upscaled but face crops were restored at a smaller internal size — the face can end up slightly soft relative to the sharpened background. Keep `scale` modest (2–4) unless the input is genuinely small.
- **No face-specific fidelity knob.** Unlike CodeFormer's `codeformer_fidelity`, GFPGAN has no parameter to trade identity preservation vs aggressive restoration — you pick a version and live with it.
- **No-face inputs.** If the face detector finds nothing, GFPGAN falls back to background upscaling via Real-ESRGAN. You won't get an error, but you also won't get face restoration — the output is essentially just an upscale.
- **Output is always a single PNG** — no intermediate face crops exposed, no side-by-side, no per-face output.
- **No background-enhance toggle.** Real-ESRGAN background upscaling is always applied as part of `scale`. If you want face-only restoration at original background resolution, this model can't do it — use CodeFormer with `background_enhance=false`.
