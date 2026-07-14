# flux-kontext-apps/multi-image-kontext-max

Model page: <https://replicate.com/flux-kontext-apps/multi-image-kontext-max>

**Flux Kontext (multi-image, Max tier).** Part of Black Forest Labs' **Flux Kontext** family — prompt-driven image editing that _preserves subject, identity, and style_ from reference images while applying a text instruction. This is the **multi-image** variant: it takes **two reference images** plus a prompt and composes/blends/merges them into a single cohesive output. The `-max` suffix denotes BFL's top-quality tier (best prompt adherence and typography, highest price) within the Kontext line. The model's own description calls it "experimental" — behavior and schema may shift.

## When to pick this over sibling models

- **`flux-kontext-apps/multi-image-kontext-pro`** — same two-input composition job, Pro tier instead of Max. Cheaper per run, slightly lower fidelity and prompt adherence. Pick Pro for volume/iteration, Max for hero shots.
- **`black-forest-labs/flux-kontext-max` / `flux-kontext-pro`** — **single**-image Kontext editors. One reference image plus a prompt. Pick these when you only need to edit/restyle one image, not merge two.
- **`black-forest-labs/flux-canny-pro` / `flux-depth-pro`** — ControlNet-style structural preservation (edges / depth). Kontext is _semantic_ preservation (subject, style, identity); Canny/Depth is _geometric_ preservation. Different jobs.
- **Generic img2img / SDXL inpainting** — Kontext is dramatically better at keeping a specific subject's identity across an edit. Use img2img only when you want loose variation, not identity preservation.
- **Face-swap / IP-adapter pipelines** — narrower (faces / single-subject identity transfer). Kontext handles broader "put subject A into scene B in style C" composition from two references.

## Input schema

| Field              | Type         | Required | Default               | Description                                                                                                                                                                                                                                                   |
| ------------------ | ------------ | -------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`           | string       | Yes      | —                     | Text description of how to combine or transform the two input images.                                                                                                                                                                                         |
| `input_image_1`    | string (URI) | Yes      | —                     | **First** input image. Must be **jpeg, png, gif, or webp**. Local paths are auto-uploaded by `run_model.py`.                                                                                                                                                  |
| `input_image_2`    | string (URI) | Yes      | —                     | **Second** input image. Same format requirements.                                                                                                                                                                                                             |
| `aspect_ratio`     | enum         |          | `"match_input_image"` | One of `"match_input_image"`, `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"`, `"4:5"`, `"5:4"`, `"21:9"`, `"9:21"`, `"2:1"`, `"1:2"`. `match_input_image` matches the aspect ratio of the (first) input image.                               |
| `output_format`    | enum         |          | `"png"`               | One of `"jpg"` or `"png"`. Note: default is **png** here (unlike most other BFL endpoints which default to `jpg`).                                                                                                                                            |
| `safety_tolerance` | integer      |          | `2`                   | BFL safety filter strictness. **Range: 0 (strictest) – 2 (most permissive). 2 is currently the maximum allowed** (the multi-image variants cap lower than the single-image Kontext endpoints, which allow up to 6). Default is already the permitted maximum. |
| `seed`             | integer      |          | random                | Random seed. Set for reproducible generation.                                                                                                                                                                                                                 |

**Two images, numbered fields.** The schema does **not** use an array — you must pass **exactly two reference images** via the distinct `input_image_1` and `input_image_2` fields. There is no `input_image_3` / N-image support on this endpoint; if you need three or more references you'll have to chain runs (merge A+B, then merge result+C) or switch to a different pipeline.

**No knobs for `steps`, `guidance`, or `prompt_upsampling`** on this endpoint — unlike `flux-canny-pro` / `flux-depth-pro`, the Max Kontext endpoint exposes only the fields above. Quality/adherence is tuned internally.

## Output

A **single URI string** pointing to the generated image (not an array). Saved as `flux-kontext-apps_multi-image-kontext-max_0.<ext>` where `<ext>` matches `output_format` (default `png`).

Typical prediction time: **~8 seconds** (from the default example metrics).

## Pricing

