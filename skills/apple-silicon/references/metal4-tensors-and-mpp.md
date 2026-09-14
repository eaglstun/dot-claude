---
topic_id: "v2:POGN"
topic_path: "msl-math"
semantic_id: "XFP8yp0caDxgjOFWD0QANgjEGQodsAAK"
related_ids:
  - "Elx8740-aFgjj-b0q0VBI4REGYwdMAAA"
  - "VlHQ3h8-2XhkH-EWanAgCkrCmMgXsAAD"
---

# Metal 4 tensors & Metal Performance Primitives — is there a supported int8 matmul?

Sources: Apple DocC JSON (fetched 2026-06-11):
<https://developer.apple.com/documentation/metal/mtltensor>,
<https://developer.apple.com/documentation/metal/mtltensordatatype>,
<https://developer.apple.com/documentation/metal/mtl4machinelearningcommandencoder>;
MSL spec v4.1 (2026-06-04) §2.22 (Tensor Types) and §7 (Metal Performance Primitives),
<https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf>.
Everything below is what those sources state; gaps are flagged. The backend uses none of
this today.

**THE answer this file exists for: YES — MSL §7.2.1 Table 7.3 lists `char × char → int`
as a supported `matmul2d` combination at base Metal 4** (macOS 26 per the DocC platform
stamps; this repo's dev box runs macOS 26.4.1). Details and the honest caveats below.

## MTLTensor — the host-side resource [Apple doc, macOS 26.0+]

`protocol MTLTensor : MTLResource` — "a multi-dimensional array that you can use with
machine learning workloads." Properties: `dataType`, `dimensions`, `strides`, `usage`,
`gpuResourceID`, and crucially `buffer`/`bufferOffset` — a tensor **can share storage
with an existing `MTLBuffer`** (nil/zero when it doesn't), i.e. a zero-copy wrap of
already-resident weights. `getBytes`/`replace` copy slices CPU-side. Created via
`MTLTensorDescriptor` (separate page, same macOS 26 stamp).

`MTLTensorDataType` enumerates: **int8**, uint8, int4, uint4, int2, uint2, int16/uint16,
int32/uint32, float16, **bfloat16**, float32, plus fp8 (e4m3, e5m2, ue8m0) and fp4
(e2m1). So int8 _storage_ is first-class.

## MTL4 machine-learning encoder [Apple doc, macOS 26.0+]

Metal 4 command buffers add `MTL4MachineLearningCommandEncoder`: `setPipelineState(_:)`,
`setArgumentTable(_:)`, `dispatchNetwork(intermediatesHeap:)` — it dispatches a whole
pre-built ML _network_ as a pass, with a heap for intermediates. This is the
graph/network surface (closer to "run a CoreML-style net inside Metal" — how the network
pipeline state is built is on pages not fetched here); it is NOT the per-op matmul
surface CT2 would want. That one is shader-side, below.

## MSL §2.22: `tensor<>` in shaders [spec, Metal 4+]

- `tensor<ElementType, Extents, DescriptorType, Tags…>` — a **non-owning view**; element
  value types: half, bfloat, float, **char, uchar**, short, ushort, int, uint (Metal 4.1
  adds packed "format types" — int4b/uint4b/int2b/uint2b, fp8/fp4 — with 128-byte
  alignment and block-multiple extent rules, Table 2.24).
- **Shader-allocated tensors (§2.22.2.7): a kernel can construct a `tensor_inline` view
  directly from a raw `device`/`threadgroup`/`constant` pointer + extents (+ strides)** —
  no host-side `MTLTensor` object needed. This is the load-bearing fact for retrofitting:
  existing `MTLBuffer`-bound kernel args can be wrapped in-shader.
- `cooperative_tensor<>` (§2.22.3): thread-local storage pre-partitioned across
  participating threads — the accumulator form for matmul.

## MSL §7: Metal Performance Primitives [spec, Metal 4+]

"All OS: Metal 4 and later." Header `<MetalPerformancePrimitives/MetalPerformancePrimitives.h>`,
namespace `mpp::tensor_ops`, "tuned for Apple silicon GPUs"; for supported GPU families
the spec defers to the Metal Feature Set Tables (not stated inline — **flag: hardware
floor unverified here**, only the OS floor is documented).

- Execution scopes (§7.1): `execution_thread`, `execution_simdgroup`,
  `execution_simdgroups<N>` — a matmul executed cooperatively by N SIMD-groups. All
  threads in scope must call `run` (uniform-control-flow rule); barrier before reading
  device/threadgroup results.
- `matmul2d_descriptor(M, N, K, transpose_left, transpose_right, relaxed_precision,
mode::multiply|multiply_accumulate)`; `K = dynamic_length_v<int>` is the default —
  **dynamic K is in the API**. Instantiate `matmul2d<Desc, Scope>`, call
  `run(A, B, C)` on tensors (C may be a `cooperative_tensor`). `convolution2d` likewise
  (§7.2.2).

### Table 7.3 — the dtype combinations that matter to CT2 [spec, verbatim subset]

| A      | B               | C            | Since              |
| ------ | --------------- | ------------ | ------------------ |
| char   | char            | **int**      | **Metal 4** (base) |
| half   | half            | half/float   | Metal 4            |
| char   | half            | half/float   | Metal 4            |
| bfloat | bfloat          | bfloat/float | Metal 4 + OS 26.1  |
| char   | int4b_format    | int          | Metal 4 + OS 26.4  |
| half   | fp8/fp4 formats | half/float   | Metal 4.1          |

(Full table also covers uchar at OS 26.4 and int2b at Metal 4.1.) `char×char→int` —
int8×int8 with an int32 destination, CT2's exact contract — is base-Metal-4. The int4
weight path (`char/half/bfloat × int4b_format`) is OS 26.4+.

## What the docs did NOT say — ANSWERED BY MEASUREMENT 2026-06-11 (M4 Max)

The flagged unknowns below were all resolved by the Task-6 experiment
(`experiments/mpp_matmul2d_proto.mm` / `mpp_matmul2d_tune.mm`; integrated as
`ct2_mpp_gemm_s8_nt` in `src/metal/kernels/kernels_mpp_msl.h`; numbers in
`METAL_BENCHMARKS.md`):

- **Performance: YES, dramatically.** char×char→int `matmul2d` ties MPS fp16 GEMM
  (2048³: 1.51 ms ≈ fp16's 1.49; ~11.4 T-eff-FLOPS) — 4.8× over the hand-tiled ALU
  kernel. The win REQUIRES tuning: **2 cooperating SIMD-groups** (Apple's 4-SG header
  example is 2–5× slower on every shape), 16×64 tiles, and the interior/edge
  static-extent `slice<Extents...>` split.
- **Accumulator: int32-bit-exact**, verified vs a host triple loop at k=2048 over the
  full int8 range plus saturated inputs. `mode::multiply` overwrites C (no read).
- **Runtime compile: works** via `newLibraryWithSource` with
  `options.languageVersion = MTLLanguageVersion4_0` and
  `#include <MetalPerformancePrimitives/MetalPerformancePrimitives.h>` — no Metal-4
  pipeline/encoder machinery needed; classic compute encoder + `setBuffer` suffice
  (inline tensors wrap the raw pointers in-shader).
- **Gotchas:** MPP's dispatch matches element types EXACTLY — `int8_t`/`int32_t`,
  non-const (`char` or `const int8_t` → "Unsupported type" static_assert). The
  stdlib spells the header comment's `static_slice` as `slice<Extents...>`.
  `relaxed_precision` remains float-only.
- **Hardware floor.** DocC stamps say OS 26.0; which `MTLGPUFamily` supports MPP is
  delegated to the Feature Set Tables (not fetched — PDF, not DocC).
- **Callable from a classic compute pipeline? YES — CONFIRMED 2026-08-10 (M4 Max,
  macOS 26.5.2).** This was the open question above. `matmul2d` compiles and runs through
  **PyTorch's `torch.mps.compile_shader`**, which is a plain `newLibraryWithSource` path
  with a classic compute encoder and ordinary `setBuffer` bindings — no Metal-4 pipeline,
  no `MTL4MachineLearningCommandEncoder`, no `MTLTensor` objects. Notably it worked
  **without setting `languageVersion` at all** (PyTorch does not expose that knob), so the
  compiler's default language version on macOS 26 is already new enough. If a host can
  compile MSL from a string, it can use MPP.

## The on-disk headers — read these, not the spec PDF

The MSL headers ship in the SDK and are the fastest ground truth available:

```
/Library/Developer/CommandLineTools/SDKs/MacOSX<ver>.sdk/System/Library/Frameworks/
  MetalPerformancePrimitives.framework/Versions/A/Headers/
    MPPTensorOpsMatMul2d.h        <- descriptor + a long worked-example comment
    MPPTensorOpsConvolution2d.h
    __impl/                        <- the actual template machinery
```

and the `tensor` type itself lives inside the compiler, not the SDK:

```
/System/Library/PrivateFrameworks/GPUCompiler.framework/Versions/<n>/Libraries/
  lib/clang/<n>/include/metal/metal_tensor
```

Two things the header gives you that the spec subset does not:

- **The supported-dtype list is much longer than Table 7.3's excerpt** — ~60 combinations
  including `uint8_t × uint8_t → int32_t`, every bfloat/half cross product, and the int4b
  variants.
- **`mode::multiply` is the DEFAULT** (7th ctor parameter) and it _overwrites_ C. The
  header's example comment says "Assumes C is initialized to zero", which applies to
  `multiply_accumulate`; with the default you can hand it an uninitialized destination.

### Exact spellings that cost time to discover

- **`tensor_inline` must be named explicitly as the third template argument.** The default
  descriptor is `tensor_handle`, which expects a host-provided `MTLTensor` and gives an
  unhelpful "no matching constructor" when handed a pointer:

  ```cpp
  // WRONG - tensor_handle, will not construct from a device pointer
  auto A = tensor<device int8_t, dextents<int32_t, 2>>(ptr, ext);
  // RIGHT
  auto A = tensor<device int8_t, dextents<int32_t, 2>, tensor_inline>(
               Ap, dextents<int32_t, 2>(K, M));
  ```

  The two-arg `(ptr, extents)` ctor implies packed strides (`stride[0] = 1`,
  `stride[i] = stride[i-1] * extent(i-1)`), i.e. plain row-major.

- **`extent(0) is the CONTIGUOUS axis.`** A row-major `[M,K]` matrix is
  `dextents(K, M)` — dimensions are listed fastest-first, the reverse of how the shape is
  usually written. Same for the slice index order: `C.slice<TN, TM>(n0, m0)`.
- **`slice<Extents...>(...)`**, not the header comment's `static_slice` (the comment is
  stale; `static_slice` does not exist as a member). Dynamic form is `slice(...)`.
- **Element types match EXACTLY**: `int8_t`/`int32_t`, non-const. `char` or
  `const int8_t` trips an "unsupported type" static_assert.
- **Apple's header example contradicts itself on the tgid mapping** — the dispatch comment
  uses `threadgroups = ((M+63)/64, (N+31)/32)` while the slices index M off `tgid.y`.
  Pick your own mapping and verify against a CPU reference; don't copy the comment.

### Worked example: the CTranslate2 Metal backend

- This is the documented successor question to `ct2_gemm_s8`
  (`src/metal/kernels/kernels_msl.h`): the hand-tiled kernel exists because MPSMatrix is
  float-only and `simdgroup_matrix` has no int8 (`int8-gemm-kernel-design.md`). Two
  candidates now exist: `MPSNDArrayQuantizedMatrixMultiplication` (macOS 15+,
  `mpsndarray.md`) and MSL-4 `mpp::tensor_ops::matmul2d` char×char→int (macOS 26+).
- The cheapest experiment is shader-side: §2.22.2.7 inline tensors wrap the _existing_
  buffer arguments of `ct2_gemm_s8`'s entry point, so a `matmul2d` variant could slot in
  behind the same routing in `src/metal/primitives.mm` (`metal::gemm_s8`) with the
  hand-tiled kernel as fallback — gated on language version, parity-suite first
  (`tests/metal_test.cc`, keep `Int8GemmDeepAccumulatorMatchesHostReference` green),
  then the Phase-2 benchmark shapes (`METAL_BENCHMARKS.md`).
- The target regime is the **ALU-bound large-m tiled case** (int8 7.28 ms vs fp16
  1.48 ms at 2048³) — the GEMV decode win is bandwidth-bound and already beats fp16; it
  has nothing to gain unless MPP also lifts bandwidth efficiency.
- OS floor: macOS 26 — fine for the M4 Max dev box (26.4.1), but an availability gate +
  fallback is mandatory for the library (`mtlgpufamily-and-feature-availability.md`).

### Worked example: image-gen (PyTorch MPS) — `aten::_int_mm`

Example repo, file `kernels/int_mm_mps.py`, 2026-08-10, M4 Max /
macOS 26.5.2 / torch 2.13. Independent replication of the CT2 result from a completely
different host language (Python, no Objective-C++ anywhere).

- **Why:** PyTorch ships no `aten::_int_mm` for MPS, so every int8-quantized matmul either
  raises `NotImplementedError` or, under `PYTORCH_ENABLE_MPS_FALLBACK=1`, round-trips each
  linear to the CPU. Measured cost of that fallback in a real workload: **580 s per
  diffusion step**.
- **How:** `torch.mps.compile_shader` compiles the MPP kernel at runtime; the op is bound
  onto the dispatch key with `torch.library.impl("aten::_int_mm", "MPS")`. The whole thing
  is one Python file plus a shader string — no C++ extension, no build step. Confirms MPP
  needs nothing from the Metal-4 host API.
- **Tuning replicates CT2's finding, with a different optimum.** Swept 10 tile shapes ×
  {1,2,4} SIMD-groups, correctness-gated. Best was **32×64 with 2 SIMD-groups** (CT2 found
  16×64/2). **2 SIMD-groups beat Apple's 4-SG header example on nearly every tile**, and
  the spread between best and worst config was 2.7× — the tuning is not optional.
- **Measured (int8 `matmul2d` vs the hand-tiled ALU kernel vs MPS fp16):**

  | m, n, k          | MPP int8 | hand-tiled | fp16 MPS |
  | ---------------- | -------- | ---------- | -------- |
  | 2048³            | 1.39 ms  | 6.83 ms    | 1.52 ms  |
  | 1024, 3840, 2560 | 1.42 ms  | 7.93 ms    | 1.68 ms  |
  | 4096, 3840, 3840 | 8.16 ms  | 46.6 ms    | 7.99 ms  |

  **14.8 T-op/s**, ~5.7× the hand-tiled ALU kernel, and it **ties or slightly beats fp16
  MPS at every size** — matching CT2's "ties fp16" result on the same silicon.

- **Bit-exact**, verified against a CPU int32 reference across tile-exact, ragged, M=1,
  N=1 and saturated-accumulator (67 108 864, 4× past 2²⁴) cases. Both the MPP and
  hand-tiled paths pass the same suite, so they are drop-in interchangeable.
- **End to end** (Z-Image Turbo diffusion, 1024², 8 steps): int8 went 580 s/step (CPU
  fallback) → 25.0 s/step (hand-tiled) → **5.7 s/step (MPP)**, against bf16's 5.4 s/step
  measured under the same load. int8 goes from unusable to within ~5% of bf16.
- **Gotcha worth repeating:** compiling is not proof of running — MPP's hardware floor is
  delegated to the feature-set tables, so the module runs a small self-check against a CPU
  reference at import and silently falls back to the hand-tiled kernel if it fails.

### NEGATIVE RESULT: MPP does NOT beat MPS for float GEMM — don't re-run this

Measured 2026-08-10, M4 Max / macOS 26.5.2, `kernels/bench_mpp_bf16.py` in the same repo.
The obvious follow-on to the int8 win is "does `bfloat × bfloat → bfloat` beat MPS too?"
**No. It is a tie**, at every shape tested, including four real 6B-DiT shapes at m = 4128
and a 2048³ control:

| m, n, k         | MPP bf16 | MPS bf16 | MPS fp16 |
| --------------- | -------- | -------- | -------- |
| 4128,10240,3840 | 21.01 ms | 21.36 ms | 21.33 ms |
| 4128,3840,3840  | 7.91 ms  | 8.06 ms  | 8.07 ms  |
| 2048³           | 1.17 ms  | 1.18 ms  | 1.20 ms  |

1.01× weighted by call frequency; both ~15.4–15.5 TFLOPS. Accuracy also ties (mean
relative error 1.41e-03 vs an fp32 CPU reference for both).

**Why, and the rule to carry forward:** the int8 result was never evidence that MPP is
fast. It was evidence that **MPS has no integer GEMM at all** — the thing MPP was beating
was a hand-written ALU kernel at 2.5 T-op/s. For float, `MPSMatrixMultiplication` already
dispatches to the same matrix hardware MPP does. So:

> **Reach for MPP where MPS has a hole (integer, int4, fused/cooperative shapes), not
> where MPS has a mature path (fp16/bf16/fp32 GEMM). A mature MPS path is already the
> hardware's best.**

Two secondary facts worth keeping:

- **Tile tuning does not transfer across dtypes.** Best config was 32×32 / 1 SIMD-group
  for bf16 vs 32×64 / 2 SIMD-groups for int8, on the same machine. Spread was still
  large (15.5 down to 4.1 TFLOPS), so re-sweep per dtype or lose 3×.
- **`bfloat × bfloat → float32` is bit-identical to an fp32 CPU reference** in this test,
  where bf16-out carries the usual 1.4e-03. A free accuracy option if a wider destination
  is acceptable — but there is no speed in it.
