# fermatresearch/magic-image-refiner

Model page: https://replicate.com/fermatresearch/magic-image-refiner

ControlNet + SD 1.5–style img2img detail/refinement pass, pitched by the author as "a better alternative to SDXL refiners." Give it an image plus an optional prompt and it re-renders with added texture, skin detail, micro-contrast, and an optional mild upscale to 1024 or 2048. Also supports **selective refinement via `mask`** (inpainting) and **prompt-guided detail injection**.

## When to pick it over alternatives

- **Pick it over Topaz / clarity-upscaler / Magnific clones** when you want _prompt-steerable_ refinement cheap (~$0.05/run on L40S) rather than a pure, content-agnostic upscaler. You can tell it what the image should be, not just "make it sharper."
- **Pick it over SeeSR** when you want a creativity knob and ControlNet-style structural fidelity rather than semantic super-resolution that locks closely to the input.
- **Pick Topaz / topazlabs-image-upscale instead** for high-quality commercial upscaling with no hallucination — magic-image-refiner will invent detail and can drift.
- **Pick SDXL refiner / clarity-upscaler instead** if you specifically need SDXL-native latents or 4×+ upscale ratios. This model tops out at **2048** on the long edge.
- **Sweet spot:** polish an AI-generated image (SDXL/Flux output) — add skin pores, fabric weave, realism — while keeping composition via ControlNet.

## Input schema

| Field             | Type         | Required | Default                                                                                                                          | Description                                                                                                                          |
| ----------------- | ------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `image`           | string (URI) | ✅       | —                                                                                                                                | Image to refine. Local paths are auto-uploaded by `run_model.py`.                                                                    |
| `prompt`          | string       | ✅       | —                                                                                                                                | What the refined image should look like. Drives added detail. Can be short ("UHD 4k photograph, detailed skin").                     |
| `mask`            | string (URI) |          | —                                                                                                                                | Optional. Same dimensions as `image`. White areas are refined, black areas are preserved. Turns the model into a targeted inpainter. |
| `resolution`      | enum         |          | `"original"`                                                                                                                     | One of `"original"`, `"1024"`, `"2048"`. Long-edge target. `original` preserves input dimensions (no upscale).                       |
| `resemblance`     | number       |          | `0.75`                                                                                                                           | ControlNet conditioning scale — how tightly the output follows the input's structure. Range 0–1.                                     |
| `creativity`      | number       |          | `0.25`                                                                                                                           | Denoising strength. 0 = identity, 1 = total destruction of the original. Range 0–1.                                                  |
| `hdr`             | number       |          | `0`                                                                                                                              | HDR / local-contrast boost on the input before refinement. Range 0–1.                                                                |
| `scheduler`       | enum         |          | `"DDIM"`                                                                                                                         | One of `"DDIM"`, `"DPMSolverMultistep"`, `"K_EULER_ANCESTRAL"`, `"K_EULER"`.                                                         |
| `steps`           | integer      |          | `20`                                                                                                                             | Diffusion steps. 20 is plenty; >30 rarely helps.                                                                                     |
| `guidance_scale`  | number       |          | `7`                                                                                                                              | Classifier-free guidance. Range 0.1–30. Lower (3–5) when `guess_mode=true`.                                                          |
| `seed`            | integer      |          | random                                                                                                                           | For reproducibility.                                                                                                                 |
| `negative_prompt` | string       |          | `"teeth, tooth, open mouth, longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, ..."` | Content to avoid. Default is tuned for portraits — override if refining non-portrait imagery.                                        |
| `guess_mode`      | boolean      |          | `false`                                                                                                                          | ControlNet "guess mode" — the encoder tries to infer content without the prompt. Use `guidance_scale` 3–5 when enabled.              |

## Output

An **array** of URI strings (typically length 1 — a single PNG). `run_model.py` saves the first as `fermatresearch_magic-image-refiner_0.png`.