**Not published on the model page.** The BFL Flux Kontext **Max** tier on the canonical `black-forest-labs/flux-kontext-max` endpoint runs roughly **$0.08 per image** (flat per-run, Max-tier standard across BFL's Kontext line), and this multi-image Max endpoint should price in the same neighborhood — but this is an **educated estimate**, not a confirmed number for this specific slug. Confirm via the playground price estimator at <https://replicate.com/flux-kontext-apps/multi-image-kontext-max> before running a batch. BFL Pro/Max endpoints are priced per image, not per second, so prompt complexity does not change cost.

## Examples

**1. Put a person into a specific outfit / scene** (canonical two-image use — the default example on the model page):

```json
{
  "prompt": "Put the woman into a white t-shirt with the text on it",
  "input_image_1": "./refs/portrait.png",
  "input_image_2": "./refs/tshirt_design.webp",
  "aspect_ratio": "1:1",
  "output_format": "png"
}
```

```bash
python scripts/run_model.py flux-kontext-apps/multi-image-kontext-max --input-file input.json --output ./out/
```

**2. Compose a subject into an environment** (keep subject identity from image 1, style/location from image 2):

```json
{
  "prompt": "Place the dog from the first image into the forest clearing from the second image, matching the golden-hour lighting and lens character of the scene. Keep the dog's markings, collar, and pose natural.",
  "input_image_1": "./refs/dog_studio.jpg",
  "input_image_2": "./refs/forest_clearing.jpg",
  "aspect_ratio": "16:9",
  "output_format": "jpg",
  "seed": 42
}
```

```bash
python scripts/run_model.py flux-kontext-apps/multi-image-kontext-max --input-file input.json --output ./out/
```

**3. Style transfer across subjects** (subject from image 1, painting style from image 2):

```json
{
  "prompt": "Render the person from the first image in the painting style of the second image — thick impasto brushwork, muted palette, visible canvas texture. Preserve the person's facial identity and pose.",
  "input_image_1": "./refs/headshot.png",
  "input_image_2": "./refs/van_gogh_reference.jpg",
  "aspect_ratio": "match_input_image",
  "output_format": "png"
}
```

```bash
python scripts/run_model.py flux-kontext-apps/multi-image-kontext-max --input-file input.json --output ./out/
```

## Strengths / gotchas

**Good at:**

- Identity preservation across a composition — faces, specific garments, specific objects stay recognizable from reference to output.
- "Put X from image 1 into Y from image 2" prompts — canonical multi-image Kontext use.
- Style transfer where image 2 supplies the aesthetic and image 1 supplies the subject.
- Typography / text-in-image rendering is the `-max` tier's headline improvement over `-pro` (e.g. legible text on the t-shirt in the default example).
- Max-tier photoreal output quality, noticeably above `multi-image-kontext-pro`.

**Gotchas:**

- **Exactly two reference images, numbered fields, no array.** You must supply both `input_image_1` **and** `input_image_2` — both are required; passing only one will 422. There is no N>2 input slot on this endpoint.
- **How the two images are blended is prompt-driven**, not positionally fixed. The model doesn't automatically treat image 1 as "subject" and image 2 as "scene" — your prompt has to explicitly reference which image supplies what ("from the first image", "the style of the second image"). Ambiguous prompts produce unpredictable blends.
- **`safety_tolerance` caps at 2** (default is 2 — the permitted max). This is stricter than the single-image Kontext endpoints (which allow up to 6). Expect the filter to reject more borderline prompts than on `black-forest-labs/flux-kontext-max`. Dropping to 0 or 1 only _increases_ strictness.
- **`aspect_ratio` default is `match_input_image`** — matches **`input_image_1`**. If your two inputs have different aspect ratios and you don't want image 1's to win, set an explicit enum value.
- **`output_format` defaults to `png`** (not `jpg` like most BFL endpoints). Set `jpg` if you want smaller files for downstream web use; keep `png` for lossless compositing.
- **No `steps` / `guidance` / `prompt_upsampling` controls.** You cannot tune prompt adherence the way you can on `flux-canny-pro` — if output drifts from the prompt, rewrite the prompt (more explicit "from image 1 / image 2" phrasing) or reroll seeds.
- **Single output per call.** Returns one URI. Loop with different seeds for variations.
- **"Experimental" model** per BFL's own description — schema and behavior may change; don't hard-code assumptions for long-lived production pipelines without monitoring.
- **Commercial use:** the `flux-kontext-apps` collection is noted as usable commercially via Replicate's BFL hosting. Verify current BFL commercial terms at <https://blackforestlabs.ai/> before shipping generated assets.
- **Cover image / default example** on the model page (<https://tjzk.replicate.delivery/models_models_featured_image/034b26ea-3843-465e-8c21-34ac7b4869bf/multi-cover.webp>) illustrates the canonical "put subject from image 1 into outfit/scene from image 2" behavior.
