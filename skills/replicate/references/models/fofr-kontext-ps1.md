# fofr/kontext-ps1

Model page: <https://replicate.com/fofr/kontext-ps1>

**Kontext fine-tune for the PS1 / early-3D video-game aesthetic.** A LoRA-fine-tune of Black Forest Labs' **Flux Kontext** (the prompt-driven, identity-preserving image editor) by [fofr](https://replicate.com/fofr), tuned to restyle any input photo or illustration into the look of mid-1990s 3D console games — low-poly geometry, low-resolution textures, dithered shading, vertex wobble, limited palette, and the characteristic "PS1 jank." The model description says it covers both **PS1 and PS2** eras. Unlike a generic LoRA load on `flux-dev`, the Kontext base means structural composition and subject identity are preserved during the restyle — your portrait's face, pose, and framing survive the transformation.

This is a **stylization** fine-tune, not a restoration tool. It actively **degrades** the input toward an early-3D look; it will not enhance or upscale.

## When to pick this over alternatives

- **Generic LoRA-style-transfer** (e.g. running a community PS1-style LoRA on `black-forest-labs/flux-dev-lora`) — those need LoRA hosting, weight management, careful trigger words, and prompt engineering to dial in the look. `fofr/kontext-ps1` is a **single-purpose endpoint** with the LoRA pre-loaded and the style baked in. Less flexible, far less fiddly.
- **Generic img2img / refinement** (`fermatresearch/magic-image-refiner`) — those refine toward photoreal under prompt control; getting "PS1 game" out of them requires a strong, well-crafted prompt and significant `creativity`. Kontext-PS1 is **hardcoded** to the aesthetic — the prompt is for nudging, not for defining the style.
- **Vintage / film-look filters** (`levelsio/lomography`, etc.) — different aesthetic axis. Lomo / cross-process / VHS filters target **late-1990s–2000s analog photography**. PS1-style targets **1994–2000 console 3D rendering** (geometry artifacts, not film artifacts). Don't confuse the two — pick by whether you want "old camera" or "old game engine."
- **`fofr/kontext-fix-jpeg-compression`** (sibling fofr Kontext fine-tune) — opposite direction: that one **removes** compression artifacts; this one **adds** stylization artifacts.
- **Sweet spot:** memes, retro-gaming content, nostalgia art, character-portrait restyles, "what would I look like as a Final Fantasy VII NPC" projects, social-media / album-art bits.

## Input schema

| Field                    | Type         | Required | Default               | Description                                                                                                                                                                                                                                                             |
| ------------------------ | ------------ | -------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                 | string       | Yes      | —                     | Editing instruction. The PS1 style is baked into the LoRA, but you still must pass a prompt — the default example uses `"render this image like a ps1 game (no UI)"`. Use this field to nudge specific aspects (e.g. "heavy dithering", "emphasize low-poly", "no UI"). |
| `input_image`            | string (URI) | Yes      | —                     | Image to restyle. Must be **jpeg, png, gif, or webp**. Local paths are auto-uploaded by `run_model.py`.                                                                                                                                                                 |
| `aspect_ratio`           | enum         |          | `"match_input_image"` | Output aspect ratio. `match_input_image` preserves the input's aspect ratio (recommended for restyles).                                                                                                                                                                 |
| `megapixels`             | enum         |          | `"1"`                 | Approximate output size in megapixels. Inherited Kontext field.                                                                                                                                                                                                         |
| `num_inference_steps`    | integer      |          | `30`                  | Diffusion steps. Range **4–50**.                                                                                                                                                                                                                                        |
| `guidance`               | number       |          | `2.5`                 | Classifier-free guidance scale. Range **0–10**. Kontext defaults are low (2.5) — raising it pushes harder toward the prompt at the cost of artifacts.                                                                                                                   |
| `seed`                   | integer      |          | random                | Random seed for reproducible runs. Leave blank for random.                                                                                                                                                                                                              |
| `output_format`          | enum         |          | `"webp"`              | Output image format (typically `"webp"`, `"png"`, `"jpg"`).                                                                                                                                                                                                             |
| `output_quality`         | integer      |          | `80`                  | Encoder quality 0–100. Ignored for `png`.                                                                                                                                                                                                                               |
| `disable_safety_checker` | boolean      |          | `false`               | Disable the NSFW filter on output.                                                                                                                                                                                                                                      |
| `lora_strength`          | number       |          | `1`                   | Strength of the PS1 LoRA. **Lower (~0.6–0.8) = subtler stylization; higher (>1) = more aggressive but risks artifacts.** This is the main tuning knob for "how PS1."                                                                                                    |
| `replicate_weights`      | string       |          | —                     | Path to alternative LoRA weights. Inherited from the Kontext-LoRA template; **you almost certainly do not want to set this** — overriding it replaces the PS1 LoRA with whatever weights you point at, defeating the purpose of using this endpoint.                    |

**`prompt` is required but the style is hardcoded.** The PS1 look comes from the LoRA, not the prompt. The prompt is an editing instruction in the Kontext sense — it can carry useful nudges ("no UI", "no HUD", "third-person view", "render at low resolution"), but you do not have to (and should not need to) re-describe the PS1 aesthetic in words.

**`safety_tolerance` is not exposed on this endpoint.** Unlike the `black-forest-labs/flux-kontext-*` canonical endpoints, this fine-tune surfaces only `disable_safety_checker` (boolean), not the BFL 0–6 safety dial.

