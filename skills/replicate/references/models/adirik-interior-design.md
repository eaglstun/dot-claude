# adirik/interior-design

Model page: <https://replicate.com/adirik/interior-design>

Interior-room restyling via text prompt. Feed in a photo of a real or empty room, add a prompt like `"scandinavian living room with oak floors, linen sofa, large windows"`, and get back a restyled version of that same room. Under the hood it's **Realistic Vision V3.0 (SD 1.5)** with **two ControlNets stacked — MLSD (straight-line/architectural) + segmentation** — which is what makes it preserve room geometry (walls, windows, doorways, ceiling lines) while letting the diffusion freely replace furniture, materials, color, and styling. GitHub: <https://github.com/neuralwork/sd-interior-design>.

## When to pick this over alternatives

- **Pick it over plain img2img (SD / SDXL / Flux img2img)** when you need the architectural bones of the room to survive — img2img has no structure prior and will happily rotate walls, move windows, or re-proportion the ceiling. This model's MLSD + seg stack nails those down.
- **Pick it over generic ControlNet pipelines** when you don't want to produce the MLSD line-map and segmentation mask yourself. This model runs both extractors internally from a single RGB input.
- **Sweet spot:** virtual staging (empty room → fully furnished), style swaps (modern → rustic, beige → maximalist), real-estate before/after renders, quick client-facing mood iteration.
- **Skip it** for: exterior shots, landscape / garden design, product-only composites, or when you want to _redesign_ the architecture itself (move a wall, add a skylight) — the ControlNets will fight you.

## Input schema

| Field                 | Type         | Required | Default                                                                                                                                                                                                                            | Description                                                                                                                                        |
| --------------------- | ------------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `image`               | string (URI) | yes      | —                                                                                                                                                                                                                                  | Source room photo. Local paths are auto-uploaded by `run_model.py`. MLSD + segmentation are extracted from this image internally.                  |
| `prompt`              | string       | yes      | —                                                                                                                                                                                                                                  | Text prompt describing the desired style / furnishing. Be specific about style label, materials, key pieces, and lighting.                         |
| `negative_prompt`     | string       |          | `"lowres, watermark, banner, logo, watermark, contactinfo, text, deformed, blurry, blur, out of focus, out of frame, surreal, extra, ugly, upholstered walls, fabric walls, plush walls, mirror, mirrored, functional, realistic"` | Content to exclude. The default is already well-tuned — keep it and append, don't replace wholesale.                                               |
| `num_inference_steps` | integer      |          | `50`                                                                                                                                                                                                                               | Diffusion steps. Range `1–500`. `50` is the sweet spot; above `80` rarely helps on SD 1.5.                                                         |
| `guidance_scale`      | number       |          | `15`                                                                                                                                                                                                                               | Classifier-free guidance. Range `1–50`. Unusually high default (most SD 1.5 pipelines sit at 7–9). Higher = more prompt-literal but risks burn-in. |
| `prompt_strength`     | number       |          | `0.8`                                                                                                                                                                                                                              | **Main tuning knob.** Range `0–1`. How much of the source image gets overwritten by the prompt. `1.0` = full destruction of input; see below.      |
| `seed`                | integer      |          | random                                                                                                                                                                                                                             | Set for reproducibility. Useful for style-swap sweeps over the same room.                                                                          |

Local file paths for `image` are auto-uploaded by `run_model.py`.

## Output

A **single URI** (not an array) pointing to the restyled PNG. Saved as `adirik_interior-design_0.png`.

## Pricing

**~$0.0076 per run** on Nvidia L40S — roughly **131 runs per $1**. Predictions typically complete in **~8 seconds**. Cheap enough to run seed sweeps and prompt-strength ladders per room without worrying about cost.

## Examples

**Empty room → fully staged in a given style.** Default `prompt_strength: 0.8` is right for this case — the room has little content to preserve, so you want the model to freely invent furniture:

```json
{
  "image": "./empty_living_room.jpg",
  "prompt": "a scandinavian living room with light oak flooring, a pale linen sofa, a round marble coffee table, a tall fiddle-leaf fig in a woven basket, abundant natural daylight, minimalist Nordic aesthetic, warm and inviting",
  "guidance_scale": 15,
  "prompt_strength": 0.8,
  "num_inference_steps": 50,
  "seed": 42
}
```

```bash
python scripts/run_model.py adirik/interior-design \
    --input-file input.json \
    --output ./out/
```

**Existing furnished room → style swap (modern → rustic).** Drop `prompt_strength` to `0.6–0.7` so the room's architectural proportions and framing stay locked in:

