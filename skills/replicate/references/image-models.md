# Image models on Replicate

Model schemas drift; verify the model page on replicate.com before relying on exact field names or ranges. The selection tables and defaults below are accurate as of 2026-Q1. Per-model deep-dives (full schema tables, examples, gotchas) live in `references/models/<slug>.md`.

## Quick picks

- **Default T2I when the user hasn't specified:** `black-forest-labs/flux-dev-lora` at default settings (no LoRA URL needed — still the best general Flux-Dev path).
- **Cheapest T2I:** `fofr/latent-consistency-model` (effectively <$0.001 per image in batch mode) or `lucataco/realistic-vision-v5.1` (~$0.001–0.003 for portraits).
- **Highest quality T2I:** `bria/fibo` for structured, rights-clear hero renders; step up to Flux Pro endpoints if available.
- **LoRA-aware:** `black-forest-labs/flux-dev-lora` (up to 2 LoRAs, official) or `lucataco/flux-dev-multi-lora` (up to 20 LoRAs, cheaper but no `go_fast`).
- **Default edit/compose:** [flux-kontext-apps/multi-image-kontext-max](models/flux-kontext-apps-multi-image-kontext-max.md) for 2-image semantic merges; [black-forest-labs/flux-canny-pro](models/black-forest-labs-flux-canny-pro.md) for outline-preserving restyles.
- **JPEG cleanup without upscale:** [fofr/kontext-fix-jpeg-compression](models/fofr-kontext-fix-jpeg-compression.md) — same-resolution artifact removal, distinct from upscalers that clean as a side effect of resizing.
- **Retro-nostalgic stylization:** [fofr/kontext-ps1](models/fofr-kontext-ps1.md) for PS1 / early-3D video-game look (Kontext fine-tune, identity preserved); [levelsio/lomography](models/levelsio-lomography.md) for analog Lomo film aesthetic (Flux LoRA, requires `TOK lomography` trigger); [aramintak/flux-film-foto](models/aramintak-flux-film-foto.md) for neutral 35mm / medium-format film look (Flux LoRA, trigger `flmft photo style`); [fofr/flux-bad-70s-food](models/fofr-flux-bad-70s-food.md) for the novelty 1970s-cookbook-photography look (Flux LoRA, trigger `bad 70s food`); [afterpeak/flux-slowed](models/afterpeak-flux-slowed.md) for the slowed-audio-cover-art female-portrait template (Flux LoRA, trigger `SLOW3D`).
- **Default face restore:** [sczhou/codeformer](models/sczhou-codeformer.md) (dial `codeformer_fidelity`); try [tencentarc/gfpgan](models/tencentarc-gfpgan.md) if CodeFormer looks plastic.
- **"Realism enhancer" / "make this AI portrait look real":** [sczhou/codeformer](models/sczhou-codeformer.md) at `codeformer_fidelity` ~0.6 — turns a stylized/illustrated AI face photoreal while keeping its identity. (For whole-image, non-face realism via re-painted texture, see [recraft-ai/recraft-creative-upscale](models/recraft-ai-recraft-creative-upscale.md).)
- **Default upscaler:** [topazlabs/image-upscale](models/topazlabs-image-upscale.md) for clean commercial upscales; [cswry/seesr](models/cswry-seesr.md) for severely degraded inputs.
- **Upscaler fidelity ↔ creativity axis:** [topazlabs/image-upscale](models/topazlabs-image-upscale.md) is the faithful / identity-preserving end from a commercial vendor (classical super-res, tunable, five source-aware variants). [recraft-ai/recraft-creative-upscale](models/recraft-ai-recraft-creative-upscale.md) is the creative / hallucinate-detail end — it **re-paints** textures and micro-detail rather than preserving pixels. [recraft-ai/recraft-crisp-upscale](models/recraft-ai-recraft-crisp-upscale.md) is the **faithful end of Recraft's own axis** (same vendor as creative, identical 1-input API, ~5× faster) — pick it when you want Recraft's cleanup pass without pixel re-painting. Pick Topaz for people, products, evidence, client deliverables needing explicit control; pick Recraft-crisp for a zero-config Recraft-native faithful pass; pick Recraft-creative for generative art where "shot-at-resolution" look beats pixel-exact fidelity.

Call out the cost before running anything above ~$0.10 per image (Topaz at 6×, Flux Pro tier, BFL Max) unless the user explicitly picked the model.

## Text-to-image

