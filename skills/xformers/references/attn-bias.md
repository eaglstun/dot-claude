---
topic_id: "v2:HCJB"
topic_path: "mixed"
semantic_id: "iLz04zfFpHbddVptNwmC0Ya-A0DAUAAL"
related_ids:
  - "29vkbpdUwtzcdDs6uAuZxfSY6CjE8AAD"
---
# `attn_bias` family — causal, varlen, paged masks

- Source: https://github.com/facebookresearch/xformers/blob/v0.0.35/xformers/ops/fmha/attn_bias.py
  - https://facebookresearch.github.io/xformers/_modules/xformers/ops/fmha/attn_bias.html
- Fetched: 2026-06-29
- Reflects: **xFormers 0.0.35** / PyTorch 2.10. (On `main`/0.0.36 these live in `mslk.attention.fmha.attn_bias`
  and are re-exported unchanged.)
- Import: `from xformers.ops import fmha` then `fmha.LowerTriangularMask`, or `import xformers.ops as xops`.

## What it's for

An `AttentionBias` is a structured stand-in for a dense additive mask added to `Q @ Kᵀ` before
softmax. Using a class instead of a dense tensor lets the kernel (a) avoid loading the bias from
memory and (b) know in advance which blocks of the attention matrix to skip (e.g. causal). Always
prefer these over a raw `torch.Tensor` mask — the tensor path is slower and supported by fewer ops.

## Pick-the-right-one

### Plain causal (single sequence per batch row)

- **`LowerTriangularMask()`** — standard top-left causal: query i attends to keys 0..i. Use for
  training / prefill where Mq == Mkv.
- **`LowerTriangularFromBottomRightMask()`** — causal aligned to the **bottom-right** corner. Identical
  to `LowerTriangularMask` when Mq == Mkv; when Mq < Mkv (decoding: few new queries against a long
  cache) it shifts so the **last query attends to the last key**. Use this for incremental decoding /
  appended queries — top-left would mask the wrong keys.
- **`LowerTriangularMaskWithTensorBias(bias)`** — causal PLUS an arbitrary additive tensor bias
  (e.g. ALiBi). Only ops supporting tensor bias accept it.
- **`LowerTriangularFromBottomRightLocalAttentionMask`** / `LocalAttentionFromBottomRightMask` —
  sliding-window (local) variants.

### Top-left vs bottom-right (the core distinction)

Top-left: position 0 = matrix top-left; correct when Mq == Mkv. Bottom-right: causality anchored to
the final key/query; correct for variable-length and decoding where each row's query count differs
from its key count. Bottom-right requires **num_keys ≥ num_queries** per block (else softmax sees an
all-`-inf` row and the forward is undefined).

### Variable-length / packed batches (concatenate sequences, batch dim = 1)

- **`BlockDiagonalMask`** — queries/keys split into N blocks; block i attends only within block i. The
  way to batch sequences of different lengths without padding. Non-causal.
  - `BlockDiagonalMask.from_seqlens(q_seqlen, kv_seqlen=None, *, device=None)` — build from length lists.
  - `BlockDiagonalMask.from_tensor_list(tensors)` → `(bias, concat_tensor)` — concat a list of
    `[B, M_i, *]` tensors along seq into `[1, ΣM_i, *]` and get the matching bias.
  - `from_tensor_lists_qkv(tensors_q, tensors_k, tensors_v)` — when q and kv lengths differ.
  - `.split(tensor)` / `.split_queries(t)` / `.split_kv(t)` — undo the concatenation on the output.
  - Converters: `.make_causal()`, `.make_causal_from_bottomright()`, `.make_local_attention(window)`,
    `.make_local_attention_from_bottomright(window)`.
- **`BlockDiagonalCausalMask`** — block-diagonal AND causal within each block (top-left). The standard
  mask for training on packed/concatenated variable-length sequences.
- **`BlockDiagonalCausalFromBottomRightMask`** — block-diagonal causal with bottom-right alignment;
  allows a non-causal prefix. Requires `num_keys ≥ num_queries` per block.
- **`BlockDiagonalCausalLocalAttentionMask`** / `...FromBottomRightMask` / `...PaddedKeysMask` —
  add a sliding window to the block-diagonal causal mask.

### Decoding / KV-cache (padded & paged keys)

- **`BlockDiagonalCausalWithOffsetPaddedKeysMask`** — block-diagonal causal where k/v are **padded to a
  fixed length** (KV cache slots) and only the first `kv_seqlen[i]` of each block are used.
  `from_seqlens(q_seqlen, kv_padding: int, kv_seqlen, causal_diagonal=None, *, device=None)`.
  `kv_padding` is the per-block cache capacity / upper bound. (`causal_diagonal` arg is dead — kept for
  backward-compat only; removed as a behavior in 0.0.21.) This is the mask `rope_padded` targets.
- **`BlockDiagonalPaddedKeysMask`** / `BlockDiagonalGappyKeysMask` /
  `BlockDiagonalCausalWithOffsetGappyKeysMask` — padded (contiguous used region) vs gappy
  (non-contiguous key positions) cache layouts.
- **`PagedBlockDiagonalCausalWithOffsetPaddedKeysMask`**, `PagedBlockDiagonalPaddedKeysMask`,
  `PagedBlockDiagonalGappyKeysMask`, `PagedBlockDiagonalCausalLocalPaddedKeysMask` — **paged-attention**
  variants (vLLM-style block tables) for fragmented KV-cache pages.

`fmha.VARLEN_BIASES` is the tuple of biases the dispatcher treats as variable-length (affects which
backward op is chosen — they need matching `VARLEN_LSE_PACKED`; see `fmha-backends-dispatch.md`).

## Materialize / debug

Every bias has `.materialize(shape, dtype=torch.float32, device="cpu") -> Tensor` to render the dense
additive mask (0 where allowed, `-inf` where masked) for inspection/tests, and `.to(device)`. Block
biases store `q_seqinfo` / `k_seqinfo` (`_SeqLenInfo` / `_PaddedSeqLenInfo`) with the seqstart offsets.

## Example (varlen pack + split)

```python
from xformers.ops import fmha
list_x = [torch.randn([1, m, 1, K], dtype=torch.float16, device="cuda") for m in (3, 6, 2)]
attn_bias, x = fmha.BlockDiagonalMask.from_tensor_list(list_x)
q, k, v = linear(x).reshape([1, -1, 1, 3, K]).unbind(-2)
out = fmha.memory_efficient_attention(q, k, v, attn_bias=attn_bias)
list_out = attn_bias.split(out)        # back to [1,3,1,K], [1,6,1,K], [1,2,1,K]
```