```json
{
  "image": "./modern_bedroom.jpg",
  "prompt": "rustic farmhouse bedroom with a reclaimed-wood four-poster bed, handwoven wool throws in cream and rust, a vintage kilim rug, wrought-iron sconces with warm Edison bulbs, white-washed timber ceiling beams, cozy evening light",
  "negative_prompt": "lowres, watermark, text, deformed, blurry, modern minimalist, glass, chrome, neon",
  "guidance_scale": 14,
  "prompt_strength": 0.65,
  "num_inference_steps": 60,
  "seed": 12345
}
```

```bash
python scripts/run_model.py adirik/interior-design \
    --input-file input.json \
    --output ./out/
```

**Prompt-strength sweep** — the recommended way to dial a specific room. Same prompt, four strengths, pick the one that balances structure preservation vs style commitment:

```json
{
  "image": "./kitchen.jpg",
  "prompt": "a japandi kitchen with matte black cabinetry, light oak open shelving, white oak countertops, brass fixtures, a single statement pendant, soft diffused morning light, calm and uncluttered",
  "prompt_strength": 0.7,
  "guidance_scale": 15,
  "num_inference_steps": 50,
  "seed": 7
}
```

```bash
for s in 0.55 0.7 0.85 0.95; do
  jq ".prompt_strength = $s" input.json > _tmp.json
  python scripts/run_model.py adirik/interior-design \
      --input-file _tmp.json \
      --output "./out/ps_${s}/"
done
```

## Strengths / gotchas

**Good at:**

- Preserving architectural features — windows, doorways, wall corners, ceiling height, floor lines — thanks to the MLSD ControlNet locking in straight-line geometry.
- Respecting room zoning (floor vs wall vs furniture vs ceiling) thanks to the segmentation ControlNet.
- Restyling furniture, materials, palette, lighting mood, and decor — the parts of the room that _should_ change across design variations.
- Virtual staging of empty rooms, which is the cleanest use-case: no existing clutter to fight.
- Fast + cheap enough (~8s, ~$0.008) for interactive iteration with a client.

**The `prompt_strength` knob (most important control):**

- `~0.5–0.65` → gentle restyle. Keeps much of the source — colors, approximate furniture layout, materials shift but identity remains. Best when you want "the same room, but darker / warmer / more modern."
- `~0.75–0.85` (default `0.8`) → standard restyle. Furniture can be replaced wholesale; style is committed. Recommended for most style-swap jobs.
- `~0.9–1.0` → aggressive. Approaches "room silhouette only, everything else from prompt." Use for empty-room staging or when the source furniture is so ugly you want it gone entirely. At `1.0` you're essentially doing ControlNet-only generation.

**Gotchas:**

- **Existing clutter and people are a problem.** The segmentation ControlNet will see a person or a pile of laundry as an object to preserve — you often get a blurry humanoid or warped clutter in the output. Either mask/remove people first, or push `prompt_strength` up toward `0.9+` to overwrite them.
- **Source image quality matters a lot.** Tilted phone photos, fisheye distortion, heavy shadows, or motion blur degrade the MLSD line extraction and you lose structure preservation. Feed in clean, well-lit, roughly level shots.
- **Aspect ratio is inherited from the input image** — there's no `width`/`height` knob. If you want a specific output ratio, crop the input first. Very wide panoramas (>2:1) can confuse the SD 1.5 backbone; cropping to a more typical ~3:2 or 4:3 real-estate ratio helps.
- **`guidance_scale: 15` is high by SD 1.5 standards.** It's tuned for interior-design prompts (which tend to be long and stylistically specific). If outputs look over-saturated or have "burned" highlights, try `10–12`.
- **The default `negative_prompt` already excludes `"mirror, mirrored, realistic, upholstered walls, fabric walls"`** — weird interior-design-specific failure modes the author has seen. Keep it and append, don't delete.
- **Style-label literalism.** Naming a recognizable style ("scandinavian", "japandi", "art deco", "mid-century modern", "wabi-sabi", "boho", "brutalist") works far better than describing the mood abstractly. The SD 1.5 backbone has strong priors on named styles.
- **Output is always a single PNG** via a single URI (not an array). `num_outputs` is not in the schema — to get variations, re-run with different seeds.
- **Not a renovation tool.** If you prompt "add a skylight" or "knock out this wall", the ControlNets will prevent it. This model restyles _within_ existing geometry. For structural changes, use an inpainting model with a manually-painted mask.
