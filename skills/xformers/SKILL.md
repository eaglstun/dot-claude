---
name: xformers
description: xFormers reference for optimized PyTorch attention and related ops. Use for memory_efficient_attention, attention biases and packed sequences, backend dispatch and capability errors, SwiGLU/RoPE, performance problems, or xFormers/PyTorch/CUDA installation mismatches.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: SQ6X4znNOKQlMBEDLUyKMCGiRfhSAAAL
  related_ids: '["SQyzozHPOGal8Nf7LUgaGgIvxLmwAAAH","W68X52QNrzB1NCaxzZG6I0l2CcCCQAAH"]'
---

# xFormers reference

Condensed, source-cited notes from the official xFormers documentation
(`facebookresearch.github.io/xformers/`) and the GitHub source — Meta's library
of optimized, composable Transformer building blocks for PyTorch.

This is a **standalone PyTorch reference**, not tied to any one repo. Repo
conventions (a project CLAUDE.md, an existing pin in `requirements.txt`)
override anything here — and the pinned version is the final authority.

> ⚠️ **Version stamps matter here.** xformers churns and is pinned to a specific
> PyTorch + CUDA build. Every page records the **xformers version + source URL +
> fetch date** it reflects; re-pull when the target project's pinned version
> changes, and prefer `python -m xformers.info` plus the GitHub source over
> stale docs.

Current pull reflects **xFormers 0.0.35** (released 2026-02-20, pairs with
**PyTorch 2.10.0**), grounded on the `v0.0.35` git tag. Note: on `main` (heading
to 0.0.36) the FMHA implementation has been extracted to a separate **`mslk`**
package and `xformers.ops.fmha.*` are now thin re-export shims — the public API
is unchanged; re-pull from `mslk.attention.fmha` once 0.0.36 ships.

Written and consulted by the **`xformers-references`** agent, which pulls new
pages on demand. Prefer reading what is here before re-fetching.

## References — load on demand

Detail lives in `references/`. One pointer per page:

### The attention path

- **[memory-efficient-attention.md](references/memory-efficient-attention.md)**
  — the main FMHA entry point: signature, the `[B, M, H, K]` layout (**not**
  SDPA's), `attn_bias`/`p`/`scale`/`op`, exact-not-approximate semantics,
  dtype/head-dim/contiguity constraints, forward-only and partial variants.
  _Read before the first call, and whenever the shapes don't line up._

- **[attn-bias.md](references/attn-bias.md)**
  — the `AttentionBias` family: `LowerTriangularMask`, top-left vs bottom-right
  causal, `BlockDiagonal*` varlen (`from_seqlens` / `from_tensor_list` /
  `split`), padded / gappy / paged KV-cache masks, and which to use when.
  _Read for any masking, packing, or KV-cache question._

- **[fmha-backends-dispatch.md](references/fmha-backends-dispatch.md)**
  — the flash / cutlass / flash3 / cutlass-blackwell / ck / `triton_splitk`
  backends, per-op support flags (SM, dtype, max-K), how
  `memory_efficient_attention` auto-selects, the FA3 toggle, pinning with `op=`.
  _Read when attention is slow or raises `NotImplementedError`._

- **[fmha-op-classes.md](references/fmha-op-classes.md)**
  — the `AttentionFwOpBase` / `AttentionBwOpBase` capability-flag model,
  `supports()` and `not_supported_reasons()`, `Inputs`/`Context`/`Gradients`,
  partial attention and `merge_attentions` (split-K / paged). _Read when
  selecting or writing against a specific operator._

### Everything else

- **[swiglu-rope.md](references/swiglu-rope.md)**
  — `swiglu` / `swiglu_packed` / `SwiGLU` gated FFN (A100+ fp16/bf16, else an
  eager fallback) and `rope_padded` (fused RoPE + KV-cache emplacement for
  decode; Triton-only, inference-only; `adjacents` LLaMA vs HF). _Read when
  wiring the FFN or the rotary embedding._

- **[install-compat-diagnostics.md](references/install-compat-diagnostics.md)**
  — the torch↔xformers↔CUDA wheel matrix (cu126/128/130, rocm7.1), building
  from source with `TORCH_CUDA_ARCH_LIST`, and every field of
  `python -m xformers.info` and how to read it. _Read first on any install
  failure — this is the #1 source of "no kernel / silently slow"._

## Working rules for xformers

1. **Check the pinned version before answering.** `pip show xformers` /
   `python -m xformers.info`. An API that shipped in 0.0.35 is not in the 0.0.28
   a project froze two years ago.
2. **The layout is `[B, M, H, K]`**, not PyTorch SDPA's `[B, H, M, K]`. Most
   "wrong results" reports are a missing transpose.
3. **A silently-slow path is a dispatch failure**, not a hardware limit. Ask
   `op.not_supported_reasons(inputs)` rather than guessing.
4. **Install problems are version-matrix problems.** Read `xformers.info`
   output before changing any code.

## Conventions for this shelf

- Each page starts with its source URL(s), fetch date, and the xformers version
  it reflects; it keeps signatures and the dtype/SM/head-dim constraints that
  decide whether a fast kernel actually runs, and drops boilerplate.
- Keep SKILL.md lean: two-line pointers only. Detail lives on the shelf. This
  file is the only index — there is deliberately no second one to keep in sync.
- To add a topic: write `references/<topic>.md` in the same format (source +
  fetch date + version block up top), then add a pointer above.
- Matches the layout of the `cuda`, `apple-silicon`, `c-plusplus`, and `swift`
  shelves.