| Use case                       | Model                                                                        | Why                                                              |
| ------------------------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Default T2I**                | [black-forest-labs/flux-dev-lora](models/black-forest-labs-flux-dev-lora.md) | 12B Flux Dev, modern prompt adherence, optional LoRAs            |
| Rights-clear / enterprise      | [bria/fibo](models/bria-fibo.md)                                             | 8B, licensed training data, structured JSON prompt for control   |
| Rights-clear / fast & simple   | [bria/image-3.2](models/bria-image-3.2.md)                                   | 4B sibling of FIBO, pure text prompt, no structured modes        |
| Unified T2I + edit + VQA       | [bytedance/bagel](models/bytedance-bagel.md)                                 | One endpoint, three modes via `task` enum                        |
| Cheapest / fastest iteration   | [fofr/latent-consistency-model](models/fofr-latent-consistency-model.md)     | LCM-distilled SD1.5, 1–8 steps, batch up to 50 images per call   |
| Cheap photoreal portraits      | [lucataco/realistic-vision-v5.1](models/lucataco-realistic-vision-v5.1.md)   | SD 1.5 fine-tune, ~2s per 512×728 image, portrait-tuned defaults |
| Heavy LoRA stacking (up to 20) | [lucataco/flux-dev-multi-lora](models/lucataco-flux-dev-multi-lora.md)       | Stack subject + style + detail + aspect LoRAs in one call        |

## Image editing / composition

| Use case                                  | Model                                                                                            | Why                                                                    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| Merge 2 images by prompt                  | [flux-kontext-apps/multi-image-kontext-max](models/flux-kontext-apps-multi-image-kontext-max.md) | Semantic identity preservation across A+B composition                  |
| Outline-preserving restyle                | [black-forest-labs/flux-canny-pro](models/black-forest-labs-flux-canny-pro.md)                   | Canny ControlNet + Flux Pro, keeps exact silhouettes                   |
| Detail polish / inpaint                   | [fermatresearch/magic-image-refiner](models/fermatresearch-magic-image-refiner.md)               | Cheap ControlNet + SD1.5 refiner, optional `mask` inpaint              |
| Doodle → image                            | [jagilley/controlnet-scribble](models/jagilley-controlnet-scribble.md)                           | Classic SD 1.5 scribble ControlNet, cents per run                      |
| Restyle interior rooms                    | [adirik/interior-design](models/adirik-interior-design.md)                                       | MLSD + seg ControlNets pin architecture, swap furniture/style          |
| Put a person into a new scene             | [fofr/face-swap-with-ideogram](models/fofr-face-swap-with-ideogram.md)                           | Ideogram character-reference (generative, not pixel-graft)             |
| PS1 / early-3D game aesthetic             | [fofr/kontext-ps1](models/fofr-kontext-ps1.md)                                                   | Kontext fine-tune, low-poly + dithered look, identity-preserving       |
| Analog Lomo / retro film look             | [levelsio/lomography](models/levelsio-lomography.md)                                             | Flux LoRA, vignette/light-leaks/saturated colors (needs trigger)       |
| Neutral 35mm / film-photo look            | [aramintak/flux-film-foto](models/aramintak-flux-film-foto.md)                                   | Flux LoRA, believable Portra/Ektar grain + halation (needs trigger)    |
| 1970s cookbook (novelty)                  | [fofr/flux-bad-70s-food](models/fofr-flux-bad-70s-food.md)                                       | Flux LoRA, intentionally unappetizing flash-harsh food-photo aesthetic |
| Slowed-audio cover art (female portraits) | [afterpeak/flux-slowed](models/afterpeak-flux-slowed.md)                                         | Flux LoRA, soft-lit TikTok/YouTube-thumbnail template (female-bias)    |

## Image restoration / upscaling

| Use case                               | Model                                                                                | Why                                                                       |
| -------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| Commercial upscale up to 6×            | [topazlabs/image-upscale](models/topazlabs-image-upscale.md)                         | Five source-aware variants, face-enhance, up to 512 MP                    |
| Faithful upscale (sharpen/clean)       | [recraft-ai/recraft-crisp-upscale](models/recraft-ai-recraft-crisp-upscale.md)       | Recraft's faithful tier — zero-config sharpen/clean, no re-painted detail |
| Creative upscale (hallucinate detail)  | [recraft-ai/recraft-creative-upscale](models/recraft-ai-recraft-creative-upscale.md) | Re-paints texture and micro-detail — opposite of Topaz's faithful tier    |
| Clean up JPEG artifacts (same res)     | [fofr/kontext-fix-jpeg-compression](models/fofr-kontext-fix-jpeg-compression.md)     | Kontext fine-tune for blocking/ringing/banding — no resize                |
| Severely degraded / semantic super-res | [cswry/seesr](models/cswry-seesr.md)                                                 | Diffusion SR with text guidance, tolerant of heavy noise                  |
| Blind face restoration (sharp)         | [sczhou/codeformer](models/sczhou-codeformer.md)                                     | Transformer codebook, `codeformer_fidelity` dial                          |
| Blind face restoration (soft)          | [tencentarc/gfpgan](models/tencentarc-gfpgan.md)                                     | StyleGAN2 prior, gentle on old film scans                                 |

