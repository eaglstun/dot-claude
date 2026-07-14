---
topic_id: "v2:HIEO"
topic_path: "mixed"
semantic_id: "UPKrpWJ7wPav9FO37Um-04ArBvcQIAAL"
related_ids:
  - "EJbPYxZp7CQ3cDe2Dwu-S5BupeSgYAAJ"
  - "SQyzozHPOGal8Nf7LUgaGgIvxLmwAAAH"
---
# `xformers.ops` extras — SwiGLU and RoPE (rotary)

- Source: https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/ops/swiglu_op.py
  - https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/ops/rope_padded.py
- Fetched: 2026-06-29
- Reflects: **xFormers 0.0.35** / PyTorch 2.10.
- Both exported from `xformers.ops` (`xops.swiglu`, `xops.SwiGLU`, `xops.rope_padded`).

---

## SwiGLU — fused gated FFN

`SwiGLU` is the gated feed-forward block used in LLaMA-style models: two parallel projections, SiLU
gate on one, elementwise product, then an output projection. xFormers fuses this (incl. a dual-GEMM)
to cut memory traffic and kernel launches vs. naive PyTorch.

### Functional API

```python
xops.swiglu(
    x: Tensor,
    w1, b1,            # gate projection weight + optional bias
    w2, b2,            # value projection weight + optional bias
    w3, b3,            # output projection weight + optional bias
    *, op: Optional[SwiGLUOp] = None,
) -> Tensor
```

Equivalent PyTorch: `hidden = F.silu(F.linear(x, w1, b1)) * F.linear(x, w2, b2); return F.linear(hidden, w3, b3)`.

`xops.swiglu_packed(x, w1w2, b1b2, w3, b3, *, op)` — same math but takes `w1`/`w2` (and biases)
**pre-stacked into one tensor** for the fast packed-weight path. Pack with
`w1, w2 = xformers.ops.unbind(w12, 0)` style storage (w1/w2 sharing one buffer enables the dual-GEMM).

### Module API

```python
xops.SwiGLU(in_features, hidden_features, out_features=None, bias=True, *, _pack_weights=True)
```

Holds the three linear layers (w1/w2 packed by default) and calls `swiglu` in `forward`.

### When it helps / constraints

- **Optimized only on A100+ (SM 8.0+)** with `torch.half` or `torch.bfloat16` (autocast supported).
  On any other GPU/dtype it **falls back to a plain PyTorch functional implementation** — correct but
  not faster. Leave `op=None` to let `SwiGLUOpDispatch.from_arguments(...)` pick the best op.
- Note (CHANGELOG): the **A100 SwiGLU optimized fast-path was removed in 0.0.34** — verify it still
  benefits your hardware on the version you run; on newer arch it may dispatch to the eager fallback.
- Shape rules enforced: `w1.shape == w2.shape`, both 2-D; `w3.shape[1] == w2.shape[0]`; biases 1-D
  matching the out features of their layer.

---

## RoPE — `rope_padded` (rotary embeddings + KV-cache emplacement)

Inference-oriented: applies rotary position embeddings to Q and K **and writes K/V into the right KV
cache slots in one fused Triton kernel**, for a heterogeneous (variable-length) batch laid out for
`BlockDiagonalCausalWithOffsetPaddedKeysMask`. The batch is concatenated along seq, so dim-0 length
is 1. EXPERIMENTAL API (may change without warning); **inference only — gradients not supported**.

### Signature

```python
xops.rope_padded(
    xq, xk, xv,                  # (1, slen, n_heads, dim); xq heads may differ from xk/xv (GQA)
    cache_k, cache_v,            # KV caches — MODIFIED IN PLACE (roped xk / raw xv written in)
    attn_bias: BlockDiagonalCausalWithOffsetPaddedKeysMask,   # defines cache layout + positions
    *,
    theta: float = 10000.0,
    linear_scale: float = 1.0,           # divide seq ids by this (linear position interpolation)
    use_dynamic_scaling: bool = False,   # YaRN-style dynamic NTK scaling
    dynamic_old_context_len: float = 8192.0,
    dynamic_scale_factor: float = 16.0,
    dynamic_low_freq_factor: float = 1.0,
    dynamic_high_freq_factor: float = 32.0,
    out_q: Optional[Tensor] = None,      # optional preallocated output for roped Q
    first_seqpos: Optional[Tensor] = None,  # per-batch cache start position (numeric only)
    seqpos: Optional[Tensor] = None,     # explicit per-query positions, len == xq.shape[1]
    adjacents: bool = True,              # True: interleaved pairs (LLaMA); False: split-half (HF)
    internal_dtype: str = "",            # "f32"/"f64" to force compute precision
)  # returns out_q (the roped queries)
```

### Usage pattern

After calling it, caches are ready for attention:

```python
out_q = xops.rope_padded(xq, xk, xv, cache_k, cache_v, attn_bias=bias)
y = xops.memory_efficient_attention(out_q, cache_k, cache_v, attn_bias=bias)
```

### When it helps / constraints

- Use for **incremental LLM decoding** with a padded/paged KV cache and a varlen batch: it removes a
  separate RoPE pass and cache-scatter, fusing both into the attention pipeline.
- **Requires Triton** (`_is_triton_available()` asserted) → CUDA/ROCm with a working Triton; no CPU.
- `adjacents=True` matches released LLaMA weight layout; `adjacents=False` matches HuggingFace's
  rotate-half convention — pick to match your checkpoint or RoPE will be wrong.
- `xq.ndim` must be 4 or 5 (5 = grouped heads). Caches are written **in place** — pass the real cache
  tensors. There is also `xops.RMSNorm` in the same `ops` namespace for the norm half of the block.

```

```
