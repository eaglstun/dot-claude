---
topic_id: "v2:HIND"
topic_path: "mixed"
semantic_id: "EJbPYxZp7CQ3cDe2Dwu-S5BupeSgYAAJ"
related_ids:
  - "WZbfq3SJpGK3cKauLl-tCyVu7eSoYAAC"
  - "UPKrpWJ7wPav9FO37Um-04ArBvcQIAAL"
---
# FMHA forward/backward operator classes

> **Scope choice (topic 6):** I document the **memory-efficient-attention FW/BW op classes** here
> rather than the classic block-sparse attention API. In 0.0.x the legacy `xformers.components.attention`
> block-sparse path is largely deprecated/undocumented, whereas the `AttentionFwOpBase`/`AttentionBwOpBase`
> model is the actively documented, source-of-truth surface. (Structured 2:4 sparsity also lives, separately,
> in `xformers.ops.sp24`: `Sparse24Tensor`, `sparsify24`, `sparsify24_like` — not attention.)

- Source: https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/ops/fmha/common.py
  - https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/ops/common.py
- Fetched: 2026-06-29
- Reflects: **xFormers 0.0.35** / PyTorch 2.10. (On `main`/0.0.36 under `mslk.attention.fmha.common`,
  re-exported via `xformers.ops.fmha.common`.)

## Class hierarchy

`BaseOperator` → `AttentionOpBase` → `AttentionFwOpBase` / `AttentionBwOpBase`.
An "op" (e.g. `xops.MemoryEfficientAttentionFlashAttentionOp`) is an `(FwOp, BwOp)` tuple; each side is
a subclass that declares capability flags and implements `apply()`. Concrete subclasses:
`flash.FwOp/BwOp`, `cutlass.FwOp/BwOp`, `flash3.FwOp/BwOp`, `cutlass_blackwell.FwOp/BwOp`,
`ck.FwOp/BwOp`, `ck_splitk.FwOp`, `triton_splitk.FwOp`.

## `AttentionOpBase` — capability flags (drive dispatch)

```
OPERATOR                                  # the underlying kernel callable (None ⇒ unavailable)
SUPPORTED_DEVICES: Set[str]               # e.g. {"cuda"}
CUDA_MINIMUM_COMPUTE_CAPABILITY = (5, 0)  # min SM; flash/flash3 override to (8,0), blackwell (10,0)
CUDA_MAXIMUM_COMPUTE_CAPABILITY = None    # cutlass/flash3 set (9,0)
SUPPORTED_DTYPES: Set[torch.dtype]        # flash={half,bf16}; cutlass adds float
SUPPORTED_MAX_K: float                    # max head dim (flash 256, cutlass 65536, triton 512, bw128)
SUPPORTED_MIN_K: int = 0
SUPPORTED_ATTN_BIAS_TYPES = (type(None),) # which AttentionBias subclasses are allowed
SUPPORTS_DROPOUT: bool
SUPPORTS_CUSTOM_SCALE = False
SUPPORTS_DIFFERENT_VALUE_EMBED = False    # allow K != Kv (cutlass: True)
SUPPORTS_OUTPUT_DTYPE = False
SUPPORTS_PARTIAL = False                  # works with memory_efficient_attention_partial
IS_DETERMINISTIC = True
SUPPORTS_BMGHK = False                    # 5-dim MQA/GQA layout
VARLEN_LSE_PACKED = True                  # LSE format for varlen biases (fw & bw must match)
NAME: str                                 # what `python -m xformers.info` prints
OPERATOR_CATEGORY = "memory_efficient_attention"
```

### Support-check methods (how dispatch and you both query an op)

- `op.supports(inp: Inputs) -> bool` — True iff the op can run these inputs.
- `op.not_supported_reasons(inp: Inputs) -> List[str]` — empty list ⇒ supported; otherwise a list of
  human-readable reasons (wrong dtype, head dim too big, unsupported bias, bad SM, stride≠1, …). This is
  exactly what the dispatcher iterates over and what the `NotImplementedError` message is built from.
- `op.shape_not_supported_reasons(Mq, Mkv, K, Kv)` — the shape/head-dim subset (K!=Kv, K>MAX_K, K<MIN_K).
- `BaseOperator.is_available()` — whether the kernel compiled/loaded at all (drives `xformers.info`).
  Returns False if `OPERATOR is None` or named `"no_such_operator"`.

### FW vs BW specifics

- `AttentionFwOpBase.apply(cls, inp, needs_gradient) -> (out, Optional[Context])`. Carries per-dtype
  numerical tolerances `ERROR_ATOL`/`ERROR_RTOL` (used by tests).
- `AttentionBwOpBase.apply(...) -> Gradients`. Extra flags: `SUPPORTS_ATTN_BIAS_GRAD=False` (most ops
  can't backprop into a tensor bias), `SUPPORTS_PARTIAL=True`. Looser tolerances (bw recomputes Q@Kᵀ,
  so high `scale` amplifies error).

## Supporting dataclasses (`xformers.ops.fmha`)

- **`Inputs`** — bundle passed to ops: `query, key, value, attn_bias=None, p=0.0, scale=None,
output_dtype=None, is_partial=False`. Helpers: `.device`, `.scale_float` (defaults to `K**-0.5`),
  `.get_qkv_in_bmghk()`, `.normalize_bmhk()`, `.validate_inputs()`, `.nbytes`.
- **`Context`** (fw → bw) — `lse: Tensor` (log-sum-exp), `out: Tensor`, `op_bw`, `rng_state`
  (dropout reproducibility), `qkv_share_storage`. `.get_padded_lse(pad_to, force_pad_inf=False)`.
- **`Gradients`** — `dq, dk, dv, db=None` (`db` is the bias gradient, None unless a tensor bias
  requires grad).

## Partial attention / merging (split-K, paged decode)

For ops with `SUPPORTS_PARTIAL=True` (flash, cutlass bw, triton_splitk): run attention over chunks of
keys/values and combine using the LSE.

- `memory_efficient_attention_partial(query, key, value, attn_bias=None, p=0.0, scale=None, *, op=None)`
  → returns `(out_chunk, lse_chunk)` for a KV chunk.
- `merge_attentions(attn_split, lse_split, ...)` (also `triton_splitk.merge_attentions` /
  `merge_attentions_varargs`) → combine chunk outputs+LSEs into the final attention. This is the
  mechanism behind split-KV decoding and paged attention.

## Using the op classes directly

```python
import xformers.ops as xops
inp = xops.fmha.Inputs(query=q, key=k, value=v, attn_bias=bias, p=0.0)

# Will flash run? Why not?
reasons = xops.fmha.flash.FwOp.not_supported_reasons(inp)
print(reasons or "flash OK")

# Force a specific op pair:
y = xops.memory_efficient_attention(q, k, v, attn_bias=bias,
        op=(xops.fmha.cutlass.FwOp, xops.fmha.flash.BwOp))
```
