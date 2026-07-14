---
name: ai-dev
public: true
description: Curated glossary of AI/ML development terms — architecture (transformer, attention, embeddings, latent space), training (gradient descent, LoRA, ablation, validation loss), numerics (fp16/bf16, quantization, GGUF, parameters), GPU compute (CUDA, Metal, MPS, Vulkan), and runtimes (llama.cpp, Ollama, MLX). Use ONLY when the user explicitly asks what a specific term MEANS — "what's GGUF", "define latent space". The full term list is in references/; do NOT trigger just because a task mentions AI/ML concepts in passing. This is a lookup reference, not a general AI-dev assistant.
version: 1.0.0
semantic_id: "7m5OCL78NgmNdiVUAIVGZSkS97TO0AAN"
related_ids:
  - "fnwODJ9cb2gNXrBaOGYOx3MS9zaF0AAL"
  - "fP6LKc5_k0iI3wzwNo-EQWES1TZUUAAD"
topic_id: "v2:JIJA"
topic_path: "ai-concepts/training-fundamentals"
---

# AI Dev Skill

A personal, curated reference for AI/ML development — definitions, concepts, and
local-inference tooling — kept short so it's quick to refer to mid-task. This file is an
index; load the one glossary entry you need (each is self-contained, ~1 paragraph).

## Glossary — load on demand

| Term                 | File                                          | One-liner                                                   |
| -------------------- | --------------------------------------------- | ----------------------------------------------------------- |
| Ablation             | `references/glossary/ablation.md`             | cut a component out to prove it was doing real work         |
| AGI                  | `references/glossary/agi.md`                  | hypothetical human-level general AI; a contested term       |
| Alignment            | `references/glossary/alignment.md`            | making a model want what you meant, not what you said       |
| Attention            | `references/glossary/attention.md`            | Q/K/V mechanism that lets tokens weigh each other           |
| CUDA                 | `references/glossary/cuda.md`                 | NVIDIA's GPU-compute platform; the ML default backend       |
| cuDNN / cuBLAS       | `references/glossary/cudnn-cublas.md`         | NVIDIA's CUDA math/DL libraries; the cuDNN/cuBLAS combo     |
| Dimensions           | `references/glossary/dimensions.md`           | axes of variation; how to reason about high-D spaces        |
| Embeddings           | `references/glossary/embeddings.md`           | dense vectors where distance/direction encode meaning       |
| Epsilon gate         | `references/glossary/epsilon-gate.md`         | a hardcoded threshold that silently eats good results       |
| GAN                  | `references/glossary/gan.md`                  | generator-vs-discriminator generative architecture          |
| GELU                 | `references/glossary/gelu.md`                 | the smooth activation gate inside modern transformers       |
| GGML                 | `references/glossary/ggml.md`                 | C/C++ tensor library powering llama.cpp; runs GGUF          |
| GGUF                 | `references/glossary/gguf.md`                 | llama.cpp single-file format for quantized local LLMs       |
| GPT                  | `references/glossary/gpt.md`                  | generative pre-trained (decoder-only) transformer LLM       |
| Gradient descent     | `references/glossary/gradient-descent.md`     | the downhill-on-the-loss algorithm that makes models learn  |
| Latent space         | `references/glossary/latent-space.md`         | the hidden vector space where geometry encodes meaning      |
| llama.cpp vs Ollama  | `references/glossary/llamacpp-vs-ollama.md`   | local-inference engine vs the wrapper built on it           |
| LoRA                 | `references/glossary/lora.md`                 | low-rank adapters; parameter-efficient fine-tuning          |
| Machine learning     | `references/glossary/machine-learning.md`     | learning patterns from data; the umbrella field             |
| Metal                | `references/glossary/metal.md`                | Apple's GPU-compute API; powers MLX and Metal-backed ML     |
| MLX                  | `references/glossary/mlx.md`                  | Apple-silicon ML framework; the Mac answer to GGUF          |
| Model welfare        | `references/glossary/model-welfare.md`        | whether a model's experience could matter morally           |
| MPS                  | `references/glossary/mps.md`                  | Metal Performance Shaders; Apple's cuDNN-equivalent ops     |
| Norm placement       | `references/glossary/norm-placement.md`       | pre- vs post- vs sandwich-norm; whether a deep stack trains |
| Parameters (7B)      | `references/glossary/parameters.md`           | learned weights; the count is model size & memory cost      |
| Precision            | `references/glossary/precision.md`            | fp32/fp16/bf16 bit budgets, and why that isn't quantizing   |
| Qwen                 | `references/glossary/qwen.md`                 | Alibaba's open-weight LLM family; the local-run default     |
| ReLU                 | `references/glossary/relu.md`                 | the original hard activation gate; negatives to zero        |
| Residual connections | `references/glossary/residual-connections.md` | skip wiring that lets networks go deep without fading       |
| RSS sampler          | `references/glossary/rss-sampler.md`          | timed self-monitor of real RAM use; catches the OOM cliff   |
| Temperature          | `references/glossary/temperature.md`          | the sampling knob for how boldly a model gambles            |
| Tensor               | `references/glossary/tensor.md`               | n-dimensional numeric array; the core ML data structure     |
| Token                | `references/glossary/token.md`                | the subword unit a model actually reads and writes          |
| Transformer          | `references/glossary/transformer.md`          | self-attention architecture behind modern LLMs              |
| Val loss             | `references/glossary/val-loss.md`             | held-out validation error; the overfitting tripwire         |
| Vulkan               | `references/glossary/vulkan.md`               | cross-vendor GPU-compute API; the portable ML fallback      |

