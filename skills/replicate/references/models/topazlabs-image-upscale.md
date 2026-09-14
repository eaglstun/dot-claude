# topazlabs/image-upscale

Model page: https://replicate.com/topazlabs/image-upscale

Topaz Labs' commercial-grade image upscaler on Replicate. Handles upscaling up to **6×** with five model variants tuned to different source types, plus optional face enhancement and subject-aware processing. Output can go up to **512 MP** — this is a serious tool for print-prep, photo restoration, and cleaning up AI-generated images.

## Model variants (`enhance_model`)

Pick the one that matches your source. Exact strings (case-sensitive):

| Variant                 | When to use                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------- |
| `Standard V2` (default) | General-purpose. Good default for photos from phones/cameras.                                         |
| `Low Resolution V2`     | Very small / highly degraded sources (old web thumbnails, compressed JPEGs).                          |
| `CGI`                   | 3D renders, digital art, vector-looking images.                                                       |
| `High Fidelity V2`      | Preserves fine detail — use when the source is already sharp and you want to scale without softening. |
| `Text Refine`           | Documents, screenshots, anything with readable text.                                                  |

## Input schema

| Field                         | Type         | Required | Default         | Description                                                                                                                                                                         |
| ----------------------------- | ------------ | -------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `image`                       | string (URI) | ✅       | —               | Source image.                                                                                                                                                                       |
| `enhance_model`               | enum         |          | `"Standard V2"` | One of the five variants above.                                                                                                                                                     |
| `upscale_factor`              | enum         |          | **`"None"`**    | `None`, `2x`, `4x`, `6x`. ⚠ Default is `None` — enhancement only, no resolution change.                                                                                             |
| `output_format`               | enum         |          | `"jpg"`         | `jpg` or `png`.                                                                                                                                                                     |
| `subject_detection`           | enum         |          | `"None"`        | `None`, `All`, `Foreground`, `Background`. Limits where enhancement is applied.                                                                                                     |
| `face_enhancement`            | boolean      |          | `false`         | Dedicated face-improvement pass. Most impactful on blurry portraits.                                                                                                                |
| `face_enhancement_strength`   | number       |          | `0.8`           | 0–1. How sharp the enhanced faces are vs. background. Ignored when `face_enhancement` is off.                                                                                       |
| `face_enhancement_creativity` | number       |          | `0`             | 0–1. How freely the model reimagines the face. `0` = preserve features; higher = more creative (and more likely to drift from the subject). Ignored when `face_enhancement` is off. |

Local `image` path auto-uploaded by `run_model.py`.

## Output

A single URI to the upscaled image. Saved as `topazlabs_image-upscale_0.jpg` (or `.png`).

## Pricing

Scales by **output megapixel count**:

| Output size  | Cost  |
| ------------ | ----- |
| 12–24 MP     | $0.05 |
| ~96 MP       | $0.20 |
| 512 MP (max) | $0.82 |

Cost math to keep in mind: a 2048×2048 (4 MP) source at 6x becomes 12288×12288 = **151 MP**. Plan the upscale factor against your source resolution to land in the right cost tier.

## Examples

**Enhance-only (no resolution change) — cheapest pass:**

```bash
python scripts/run_model.py topazlabs/image-upscale \
    --input '{
      "image": "./photo.jpg",
      "enhance_model": "Standard V2"
    }' \
    --output ./out/
```

**2× upscale of a phone photo:**

```bash
python scripts/run_model.py topazlabs/image-upscale \
    --input '{
      "image": "./phone_photo.jpg",
      "enhance_model": "Standard V2",
      "upscale_factor": "2x",
      "output_format": "png"
    }' \
    --output ./out/
```

**Portrait upscale with face enhancement:**

```bash
python scripts/run_model.py topazlabs/image-upscale \
    --input '{
      "image": "./portrait.jpg",
      "enhance_model": "High Fidelity V2",
      "upscale_factor": "4x",
      "face_enhancement": true,
      "face_enhancement_strength": 0.85,
      "face_enhancement_creativity": 0.1
    }' \
    --output ./out/
```

**Restore a low-res web thumbnail:**

```bash
python scripts/run_model.py topazlabs/image-upscale \
    --input '{
      "image": "./tiny_thumbnail.jpg",
      "enhance_model": "Low Resolution V2",
      "upscale_factor": "6x"
    }' \
    --output ./out/
```

**Screenshot / document scan:**

```bash
python scripts/run_model.py topazlabs/image-upscale \
    --input '{
      "image": "./scanned_page.jpg",
      "enhance_model": "Text Refine",
      "upscale_factor": "4x"
    }' \
    --output ./out/
```

**Upscale AI-generated art (flux/sdxl output):**

```bash
python scripts/run_model.py topazlabs/image-upscale \
    --input '{
      "image": "./flux_render.png",
      "enhance_model": "CGI",
      "upscale_factor": "4x"
    }' \
    --output ./out/
```

## Face enhancement tuning

`face_enhancement` runs a dedicated pass on detected faces. Two knobs:

- **`face_enhancement_strength` (default 0.8)** — how sharp faces are relative to the rest. Higher = face pops more; lower = blends naturally.
- **`face_enhancement_creativity` (default 0)** — how much freedom to reimagine features. `0` preserves the actual person; `0.3+` risks identity drift.

**Default recipe for real people:** `strength: 0.8, creativity: 0` — safe, faithful.
**For stylized art / fantasy characters:** bump `creativity: 0.2–0.4` to let it dream in details.
**For group photos:** keep `creativity: 0` — you don't want faces morphing into other people.

## Subject detection

Use `subject_detection` when you want enhancement focused on one region:

- `Foreground` — sharpens the main subject more than the background (natural "depth of field" look)
- `Background` — enhances the background, leaves subject untouched
- `All` — enhances everything equally with subject-aware tuning
- `None` (default) — uniform pass across the whole image

Useful for portraits where you want a crisp subject over a subtly-processed background.

## Gotchas

- **`upscale_factor` defaults to `"None"`.** If you just want to "upscale my image" you must explicitly set `"2x"`, `"4x"`, or `"6x"`. The default pass is enhance-only.
- **Exact model-name casing.** `"Standard V2"` with the space and capital V, not `"standard_v2"`. 422 validation errors usually point here.
- **6× a large input hits the 512 MP cap fast.** A 3000×3000 source (9 MP) at 6× is 324 MP. Know your math before kicking off.
- **Face enhancement creativity at 0.5+** can noticeably change the person. Keep at 0 for identity-preserving work.
- Output format `jpg` is lossy — prefer `png` for art/CGI or when the output is a pipeline input to another model.
