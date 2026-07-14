---
topic_id: "v2:HINB"
topic_path: "mixed"
semantic_id: "WQbTQ3vPeKYl8LG1LUSaMCOm5fgIAAAE"
related_ids:
  - "SQyzozHPOGal8Nf7LUgaGgIvxLmwAAAH"
  - "TQDbGF_lWQUd5pFwK02S1X9ww_5EUAAE"
---
# xFormers references — PyTorch transformer building blocks

Condensed, source-cited notes from the official xFormers documentation
(`facebookresearch.github.io/xformers/`) and GitHub source — Meta's library of optimized,
composable Transformer building blocks for PyTorch (`memory_efficient_attention` / FMHA, attention
biases, SwiGLU/RoPE, sparse attention, the modular `components`, and the install/version matrix).

This is a **standalone PyTorch reference** — not tied to any one repo. Written and consulted by the
**`xformers-references`** agent.

> ⚠️ **Version stamps matter here.** xformers churns and is pinned to a specific PyTorch + CUDA
> build. Every file records the **xformers version + source URL + fetch date** it reflects; re-pull
> when the target project's pinned version changes, and prefer `python -m xformers.info` + the
> GitHub source over stale docs.

Convention (matching the `cuda`/`apple-silicon`/`arkit` shelves): each file starts with its source
URL(s), fetch date, and xformers version; keeps signatures and the dtype/SM/head-dim constraints
that decide whether a fast kernel actually runs; drops boilerplate. Pull on demand.

## Index

Current pull reflects **xFormers 0.0.35** (released 2026-02-20, pairs with **PyTorch 2.10.0**).
Grounded on the `v0.0.35` git tag. Note: on `main` (heading to 0.0.36) the FMHA implementation has
been extracted to a separate **`mslk`** package and `xformers.ops.fmha.*` are now thin re-export
shims — the public API is unchanged; re-pull from `mslk.attention.fmha` once 0.0.36 ships.

- [memory-efficient-attention.md](memory-efficient-attention.md) — `memory_efficient_attention` main entry: signature, `[B,M,H,K]` layout (not SDPA's), `attn_bias`/`p`/`scale`/`op`, exact-not-approximate, dtype/head-dim/contiguity constraints, fwd-only & partial variants.
- [attn-bias.md](attn-bias.md) — the `AttentionBias` family: `LowerTriangularMask`, top-left vs bottom-right causal, `BlockDiagonal*` varlen (`from_seqlens`/`from_tensor_list`/`split`), padded/gappy/paged KV-cache masks, when to use which.
- [fmha-backends-dispatch.md](fmha-backends-dispatch.md) — flash / cutlass / flash3 / cutlass-blackwell / ck / triton_splitk backends, per-op support flags (SM, dtype, max-K), how `memory_efficient_attention` auto-selects, FA3 toggle, pinning via `op=`, debugging "slow / NotImplementedError".
- [install-compat-diagnostics.md](install-compat-diagnostics.md) — torch↔xformers↔CUDA wheel matrix (cu126/128/130, rocm7.1), build-from-source + `TORCH_CUDA_ARCH_LIST`, and `python -m xformers.info` (every field + how to read it). The #1 "no kernel / silently slow" source.
- [swiglu-rope.md](swiglu-rope.md) — `swiglu`/`swiglu_packed`/`SwiGLU` gated FFN (A100+ fp16/bf16, else eager fallback) and `rope_padded` (fused RoPE + KV-cache emplacement for decode; Triton-only, inference-only; `adjacents` LLaMA vs HF).
- [fmha-op-classes.md](fmha-op-classes.md) — `AttentionFwOpBase`/`AttentionBwOpBase` capability-flag model, `supports()`/`not_supported_reasons()`, `Inputs`/`Context`/`Gradients`, partial attention + `merge_attentions` (split-K/paged). Topic-6 choice noted (op classes over deprecated block-sparse; 2:4 sparsity is `ops.sp24`).
