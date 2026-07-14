# Pruna-optimized models on Replicate

Source: https://replicate.com/docs/guides/build/optimize-models-with-pruna

Pruna is an open-source framework that compresses models via quantization, pruning, compilation, and caching. On Replicate this shows up in two ways:

1. **Consuming** pre-optimized models published by the `prunaai` account — usually 2–5× faster and cheaper than the base model for comparable quality. This is the common path.
2. **Building** your own Pruna-optimized Cog model for a custom pipeline. Advanced.

Unless the user has a custom pipeline to build, default to the consumption path — it's a one-line model-slug swap in `run_model.py`.

## Pre-optimized models (consumption path)

### Flux family

| Slug                         | What it is                                | When to pick                                 |
| ---------------------------- | ----------------------------------------- | -------------------------------------------- |
| `prunaai/flux-schnell`       | ~3× faster FLUX.1 [schnell]               | Cheap fast iteration; baseline default       |
| `prunaai/flux-schnell-ultra` | Flux-Schnell at 4 megapixels              | High-res with speed                          |
| `prunaai/flux.1-juiced`      | Optimized FLUX.1 [dev]                    | Higher-quality tier than schnell, still fast |
| `prunaai/flux.1-dev-lora`    | ~3× faster FLUX.1 [dev] with LoRA support | LoRA workflows on dev quality                |
| `prunaai/flux-fast`          | "Fastest Flux endpoint"                   | When latency matters most                    |
| `prunaai/flux-kontext-fast`  | Ultra-fast Flux Kontext                   | Kontext (editing/inpainting-style) workflows |
| `prunaai/flux-2-fast`        | Step-distilled FLUX.2, ~1s generation     | FLUX.2 at speed                              |
| `prunaai/flux-2-turbo`       | Distilled FLUX.2 [dev]                    | FLUX.2 at quality                            |

### SDXL

| Slug                     | What it is                      |
| ------------------------ | ------------------------------- |
| `prunaai/sdxl-cheetah`   | Optimized SDXL                  |
| `prunaai/sdxl-lightning` | Fastest SDXL-Lightning endpoint |

### Video / other

| Slug                    | What it is                                      |
| ----------------------- | ----------------------------------------------- |
| `prunaai/wan-2.2-image` | 2MP cinematic image gen, 3–4s (Wan-based image) |
| `prunaai/hunyuan3d-2`   | Optimized HunYuan 3D                            |

### Proprietary fast models

| Slug                    | What it is                        |
| ----------------------- | --------------------------------- |
| `prunaai/z-image-turbo` | 6B-param super-fast text-to-image |
| `prunaai/p-image`       | Sub-1s production text-to-image   |
| `prunaai/p-image-edit`  | Sub-1s multi-image editing        |

## Invoking a pre-optimized model

Inputs generally mirror the base model's schema. Example:

```bash
python scripts/run_model.py prunaai/flux.1-juiced \
    --input '{"prompt":"a tiny origami koala on a wooden desk, soft light"}' \
    --output ./out/
```

For the LoRA-capable variant, same `hf_lora` / `lora_scale` fields as other LoRA-aware Flux models (see `loras.md`):

```bash
python scripts/run_model.py prunaai/flux.1-dev-lora \
    --input '{
      "prompt": "ZIKI the man standing on a beach at golden hour",
      "hf_lora": "zeke/ziki-flux",
      "lora_scale": 1.0
    }' \
    --output ./out/
```

Always check the specific model's page for current input field names — optimized forks sometimes drop or rename fields (e.g. `num_inference_steps` may be locked or absent on "fast" variants).

## Quality tradeoffs

Pruna optimizations aim for imperceptible quality loss at comparable settings, but at the aggressive end (`turbo`, `lightning`, step-distilled) you'll see:

- Slightly less fine detail at high zoom
- Reduced prompt adherence on long/complex prompts
- Fewer usable sampling steps (often locked low)

Rule of thumb: start with the optimized model. If output is clearly worse than you need, fall back to the base (e.g. `black-forest-labs/flux-dev`).

## Building your own Pruna-optimized model (advanced)

For custom pipelines not covered by an existing `prunaai/*` model, you build with Cog. Rough shape:

**cog.yaml**

```yaml
build:
  gpu: true
  cuda: "12.1"
  python_version: "3.11"
  run:
    - command: pip install pruna
predict: "predict.py:Predictor"
```

**predict.py**

```python
import torch
from cog import BasePredictor, Input, Path
from pruna import SmashConfig, smash
from diffusers import FluxPipeline

class Predictor(BasePredictor):
    def setup(self):
        self.pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.bfloat16,
        ).to("cuda")

        cfg = SmashConfig()
        cfg["compiler"] = "torch_compile"
        cfg["cacher"] = "fora"
        cfg.add_tokenizer(self.pipe.tokenizer)

        self.pipe = smash(model=self.pipe, smash_config=cfg)

    def predict(self, prompt: str = Input(description="Prompt"),
                num_inference_steps: int = 28,
                guidance_scale: float = 0.0,
                seed: int = 42) -> Path:
        image = self.pipe(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=torch.Generator("cuda").manual_seed(seed),
        ).images[0]
        out = "/tmp/out.png"
        image.save(out)
        return Path(out)
```

Deploy with:

```bash
cog login
cog push r8.im/<your-user>/<model-name>
```

`SmashConfig` composes multiple algorithms (compiler, cacher, quantizer, pruner). Start with one (`torch_compile` or a cacher like `fora` / `deepcache`) before stacking — layering can compound quality loss or produce weird interactions.

## Discovery

Browse the full catalog at https://replicate.com/prunaai — it's a small, curated account so it's easy to scan.
