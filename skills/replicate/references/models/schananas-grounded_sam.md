# schananas/grounded_sam

Model page: <https://replicate.com/schananas/grounded_sam>

Grounded SAM — **text-prompt-driven image segmentation**. Combines [Grounding DINO](https://github.com/IDEA-Research/GroundingDINO) (zero-shot object detection from natural-language prompts) with [Segment Anything (SAM)](https://github.com/facebookresearch/segment-anything): DINO turns a comma-separated list of labels into bounding boxes, then SAM promotes each box to a pixel-accurate mask. You name what you want in text, and you get masks back. Billed as the "integral cog of doiwear.it" — its original use case is automated clothing segmentation for virtual try-on. GitHub: <https://github.com/schananas/grounded_sam_replicate>.

## When to pick Grounded SAM over alternatives

- **Pick it over `meta/sam-2`** when you don't want to click points or draw boxes — SAM-2 is prompt-based (clicks/boxes/masks), Grounded SAM is prompt-based on _words_. The sweet spot: "give me a mask of every dog in this photo" from a string, zero UI.
- **Pick it over `cjwbw/semantic-segment-anything`** when you know what you're looking for. Semantic-SAM auto-labels everything in the scene; Grounded SAM only segments what you ask for, which is much cleaner when you want a specific subject.
- **Skip it** when the concept you want is outside Grounding DINO's vocabulary (abstract states, fine-grained attributes, proper nouns, pose-based concepts like "person running"). DINO recognizes common nouns and some short noun phrases; it isn't a VLM.
- **Sweet spot:** isolating clothing regions, pulling subjects for compositing, auto-masking for inpainting pipelines, batch-cropping objects by category.

## Input schema

| Field                  | Type         | Required | Default             | Description                                                                                                                                                 |
| ---------------------- | ------------ | -------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `image`                | string (URI) | ✅       | (demo outfit photo) | Input image. Local paths are auto-uploaded by `run_model.py`.                                                                                               |
| `mask_prompt`          | string       |          | `"clothes,shoes"`   | **Positive** text prompt — comma-separated list of labels to segment. One word per concept works best.                                                      |
| `negative_mask_prompt` | string       |          | `"pants"`           | **Negative** text prompt — labels to _subtract_ from the positive mask (same comma-separated format).                                                       |
| `adjustment_factor`    | integer      |          | `0`                 | Mask adjustment. **Negative = erosion** (shrink mask, tighter), **positive = dilation** (grow mask, more permissive). Example values in the demo use `-15`. |

Notes:

- There is **no explicit `box_threshold` / `text_threshold`** knob on this particular Replicate wrapper (contrary to the vanilla Grounded-SAM repo). Tuning is done via `adjustment_factor` and by wording the prompt. If you need threshold control, use a different Grounded-SAM cog.
- `mask_prompt` takes multiple labels at once: `"cat, dog"` will include both. Use `negative_mask_prompt` to carve out subregions (e.g. positive `"clothes"` minus negative `"pants"` → tops only).

## Output

An **array of 4 image URIs**, in this order:

1. `annotated_picture_mask.jpg` — the input image with the positive-prompt mask visualized on top (colored overlay + bounding boxes).
2. `neg_annotated_picture_mask.jpg` — same visualization for the negative-prompt mask.
3. `mask.jpg` — the clean binary mask (white = positive-minus-negative region). **This is usually the one you want** for downstream pipelines (inpainting, compositing, matting).
4. `inverted_mask.jpg` — the logical inverse of `mask.jpg`.

`run_model.py` saves these as `schananas_grounded_sam_0.jpg`, `..._1.jpg`, `..._2.jpg`, `..._3.jpg` in the output directory. If nothing matches the prompt, the mask will be all-black (and the annotated image will come back with no boxes) — no hard error.

## Pricing

No per-run rate is published on the model page; Replicate bills this one by **hardware-second** on an Nvidia T4 (predict time ~4s in the default example, so roughly sub-cent per run). Use the Replicate playground estimator for a current quote: <https://replicate.com/schananas/grounded_sam>.

## Examples

Using `--input-file` so comma-separated prompt values don't need shell-escaping.

**Single-label segmentation** — mask every cat in the image:

`input.json`:

```json
{
  "image": "./living_room.jpg",
  "mask_prompt": "cat"
}
```

```bash
python scripts/run_model.py schananas/grounded_sam \
    --input-file input.json \
    --output ./out/
```

**Multi-label segmentation** — street-scene layer masks for person, dog, and car at once:

`input.json`:

```json
{
  "image": "./street.jpg",
  "mask_prompt": "person, dog, car"
}
```

```bash
python scripts/run_model.py schananas/grounded_sam \
    --input-file input.json \
    --output ./out/
```

**Positive-minus-negative with dilation** — tops only (clothes minus pants), grown slightly for safer inpainting:

`input.json`:

```json
{
  "image": "./model_photo.jpg",
  "mask_prompt": "clothes, shoes",
  "negative_mask_prompt": "pants",
  "adjustment_factor": 10
}
```

```bash
python scripts/run_model.py schananas/grounded_sam \
    --input-file input.json \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Turning short text lists into pixel-accurate masks with zero user interaction.
- Multi-class scenes — DINO handles several labels in one prompt cheaply.
- Fashion / product segmentation (original design target).
- Producing both positive and inverted masks in one run, handy for "keep subject / replace background" pipelines.

**Gotchas:**

- **Prompt must be nouns DINO recognizes.** Common objects work (`cat`, `car`, `bag`, `shoe`, `person`, `tree`). Abstract concepts (`shadow`, `reflection`, `negative space`), actions (`running`), or proper nouns (`a Labrador named Rex`) generally don't.
- **No threshold knob** on this cog — you can't dial detection confidence. If DINO misses small/occluded objects you can't lower a threshold to recover them; rephrase the prompt or use a different model.
- **`adjustment_factor` is the only mask-tuning lever.** Negative erodes, positive dilates. Values in the single digits to low teens (`-15` to `+15`) are the usable range; large magnitudes degrade to uselessly-small or blob-shaped masks.
- **No-match is silent.** A prompt DINO can't ground returns a black `mask.jpg` with no error. Check the annotated image to confirm detections happened.
- **Occluded / small / stacked objects** can merge into a single mask or get dropped — SAM is accurate on what DINO finds, but DINO's recall on tiny/cluttered objects is mediocre.
- **Negative prompts subtract; they don't refine class boundaries.** `negative_mask_prompt: "pants"` with `mask_prompt: "clothes"` works because "pants" is a recognizable DINO class. A nonsense negative like `"lower half"` will be ignored.
- **Output is always JPEG** (4 files), which means the binary mask is lossy — there can be faint gray pixels at mask edges. Threshold downstream (e.g. `> 127`) to get a clean binary.
