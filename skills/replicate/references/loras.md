# Working with LoRAs on Replicate

Source: https://replicate.com/docs/guides/extend/working-with-loras

## What a LoRA is

A small set of weights (typically a few MB) that layers on top of a frozen base model to apply a style, subject, or concept. Cheaper and more flexible than fine-tuning the full model. Multiple LoRAs can stack on the same generation.

## Base models that accept LoRAs

| Modality | Models                                     |
| -------- | ------------------------------------------ |
| Image    | Flux Dev, Flux Schnell, SDXL, RealVisXL v3 |
| Video    | Wan2.1, HunYuan Video                      |

## LoRA-aware models on Replicate

**Image:**

- `black-forest-labs/flux-dev-lora` — single LoRA on Flux Dev
- `black-forest-labs/flux-schnell-lora` — single LoRA on Flux Schnell (fast/cheap)
- `lucataco/flux-dev-multi-lora` — two LoRAs combined
- `lucataco/flux-schnell-lora`
- `fofr/realvisxl-v3-multi-controlnet-lora`

**Video:**

- `fofr/wan2.1-with-lora`
- `zsxkib/hunyuan-video-lora`

## Where LoRAs come from

Any of the following are valid for `hf_lora` / `extra_lora` / `lora_weights` fields:

- **Replicate trained model** — slug: `username/model-name` (e.g., `zeke/ziki-flux`) or pinned `username/model-name:version_id`
- **Hugging Face repo** — slug: `hf-user/repo-name`
- **Civitai** — direct download URL to the `.safetensors` file
- **Direct HTTPS URL** — to a `.safetensors` file anywhere

Replicate's "Flux fine-tunes" collection is a good discovery starting point.

## Common input fields

Field names differ per model — always check the model page — but these are the recurring ones:

| Field                       | What it does                             | Typical range   |
| --------------------------- | ---------------------------------------- | --------------- |
| `hf_lora` or `lora_weights` | The primary LoRA to apply                | slug / URL      |
| `lora_scale`                | Strength of the primary LoRA             | 0–2 (default 1) |
| `extra_lora`                | Secondary LoRA (multi-lora models only)  | slug / URL      |
| `extra_lora_scale`          | Strength of secondary LoRA               | -1 to 2         |
| `prompt`                    | Must include trigger words for each LoRA | —               |

**Trigger words are critical.** Each trained LoRA has its own activation token (e.g. `ZIKI`, `in MSMRB style`). Without them in the prompt, the style often won't apply. The trigger words are listed on the LoRA's Replicate or Hugging Face page.

## Single LoRA example

```bash
python scripts/run_model.py black-forest-labs/flux-dev-lora \
    --input '{
      "prompt": "ZIKI the man standing on a beach at golden hour",
      "hf_lora": "zeke/ziki-flux",
      "lora_scale": 1.0,
      "aspect_ratio": "1:1",
      "num_outputs": 1
    }' \
    --output ./out/
```

## Multi-LoRA example (stacking two styles)

```bash
python scripts/run_model.py lucataco/flux-dev-multi-lora \
    --input '{
      "prompt": "ZIKI the man, illustrated MSMRB style",
      "hf_lora": "zeke/ziki-flux",
      "lora_scale": 1.0,
      "extra_lora": "jakedahn/flux-midsummer-blues",
      "extra_lora_scale": 1.1,
      "aspect_ratio": "1:1",
      "guidance_scale": 3.5,
      "num_outputs": 4
    }' \
    --output ./out/
```

Tuning tip: when stacking, start both scales in the **0.9–1.1** window. If one style dominates, lower its scale first rather than cranking the other.

## Video LoRA example (Wan2.1)

```bash
python scripts/run_model.py fofr/wan2.1-with-lora \
    --input '{
      "prompt": "a dragon soaring over mountains, cinematic",
      "lora_url": "https://huggingface.co/some-user/wan-dragon-lora/resolve/main/model.safetensors",
      "lora_strength": 1.0,
      "duration": 5
    }' \
    --output ./out/
```

The field name on Wan-with-LoRA models is often `lora_url` or `lora_weights` rather than `hf_lora` — confirm on the model page.

## Training your own LoRA

For Flux, the standard trainer is **`ostris/flux-dev-lora-trainer`**. The iterative workflow:

1. Gather 10–30 images of your subject/style, high-quality and consistent.
2. Upload as a zip.
3. Run the trainer; it produces a model you can call directly or use as `hf_lora`.
4. (Optional) Generate synthetic data with your new LoRA + community LoRAs, curate the best outputs, and retrain for a sharper result.

The trainer takes inputs like `input_images` (zip URL), `trigger_word`, `steps`, and `lora_rank`. Training runs are 20–40min and cost ~$2–5.

## Gotchas

- **Trigger word missing from prompt** → LoRA seems inactive. First thing to check.
- **Scale too high** (>1.3) → artifacts, deep-fried look. Pull back toward 1.0.
- **Mismatched base model** → a Flux LoRA won't work on SDXL and vice versa. Check the LoRA's base before picking the Replicate model.
- **Civitai URLs** sometimes redirect; use the direct `.safetensors` download link, not the gallery page.
