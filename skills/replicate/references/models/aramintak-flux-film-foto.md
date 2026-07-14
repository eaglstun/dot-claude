# aramintak/flux-film-foto

Model page: <https://replicate.com/aramintak/flux-film-foto>

**Flux LoRA for realistic film-photography aesthetic** — a Flux-dev LoRA fine-tune by `aramintak` that applies a neutral "actual film" look (grain, color science reminiscent of negative film stocks, halation around highlights, softer rolloff, print-like texture) to prompt-driven generations. Unlike a Lomo / toy-camera filter, this one aims at a believable 35mm / medium-format photograph — the kind of output you'd get from shooting Portra, Ektar, or CineStill — rather than an exaggerated cross-processed effect. It's a thin wrapper around `black-forest-labs/flux-dev` with a single baked-in LoRA and the full Flux-LoRA-inference schema exposed (including `extra_lora` stacking).

The model description is terse: _"Flux lora in a realistic film style. Use flmft photo style to trigger the image generation."_ That sentence is the entire README.

## When to pick it over alternatives

- **Pick over `levelsio/lomography`** when you want a neutral, plausible film-photograph look — no heavy vignette, no cross-processed color shifts, no light leaks. Lomography is deliberately toy-camera / lo-fi extreme; film-foto is "looks like it came out of a lab scanner."
- **Pick over `fofr/kontext-ps1`** when you want _analog film_ nostalgia (1970s–2000s photography), not _early-3D video-game_ nostalgia. Different decades, different mediums, different artifact vocabulary.
- **Pick over generic Flux with a prompt like `"shot on Portra 400, 35mm film grain, halation"`** when you want consistency — the LoRA is purpose-trained on film-look imagery and produces the aesthetic more reliably than prompt-only steering, which Flux-dev tends to half-apply or ignore once the prompt has competing subject detail.
- **Pick a dedicated film-emulation LUT/plugin (Dehancer, FilmConvert) instead** if you have an existing photo you want to deterministically grade without any re-rendering of content. This model _generates_ film-look images; it's not a one-way LUT pass.
- **Sweet spot:** editorial-style portraits, "looks like a scanned negative" landscapes, product shots with organic warmth, album art, moodboards. Less ideal for images needing surgical color accuracy (product catalog, e-commerce where color must match SKU).

## Input schema

Fully-loaded Flux-dev LoRA inference template — every knob is exposed.