## Novelty

| Use case                       | Model                                                        | Why                                                   |
| ------------------------------ | ------------------------------------------------------------ | ----------------------------------------------------- |
| Hide QR code / logo in a scene | [andreasjansson/illusion](models/andreasjansson-illusion.md) | qrcode-monster ControlNet on SD1.5 + Realistic Vision |

## Per-model summaries

### bria/fibo

8B licensed-data T2I with three modes (Generate / Refine / Inspire) selected by which inputs you pass. Headline feature: **structured JSON prompt** for fine lighting/camera/composition control, round-trippable across calls. Inputs: `prompt` (required), optional `structured_prompt` (JSON string), `image` (Inspire mode), `aspect_ratio`, `guidance_scale` (capped 3–5). Output: PNG. Pricing not published — expect cheap-image-model range (~15s on default). Signature gotcha: `guidance_scale` silently caps at 3–5 despite the description claiming 1–10. See [models/bria-fibo.md](models/bria-fibo.md).

### bria/image-3.2

4B sibling of FIBO — same rights-clear pitch, simpler API. Pure text-to-image, no structured prompt, no reference image. Inputs: `prompt` (required), `aspect_ratio` (enum or float 0.5–3.0), `guidance_scale` (same 3–5 cap), `prompt_enhancement`, `enhance_image`. Output: PNG (~8s per image, 4B params). Pricing not published — cheapest of the Bria line. Signature gotcha: same `guidance_scale` enforcement cap as FIBO; `prompt_enhancement: true` silently rewrites your prompt before generation. See [models/bria-image-3.2.md](models/bria-image-3.2.md).

### bytedance/bagel

7B unified multimodal endpoint — T2I, image editing, and image understanding/VQA in one model selected via `task` enum. Filed under T2I since that's the most common use; also appears under editing. Inputs: `prompt` + `task` (required), `image` (required for editing/understanding), optional `enable_thinking`, `cfg_text_scale`, `cfg_img_scale`. Output shape **changes by mode**: `{text, image}` with one field null. ~$0.096/run, ~99s at default 50 steps. Signature gotcha: `task` is manual — passing `image` with `task: "text-to-image"` silently ignores the image. See [models/bytedance-bagel.md](models/bytedance-bagel.md).

### fofr/latent-consistency-model

LCM-distilled SD 1.5: 1–8 step generation, **10× faster** than vanilla SD, up to 50 images per call. Inputs: `prompt` (one per line for multi-prompt batching), `num_images` (1–50), `num_inference_steps` (1–8 recommended), `guidance_scale` (1–2 recommended). Supports img2img and Canny ControlNet in-endpoint. ~$0.039/run → effectively <$0.001/image in batch. Signature gotcha: **default `guidance_scale: 8` is wrong for LCM** — the model burns out unless you drop to ~1.5. No `negative_prompt` by design. See [models/fofr-latent-consistency-model.md](models/fofr-latent-consistency-model.md).

### lucataco/realistic-vision-v5.1

Cog-packaged Realistic Vision v5.1 (SD 1.5 photoreal fine-tune) with baked-in VAE. ~2s per 512×728 portrait on A40, ~$0.001–0.003 per image. Inputs: `prompt`, `negative_prompt` (long default — keep it), `steps` (20–30), `guidance` (3.5–7), `scheduler` (`EulerA` or `MultistepDPM-Solver`), `width`/`height`. Single-image PNG output. Signature gotcha: field is `guidance` **not** `guidance_scale` (silently ignored if you pass the wrong name); SD 1.5 resolution ceiling means stay ≤768 short-edge. See [models/lucataco-realistic-vision-v5.1.md](models/lucataco-realistic-vision-v5.1.md).

### black-forest-labs/flux-dev-lora