## Pricing

**~$0.05 per run** (roughly 20 runs per $1) on Nvidia L40S. Typical completion ~52 seconds, though the default example at 20 steps / 512-ish input finishes in ~3.4 seconds — so cost scales with `resolution` and `steps`.

## Examples

**Basic refine of a noisy AI-generated image** (defaults are already tuned well for this):

```bash
python scripts/run_model.py fermatresearch/magic-image-refiner \
    --input '{
      "image": "./sdxl_output.png",
      "prompt": "UHD 4k photograph, sharp focus, detailed skin texture, natural lighting",
      "resolution": "1024",
      "creativity": 0.25,
      "resemblance": 0.75
    }' \
    --output ./out/
```

**Prompt-guided detail pass** (push harder — add specific texture while holding structure):

```bash
python scripts/run_model.py fermatresearch/magic-image-refiner \
    --input '{
      "image": "./portrait.png",
      "prompt": "hyperrealistic portrait, visible skin pores, subsurface scattering, wool sweater fibers, shallow depth of field",
      "resolution": "2048",
      "creativity": 0.45,
      "resemblance": 0.85,
      "hdr": 0.2,
      "steps": 25,
      "scheduler": "DPMSolverMultistep",
      "guidance_scale": 7.5
    }' \
    --output ./out/
```

**Masked selective refinement** (inpaint just the face region of an otherwise good image):

```bash
python scripts/run_model.py fermatresearch/magic-image-refiner \
    --input '{
      "image": "./scene.png",
      "mask": "./face_mask.png",
      "prompt": "detailed photorealistic face, natural skin",
      "resolution": "original",
      "creativity": 0.35,
      "resemblance": 0.8
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Cheap (~$0.05) prompt-steerable polish for AI-generated images.
- ControlNet preserves composition even at higher `creativity`.
- Portrait-friendly default `negative_prompt` (teeth/anatomy fixes baked in).
- Supports masked inpainting in the same endpoint — no separate model needed.
- Fast on L40S — viable for batch iteration loops.

**Gotchas:**

- **`creativity` vs `resemblance` is the main tuning axis.** Too creative (>0.5) and it drifts from the input — new features, changed eye color, altered composition. Too low (<0.15) and nothing visibly changes. The default pair (0.25 / 0.75) is a safe polish. For "add real detail" bump `creativity` to 0.35–0.45 and raise `resemblance` to 0.85.
- **Base model is SD 1.5-era**, not SDXL — so very high-resolution native outputs aren't its strength. Cap at `resolution: "2048"` (schema max). For 4×+ upscales, chain into a dedicated upscaler.
- **Aspect-ratio preservation** follows `resolution`: `original` keeps dimensions; `1024` / `2048` scale the **long edge** to that value and preserve aspect.
- **Default `negative_prompt` is portrait-tuned** (`teeth, tooth, open mouth, bad anatomy, ...`). If refining landscapes, products, or illustrations, override it or results can under-refine expected content (e.g., a landscape photo's default negatives do nothing useful).
- **Photoreal vs illustrated inputs:** trained/tuned for photoreal. Illustrated inputs with low `creativity` work fine, but raising `creativity` on illustrations tends to drag them toward photoreal — preserve style with `creativity ≤ 0.2` or add stylistic anchors to the prompt ("flat vector illustration, cel-shaded, no photorealism").
- **Scheduler effects:** `DDIM` (default) is the most faithful. `DPMSolverMultistep` adds micro-detail at the same step count. `K_EULER_ANCESTRAL` introduces more variation per seed — useful for exploring but less deterministic.
- **Output is an array**, not a single string — index `[0]` when wiring the response.
- **Mask must match image dimensions exactly** — resize before uploading or the API will reject or produce garbage.
- README on Replicate says "documentation is unavailable" — the schema + GitHub repo (https://github.com/BatouResearch/magic-image-refiner) are your only sources.
