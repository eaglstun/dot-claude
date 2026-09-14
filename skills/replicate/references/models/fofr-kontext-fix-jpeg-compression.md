# fofr/kontext-fix-jpeg-compression

Model page: <https://replicate.com/fofr/kontext-fix-jpeg-compression>

**Flux Kontext fine-tune targeting JPEG compression artifacts.** Take a blocky/banded/ringy JPEG, get a clean version back at the **same resolution**. Built on Black Forest Labs' Flux Kontext architecture (the same base used by `black-forest-labs/flux-kontext-pro` / `flux-kontext-max` for prompt-driven image edits) with a LoRA fine-tune by **fofr** specialized for one job: identifying and undoing the visual signatures of lossy JPEG compression — 8x8 blocking, chroma subsampling color smearing, mosquito noise / ringing around high-contrast edges, and low-bitrate banding in smooth gradients. The default prompt the author uses is literally `"fix the jpeg compression"`.

## When to pick this over alternatives

- **vs. generic upscalers (`topazlabs/image-upscale`, `recraft-ai/recraft-crisp-upscale`, `nightmareai/real-esrgan`)** — those models upscale **and** clean as a side effect. This model does **same-resolution cleanup** without changing dimensions. Pick this when the resolution is already what you want and you only need the artifacts gone.
- **vs. generic img2img refiners (`fermatresearch/magic-image-refiner`, clarity-upscaler, magnific clones)** — those add _creative_ detail driven by a prompt and a `creativity` knob; they will hallucinate skin pores, fabric weave, etc. that weren't in the source. This Kontext fine-tune is targeted at **artifact removal specifically**, with much less invention.
- **vs. face restoration (`sczhou/codeformer`, `tencentarc/gfpgan`, `tencentarc/codeformer`)** — those are face-specific and will smear or ignore non-face content. This is **whole-image** cleanup — works on landscapes, products, screenshots, illustrations, not just portraits.
- **vs. base Flux Kontext (`black-forest-labs/flux-kontext-pro` with a "remove jpeg artifacts" prompt)** — the LoRA in this fine-tune is purpose-trained for the artifact distribution, so it tends to be more reliable and less prompt-sensitive than asking generic Kontext to do the same job.
- **Sweet spot:** social-media-cached images (Instagram / Facebook re-encodes), **WhatsApp recompression**, screenshots of screenshots, aggressive CDN compression, low-quality JPEGs from older cameras or scanned-then-saved-as-JPEG workflows. Restore visual quality without changing the file's dimensions.

## Input schema

| Field                    | Type         | Required | Default               | Description                                                                                                                                                                                                             |
| ------------------------ | ------------ | -------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                 | string       | Yes      | —                     | Text instruction. The author's default example uses `"fix the jpeg compression"`. The field is a real knob (not hardcoded), so you can steer with phrases like `"fix the jpeg compression and preserve film grain"`.    |
| `input_image`            | string (URI) | Yes      | —                     | Image to clean up. Must be **jpeg, png, gif, or webp**. Local paths are auto-uploaded by `run_model.py`.                                                                                                                |
| `aspect_ratio`           | enum         |          | `"match_input_image"` | Aspect ratio of the generated image. `"match_input_image"` keeps the input's aspect (the right default for cleanup work — preserves framing).                                                                           |
| `megapixels`             | enum         |          | `"1"`                 | Approximate output megapixels. Drives the actual pixel dimensions Kontext targets (default `"1"` ≈ 1 MP, e.g. ~1152×896 for a 4:3 input as seen in the default example). Note: this is NOT same-pixel-size by default.  |
| `num_inference_steps`    | integer      |          | `30`                  | Diffusion steps. Range **4–50**. Default 30 is the sensible middle; lower for speed, higher rarely improves artifact removal noticeably.                                                                                |
| `guidance`               | number       |          | `2.5`                 | Guidance scale. Range **0–10**. Low default (2.5) is typical for Flux/Kontext — raising it pushes harder toward the prompt instruction (more aggressive cleanup) at the cost of detail preservation.                    |
| `seed`                   | integer      |          | random                | Random seed for reproducible generation. Leave blank for random.                                                                                                                                                        |
| `output_format`          | enum         |          | `"webp"`              | Output container. Defaults to **`webp`** (note: not `png` or `jpg` — set explicitly if you need lossless or want to avoid recompression).                                                                               |
| `output_quality`         | integer      |          | `80`                  | Encoding quality 0–100 for `webp`/`jpg`. Ignored for `png`. **Important:** the default 80 means the model's clean output is itself re-encoded at WebP-80 — bump to 95–100 if you don't want the cleanup undone on save. |
| `disable_safety_checker` | boolean      |          | `false`               | Disable the NSFW safety checker. Off by default.                                                                                                                                                                        |
| `lora_strength`          | number       |          | `1`                   | Strength of the JPEG-fix LoRA. `1.0` is the trained default. Drop toward `0` to weaken the cleanup effect (and approach base Kontext behavior); rarely useful to push above `1`.                                        |
| `replicate_weights`      | string       |          | —                     | Path to alternate LoRA weights. Advanced override — leave unset to use the JPEG-fix LoRA the model ships with.                                                                                                          |

**The prompt is a real input**, not a fixed pipeline. The default example uses `"fix the jpeg compression"`, but you can append context (e.g. `"...without smoothing the film grain"`) to nudge behavior.

## Output

A **single URI string** pointing to the cleaned image (not an array). `run_model.py` saves it as `fofr_kontext-fix-jpeg-compression_0.<ext>` where `<ext>` matches `output_format` (default `webp`).

Default-example dimensions in the response: `1152x896` for a 4:3 input at `megapixels: "1"`.

## Pricing

