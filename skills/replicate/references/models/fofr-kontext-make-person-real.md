# fofr/kontext-make-person-real

Model page: <https://replicate.com/fofr/kontext-make-person-real>

A **FLUX.1 Kontext fine-tune specifically trained to fix plastic AI skin** — take an AI-generated portrait with smooth, waxy, over-rendered skin and return it with realistic pores, subtle imperfections, natural skin texture, and de-smoothed facial detail. The training data pairs heavy "AI skin" shots with photoreal counterparts, so the baked-in LoRA does the corrective mapping while Flux Kontext handles the image-editing pass. Latest version: `3f0b0f59...` (2025-07-20). Heavily used in the wild (~20k runs as of 2026-04).

## When to pick this over alternatives

- **Pick it over `sczhou/codeformer` or `tencentarc/gfpgan`** when your input is an **AI render** (Flux, SDXL, MJ) that looks plastic. CodeFormer/GFPGAN are blind face **restoration** models tuned for degraded/old photos — on clean AI output they barely move the needle. This model is the opposite: trained to add texture back to over-smoothed AI skin.
- **Pick it over base `black-forest-labs/flux-kontext-max`** when the edit you want is specifically "make this person look real". You can do it with Kontext Max + a good prompt, but the specialized LoRA here gets there with far less prompt engineering and less identity drift.
- **Pick it over a fresh T2I re-roll** when you want to preserve the pose, composition, wardrobe, and overall likeness of an existing image — this is an **editor**, not a regenerator.
- **Skip it** for photos (non-AI sources) — its correction target is AI-over-smoothed skin, and it can over-texture real photographs.

## Input schema

| Field                    | Type         | Required | Default               | Description                                                                                                                                 |
| ------------------------ | ------------ | -------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                 | string       | yes      | —                     | Edit instruction. The standard pattern is `"make this person look real, bad skin"` — describe the target, not the source.                   |
| `input_image`            | string (URI) | yes      | —                     | Source image (jpeg/png/gif/webp). Local paths are auto-uploaded by `run_model.py`.                                                          |
| `aspect_ratio`           | enum         |          | `"match_input_image"` | `1:1`, `16:9`, `21:9`, `3:2`, `2:3`, `4:5`, `5:4`, `3:4`, `4:3`, `9:16`, `9:21`, or `match_input_image`. Default matches the input.         |
| `megapixels`             | enum         |          | `"1"`                 | `"1"` (full megapixel) or `"0.25"` (quarter-MP, faster/cheaper drafts). Strings, not numbers.                                               |
| `num_inference_steps`    | integer      |          | `30`                  | Range `4–50`. 30 is the sweet spot; below 20 the correction thins out; above 40 rarely helps.                                               |
| `guidance`               | number       |          | `2.5`                 | Classifier-free guidance, range `0–10`. Kontext-appropriate range is `2–4`; Flux Kontext collapses if you push it toward typical SD values. |
| `lora_strength`          | number       |          | `1`                   | Strength of the bundled "make person real" LoRA. Range in practice `0–1.5`. **Main tuning knob** — see gotchas.                             |
| `replicate_weights`      | string       |          | —                     | Optional extra LoRA path (Replicate URL to a `.safetensors`). Stacks on top of the bundled one.                                             |
| `seed`                   | integer      |          | random                | Set for reproducibility. Same seed + same inputs = same output.                                                                             |
| `output_format`          | enum         |          | `"webp"`              | `webp`, `jpg`, or `png`. Use `png` for lossless, `webp` for smallest file.                                                                  |
| `output_quality`         | integer      |          | `80`                  | `0–100`. Ignored for PNG. `100` = max quality.                                                                                              |
| `disable_safety_checker` | boolean      |          | `false`               | Flip to `true` only if you're running trusted inputs and don't want false-positive blocks. Leave `false` for anything user-facing.          |

## Output

**Bare URI string** — single image file (format per `output_format`). Saved as `fofr_kontext-make-person-real_0.{ext}` by `run_model.py`.

## Pricing and runtime

Not listed explicitly in the schema — confirm on the model page. Flux Kontext fine-tunes typically run **~$0.04 per image** on L40S-class hardware. Default example predicted in **~11 seconds** — fast enough for iterative `lora_strength` sweeps.

## Examples

**Default de-plastic pass** — minimum-effort invocation on any AI portrait:

```json
{
  "input_image": "./ai_portrait.png",
  "prompt": "make this person look real, bad skin",
  "lora_strength": 1.2,
  "output_format": "png",
  "output_quality": 100
}
```

```bash
python scripts/run_model.py fofr/kontext-make-person-real \
    --input-file input.json \
    --output ./out/
```

**Subtle correction** — for images that only have slight smoothing, don't over-texture:

```json
{
  "input_image": "./ai_portrait.png",
  "prompt": "make this person look real, natural skin texture, subtle pores",
  "lora_strength": 0.7,
  "guidance": 2.5,
  "num_inference_steps": 30,
  "output_format": "png"
}
```

**Lora-strength sweep** — the recommended workflow for landing the right amount of correction per image:

```bash
for s in 0.7 1.0 1.2 1.4; do
  jq ".lora_strength = $s" input.json > _tmp.json
  python scripts/run_model.py fofr/kontext-make-person-real \
      --input-file _tmp.json \
      --output "./out/lora_${s}/"
done
```

## Strengths / gotchas

**Good at:**

- Fixing Flux/SDXL/MJ "porcelain doll" skin — restores pores, subsurface scattering look, subtle imperfections
- Preserving identity through the edit — the same face comes back with better skin, not a different face
- Light-lift fixes where you don't want to regenerate the whole image
- Preserving wardrobe, hair, pose, and lighting direction while only nudging skin realism

**Gotchas:**

- **`lora_strength` is the main knob.** Default `1.0` is a reasonable middle; the default-example showcase uses `1.2`. Go higher (`1.3–1.5`) for images that look **severely** plastic; go lower (`0.6–0.9`) for mild smoothing — above ~1.5 you start seeing over-pronounced blemishes and texture artifacts.
- **Not a general super-res or restorer.** Won't upscale, won't fix blur, won't recover lost detail. For degraded photos use `sczhou/codeformer`; for AI plastic-skin specifically, use this.
- **Prompt pattern matters.** `"make this person look real, bad skin"` (counterintuitively, the phrase "bad skin" steers the model toward natural imperfections) is the baseline. Freeform prompts like `"photorealistic portrait of a person"` work less reliably.
- **`guidance` low band only.** Flux Kontext wants `2–4`; pushing to 7–8 (normal SD values) yields washed-out, over-contrasted output. Leave `guidance` at its default `2.5` unless you know you're fighting a specific failure.
- **Megapixels is a string enum.** `"1"` or `"0.25"` — quoting matters. Use `"0.25"` for fast `lora_strength` sweeps, then re-render winners at `"1"`.
- **Can over-texture real photos.** If the input is a real photograph that only looks slightly soft, expect aggressive pore/imperfection addition. Lower `lora_strength` or skip the model entirely for photo sources.
- **Output format default is `webp`.** Override to `png` + `output_quality: 100` for further downstream editing (Photoshop, compositing) — webp + 80 loses detail you can't get back.
- **Safety checker on by default.** Good — keep it that way for user-facing surfaces. Only disable for trusted internal pipelines.
- **Version pin:** `fofr/kontext-make-person-real:3f0b0f59a22997052c144a76457f113f7c35f6573b9f994f14367ec35f96254d` — pin if you want byte-reproducible behavior, since fofr iterates on LoRA weights periodically.