## Output

A **single URI string** pointing to the generated image (not an array). `run_model.py` saves it as `fofr_kontext-ps1_0.<ext>` where `<ext>` matches `output_format` (default `webp`).

Typical prediction time: **~10–24 seconds** on H100 (default example finished in ~10s; the model card cites ~24s as the typical case).

## Pricing

**$0.036 per run** (~27 runs per $1) on Nvidia H100. Flat per-run pricing — runtime variation does not change cost. Confirm at <https://replicate.com/fofr/kontext-ps1> before batching.

## Examples

**1. Photo → PS1 character render** (canonical use — the default example):

```bash
python scripts/run_model.py fofr/kontext-ps1 \
    --input '{
      "prompt": "render this image like a ps1 game (no UI)",
      "input_image": "./refs/cool_selfie.webp",
      "aspect_ratio": "match_input_image",
      "output_format": "webp"
    }' \
    --output ./out/
```

**2. Illustration → PS1** (digital art / cartoon → low-poly game look; raise `lora_strength` slightly for a stronger restyle on already-stylized inputs):

```bash
python scripts/run_model.py fofr/kontext-ps1 \
    --input '{
      "prompt": "render this character as a ps1 era 3d game model, third-person view, no HUD",
      "input_image": "./refs/concept_art.png",
      "aspect_ratio": "match_input_image",
      "lora_strength": 1.1,
      "num_inference_steps": 35,
      "output_format": "png",
      "seed": 42
    }' \
    --output ./out/
```

**3. Prompt-nudged restyle** (use the prompt to push specific PS1 sub-aesthetics — heavy dithering, hard polygon edges, fixed-camera survival-horror look à la _Resident Evil_ / _Silent Hill_):

```bash
python scripts/run_model.py fofr/kontext-ps1 \
    --input '{
      "prompt": "ps1-era 3d render, heavy ordered dithering, emphasize low-poly geometry with visible hard edges, muddy low-resolution textures, fixed camera angle survival horror aesthetic",
      "input_image": "./refs/hallway.jpg",
      "aspect_ratio": "match_input_image",
      "guidance": 3.5,
      "lora_strength": 1.0,
      "num_inference_steps": 40,
      "output_format": "png"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Faithful PS1/PS2-era aesthetic out of the box — texture warping (the affine perspective-correction artifact), vertex wobble, dithered shading, limited color palette, low-resolution texturing all show up without needing prompt coaching.
- Composition and subject identity are preserved well (Kontext base) — the person, pose, and framing of your input survive the restyle, which is the differentiator vs a raw `flux-dev` LoRA pass.
- Cheap (~$0.036) and fast (~10–24s on H100) — viable for batch / iteration.
- Works on photos, illustrations, and digital art alike. Strongest results on portraits and character-centric inputs (PS1 was a character-rendering era — that's what the LoRA was trained on).
- The prompt is a real editing knob — useful nudges like `"no UI"`, `"no HUD"`, `"third-person camera"`, `"fixed camera"`, `"emphasize dithering"` all land.

**Gotchas:**

- **Stylization, not restoration.** The model **degrades** the input toward 1990s rendering quality — low res, low poly, color banding. Do not use as an enhancer.
- **Modern faces in low-poly look uncanny.** PS1-era character models had ~300–500 polys for an entire human; faces become flat, eye geometry collapses, and the result can land in uncanny-valley territory rather than charming retro. This is a known PS1 aesthetic feature, but if you wanted "cute retro," portraits with extreme detail can read as creepy. Caricatured / stylized source faces handle the conversion more flatteringly than realistic studio portraits.
- **Composition is preserved more than identity at the pixel level.** Framing, subject placement, and pose survive. Fine-grained facial identity does not — Kontext keeps "a person who looks roughly like this" but the polygon reduction destroys micro-features. Don't expect a recognizable likeness of a specific person.
- **`lora_strength` is the main quality knob.** Default `1.0` is the trained sweet spot. Drop to `0.6–0.8` if the output is too aggressive / abstract and you want a hint of PS1 over a more legible image. Raise to `1.1–1.3` for stronger PS1 commitment, but expect more artifacts and identity loss above ~1.2.
- **Do not set `replicate_weights`** unless you mean to override the PS1 LoRA with your own weights (which makes this endpoint pointless — use `black-forest-labs/flux-dev-lora` instead).
- **`prompt` is required.** Even if you have nothing specific to say, you must pass a string — `"render this image like a ps1 game (no UI)"` (the default example) is a reasonable always-on baseline.
- **`output_format` defaults to `webp`** — fine for web display, less ideal for re-editing or print. Set `png` for lossless output if you intend to composite further.
- **No README on Replicate.** The model description is one sentence; everything else is reverse-engineered from the schema and default example. fofr's broader work is on GitHub: <https://github.com/fofr>.
- **PS1 vs PS2 selectivity:** the description mentions both eras but exposes no toggle. The trained look skews toward PS1-era aesthetics (more aggressive low-poly, dithering); for a cleaner PS2 / Dreamcast look you can try prompting `"ps2 era 3d render, smoother textures"` but results may not differ dramatically — the LoRA dominates the prompt.
- **Single output per call.** Returns one URI. Loop with different seeds for variations.
