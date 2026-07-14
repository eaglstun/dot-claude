---
topic_id: "v2:HIPF"
topic_path: "mixed"
semantic_id: "WZbfq3SJpGK3cKauLl-tCyVu7eSoYAAC"
related_ids:
  - "EJbPYxZp7CQ3cDe2Dwu-S5BupeSgYAAJ"
  - "W68X52QNrzB1NCaxzZG6I0l2CcCCQAAH"
---
# FMHA backends + operator dispatch

- Source: https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/ops/fmha/dispatch.py
  - `__init__.py`, `flash.py`, `cutlass.py`, `flash3.py`, `cutlass_blackwell.py`, `triton_splitk.py`
- Fetched: 2026-06-29
- Reflects: **xFormers 0.0.35** / PyTorch 2.10. (On `main`/0.0.36 these live under `mslk.attention.fmha`,
  re-exported via `xformers.ops.fmha.*` shims.)

## The backends (each is an `(FwOp, BwOp)` pair exported from `xformers.ops`)

| Op constant                                   | FwOp / BwOp                   | Backend                 | Notes                    |
| --------------------------------------------- | ----------------------------- | ----------------------- | ------------------------ |
| `MemoryEfficientAttentionFlashAttentionOp`    | `flash.FwOp/BwOp`             | Flash-Attention 2       | fp16/bf16 only           |
| `MemoryEfficientAttentionCutlassOp`           | `cutlass.FwOp/BwOp`           | CUTLASS (xFormers' own) | fp32 + big head dims     |
| `MemoryEfficientAttentionCutlassFwdFlashBwOp` | `(cutlass.FwOp, flash.BwOp)`  | mixed                   | cutlass fwd + flash bwd  |
| `MemoryEfficientAttentionCutlassBlackwellOp`  | `cutlass_blackwell.FwOp/BwOp` | CUTLASS Blackwell       | SM 10.0 (B200)           |
| `MemoryEfficientAttentionCkOp`                | `ck.FwOp/BwOp`                | Composable Kernel       | **ROCm/AMD** path        |
| `MemoryEfficientAttentionSplitKCkOp`          | `(ck_splitk.FwOp, ck.BwOp)`   | CK split-K              | ROCm decoding            |
| (also)                                        | `flash3.FwOp/BwOp`            | Flash-Attention 3       | SM 9.0 (H100), see below |
| (also)                                        | `triton_splitk.FwOp`          | Triton split-K          | decode/MQA, fwd-only     |

## Per-op support constraints (forward) — these decide dispatch

From the `FwOp` class attributes (`not_supported_reasons(inp)` returns why an op is rejected):

**flash.FwOp** (FA2): `SUPPORTED_DEVICES={cuda}`, `CUDA_MINIMUM_COMPUTE_CAPABILITY=(8,0)` (Ampere+),
`SUPPORTED_DTYPES={half, bfloat16}`, `SUPPORTED_MAX_K=256`, `SUPPORTS_DROPOUT=True`,
`SUPPORTS_CUSTOM_SCALE=True`, `SUPPORTS_DIFFERENT_VALUE_EMBED=False` (needs K==Kv), `SUPPORTS_BMGHK=True`
(MQA/GQA), `SUPPORTS_PARTIAL=True`, `VARLEN_LSE_PACKED=True`. Rich `SUPPORTED_ATTN_BIAS_TYPES`:
LowerTriangular(+FromBottomRight, +Local), all `BlockDiagonal*`, gappy/padded keys, and the paged
`PagedBlockDiagonalCausalWithOffsetPaddedKeysMask` / `PagedBlockDiagonalPaddedKeysMask`.

**cutlass.FwOp**: `SUPPORTED_DEVICES={cuda}`, min CC inherits base `(5,0)` and
`CUDA_MAXIMUM_COMPUTE_CAPABILITY=(9,0)`, `SUPPORTED_DTYPES={float, half, bfloat16}` (**only backend that
runs fp32**), `SUPPORTED_MAX_K=65536`, `SUPPORTS_DROPOUT=True`, `SUPPORTS_CUSTOM_SCALE=True`,
`SUPPORTS_DIFFERENT_VALUE_EMBED=True` (K != Kv OK), `SUPPORTS_BMGHK=True`.

**flash3.FwOp** (FA3): `CUDA_MINIMUM/MAXIMUM_COMPUTE_CAPABILITY=(8,0)/(9,0)` (effectively SM 9.0 H100),
fp16/bf16, `SUPPORTED_MAX_K=256`.

**cutlass_blackwell.FwOp**: `CUDA_MINIMUM_COMPUTE_CAPABILITY=(10,0)` (Blackwell B200), bf16/fp16,
`SUPPORTED_MAX_K=128`.

**triton_splitk.FwOp**: `CUDA_MINIMUM_COMPUTE_CAPABILITY=(8,0)`, dtypes `{half, bfloat16}` (K/V may be
int32 in the quantized case), `SUPPORTED_MAX_K=512`, `SUPPORTS_DROPOUT=False`, `SUPPORTS_BMGHK=True`.
Forward-only; built for MQA/GQA decoding (short Q, long KV).

## How auto-dispatch picks (when `op=None`)

`_dispatch_fw(inp, needs_gradient)` runs `_dispatch_fw_priority_list` then `_run_priority_list` — it
returns the **first op whose `not_supported_reasons(inp)` is empty**.

Forward priority list (`_dispatch_fw_priority_list`):

- **CUDA**: `[flash3.FwOp (if FA3 enabled)] + [flash.FwOp, cutlass.FwOp]`.
- **ROCm**: `[ck.FwOp]`.
- **Decoding special-case** (when `needs_gradient=False`): if MQA/GQA (k stride on head dim == 0,
  > 1 head) AND `query.shape[1] <= 32` AND `key.shape[1] >= 256` AND parallelism `B*H < 64`, it
  > prepends **`triton_splitk.FwOp`** (split-KV is faster for short-Q/long-KV decode). Without a varlen
  > bias on CUDA it instead moves `flash.FwOp` to the front.

Backward priority (`_dispatch_bw`): CUDA `[flash.BwOp, cutlass.BwOp]` (+`flash3.BwOp` if FA3 on);
ROCm `[ck.BwOp]`. For a **varlen bias** with >1 sequence, the bw op's `VARLEN_LSE_PACKED` must match the
fw op's LSE format — mismatched ops are filtered out (this is why varlen sometimes can't use flash bw).

