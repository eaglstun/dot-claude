# cjwbw/semantic-segment-anything

Model page: <https://replicate.com/cjwbw/semantic-segment-anything>

Semantic Segment Anything (SSA) — **automatic dense segmentation + semantic labeling**. Runs SAM to generate masks for every region in an image, then a separate classifier assigns a class label to each mask. The result is a fully labeled segmentation map of the whole image, no prompts required. GitHub: <https://github.com/chenxwh/Semantic-Segment-Anything>.

## When to pick SSA over alternatives

- **Pick it over `schananas/grounded_sam`** when you want to label _every_ region, not just the objects matching a text prompt. Grounded SAM is prompt-driven ("find the dog") and returns only matching masks; SSA returns the whole scene, labeled.
- **Pick it over `meta/sam-2`** when you need class names, not just masks. SAM/SAM-2 are pure segmenters — they produce shapes but no idea what the shapes are. SSA adds the "what" on top.
- **Sweet spot:** "label every region in this photo" — scene parsing, dataset annotation, automatic alt-text per region, downstream pipelines that need class-aware masks.
- **Skip it** when you already know what you're looking for (use grounded SAM) or when you only need pixel-perfect masks without labels (use SAM-2).

## Input schema

| Field         | Type         | Required | Default | Description                                                                                       |
| ------------- | ------------ | -------- | ------- | ------------------------------------------------------------------------------------------------- |
| `image`       | string (URI) | ✅       | —       | Input image. Local paths are auto-uploaded by `run_model.py`.                                     |
| `output_json` | boolean      |          | `true`  | Also return the raw per-mask JSON (class names, scores, mask metadata) alongside the labeled PNG. |

Schema note: **this is the entire input surface.** No model-size toggle (vit-b/l/h), no classifier selection, no threshold. The replica of the upstream repo hard-codes those choices; you get one segmentation pipeline, take it or leave it. If you need to tune SAM size or swap the classifier, fork the repo — the Replicate endpoint does not expose those.

## Output

A **dict** with two file keys (confirmed from `default_example`):

| Key        | Type         | Description                                                                                                 |
| ---------- | ------------ | ----------------------------------------------------------------------------------------------------------- |
| `img_out`  | string (URI) | The semantic-labeled segmentation PNG (colored overlay, one color per class).                               |
| `json_out` | string (URI) | Per-mask JSON with class names, confidence scores, and mask metadata. Only present when `output_json=true`. |

`run_model.py` saves each key as a separate file with the key appended as a suffix:

- `cjwbw_semantic-segment-anything_img_out.png`
- `cjwbw_semantic-segment-anything_json_out.json`

Typical run time is ~45–120 seconds (SAM dense mask generation is the bottleneck).

## Pricing

**Unpublished** on the model page — no per-run price or per-second rate listed. Billed at Replicate's standard per-second GPU rate for the hardware the model is pinned to (historically an A100-class GPU). Expect a few cents per image in the absence of an official number; benchmark a couple of runs if cost matters.

## Examples

**Basic scene labeling** — let SSA label everything in the photo:

```bash
python scripts/run_model.py cjwbw/semantic-segment-anything \
    --input-file input.json \
    --output ./out/
```

```json
{
  "image": "./street_scene.jpg"
}
```

**Labeled PNG only** (skip the JSON if you only need the overlay):

```bash
python scripts/run_model.py cjwbw/semantic-segment-anything \
    --input-file input.json \
    --output ./out/
```

```json
{
  "image": "https://example.com/kitchen.jpg",
  "output_json": false
}
```

**Full output for downstream processing** (keep the JSON so you can filter masks by class name):

```bash
python scripts/run_model.py cjwbw/semantic-segment-anything \
    --input-file input.json \
    --output ./out/
```

```json
{
  "image": "./dataset/img_0042.png",
  "output_json": true
}
```

## Strengths / gotchas

**Good at:**

- Fully automatic — no prompts, no bounding boxes, no clicks. Point it at an image, get back a labeled segmentation map.
- Dense coverage — every region gets a mask, including background/stuff classes (sky, road, grass), not just foreground objects.
- Pairs naturally with downstream filtering: load the JSON, grep for the class you want, pull the matching mask.

**Gotchas:**

- **No model-size knob.** The schema does not expose vit-b / vit-l / vit-h selection. Whatever the repo ships with is what you get — you cannot trade speed for quality on this endpoint. (For reference, upstream: vit-b is fastest but misses small masks, vit-h is slowest and most thorough.)
- **Label quality depends on the classifier's training set.** The labels come from a COCO-style / ADE20K-style taxonomy — "person", "car", "dog", "sky", "tree", "road" work well; novel, domain-specific, or fine-grained concepts ("golden retriever", "MacBook Pro", specific product names) will get coerced to the nearest training class or mislabeled.
- **Tiny objects get missed or mislabeled.** SAM's automatic mask generator has a minimum region size; small distant objects often get absorbed into a larger mask or dropped. If you care about small objects, use grounded SAM with an explicit text prompt instead.
- **JSON output format:** an array of per-mask records containing at minimum the class name/ID, confidence, and mask metadata (bbox, area, and typically an RLE-encoded mask). Consumers should decode the mask field with pycocotools or equivalent; the colored `img_out` PNG is for visualization, not programmatic use (colors are assigned arbitrarily).
- **Always a dict output** — even with `output_json=false`, `run_model.py` will save a dict with at least `img_out`. Scripts that assume a single-URI output will break; iterate over the dict keys.
- **~1–2 minute latency per image** is typical. Not suitable for real-time use; batch overnight for dataset-scale jobs.