**$0.10 per run** (10 runs per $1) on **Nvidia H100**. Flat per-run, not per-second. Predictions typically complete within **~68 seconds**, though the default example finished in ~14.7 seconds of predict time at 30 steps / 1 MP. Higher than the BFL Pro tier (~$0.03–$0.04/img) because this runs as a **fine-tuned Kontext deployment on dedicated H100 hardware**, not the BFL-hosted commercial endpoint.

## Examples

**1. Default cleanup pass** — the canonical use, matching the model page's default example:

```bash
python scripts/run_model.py fofr/kontext-fix-jpeg-compression --input-file input.json --output ./out/
```

```json
{
  "prompt": "fix the jpeg compression",
  "input_image": "./compressed.jpg",
  "aspect_ratio": "match_input_image",
  "megapixels": "1",
  "output_format": "webp",
  "output_quality": 95
}
```

**2. Lossless output** — keep the cleaned result lossless so your downstream processing isn't re-quantized:

```bash
python scripts/run_model.py fofr/kontext-fix-jpeg-compression --input-file input.json --output ./out/
```

```json
{
  "prompt": "fix the jpeg compression artifacts, preserve fine texture",
  "input_image": "./whatsapp_recompressed.jpg",
  "aspect_ratio": "match_input_image",
  "megapixels": "1",
  "num_inference_steps": 30,
  "guidance": 2.5,
  "output_format": "png",
  "seed": 42
}
```

**3. Aggressive cleanup on a heavily blocked image** — push guidance and steps for a worst-case JPEG:

```bash
python scripts/run_model.py fofr/kontext-fix-jpeg-compression --input-file input.json --output ./out/
```

```json
{
  "prompt": "fix the jpeg compression, remove all blocking and ringing",
  "input_image": "./very_low_quality.jpg",
  "aspect_ratio": "match_input_image",
  "megapixels": "1",
  "num_inference_steps": 40,
  "guidance": 4,
  "lora_strength": 1,
  "output_format": "png"
}
```

## Strengths / gotchas

**Good at:**

- Removing 8x8 JPEG blocking from low-bitrate / heavily-recompressed images.
- Smoothing chroma-subsampling color smearing along edges.
- De-ringing mosquito noise around high-contrast text and edges.
- Cleaning gradient banding in skies / soft backgrounds.
- Preserving overall composition, color, and subject identity (Kontext's strength) — unlike a generic img2img refiner, it doesn't drift the content.
- Working on whole images regardless of subject — portraits, landscapes, products, screenshots, illustrations.

**Gotchas:**

- **`megapixels` defaults to `"1"`, not "match input."** A 2 MP input gets resampled down to ~1 MP unless you change this. For true same-resolution cleanup of larger images, raise `megapixels` (the schema is an enum — common values `"0.25"`, `"1"`, etc.; check the playground for the full list) or accept that the output is being resized along with cleaning. There is **no `"match_input"`** option for `megapixels` like there is for `aspect_ratio`.
- **Output defaults to `webp` at quality 80.** The model cleans the JPEG, then the API **re-encodes the result as WebP-80**, which can reintroduce mild compression artifacts of a different kind. For best results set `output_format: "png"` (lossless) or `output_quality: 95–100`.
- **Over-smoothing risk.** The LoRA is trained to identify "compression artifacts" and erase them. **Genuine fine texture that resembles compression noise — film grain, faint skin pores, subtle fabric weave, photographic noise — can get smoothed away** along with the artifacts. If grain matters, mention it in the prompt (`"...preserve film grain"`) and consider lowering `lora_strength` (e.g. 0.7–0.8). The model has no way to distinguish intentional noise from compression noise.
- **Hallucination on text and small detail.** Like all diffusion-based cleanup, the model **reconstructs** rather than truly de-compresses. Small text, license plates, distant faces can come back **looking sharp but reading wrong** — characters substituted, features re-invented. For OCR-critical or evidentiary work, prefer a non-generative denoiser.
- **Aspect ratio:** `"match_input_image"` is the right default. Override with explicit ratios only if you want to crop/letterbox.
- **Prompt _is_ a knob, not cosmetic.** The default `"fix the jpeg compression"` is fine for 95% of cases. You can add steering — `"fix the jpeg compression, preserve film grain"` or `"fix the jpeg compression on the background only"` — but the LoRA dominates behavior; don't expect arbitrary edits like a normal Kontext model.
- **`guidance` 2.5 is the Flux/Kontext sweet spot.** Pushing above 5 starts to over-process — clean but plasticky. Below 1.5 the cleanup weakens.
- **Same-resolution cleanup is the niche.** If you _also_ want to upscale, chain into a dedicated upscaler (`topazlabs/image-upscale`, `recraft-ai/recraft-crisp-upscale`) afterward — don't expect this model to do both.
- **EXIF / color-profile preservation:** the output is a fresh-encoded WebP/PNG/JPG from the diffusion pipeline. **EXIF metadata, ICC color profiles, and original encoder chunks are not preserved** — re-attach them downstream if you need them (`exiftool -tagsFromFile orig.jpg out.webp`).
- **Single output per call.** Returns one URI. Loop with different seeds for variations if the first pass under- or over-cleans.
- **Failure modes to watch for:** (1) plastic / waxy skin when overdone, (2) text that's sharp but says the wrong thing, (3) loss of intentional grain or noise, (4) occasional residual blocking in dark uniform areas where the LoRA undertrained, (5) subtle color shift on already-clean regions because everything goes through a diffusion pass.
- **No README on the model page** — the schema, the default example (`"fix the jpeg compression"` prompt, ~14.7s on H100, 1152x896 output), and the Kontext-family conventions are the authoritative documentation.
