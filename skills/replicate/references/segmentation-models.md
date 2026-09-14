# Segmentation models on Replicate

"Segmentation" here covers producing pixel masks from an image — either for objects you name, for every region the model can find, or for every region plus a class label. Model schemas drift; verify the model page on replicate.com before relying on exact field names or ranges. Per-model deep-dives live in `references/models/`.

Output shapes vary wildly across these three models (4-image array vs dict-of-masks vs dict-with-labels) — see the [Output-shape variance](#output-shape-variance) callout before wiring any of them into a pipeline.

## Selection guide

| I want to…                                   | Use                                                     | Why                                                                                                                           |
| -------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Mask what I say in text**                  | `schananas/grounded_sam`                                | Comma-list of labels → binary mask. No clicks, no UI.                                                                         |
| **Mask everything automatically**            | `meta/sam-2`                                            | Meta official SAM 2 auto-mask-generator. Returns 30–60 masks per image.                                                       |
| **Mask everything + label what it is**       | `cjwbw/semantic-segment-anything`                       | SAM masks plus a classifier head → labeled segmentation map.                                                                  |
| **Click-point or box-prompted segmentation** | `meta/sam-2-video` _(not yet documented in this skill)_ | Different slug — accepts `click_coordinates`, `click_labels`, boxes, and video. See <https://replicate.com/meta/sam-2-video>. |

**Default pick when the user hasn't specified:** if they named a target, use `schananas/grounded_sam`. If they said "segment the image" with no target, use `meta/sam-2`. If they want labels too, use `cjwbw/semantic-segment-anything`.

## Per-model summaries

### schananas/grounded_sam

Text-prompt segmentation via Grounding DINO + SAM. [model](models/schananas-grounded_sam.md).

- **Required:** `image`. **Optional:** `mask_prompt` (comma-list, default `"clothes,shoes"`), `negative_mask_prompt`, `adjustment_factor` (erode/dilate).
- **Output:** an **array of 4 JPEGs** in fixed order — `[annotated, neg_annotated, mask, inverted_mask]`. Usually you want index 2.
- **Gotcha:** the wrapper exposes only those 4 inputs — no `box_threshold` / `text_threshold` knobs from the upstream Grounded-SAM repo. Tuning is via prompt wording and `adjustment_factor`. Silent no-match returns a black mask, not an error.

### meta/sam-2

Meta's official SAM 2 image endpoint in **automatic segment-everything** mode. [model](models/meta-sam-2.md).

- **Required:** `image`. **Optional:** `points_per_side` (default `32`), `pred_iou_thresh`, `stability_score_thresh`, `use_m2m`.
- **Output:** a **dict** `{combined_mask, individual_masks[]}` — one colored overlay PNG plus an array of binary mask PNGs (often 30–60, data-dependent; official example returns 46).
- **Gotcha:** **no** text / click / box / video support on this slug. For prompted or video work use sibling `meta/sam-2-video`. Masks are unordered, unlabeled, and may overlap. ~$0.011/run on L40S.

### cjwbw/semantic-segment-anything

Auto segment-everything **plus** semantic class labels per mask. [model](models/cjwbw-semantic-segment-anything.md).

- **Required:** `image`. **Optional:** `output_json` (default `true`). That is the entire input surface — no SAM-size toggle, no classifier choice, no thresholds.
- **Output:** a **dict** `{img_out, json_out}` — a labeled PNG overlay and a JSON with per-mask class name, score, and mask metadata (typically RLE-encoded).
- **Gotcha:** always returns a dict even with `output_json=false` (`img_out` is still there) — consumers that assume a single-URI output will break. Labels come from a COCO/ADE20K-style taxonomy; fine-grained concepts get coerced. ~1–2 min per image.

## Output-shape variance

This is the defining gotcha of the category — **no two of these models return the same shape**:

| Model                             | Output type         | Shape                                                                          |
| --------------------------------- | ------------------- | ------------------------------------------------------------------------------ |
| `schananas/grounded_sam`          | **Array of 4 URIs** | `[annotated.jpg, neg_annotated.jpg, mask.jpg, inverted_mask.jpg]` (positional) |
| `meta/sam-2`                      | **Dict**            | `{combined_mask: URI, individual_masks: [URI, URI, ...]}`                      |
| `cjwbw/semantic-segment-anything` | **Dict**            | `{img_out: URI, json_out: URI}`                                                |

Implications:

- Code that unpacks Grounded SAM by index won't work on the others.
- `meta/sam-2` produces an **unbounded** number of files per call; budget disk and downstream iteration accordingly.
- Only `cjwbw/semantic-segment-anything` gives you class names — the other two are geometry only.
- Masks from `meta/sam-2` are unordered and can overlap (nested regions). Sort by area / centroid if you care.

## Quick picks

- **Have a text label** ("segment the dog"): `schananas/grounded_sam` with `mask_prompt: "dog"`.
- **Want a full scene decomposition** (no labels needed): `meta/sam-2`.
- **Need per-region labels** for scene parsing / dataset annotation: `cjwbw/semantic-segment-anything`.
- **Need click-point or bounding-box prompting, or video tracking:** `meta/sam-2-video` — **not yet documented in this skill**, see <https://replicate.com/meta/sam-2-video>. Don't try to force `meta/sam-2` into this role; it has no prompt inputs.
