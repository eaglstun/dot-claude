# cswry/seesr

Model page: https://replicate.com/cswry/seesr

SeeSR — **Semantics-Aware Real-World Image Super-Resolution** (diffusion-based). A Stable-Diffusion-backed upscaler that uses text/semantic guidance to decide what to sharpen vs what to smooth, and is specifically tuned for _severely degraded_ real-world inputs (JPEG artifacts, noise, low-light compression, historical photos) rather than clean-but-small images. Paper: "SeeSR: Towards Semantics-Aware Real-World Image Super-Resolution." GitHub: https://github.com/lucataco/SeeSR.

## When to pick SeeSR over alternatives

- **Pick SeeSR over `topazlabs/image-upscale`** when the input is badly degraded (heavy noise, ringing, block artifacts) — SeeSR hallucinates plausible detail guided by semantics, Topaz is more conservative/general-purpose and closer-source commercial.
- **Pick SeeSR over Real-ESRGAN / classic GAN upscalers** when you want the model to _understand_ what it's restoring (skin vs fabric vs foliage) instead of applying a uniform sharpening prior. Pair it with `user_prompt` to steer semantics when auto-tagging is uncertain.
- **Pick Real-ESRGAN / Topaz instead** for clean photo inputs where you just need resolution — SeeSR's diffusion pass is slower and can introduce creative-fidelity drift at high CFG.

## Input schema

| Field                  | Type         | Required | Default                                 | Description                                                                                                                                                                   |
| ---------------------- | ------------ | -------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `image`                | string (URI) | ✅       | —                                       | Input (low-resolution / degraded) image. Local paths are auto-uploaded by `run_model.py`.                                                                                     |
| `user_prompt`          | string       |          | `""`                                    | Optional free-text semantic guidance ("a close-up portrait of an elderly woman"). Augments the model's auto-extracted tag prompt. Leave empty to rely purely on auto-tagging. |
| `positive_prompt`      | string       |          | `"clean, high-resolution, 8k"`          | Quality keywords appended to the conditioning.                                                                                                                                |
| `negative_prompt`      | string       |          | `"dotted, noise, blur, lowres, smooth"` | Artifacts to suppress.                                                                                                                                                        |
| `cfg_scale`            | number       |          | `5.5`                                   | Classifier-free guidance scale. Range **0.1–10**. `>1` to enable guidance; higher = stronger prompt adherence but more hallucination.                                         |
| `num_inference_steps`  | integer      |          | `50`                                    | Diffusion steps. Range **10–100**. 30–50 is the sweet spot; >50 rarely pays off.                                                                                              |
| `sample_times`         | integer      |          | `1`                                     | Number of samples to generate per call (returned as an array). Range **1–10**.                                                                                                |
| `latent_tiled_size`    | integer      |          | `320`                                   | Latent-space tile size for the tiled VAE/UNet passes. Range **128–480**. Lower = less VRAM, more tile seams; higher = cleaner but more VRAM.                                  |
| `latent_tiled_overlap` | integer      |          | `4`                                     | Overlap between latent tiles. Range **4–16**. Increase if you see tile boundary artifacts.                                                                                    |
| `scale_factor`         | integer      |          | `4`                                     | Upscale factor. Schema has no explicit min/max; 4× is the trained/default setting. Other integer values accepted but 2× or 4× are safest.                                     |
| `seed`                 | integer      |          | `231`                                   | Random seed (range 0–2147483647). Note the default is **fixed at 231**, not random — set explicitly for varied outputs across runs.                                           |

Notes on prompting: SeeSR internally runs a **DAPE (Degradation-Aware Prompt Extractor)** tagger on the input to derive a semantic "tag prompt" automatically — `user_prompt` is concatenated on top of that, not a replacement. Short noun-phrase prompts work best ("a tabby cat on a sofa"), matching the tag-style conditioning the model was trained with.

## Output

An **array of PNG URIs** (one per sample). Even with the default `sample_times=1` the output is an array of length 1 — iterate, don't index directly if you ever raise sample_times. Saved as `cswry_seesr_0.png`, `cswry_seesr_1.png`, ... by `run_model.py`.

## Pricing

**Not published on the model page** — typical for older community-uploaded diffusion super-res models. Runtime on the default example was ~6 seconds of predict time (tiny input; scales roughly linearly with pixel count and `num_inference_steps`, and multiplicatively with `sample_times`). Check the playground estimator at https://replicate.com/cswry/seesr before running a batch on large inputs.

## Examples

**Basic 4× upscale of a degraded image (auto-tagged, no user prompt):**

```bash
python scripts/run_model.py cswry/seesr \
    --input '{
      "image": "./old_scan.jpg",
      "scale_factor": 4
    }' \
    --output ./out/
```

**Semantic-guided restoration** — help the model when auto-tagging might be ambiguous (e.g. a blurry historical photo):

```bash
python scripts/run_model.py cswry/seesr \
    --input '{
      "image": "./historical_portrait.jpg",
      "user_prompt": "a black-and-white portrait of a young man in a wool suit, close-up, studio lighting",
      "cfg_scale": 6.0,
      "num_inference_steps": 50,
      "seed": 42
    }' \
    --output ./out/
```

**Multi-sample sweep** at lower CFG for a conservative, less-hallucinatory restoration (pick the best of 4):

```bash
python scripts/run_model.py cswry/seesr \
    --input '{
      "image": "./noisy_closeup.png",
      "user_prompt": "macro photograph of a dew-covered leaf",
      "cfg_scale": 3.5,
      "num_inference_steps": 30,
      "sample_times": 4,
      "latent_tiled_size": 384,
      "latent_tiled_overlap": 8
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- **Severely degraded inputs** — the whole point of the model. JPEG block artifacts, heavy sensor noise, compression mush — handled better than Real-ESRGAN / classic GAN upscalers.
- **Semantic-aware sharpening** — distinguishes skin vs fabric vs foliage, so it won't over-sharpen skin into plastic or smooth foliage into mush.
- **Tile-based inference** scales to fairly large inputs without blowing up VRAM (tiled VAE + tiled latent UNet).

**Gotchas:**

- **`seed` default is `231` (fixed), not random.** Back-to-back calls with the same input give identical output — set `seed` explicitly (e.g. to `-1`-equivalent by passing a random int) if you want variation.
- **`cfg_scale` is a hallucination dial.** At >6 the model starts inventing plausible-but-wrong detail (faces can drift identity). For faithful restoration stay in **3.5–5.5**; only push higher when you want stylization.
- **`user_prompt` augments the auto-tag, it doesn't override it** — if the auto-tagger mis-identifies the subject you can't fully suppress that. Try short tag-style phrases over long sentences.
- **Output always an array** even for a single sample. Client code iterating `output[0]` is fine; code treating it as a single URI will break.
- **`scale_factor`** is trained primarily for 4×. 2× works; odd factors or very large factors (8×+) aren't officially supported and may produce tiling artifacts.
- **VRAM / max size.** Very large inputs (multi-megapixel) are handled by tiling but at linearly-increasing cost. If you see tile-seam artifacts, raise `latent_tiled_overlap` to 8–16 and/or lower `latent_tiled_size`.
- **Slower than non-diffusion upscalers.** 50 steps × tiled inference is measured in seconds-to-minutes per image depending on input size — not a real-time pipeline.
- **Output is PNG** (confirmed from default_example output URL extension). Can be multi-MB per sample at 4× of a typical input.
