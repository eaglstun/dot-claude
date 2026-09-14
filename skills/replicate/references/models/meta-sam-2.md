# meta/sam-2

Model page: <https://replicate.com/meta/sam-2>

Meta's official **SAM 2 (Segment Anything v2) for images** — the "automatic mask generator" mode. Given an input image, it sweeps a grid of point prompts across the frame and returns **every plausible object/region** as a separate binary mask, plus a single combined colored overlay. No text, no click points, no boxes: you feed an image, you get back dozens of masks. Think of it as "label everything in this picture." 2x faster than SAM 1 with better occlusion handling. GitHub: <https://github.com/zsxkib/segment-anything-2>. Paper: <https://ai.meta.com/research/publications/sam-2-segment-anything-in-images-and-videos/>.

## When to pick this endpoint vs alternatives

- **`meta/sam-2` (this model)** — image-only, automatic "segment everything." No prompts; you get an exhaustive mask set. Use when you want to enumerate regions for downstream labeling, filtering, or matting pipelines.
- **`meta/sam-2-video`** — sibling endpoint that takes **click coordinates** (`[x,y],[x,y],...`), **click labels** (`1=foreground, 0=background`), and **per-frame tracking** for both images and video. If you want prompt-based precise segmentation (click a specific object and mask just that), **you want `meta/sam-2-video`, not this one.** This slug does not accept click/box prompts.
- **`schananas/grounded_sam`** — text-driven ("segment the red car"). Use when you can describe the target in words.
- **`cjwbw/semantic-segment-anything`** — auto everything + semantic class labels attached. Pick over `meta/sam-2` if you need class names out of the box.

**Sweet spot for this endpoint:** exhaustive unsupervised region proposals for an image (rotoscoping start, dataset labeling, background-removal candidates, "find all the objects" analytics).

## Input schema

| Field                    | Type         | Required | Default | Description                                                                                                       |
| ------------------------ | ------------ | -------- | ------- | ----------------------------------------------------------------------------------------------------------------- |
| `image`                  | string (URI) | ✅       | —       | Input image. Local paths are auto-uploaded by `run_model.py`.                                                     |
| `points_per_side`        | integer      |          | `32`    | Grid density of point prompts per image edge. Higher = more, smaller masks. 32 → 1024 candidate points per image. |
| `pred_iou_thresh`        | number       |          | `0.88`  | Drop mask candidates whose predicted IoU score is below this. Higher = fewer, more confident masks.               |
| `stability_score_thresh` | number       |          | `0.95`  | Drop masks whose binarization stability is below this. Higher = stricter filter.                                  |
| `use_m2m`                | boolean      |          | `true`  | Use the one-step mask-to-mask refinement head. Usually leave on; cleaner boundaries.                              |

**There is no click-point, bounding-box, or mask-input prompt on this endpoint.** If you need those, call `meta/sam-2-video` (which accepts `click_coordinates` as `"[x,y],[x,y],..."` and `click_labels` as `"1,1,0"` — and which also handles single-image inputs).

## Output

```json
{
  "combined_mask": "https://.../combined_mask.png",
  "individual_masks": [
    "https://.../mask_0.png",
    "https://.../mask_1.png",
    "..."
  ]
}
```

- `combined_mask` — a single colored-overlay PNG where every detected region is painted a distinct color on top of the input. One file.
- `individual_masks` — an **array** of PNGs, one per detected region. Each is a binary mask the size of the input image. Count is data-dependent — the official example on a photo of cars returned **46 masks**.

`run_model.py` saves these as `meta_sam-2_combined_mask.png` and `meta_sam-2_mask_0.png`, `meta_sam-2_mask_1.png`, ... `meta_sam-2_mask_N.png`. Expect dozens of files per call with defaults.

## Pricing

**~$0.011 per run** on Nvidia L40S (~90 runs per $1). Typical prediction time ~12 seconds. Cost is per prediction, not per mask — raising `points_per_side` may slow it down but does not inflate price.

## Examples

**Default "segment everything" pass:**

```bash
python scripts/run_model.py meta/sam-2 \
    --input '{
      "image": "./street_scene.jpg"
    }' \
    --output ./out/
```

**Coarser mask set** — drop `points_per_side` to get fewer, larger regions (good for "just give me the main objects"):

```bash
python scripts/run_model.py meta/sam-2 \
    --input '{
      "image": "./portrait.jpg",
      "points_per_side": 16,
      "pred_iou_thresh": 0.92,
      "stability_score_thresh": 0.96
    }' \
    --output ./out/
```

**Fine-grained / aggressive** — raise `points_per_side` and lower thresholds to catch small objects and textures (product photos, microscopy, dense scenes):

```bash
python scripts/run_model.py meta/sam-2 \
    --input '{
      "image": "./dense_storefront.jpg",
      "points_per_side": 64,
      "pred_iou_thresh": 0.80,
      "stability_score_thresh": 0.90,
      "use_m2m": true
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Exhaustive, prompt-free region proposals — one API call, dozens of clean masks.
- Handles occlusion and nested objects better than SAM 1.
- Stable binary masks with sharp edges thanks to the M2M refinement head.
- Fast and cheap enough to run over large image sets.

**Gotchas:**

- **This endpoint does NOT accept click points, bounding boxes, or mask prompts.** Input is just an image plus a few sampling/filter knobs. If you need "mask the thing I clicked" or "mask what's inside this box," switch to **`meta/sam-2-video`** (yes, despite the name, it accepts images too — the variant is named for its video capability but works on single images and is the one with prompt support). On `sam-2-video`, `click_coordinates` are **pixel [x,y] with origin at the top-left** passed as a string like `"[450,300],[600,420]"`, and `click_labels` are **`1=foreground, 0=background`** as `"1,0"`.
- **Video is NOT supported on this slug.** `meta/sam-2` takes a single image. For video tracking, use `meta/sam-2-video`.
- **Output mask count is unpredictable** — could be 5, could be 100+. Plan disk / UI accordingly. The default example returns ~46 masks for a busy street scene.
- **Masks are unordered and unlabeled.** `mask_0` is not "the largest" or "the foreground" — order is arbitrary. Sort by pixel count, centroid, or IoU against your ROI if you care.
- **Masks can overlap.** Multiple masks in `individual_masks` may cover the same pixel (nested regions). Don't assume mutual exclusivity.
- Raising `points_per_side` past 64 yields diminishing returns and slower runs; lower `pred_iou_thresh` first to surface missed regions.
- Only the **large** SAM 2 checkpoint is exposed on this endpoint — no base/small variants.
