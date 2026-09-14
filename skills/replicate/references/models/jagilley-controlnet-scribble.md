# jagilley/controlnet-scribble

Model page: <https://replicate.com/jagilley/controlnet-scribble>

ControlNet-scribble = **Stable Diffusion 1.5 guided by a hand-drawn (or algorithmically extracted) scribble**. Feed it a rough black-on-white line drawing plus a text prompt, and it hallucinates a detailed image that follows the scribble's silhouette/composition. This is the **original 2023 ControlNet release** (Lvmin Zhang's paper) — it's old, cheap, well-understood, and still the go-to when all you need is "turn this doodle into a picture."

## When to pick this over newer ControlNets

- **Pick this** for cheap iteration on scribble-to-image, quick brainstorming from doodles, or anywhere the SD 1.5 aesthetic is fine. Billing is per-GPU-second on a T4/A100, usually cents per run.
- **Pick a Flux ControlNet** (e.g. `black-forest-labs/flux-canny-dev`, `xlabs-ai/flux-dev-controlnet`) when you need better prompt adherence, text rendering, anatomy, or higher resolutions — at higher cost.
- **Pick an SDXL-based ControlNet** (e.g. `lucataco/sdxl-controlnet`, `fofr/sdxl-multi-controlnet-lora`) when you want SDXL quality and aspect-ratio flexibility with similar control semantics.
- **Pick sibling `jagilley/*` models** if your control signal isn't a scribble: `controlnet-canny`, `controlnet-hed`, `controlnet-hough`, `controlnet-depth2img`, `controlnet-pose`, `controlnet-seg`.

## Input schema

| Field              | Type         | Required | Default                                                                                                                       | Description                                                                                                       |
| ------------------ | ------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `image`            | string (URI) | ✅       | —                                                                                                                             | Input scribble. Black lines on white background works best. Local paths are auto-uploaded by `run_model.py`.      |
| `prompt`           | string       | ✅       | —                                                                                                                             | Text prompt describing the desired output.                                                                        |
| `num_samples`      | enum string  |          | `"1"`                                                                                                                         | Number of images to generate per run. One of `"1"`, `"4"`. (Higher values may OOM — schema caps at 4.)            |
| `image_resolution` | enum string  |          | `"512"`                                                                                                                       | Output resolution (longest side). One of `"256"`, `"512"`, `"768"`. Schema is a fixed enum — no arbitrary values. |
| `ddim_steps`       | integer      |          | `20`                                                                                                                          | DDIM sampling steps. No hard min/max in schema; ~20–50 is the useful range.                                       |
| `scale`            | number       |          | `9`                                                                                                                           | Classifier-free guidance scale. Range: `0.1`–`30`. Higher = stricter prompt adherence but more artifacts.         |
| `seed`             | integer      |          | random                                                                                                                        | Random seed. Set for reproducibility.                                                                             |
| `eta`              | number       |          | `0`                                                                                                                           | DDIM eta parameter. `0` = deterministic DDIM, `1` = DDPM-like stochasticity.                                      |
| `a_prompt`         | string       |          | `"best quality, extremely detailed"`                                                                                          | Positive prompt suffix appended to `prompt` (ControlNet convention).                                              |
| `n_prompt`         | string       |          | `"longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality"` | Negative prompt. Default is the classic SD 1.5 anti-artifact bundle.                                              |

There is **no scheduler field** on this model — it's DDIM-only (controlled via `ddim_steps` and `eta`). The model does **not** run a scribble-preprocessor on arbitrary photos; the `image` input is assumed to already be a scribble/line drawing. See sibling `controlnet-hed` or `controlnet-canny` if you want to feed a photo instead.

## Output

An **array** of URIs to generated **PNG** files — one per sample. With `num_samples="1"` you get a one-element array; with `num_samples="4"` you get four. Saved as `jagilley_controlnet-scribble_0.png`, `_1.png`, `_2.png`, `_3.png`.

## Pricing

This is an older **public community model** — Replicate bills it by **GPU-seconds on T4 / A100 hardware**, not a fixed per-run price. The default example in the API response ran in ~20s of predict time; a typical `num_samples=1, ddim_steps=20, image_resolution=512` call is **a fraction of a cent to a few cents**. Scale up with `num_samples=4` or `image_resolution=768` and runtime (and cost) roughly scales with it. Confirm current per-second rates at <https://replicate.com/pricing> (look up the hardware this version is pinned to in the model's versions list).

## Examples

**Basic scribble-to-image** (scribble already uploaded somewhere, or a local path):

```bash
python scripts/run_model.py jagilley/controlnet-scribble \
    --input '{
      "image": "./my_scribble.png",
      "prompt": "a photo of a brightly colored turtle in a lush jungle, cinematic lighting",
      "image_resolution": "512",
      "num_samples": "1",
      "ddim_steps": 20,
      "scale": 9
    }' \
    --output ./out/
```

**Hand-drawn doodle, batch of 4 variations** — good for picking the best of a set:

```bash
python scripts/run_model.py jagilley/controlnet-scribble \
    --input '{
      "image": "./doodle.png",
      "prompt": "oil painting of a medieval castle on a hill at sunset",
      "num_samples": "4",
      "image_resolution": "512",
      "ddim_steps": 30,
      "scale": 9,
      "seed": 42
    }' \
    --output ./out/
```

**Higher-fidelity 768 render, stricter prompt adherence:**

```bash
python scripts/run_model.py jagilley/controlnet-scribble \
    --input '{
      "image": "https://example.com/scribble.png",
      "prompt": "ultra-detailed ink-wash illustration of a koi fish, traditional japanese style",
      "image_resolution": "768",
      "num_samples": "1",
      "ddim_steps": 40,
      "scale": 12,
      "a_prompt": "best quality, extremely detailed, masterpiece, fine linework",
      "n_prompt": "blurry, low quality, bad anatomy, extra limbs, text, watermark"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Turning rough doodles into coherent images while respecting the silhouette/composition.
- Cheap, fast iteration — a few cents per run on T4.
- Batch-of-4 mode (`num_samples="4"`) for quick seed-exploration.
- Stable, well-documented behavior — lots of community knowledge around prompt tuning for SD 1.5.

**Gotchas / classic SD 1.5 limitations:**

- **Hands, fingers, anatomy** are unreliable — the default `n_prompt` tries to mitigate, but expect to curate outputs.
- **Text in images is essentially unreadable** — don't ask for signs, captions, or legible writing. Use Flux or Ideogram for text.
- **Resolution is capped at 768** and only comes in three fixed buckets (`256`, `512`, `768`). Non-square outputs are not supported by this endpoint — output is square at the chosen resolution. Upscale separately if you need more.
- **`num_samples` and `image_resolution` are string enums, not integers.** `"num_samples": 1` (int) will 422; pass `"1"` (string). Same for `image_resolution`.
- **Scribble contrast matters a lot.** Best results: clean black lines on white background, ~512px. Low-contrast pencil sketches, photo-extracted edges, or anti-aliased thin lines produce mushy output. If your source is a photo, preprocess via `controlnet-hed` / `controlnet-canny` first, or binarize/threshold the image yourself.
- **Non-scribble inputs (photos, rendered images) get interpreted as scribbles anyway** — the model doesn't preprocess. Expect weird results if you feed a photo directly.
- **No scheduler choice** — DDIM only. Tune via `ddim_steps` and `eta`.
- `scale` above ~15 tends to over-saturate and introduce artifacts; the default `9` is usually fine.
- SD 1.5 base means the aesthetic is dated vs. Flux/SDXL. If that matters, upgrade to a Flux ControlNet.
