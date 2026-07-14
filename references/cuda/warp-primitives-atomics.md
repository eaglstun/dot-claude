---
topic_id: "v2:KMCO"
topic_path: "cuda-gpu/warp-primitives"
semantic_id: "6CIeRq52VyfWCDHwgiPzWrngsY_fEAAA"
related_ids:
  - "6L4EauM9QUaUAZEy0F63UvfQq4xA0AAB"
  - "fGxTPoZ29dR3KvS72tGzU_vyuRJq0AAO"
---
# Warp-level primitives & atomic functions

**Source:** https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/cpp-language-extensions.html
**Fetched:** 2026-06-29 (CUDA C++ Programming Guide 13.3, "C/C++ Language Extensions")

**What it's for:** The building blocks for warp-cooperative reductions / scans / broadcasts
(softmax, layer-norm, top-k) — exchange values between lanes without shared memory — plus atomics
for cross-thread accumulation into global/shared memory.

## Warp shuffle (CC 5.0+; `_sync` mask variants since CUDA 9.0 / Volta)

```c
T __shfl_sync     (unsigned mask, T value, int srcLane,  int width = warpSize);
T __shfl_up_sync  (unsigned mask, T value, unsigned delta, int width = warpSize);
T __shfl_down_sync(unsigned mask, T value, unsigned delta, int width = warpSize);
T __shfl_xor_sync (unsigned mask, T value, int laneMask, int width = warpSize);
```

- `T` ∈ {`int`,`unsigned`,`long`,`unsigned long`,`long long`,`unsigned long long`,`float`,`double`,
  `__half`,`__half2`,`__nv_bfloat16`,`__nv_bfloat162`}.
- `mask` names the lanes that must participate (e.g. `0xFFFFFFFF` for a full warp); all named lanes
  must execute the same call or behavior is undefined.
- `width` must be a power of two in `[1, warpSize]` (1,2,4,8,16,32). `__shfl_down_sync` with a
  halving stride is the standard tree reduction; `__shfl_xor_sync(laneMask)` is the butterfly
  reduce/broadcast pattern.
- The `_sync` forms were added in CUDA 9.0 for Volta **independent thread scheduling**; the old
  non-`_sync` `__shfl*` intrinsics are **deprecated and removed** on recent toolkits — always pass a
  mask.

## Warp vote & sync

```c
int      __all_sync   (unsigned mask, int predicate);   // 1 iff predicate != 0 for all named lanes
int      __any_sync   (unsigned mask, int predicate);   // 1 iff any named lane has predicate != 0
unsigned __ballot_sync(unsigned mask, int predicate);   // bit i set iff lane i's predicate != 0
unsigned __activemask ();                                // bitmask of currently-active lanes
void     __syncwarp   (unsigned mask = 0xFFFFFFFF);      // warp-level barrier + memory fence
```

## Atomic functions (global or shared memory)

```c
T atomicAdd (T* address, T val);
T atomicSub (T* address, T val);
T atomicExch(T* address, T val);
T atomicMin (T* address, T val);
T atomicMax (T* address, T val);
T atomicCAS (T* address, T compare, T val);   // compare-and-swap; basis for custom atomics
```

Type coverage / arch gating:

- `atomicAdd`: `int`, `unsigned`, `unsigned long long`, `float`; **`double` requires CC 6.0+**;
  `__half`/`__half2` require CC 7.x+; `__nv_bfloat16`/`__nv_bfloat162` require CC 8.x+.
- `atomicSub`: `int`, `unsigned`.
- `atomicMin`/`atomicMax`: `int`, `unsigned`, `unsigned long long`, `long long`.
- `atomicExch`: `int`, `unsigned`, `unsigned long long`, `float`.
- `atomicCAS`: `int`, `unsigned`, `unsigned short`, `unsigned long long`.
- `_block` and `_system` suffixed variants narrow/widen the memory scope (block-local vs
  multi-GPU/system-wide).

### Worked example: the CTranslate2 CUDA backend

These intrinsics are the inner machinery of the reduction kernels in `src/ops/*_gpu.cu`. CT2 mostly
reaches them **through `cub::BlockReduce`** (`layer_norm_gpu.cu:180`, `rms_norm_gpu.cu:26`,
`mean_gpu.cu:26`, `topk_gpu.cu:187`) — CUB's block/warp reduce is implemented on top of
`__shfl_down_sync` / `__shfl_xor_sync` and `__syncwarp`, so the warp-shuffle availability above is
what makes those reductions efficient. Softmax-style row reductions (`src/ops/softmax_gpu.cu`)
follow the same max-then-sum warp-reduction shape. `atomicAdd` shows up where partial results from
multiple blocks accumulate into one output (scatter/gather and segment reductions); the
`double`/fp16 gating matters when CT2 builds for fp16/bf16 compute on pre-7.x/pre-8.x targets — match
it against the gates in `compute-capability-tensor-cores.md`. **Metal mirror:** the equivalents are
MSL `simd_shuffle_down` / `simd_sum` / `simd_max` (SIMD-group reductions) and `atomic_fetch_add`,
used the same way in the Apple-silicon reduction kernels.

### See also

- [[apple-silicon:simd-group-functions]] — Metal twin: simdgroups (32-wide like warps) but lockstep, no independent thread scheduling and no `_sync` masks.
- [[apple-silicon:atomic-functions]] — Metal-side atomics surface.
- [[gpu-rosetta]] — CUDA↔Metal concept map.