| Field                    | Type         | Required | Default  | Description                                                                                                                                                                                            |
| ------------------------ | ------------ | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `prompt`                 | string       | yes      | —        | Text prompt. **Include the trigger phrase `flmft photo style`** to activate the LoRA. Without it you get plain Flux-dev output silently.                                                               |
| `image`                  | string (URI) |          | —        | Input image for img2img / inpainting. If omitted, runs in pure txt2img. Local paths are auto-uploaded by `run_model.py`. When set, `aspect_ratio` / `width` / `height` are ignored.                    |
| `mask`                   | string (URI) |          | —        | Inpainting mask. White regenerated, black preserved. Requires `image`. Disables aspect_ratio/width/height.                                                                                             |
| `aspect_ratio`           | enum         |          | `"1:1"`  | Standard Flux ratios (`1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`, etc.) or `"custom"` to use `width`/`height`. Ignored when `image` is set.                                                           |
| `height`                 | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest 16. Incompatible with `go_fast`.                                                                                                  |
| `width`                  | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest 16. Incompatible with `go_fast`.                                                                                                  |
| `prompt_strength`        | number       |          | `0.8`    | img2img tuning knob. `0.0` = preserve input exactly, `1.0` = full destruction. `0.7–0.85` is typical for applying film look while keeping input legible.                                               |
| `model`                  | enum         |          | `"dev"`  | `"dev"` (28 steps, best quality) or `"schnell"` (4 steps, fast/cheap).                                                                                                                                 |
| `num_outputs`            | integer      |          | `1`      | 1–4. Grab variations at one seed cheaply.                                                                                                                                                              |
| `num_inference_steps`    | integer      |          | `28`     | 1–50. 28 matches `dev`; 4 for `schnell`.                                                                                                                                                               |
| `guidance_scale`         | number       |          | `3`      | 0–10. Flux likes low guidance — `2.5–3.5` is the photographic band. Default example used `3.5`.                                                                                                        |
| `seed`                   | integer      |          | random   | Set for reproducibility.                                                                                                                                                                               |
| `output_format`          | enum         |          | `"webp"` | `"webp"`, `"jpg"`, or `"png"`.                                                                                                                                                                         |
| `output_quality`         | integer      |          | `80`     | 0–100. Ignored for PNG.                                                                                                                                                                                |
| `disable_safety_checker` | boolean      |          | `false`  | Disable NSFW filter.                                                                                                                                                                                   |
| `go_fast`                | boolean      |          | `false`  | fp8-quantized fast path. Faster/cheaper, minor quality tradeoff. **Silently applies a 1.5x multiplier to `lora_scale` / `extra_lora_scale`** — see Gotchas. Incompatible with custom `width`/`height`. |
| `megapixels`             | enum         |          | `"1"`    | `"1"` (~1MP) or `"0.25"` (~0.25MP). Ignored when `width`/`height` set or `image` provided.                                                                                                             |
| `lora_scale`             | number       |          | `1`      | -1 to 3. **Primary strength knob.** 0 = no film effect, 1 = trained intensity, >1 = exaggerated. Sane range `0.6–1.3` for base inference; bump carefully with `go_fast` (see Gotchas).                 |
| `replicate_weights`      | string       |          | —        | Override the baked-in LoRA. Rarely useful — doing so replaces `flmft` with whatever you point at, defeating the endpoint's purpose.                                                                    |
| `extra_lora`             | string       |          | —        | Stack a second LoRA on top (Replicate slug, HuggingFace URL, CivitAI URL, or `.safetensors` URL). Useful for "film look + face LoRA" or "film look + costume/subject LoRA" combinations.               |
| `extra_lora_scale`       | number       |          | `1`      | -1 to 3. Strength of the stacked LoRA.                                                                                                                                                                 |

**Trigger word:** `flmft photo style` (confirmed from model description and default example prompt `"a gray day with mt fuji in the distance, flmft photo style"`). Drop it in as a natural part of the prompt, e.g. `"..., flmft photo style"` at the tail, or phrased as `"in flmft photo style"` mid-sentence.

## Output

An **array of URI strings** (length = `num_outputs`). With the default `num_outputs: 1` you get a one-element list. `run_model.py` saves them as `aramintak_flux-film-foto_0.<ext>` (and `_1.<ext>`, `_2.<ext>`, ... when `num_outputs > 1`). Extension follows `output_format` — default `.webp`.

## Pricing

**~$0.014 per run** on Nvidia H100 — roughly **71 runs per $1**. Predictions typically complete in **~10 seconds** at default settings (the default example logs show ~21s including a ~13s LoRA-load cold start; warm runs are faster). Cheap enough for batch stylization over a photo library. Confirm at <https://replicate.com/aramintak/flux-film-foto> before large batches.

## Examples

**Plain txt2img with the trigger word** (the canonical default-example shape — note `flmft photo style` at the end of the prompt):

```bash
python scripts/run_model.py aramintak/flux-film-foto \
    --input '{
      "prompt": "a gray day with mt fuji in the distance, flmft photo style",
      "aspect_ratio": "1:1",
      "lora_scale": 1.0,
      "guidance_scale": 3.5,
      "num_inference_steps": 28,
      "output_format": "jpg",
      "output_quality": 90
    }' \
    --output ./out/
```

**Different subject, consistency check** (portrait, 35mm-film framing — trigger phrased naturally mid-prompt):

```bash
python scripts/run_model.py aramintak/flux-film-foto \
    --input '{
      "prompt": "Editorial portrait of a woman in a cafe by the window, warm afternoon light, shallow depth of field, flmft photo style, subtle grain, natural skin tones, Portra-like color palette",
      "aspect_ratio": "4:5",
      "lora_scale": 1.0,
      "guidance_scale": 3.0,
      "num_inference_steps": 28,
      "seed": 42,
      "output_format": "jpg"
    }' \
    --output ./out/
```