Entries cross-link with `[[name]]` (slug = filename without `.md`): GGUF ↔ MLX,
GGUF ↔ GGML, GGML → tensor, cuda ↔ metal ↔ vulkan (mutual), {cuda,metal,vulkan} → ggml,
metal → mlx, mps → {metal, mlx, cuda}, cudnn-cublas → {cuda, mps, tensor},
llamacpp-vs-ollama → {gguf, ggml, metal, cuda, vulkan}, lora ↔ transformer,
lora → {tensor, gguf}, parameters ↔ {gguf, lora}, parameters → {tensor, transformer},
attention ↔ transformer, attention → {tensor, lora},
machine-learning → {tensor, transformer, gan, latent-space, val-loss, parameters},
dimensions ↔ {tensor, latent-space}, embeddings ↔ {latent-space, dimensions},
embeddings → tensor, agi → {machine-learning, gpt},
latent-space ↔ GAN, GPT ↔ transformer, transformer → tensor, tensor → MLX, GPT → GGUF,
token → {embeddings, attention, transformer, temperature, gpt},
temperature → {gpt, transformer, gguf, llamacpp-vs-ollama},
relu ↔ gelu, relu → {transformer, tensor}, gelu → {transformer, gpt, tensor},
residual-connections → {transformer, relu, tensor},
norm-placement → {residual-connections, transformer, gradient-descent, tensor},
gradient-descent → {machine-learning, parameters, val-loss, latent-space, epsilon-gate},
epsilon-gate → {gradient-descent, precision, mps, val-loss},
precision → {gguf, parameters, rss-sampler, tensor, epsilon-gate},
rss-sampler → {parameters, gguf, ggml}, ablation → {machine-learning, val-loss, parameters},
qwen → {gpt, transformer, gguf, lora}, alignment ↔ model-welfare,
alignment → {agi, machine-learning}, model-welfare → {agi, parameters}.

## Conventions (for adding entries)

- One concept per file in `references/glossary/`, named `kebab-case.md`.
- Start with `# Term`, then one tight paragraph. Add a `**See also:**` line linking
  related entries with `[[slug]]`.
- Add a row to the table above so the index stays complete.
- Runnable helpers (demos, conversions) go in `scripts/`, not the glossary.
