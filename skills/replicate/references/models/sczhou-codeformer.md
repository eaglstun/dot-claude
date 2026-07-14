# sczhou/codeformer

Model page: https://replicate.com/sczhou/codeformer

CodeFormer — blind face restoration via a **transformer-based codebook lookup**. A learned discrete codebook holds "clean face" tokens; the transformer predicts the right tokens for a degraded input face, then decodes them back to pixels. The net effect is robust restoration that survives heavy noise, JPEG compression, low resolution, blur, and AI-generation artifacts. GitHub: https://github.com/sczhou/CodeFormer.

## When to pick CodeFormer over alternatives

- **Pick it over GFPGAN / RestoreFormer** when the input is badly degraded (old scans, tiny thumbnails, heavy compression) — the codebook prior is more forgiving of extreme damage. GFPGAN tends to be gentler but can't recover as much detail from truly broken inputs.
- **Pick it over a face-enhance flag inside an upscaler** (e.g. `face_enhancement` in `topazlabs/image-upscale`) when faces are the _point_ of the job and you want a dedicated knob (`codeformer_fidelity`) to trade identity preservation vs aggressive restoration. Topaz-style face-enhance is a subtle pass; CodeFormer can be dialed up to near-synthesis.
- **Skip it** when the input is already high-quality — aggressive restoration will alter the subject's face and is a net loss.
- **Sweet spot:** old photographs, low-res stills from video, over-compressed social-media downloads, and cleaning up AI-generated faces (warped eyes, noisy mouths) before upscaling.
- **"Realism enhancer" for stylized / AI-illustrated portraits:** when a user asks to "make this look real" / "run it through a realism enhancer" on an AI-generated _illustration_ (not a degraded photo), CodeFormer is the go-to — it re-renders the face with photographic skin texture, real catch-lights, and individual hairs while keeping the composition. Use `codeformer_fidelity` ~0.6 to add realism while preserving the character's identity (lower starts inventing a different person). Validated turning a stylized daguerreotype-style Flux portrait into a photoreal one at 0.6 / `upscale: 2`.

## Input schema

| Field                 | Type         | Required | Default | Description                                                                                                          |
| --------------------- | ------------ | -------- | ------- | -------------------------------------------------------------------------------------------------------------------- |
| `image`               | string (URI) | ✅       | —       | Input image. Local paths are auto-uploaded by `run_model.py`.                                                        |
| `codeformer_fidelity` | number       |          | `0.5`   | **The famous "w" parameter.** Range `0.0–1.0`. Low = stronger restoration, high = more faithful to input. See below. |
| `background_enhance`  | boolean      |          | `true`  | Enhance the non-face background with Real-ESRGAN.                                                                    |
| `face_upsample`       | boolean      |          | `true`  | Upsample the restored face crops (recommended when combined with `upscale > 1`).                                     |
| `upscale`             | integer      |          | `2`     | Final upsampling factor applied to the whole image.                                                                  |

## Output

A single URI to the restored image (PNG). Saved as `sczhou_codeformer_0.png`.

## Pricing

**~$0.0041 per run** on Nvidia L40S — roughly **243 runs per $1**. Predictions typically complete in ~5 seconds. This is one of the cheapest models on Replicate; safe to run in batches without worrying about cost.

## Examples

**Basic face restoration** on a portrait (defaults — balanced fidelity, 2x upscale):

```bash
python scripts/run_model.py sczhou/codeformer \
    --input '{
      "image": "./old_portrait.jpg"
    }' \
    --output ./out/
```

**Aggressive restoration** for a badly-degraded image (low fidelity = let the model invent plausible detail):

```bash
python scripts/run_model.py sczhou/codeformer \
    --input '{
      "image": "./tiny_scan.jpg",
      "codeformer_fidelity": 0.1,
      "upscale": 4,
      "background_enhance": true,
      "face_upsample": true
    }' \
    --output ./out/
```

**Identity-preserving pass** on a recognizable subject (high fidelity = stay close to the input face, only lightly clean it):

```bash
python scripts/run_model.py sczhou/codeformer \
    --input '{
      "image": "./celebrity_photo.jpg",
      "codeformer_fidelity": 0.9,
      "upscale": 2
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Severely degraded inputs (low-res, JPEG-compressed, noisy, blurry).
- Restoring AI-generated faces with warped features before upscaling.
- Multi-face images — it detects and restores **all** faces in the frame, not just the largest one. Logs report e.g. `detect 3 faces`.
- Fast and cheap enough to run across entire photo archives.

**The `codeformer_fidelity` (w) parameter — critical to understand:**

- `0.0` → **maximum restoration**. Model leans on the codebook prior and may invent features (eye shape, mouth corners, skin texture). Best for unrecognizable / heavily degraded inputs where you just want "a plausible clean face."
- `0.5` (default) → balanced. Reasonable starting point for unknown inputs.
- `1.0` → **maximum fidelity**. Model stays as close as possible to the input face; least invention but also least cleanup.
- Rule of thumb: **if you care about preserving identity (specific person, client work, family photos), stay ≥ 0.7.** If you just need "any good-looking face" from a broken input, go ≤ 0.3.

**Gotchas:**

- **Aggressive restoration alters identity.** At low fidelity, the output can look like a different person — this is the single most-common complaint. Always compare fidelity sweeps (e.g. 0.3 / 0.5 / 0.7 / 0.9) before committing.
- **No-face images:** if the detector finds no faces, CodeFormer falls back to background-only enhancement (Real-ESRGAN if `background_enhance=true`). You will not get a hard error, but you also won't get face restoration — check logs for `detect 0 faces`.
- **Non-face regions are handled by Real-ESRGAN**, not CodeFormer. If `background_enhance=false`, non-face areas are kept at their original resolution (then rescaled), which can look soft against the sharpened face.
- **`face_upsample` + `upscale > 1`:** without `face_upsample=true`, the face crop stays at its internal restoration size while the background is upscaled, producing a mismatch. Keep both on unless you have a reason.
- **Output is always PNG**, single image — no batch/grid output, no intermediate crops exposed.
- Runs are ~5s on L40S, so the per-run latency is dominated by input upload and output download, not inference.