**`lora_scale` sweep** (same seed, 4 outputs — but `num_outputs` uses one scale per call, so this shows the pattern you'd wrap in a loop; pictured here at `1.2` for a stronger film commitment):

```bash
python scripts/run_model.py aramintak/flux-film-foto \
    --input '{
      "prompt": "Coastal cliff at golden hour, dramatic clouds, flmft photo style, medium-format film, halation on highlights, muted contrast",
      "aspect_ratio": "16:9",
      "lora_scale": 1.2,
      "guidance_scale": 3.0,
      "num_inference_steps": 28,
      "num_outputs": 4,
      "seed": 7
    }' \
    --output ./out/
```

To actually sweep `lora_scale`, wrap the CLI call in a shell loop over `0.6`, `0.9`, `1.1`, `1.3` and compare — there is no built-in multi-scale mode.

## Strengths / gotchas

**Good at:**

- Neutral, believable film-photograph look — grain, organic highlight rolloff, film-style color science — in one call with a short trigger phrase.
- Both txt2img (generate film-look scenes from scratch) and img2img (restyle an existing photo) in the same endpoint.
- Stacking with a second LoRA via `extra_lora` — e.g. pair with a face/identity LoRA for "film photo of a specific person," or with a costume/scene LoRA for themed shoots.
- Cheap (~$0.014) and fast (~10s warm) — viable for batch runs over large photo libraries or interactive iteration during prompt tuning.

**Gotchas:**

- **Trigger phrase required: `flmft photo style`.** Forgetting it silently produces base Flux-dev output — the model still runs and returns an image, but the film LoRA barely activates. Always include the literal token `flmft` (it's an invented trigger, not a real phrase, so a typo like `flmftg` or `film photo style` will not work). Phrasings that land: `"..., flmft photo style"` (appended), `"in flmft photo style"` (mid-sentence), `"flmft photo style of <subject>"` (leading).
- **`lora_scale` is the primary strength knob.** Default `1.0` matches training intensity. Drop to `0.6–0.8` if the film look is too overcooked (grain crushing fine detail, color too muted); push to `1.1–1.3` for more pronounced film character. Above ~1.5 the image starts to degrade — oversaturated grain, blown highlights, broken textures.
- **`go_fast: true` silently multiplies `lora_scale` by 1.5x.** A value of `1.0` becomes effectively `1.5` under the fast path, which is already near the upper safe range. If you flip `go_fast` on, **drop `lora_scale` to ~`0.66`** to target an effective `1.0`, or expect stronger effects than your slow-path baseline. Same multiplier applies to `extra_lora_scale`. This is a shared Flux-LoRA-wrapper footgun, not specific to this model.
- **`prompt_strength` is the second knob (img2img only).** `0.6–0.7` keeps the input recognizable with a film tint; `0.8–0.9` lets the film aesthetic take over and re-render textures; above `0.9` the model invents new content.
- **Face identity drifts under Flux LoRAs.** Combined with film grain and softer focus, portrait identity is not reliably preserved. For "apply film look to a photo of a specific person," lower `prompt_strength` (`0.55–0.7`) and/or stack a face LoRA via `extra_lora`. Don't use for ID photos or tasks requiring strict face fidelity.
- **Best prompt patterns include a film-stock / photographic cue alongside the trigger.** Phrases like `"Portra-like color palette"`, `"35mm film grain"`, `"medium-format"`, `"halation"`, `"natural skin tones"`, `"warm afternoon light"` steer the LoRA effectively. The trigger alone activates the style; these cues shape which _kind_ of film look.
- **Max resolution is 1440 on either axis** (Flux-dev limit). Chain into a dedicated upscaler (`fermatresearch/magic-image-refiner`, `topazlabs/image-upscale`) for larger outputs.
- **Output format defaults to webp.** Switch to `"jpg"` (with `output_quality: 90+`) for general compatibility, or `"png"` for lossless compositing.
- **Output is an array**, not a single string — index `[0]` when wiring the response into downstream tooling.
- **No README on the model page** — the model description is one sentence and there is no usage doc. Schema + default example are the only authoritative sources; everything else is reverse-engineered.
- **`go_fast: true` is incompatible with custom `width`/`height`.** If you set `aspect_ratio: "custom"`, leave `go_fast` off, or the runtime silently falls back.