## Flash-Attention 3 toggle

FA3 is preferred by default (`_USE_FLASH_ATTENTION_3 = True`). Control it:

- `fmha.dispatch._set_use_fa3(False)` to disable, `_get_use_fa3()` to read.
- `fmha.dispatch.fa3_available()` → True only if CUDA, device capability in `(8,0)..(9,0)`, and the
  FA3 C extension (`_C_flashattention3`) is built.

## Pinning a backend

```python
import xformers.ops as xops
y = xops.memory_efficient_attention(q, k, v,
        op=xops.MemoryEfficientAttentionFlashAttentionOp)   # force FA2
```

Or check support directly: `xops.fmha.flash.FwOp.supports(inp)` /
`xops.fmha.flash.FwOp.not_supported_reasons(inp)` (returns a list of human-readable rejection reasons).

## "Why is it slow / why did it pick X / NotImplementedError"

`memory_efficient_attention` raises `NotImplementedError` listing **each candidate op and why it was
rejected** when nothing matches (`_run_priority_list`). Common causes: fp32 input (only cutlass),
head dim > the op's `SUPPORTED_MAX_K`, a bias type not in `SUPPORTED_ATTN_BIAS_TYPES`, last-dim stride
≠ 1, or a too-old/too-new GPU compute capability. If it "works but is slow", it likely fell back from
flash to cutlass (e.g. fp32 or K>256) — check with an explicit `op=` or `python -m xformers.info`.