Official BFL Flux.1 [dev] endpoint with LoRA support for up to 2 stacked LoRAs from Replicate, HuggingFace, Civitai, or any `.safetensors` URL. Inputs: `prompt`, `lora_weights` + `lora_scale`, `extra_lora` + `extra_lora_scale`, `aspect_ratio`, `num_outputs` (1–4), `guidance` (Flux likes 2–4), `megapixels` (`"1"` or `"0.25"` as strings). Also supports img2img via `image` + `prompt_strength`. Signature gotcha: `go_fast: true` (default) makes outputs **non-deterministic even with `seed`** — set `false` for reproducibility. See [models/black-forest-labs-flux-dev-lora.md](models/black-forest-labs-flux-dev-lora.md).

### lucataco/flux-dev-multi-lora

Community Flux Dev that stacks **up to 20 LoRAs** via `hf_loras` (array) + `lora_scales` (parallel array). ~$0.029/run on H100, ~20s. No `go_fast` → deterministic. Inputs: `prompt` (must contain every active LoRA's trigger word), `hf_loras`, `lora_scales`, `aspect_ratio`, `num_outputs`, `guidance_scale` (not `guidance`), optional `image`/`prompt_strength` for img2img. Signature gotcha: `hf_loras` and `lora_scales` must be the same length — off-by-one silently misapplies scales. Gated LoRAs need the token **embedded in the URL** (no auth-token fields). See [models/lucataco-flux-dev-multi-lora.md](models/lucataco-flux-dev-multi-lora.md).

### black-forest-labs/flux-canny-pro

Flux.1 Pro + Canny-edge ControlNet. Extracts edges internally (no threshold knobs) — supply an RGB `control_image` and a `prompt`, and the output matches the input silhouette while content/style follow the text. Inputs: `prompt`, `control_image` (required), `steps` (15–50), `guidance` (1–100, sweet spot 25–35 — **not** the SD cfg-7 scale), `safety_tolerance` (1–6), `prompt_upsampling`, `output_format`. ~$0.05 per image, ~15s. Signature gotcha: source-image quality is load-bearing — noisy/low-contrast inputs produce bad edge maps you can't tune around. See [models/black-forest-labs-flux-canny-pro.md](models/black-forest-labs-flux-canny-pro.md).

### flux-kontext-apps/multi-image-kontext-max

BFL Flux Kontext, multi-image Max tier. Takes **exactly two** images (`input_image_1` + `input_image_2` — no array) plus a prompt, composes them into a single output while preserving identity/style semantics. Inputs: `prompt`, both input images (required), `aspect_ratio` (default `"match_input_image"` → image 1), `output_format` (defaults to **`png`**, not jpg), `safety_tolerance` (caps at 2 here, unlike single-image Kontext which allows 6), `seed`. ~$0.08/image estimated, ~8s. Signature gotcha: blending is **prompt-driven, not positional** — you must explicitly reference "from the first image" / "style of the second image" or results drift. See [models/flux-kontext-apps-multi-image-kontext-max.md](models/flux-kontext-apps-multi-image-kontext-max.md).

### fofr/kontext-fix-jpeg-compression

Flux Kontext LoRA fine-tune by fofr targeting **JPEG artifact cleanup at the same resolution** — not an upscaler. Removes 8x8 blocking, chroma smearing, mosquito noise, and gradient banding while preserving composition and subject identity (Kontext base). Required: `prompt` + `input_image`. Default prompt is literally `"fix the jpeg compression"`; the field is steerable (`"...preserve film grain"`, `"...on the background only"`). **$0.10/run** flat on H100, ~15–68s. Signature gotcha: **`megapixels` defaults to `"1"` (downsamples >1 MP inputs)** AND **`output_quality` defaults to 80 (re-encodes the cleaned output as WebP-80, partially undoing the cleanup)** — for true fidelity set `megapixels` higher and `output_format: "png"` or `output_quality: 95+`. See [models/fofr-kontext-fix-jpeg-compression.md](models/fofr-kontext-fix-jpeg-compression.md).

### fofr/kontext-ps1

Flux Kontext LoRA fine-tune by fofr that restyles inputs into the **PS1 / early-3D video-game aesthetic** (low-poly, dithered shading, vertex wobble, muddy textures). Identity and composition survive thanks to the Kontext base; the LoRA dominates style. Required: `prompt` + `input_image`. The prompt is for nudges only (`"no UI"`, `"no HUD"`, `"emphasize dithering"`, `"fixed camera survival horror"`) — the PS1 look is hardcoded in the LoRA. **$0.036/run** on H100, ~10–24s. Signature gotcha: **schema exposes only `disable_safety_checker` (boolean), not the canonical Kontext `safety_tolerance` 1–6 dial** — divergence from BFL's `flux-kontext-pro`/`max` endpoints worth flagging if you're parameterizing across the family. `lora_strength` (default 1.0) is the main "how PS1" knob; drop to 0.6–0.8 for subtler stylization. See [models/fofr-kontext-ps1.md](models/fofr-kontext-ps1.md).

### levelsio/lomography

Flux-dev LoRA fine-tune by Pieter Levels (`levelsio`) for the **analog Lomography toy-camera aesthetic** — saturated colors, heavy vignetting, light leaks, cross-processed shifts, soft focus. Works in both txt2img and img2img modes. Required: `prompt` (must include trigger phrase **`TOK lomography`** or you get a base Flux output with no Lomo effect — drop it inline like `"...in the style of TOK lomography, light leaks..."`, not as an afterthought). Optional `image` for stylization, `extra_lora` for stacking (e.g. + face LoRA). **$0.029/run** on H100, ~19s. Output is **an array** of length `num_outputs` — index `[0]` for single. Signature gotcha: `lora_scale` (default 1.0, useful 0.6–1.4) is the effect-strength knob; **with `go_fast: true` Replicate silently multiplies it by 1.5×** so adjust accordingly. Faces drift under heavy stylization — lower `prompt_strength` or stack a face LoRA for portrait identity. See [models/levelsio-lomography.md](models/levelsio-lomography.md).

### aramintak/flux-film-foto

Flux-dev LoRA by `aramintak` for a **neutral 35mm / medium-format film aesthetic** — organic grain, halation on highlights, print-like texture, Portra/Ektar/CineStill color science. Aimed at believable "scanned-negative" output, not a lo-fi toy-camera filter. Works in txt2img and img2img, stacks with `extra_lora`. Required: `prompt` containing the **invented trigger token `flmft photo style`** (the literal string `flmft` — a typo or the plain-English `"film photo style"` silently falls back to base Flux with no LoRA effect). **~$0.014/run** on H100 (~71 runs/$1), ~10s warm. Output is **an array** (index `[0]` for single). Signature gotcha: trigger is an invented token, not a phrase — misspell it and you get no effect, just plain Flux; `lora_scale` default 1.0 useful 0.6–1.3, and `go_fast: true` silently multiplies it by 1.5×. See [models/aramintak-flux-film-foto.md](models/aramintak-flux-film-foto.md).

### fofr/flux-bad-70s-food

Novelty/meme Flux-dev LoRA by fofr for the **intentionally-bad 1970s-cookbook-photography aesthetic** — gelatin salads, aspics, beige casseroles, harsh on-camera flash, yellowed color cast, doily-and-parsley staging. Trained to produce _unappetizing_ food; do not use when you want food that looks good. Required: `prompt` with the trigger phrase **`bad 70s food`** (**guessed from the default example — no README confirms it**; variants like `"1970s food"` / `"1970s cookbook photo"` also partially activate). **~$0.018/run** on H100 (~55 runs/$1), ~13s. Low run count (~1,016 lifetime) — fresh, community-sourced, expect occasional weirdness. Output is **an array**. Signature gotcha: trigger phrase is **guessed, not confirmed**, so sweep `"bad 70s food"` vs. variants if activation looks weak; **the LoRA "hits like a truck" at default `lora_scale: 1.0`** — drop to 0.6–0.8 for subtler results, push to 1.1–1.3 for maximum cursed-cookbook energy (`go_fast: true` silently multiplies by 1.5×). See [models/fofr-flux-bad-70s-food.md](models/fofr-flux-bad-70s-food.md).

### afterpeak/flux-slowed

Flux-dev LoRA by `afterpeak` for the **"slowed-audio YouTube/TikTok cover-art" aesthetic** — polished, soft-lit, shallow-DoF female portraits on plain backgrounds, the template used as thumbnail art for slowed/reverb/nightcore audio uploads. **Explicitly NOT vaporwave** and NOT a purple-tint / heavy-blur filter — the look is understated "aesthetic selfie," not overt nostalgia. Trained on ~80 images at 512×512 with a heavy **female-portrait bias** (author's own note: performs best on women) — niche/meme-adjacent, not a general-purpose stylizer. Required: `prompt` starting with the trigger word **`SLOW3D`** (literal numeral `3`, not `SLOWED` / `SLOW3E` — the default example leads with `"SLOW3D. ..."`). **~$0.045/run** on H100 (~22 runs/$1), ~23–30s. Output is **an array**. Signature gotcha: trigger is `SLOW3D` not `SLOWED`; schema default `lora_scale: 1.0` **but the author's default example uses `0.8`** — trust the example, 1.0 over-applies the style and homogenizes faces. Do not use for general subjects (male portraits, landscapes, objects) — the LoRA barely activates outside its trained niche. See [models/afterpeak-flux-slowed.md](models/afterpeak-flux-slowed.md).

### fermatresearch/magic-image-refiner

ControlNet + SD 1.5 img2img refiner for prompt-steerable detail polish, optional `mask` for inpainting, optional 1024/2048 upscale. Inputs: `image` + `prompt` (both required), `mask`, `resolution` (`"original"`/`"1024"`/`"2048"`), `creativity` (0.25 default), `resemblance` (0.75), `hdr`, `scheduler`, `steps`, `guidance_scale`. ~$0.05/run on L40S. Signature gotcha: default `negative_prompt` is **portrait-tuned** (teeth/anatomy) — override for landscapes or non-portrait imagery. `creativity` vs `resemblance` is the main tuning axis. See [models/fermatresearch-magic-image-refiner.md](models/fermatresearch-magic-image-refiner.md).

### jagilley/controlnet-scribble

Original 2023 SD 1.5 ControlNet-scribble — feed a black-on-white line drawing plus a prompt, get a coherent image following the silhouette. Inputs: `image` (scribble), `prompt`, `num_samples` (**string** `"1"`/`"4"`), `image_resolution` (**string** `"256"`/`"512"`/`"768"` — square only), `ddim_steps`, `scale`, `a_prompt`, `n_prompt`, `eta`. Billed per GPU-second, fraction of a cent to a few cents per run. Signature gotcha: `num_samples` and `image_resolution` are **string enums, not ints** — passing an int will 422. No scheduler choice (DDIM only). See [models/jagilley-controlnet-scribble.md](models/jagilley-controlnet-scribble.md).

### adirik/interior-design

Realistic Vision V3.0 (SD 1.5) with **MLSD + segmentation ControlNets stacked** — restyles a room photo while pinning wall/window/ceiling geometry. Inputs: `image` + `prompt` (required), `negative_prompt` (interior-tuned default), `num_inference_steps` (50), `guidance_scale` (**15** — high for SD 1.5), `prompt_strength` (0.8 default; 0.5–0.65 for gentle restyle, 0.9+ for empty-room staging). ~$0.0076/run on L40S, ~8s. Single PNG output. Signature gotcha: existing clutter / people in the source get preserved as warped humanoids — either mask them out or push `prompt_strength` ≥ 0.9. Aspect ratio is inherited from input (no width/height knobs). See [models/adirik-interior-design.md](models/adirik-interior-design.md).

### fofr/face-swap-with-ideogram

**Not a classical face-swap** — a pipeline that uses Ideogram's character-reference feature to re-generate the target image with a new identity. Output is a new Ideogram generation, not pixel-level grafting. Inputs: `character_image`, `target_image`, optional `prompt` (auto-generated via Claude if omitted), `cleanup` (boolean → Nano Banana post-fix pass). Signature gotcha: **target pixels are not preserved** — use a traditional face-swap model if you need pixel-for-pixel preservation outside the face region. Multi-step pipeline → multi-cost (Ideogram + Claude + optional Nano Banana all bill under the hood). See [models/fofr-face-swap-with-ideogram.md](models/fofr-face-swap-with-ideogram.md).

### cswry/seesr

Semantics-aware diffusion super-resolution for **severely degraded** inputs (JPEG artifacts, heavy noise, old scans). Internally runs a DAPE tagger to derive a semantic prompt; `user_prompt` augments it. Inputs: `image`, optional `user_prompt`, `cfg_scale` (3.5–5.5 safe, >6 hallucinates), `num_inference_steps` (30–50), `sample_times` (1–10), `latent_tiled_size`/`latent_tiled_overlap` for large inputs, `scale_factor` (default 4). Output: array of PNGs. Signature gotcha: `seed` default is **fixed at 231, not random** — identical outputs across calls unless you override. See [models/cswry-seesr.md](models/cswry-seesr.md).

### sczhou/codeformer

Transformer-codebook blind face restoration. **Detects and restores all faces** in the frame, not just the largest. Inputs: `image`, `codeformer_fidelity` (0–1 — **low = more restoration / identity drift, high = faithful**), `background_enhance` (default true, runs Real-ESRGAN), `face_upsample`, `upscale`. ~$0.0041/run on L40S, ~5s. Single PNG output. Signature gotcha: low `codeformer_fidelity` (<0.3) can change the subject's identity — always sweep fidelity values (0.3/0.5/0.7/0.9) before committing on recognizable people. See [models/sczhou-codeformer.md](models/sczhou-codeformer.md).

### tencentarc/gfpgan

Classic GAN-prior blind face restoration (StyleGAN2 backbone, 113M+ Replicate runs). Smoother/softer than CodeFormer, stronger on old film scans. Inputs: `img` (**note the field name**, not `image`), `version` (`v1.2`/`v1.3`/`v1.4`/`RestoreFormer`), `scale` (2–4 reasonable). ~$0.0027/run on L40S, ~3s. Signature gotcha: no face-fidelity knob like CodeFormer — you pick a `version` and live with it. `v1.4` default can over-sharpen clean inputs into "AI skin" look; try `v1.3` for gentler output. See [models/tencentarc-gfpgan.md](models/tencentarc-gfpgan.md).

### topazlabs/image-upscale

Topaz's commercial upscaler, up to 6× and 512 MP output. Five `enhance_model` variants: `Standard V2` (default), `Low Resolution V2`, `CGI`, `High Fidelity V2`, `Text Refine`. Pricing scales by **output megapixel count** — 12–24 MP = $0.05, ~96 MP = $0.20, 512 MP cap = $0.82. Inputs: `image`, `enhance_model`, `upscale_factor` (**defaults to `"None"` — you must set `"2x"`/`"4x"`/`"6x"` explicitly**), `subject_detection`, `face_enhancement` + strength/creativity. Signature gotcha: `upscale_factor: "None"` default means enhance-only; also model-name casing is exact (`"Standard V2"` with capital V and space). See [models/topazlabs-image-upscale.md](models/topazlabs-image-upscale.md).

### recraft-ai/recraft-creative-upscale

Recraft's **creative** upscaler — the opposite tier from Topaz on the fidelity↔creativity axis. Single-knob endpoint that enhances and resizes by **hallucinating detail** (re-painted textures, skin pores, fabric weave, foliage) rather than preserving pixels. Closest in spirit to Magnific / Clarity-upscaler "re-imagine" passes. Inputs: `image` is the **only field** — no upscale-factor selector, no creativity dial, no seed, no format choice. Output: a single **WebP** URI (not PNG). Pricing **not published as a flat per-run number on the model page** — Recraft API models on Replicate are typically in the ~$0.04–0.06 range and the creative tier is usually priced above the base text-to-image; check the playground price estimator at <https://replicate.com/recraft-ai/recraft-creative-upscale> before a batch. Signature gotcha: **by design alters the image** — re-painted skin, altered grain, invented micro-detail — so **not for identity-sensitive work** (real people, product shots, evidence, exact-pixel client deliverables). Use Topaz `High Fidelity V2` or SeeSR when faithfulness matters. ~47 s predict time in the default example — not a real-time tool. See [models/recraft-ai-recraft-creative-upscale.md](models/recraft-ai-recraft-creative-upscale.md).

### recraft-ai/recraft-crisp-upscale

Recraft's **crisp** (faithful) upscaler — the pixel-preserving sibling of `recraft-creative-upscale`. Sharpens and cleans while resizing **without hallucinating detail**: no re-painted skin, no morphed features, no invented texture. Identical API surface to the creative variant — **one input: `image`, zero knobs** (no factor selector, no format choice, no seed). Output: a single **WebP** URI. Roughly **~5× faster than creative** (~9 s vs ~47 s predict time in default examples) since it's a cleanup/sharpening pass rather than a diffusion re-paint. Pricing **not published as a flat per-run number on the model page** — check the playground estimator at <https://replicate.com/recraft-ai/recraft-crisp-upscale> before batching. Signature gotcha: no upscale-factor control — the model decides output size from input; pre-resize or use Topaz if you need explicit 2×/4×/6×. Pick this over creative whenever identity / brand / typography fidelity matters; pick it over Topaz for zero-config single-call faithful upscales. See [models/recraft-ai-recraft-crisp-upscale.md](models/recraft-ai-recraft-crisp-upscale.md).

### andreasjansson/illusion

qrcode-monster ControlNet on SD 1.5 + Realistic Vision — produces the viral "scannable QR hidden in an oil painting" effect. Inputs: `prompt`, `qr_code_content` (**required even when supplying custom `image`** — pass `""`), optional `image` (custom control, overrides QR), `controlnet_conditioning_scale` (2.2 default — **the main tuning knob**, sweep 1.4–2.6), `guidance_scale`, `width`/`height`, `num_outputs` (1–4), `border`, `qrcode_background`. ~$0.0033/run on L40S, ~4s. Signature gotchas: **(1) bare slug 404s** — must pin a version hash (`andreasjansson/illusion:75d51a73...`) pulled from the model page's API tab; **(2) scannability vs beauty is a real tradeoff** — sweep `controlnet_conditioning_scale` and test-scan with a real phone before committing. See [models/andreasjansson-illusion.md](models/andreasjansson-illusion.md).

## Modality-specific gotchas

Things that trip up image generation across most models on Replicate:

- **`aspect_ratio` enum vs float freedom.** Most models accept a fixed enum (`"1:1"`, `"16:9"`, ...). A few (Bria, some Flux variants) also accept an arbitrary float in `[0.5, 3.0]`. Arbitrary ratio strings outside the enum (`"7:11"`, `"2.3:1"`) will almost always 422 — stick to the listed enums or the numeric-float path when available. ControlNet-style models (Flux Canny, Kontext, interior-design) often inherit aspect from the input image and expose no ratio control at all — crop the input first.
- **NSFW / safety filters vary wildly by vendor.** BFL (Flux Pro, Kontext) uses `safety_tolerance: 1–6` (1 strictest). Multi-image Kontext caps at 2 even at its "max permissive". Bria models log moderation warnings but may still produce output. `disable_safety_checker: true` on Flux Dev LoRA endpoints is API-only. Expect more rejections on Kontext / Bria than on the open SD 1.5 community models.
- **Seed reproducibility is not universal.** `black-forest-labs/flux-dev-lora` with default `go_fast: true` is **non-deterministic even with `seed` set** — you must turn `go_fast: false`. `cswry/seesr` defaults to a **fixed seed of 231** (so identical outputs across calls unless overridden). `lucataco/realistic-vision-v5.1` treats `seed: 0` as "random" — pass `≥1` to pin.
- **Output format / extension defaults are inconsistent.** Flux Dev LoRA defaults to `webp`; BFL Kontext multi-image defaults to `png` (not `jpg` like other BFL endpoints); Bria models return PNG with no format control; LCM returns JPG. Some endpoints return an **array of URIs** even for `num_outputs: 1` (Flux LoRA, SeeSR, LCM, scribble, illusion, magic-refiner), while others return a single string (Canny Pro, Kontext Max, interior-design, CodeFormer, GFPGAN). Unwrap accordingly.
- **Local-path auto-upload behavior.** The repo's `scripts/run_model.py` auto-uploads local file paths given to image/URI fields — so `./portrait.jpg` works on any field documented as `string (URI)`. Straight Replicate SDK calls require you to upload or host the file first. Field names for image inputs vary by model: `image`, `img` (GFPGAN), `control_image` (Flux Canny), `input_image_1`/`input_image_2` (Kontext multi), `character_image`/`target_image` (face-swap-with-ideogram) — check the per-model schema.
- **Every Flux LoRA has a different trigger word convention — forgetting it silently falls back to base Flux.** The wrapper endpoint (`black-forest-labs/flux-dev-lora` schema) always returns an image, so a missing or mistyped trigger produces a plain Flux-dev output with no LoRA effect and no error. Conventions vary per LoRA author: default trainer placeholder like **`TOK lomography`** (`levelsio/lomography`), invented made-up tokens like **`flmft photo style`** (`aramintak/flux-film-foto`) or **`SLOW3D`** with a literal numeral 3 (`afterpeak/flux-slowed`), or natural-language phrases like **`bad 70s food`** (`fofr/flux-bad-70s-food`, guessed from the default example — not officially confirmed). Always check the per-model ref for the exact trigger string; typos (`film photo style` instead of `flmft photo style`, `SLOWED` instead of `SLOW3D`) activate nothing. This applies to the Kontext-LoRA fine-tunes (`fofr/kontext-ps1`, `fofr/kontext-fix-jpeg-compression`) as well, though those use natural-language prompts without explicit trigger tokens.

## Cost awareness

Image generation is mostly cheap, but the tail gets expensive. Rough ranges (confirm on replicate.com/<model>):

- GFPGAN, CodeFormer, illusion, interior-design: **~$0.003–0.01** per run
- Realistic Vision v5.1, LCM, scribble: **~$0.001–0.05** per run (billed per GPU-second)
- Magic refiner, Bria FIBO / image-3.2, Flux Dev LoRA, multi-LoRA: **~$0.03–0.08** per run
- BAGEL, Flux Canny Pro, Kontext Max, Topaz at low MP: **~$0.05–0.10** per run
- Topaz at high MP (6× large input, up to 512 MP): **up to $0.82** per run

Tell the user the model and rough cost before kicking off anything above ~$0.10 unless they explicitly picked it.
