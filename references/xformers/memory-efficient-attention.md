---
topic_id: "v2:HIGE"
topic_path: "mixed"
semantic_id: "W68X52QNrzB1NCaxzZG6I0l2CcCCQAAH"
related_ids:
  - "Tah5fXbBrYdyVpahHZC6-Nh3qUTo4AAF"
  - "EJbPYxZp7CQ3cDe2Dwu-S5BupeSgYAAJ"
---
# `memory_efficient_attention` — main FMHA entry point

- Source: https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/ops/fmha/__init__.py
  (docstring) + https://facebookresearch.github.io/xformers/components/ops.html
- Fetched: 2026-06-29
- Reflects: **xFormers 0.0.35** (released 2026-02-20), paired with **PyTorch 2.10.0** (prebuilt wheels).
  Note: on `main` (heading to 0.0.36) the implementation has been extracted to a separate `mslk`
  package and `xformers.ops.fmha.*` are now thin re-export shims — the public API below is unchanged.

## What it's for

Exact (NOT approximate) multi-head attention with O(N) memory instead of O(N²), following
_"Self-Attention Does Not Need O(n²) Memory"_ (arXiv 2112.05682). It is a **dispatcher**: it picks
the best available backend (flash / cutlass / flash3 / triton_splitk / ck) from the inputs unless you
pin one via `op=`. Equivalent to the standard scaled-dot-product attention math, just fused and
memory-cheap.

## Signature

```python
import xformers.ops as xops

xops.memory_efficient_attention(
    query: torch.Tensor,
    key:   torch.Tensor,
    value: torch.Tensor,
    attn_bias: Optional[Union[torch.Tensor, AttentionBias]] = None,
    p: float = 0.0,
    scale: Optional[float] = None,
    *,
    op: Optional[AttentionOp] = None,           # (FwOp, BwOp) tuple; None = auto-dispatch
    output_dtype: Optional[torch.dtype] = None,
) -> torch.Tensor                                # returns [B, Mq, H, Kv]
```

## Tensor layout (the #1 gotcha)

xFormers uses **`[B, M, H, K]`** (batch, seq, heads, head-dim) — NOT PyTorch SDPA's `[B, H, M, K]`.
Do not transpose heads in like you would for `F.scaled_dot_product_attention`.

- `query`: `[B, Mq, H, K]`, `key`: `[B, Mkv, H, K]`, `value`: `[B, Mkv, H, Kv]`
- 3-dim input is treated as `[B, M, K]` with `H=1`.
- Inputs may be **non-contiguous**, but the **last dimension's stride must be 1**.
- 5-dim `[B, M, G, H, K]` enables experimental MQA/GQA (forward only); xFormers will NOT broadcast
  k/v for you — `.expand()` the group dim yourself (see GQA example in the docstring).

## Parameters

- `attn_bias`: additive bias on `Q @ Kᵀ` before softmax. Pass an `AttentionBias` subclass (e.g.
  `LowerTriangularMask()` for causal, `BlockDiagonal*` for varlen) for the fast path — these encode
  structure so the kernel can skip masked blocks. A raw `torch.Tensor` mask also works but is slower
  and forces a backend that supports tensor bias. See `attn-bias.md`.
- `p`: dropout probability (0.0 = off). Only flash/cutlass FwOps set `SUPPORTS_DROPOUT=True`.
- `scale`: scale for `Q @ Kᵀ`. `None` → default `q.shape[-1] ** -0.5` (1/√K). Custom scale needs an op
  with `SUPPORTS_CUSTOM_SCALE=True` (flash, cutlass — yes).
- `op`: force a backend, an `(FwOp, BwOp)` tuple e.g. `xops.MemoryEfficientAttentionFlashAttentionOp`.
  Leave `None` (recommended) to auto-dispatch; see `fmha-backends-dispatch.md`.
- `output_dtype`: requires an op with `SUPPORTS_OUTPUT_DTYPE=True`.

## Constraints that decide whether a fast kernel runs

- **dtype**: docstring claims `f16`, `bf16`, `f32` on NVIDIA compute capability ≥ 6.0 (P100+). BUT the
  fast flash path requires **fp16/bf16**; **fp32 only runs on the cutlass backend** (flash FwOp
  `SUPPORTED_DTYPES = {half, bfloat16}`, SM ≥ 8.0). fp32 silently routes to the slower cutlass kernel.
- **head dim K**: flash `SUPPORTED_MAX_K = 256`; cutlass `SUPPORTED_MAX_K = 65536` and is the only one
  with `SUPPORTS_DIFFERENT_VALUE_EMBED=True` (K != Kv).
- **last-dim contiguity**: stride of the last dim must be 1 or dispatch fails with "not supported".
- If no backend matches the inputs, you get `NotImplementedError` with a per-op reason list — read it.

## Equivalent PyTorch (from the docstring)

```python
scale = 1.0 / query.shape[-1] ** 0.5
q = (query * scale).transpose(1, 2); k = key.transpose(1, 2); v = value.transpose(1, 2)
attn = q @ k.transpose(-2, -1)
if attn_bias is not None: attn = attn + attn_bias
attn = attn.softmax(-1)
attn = F.dropout(attn, p)
return (attn @ v).transpose(1, 2).contiguous()
```

## Working call patterns

```python
y = xops.memory_efficient_attention(q, k, v)                       # plain
y = xops.memory_efficient_attention(q, k, v, p=0.2)               # dropout
y = xops.memory_efficient_attention(q, k, v,
        attn_bias=xops.LowerTriangularMask())                     # causal
```

## Non-autograd / partial variants (same module)

- `memory_efficient_attention_forward(query, key, value, attn_bias=None, p=0.0, scale=None, *, op=None)`
  — forward only, no autograd graph (inference).
- `memory_efficient_attention_forward_requires_grad(...)` — returns `(out, lse)` for a manual bw.
- `memory_efficient_attention_backward(...)` — explicit backward.
- `memory_efficient_attention_partial(...)` + `merge_attentions(...)` — split-K / paged decoding: run
  attention over key/value chunks and merge with the log-sum-exp. See `fmha-op-classes.md`.
