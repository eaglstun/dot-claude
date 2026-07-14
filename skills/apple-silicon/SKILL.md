---
name: apple-silicon
version: 1.0.0
public: true
description: >-
  Apple Silicon GPU / Metal reference for GPU-compute work in any repo — PyTorch MPS
  kernels, the CTranslate2 Metal backend, or a standalone Metal project. Covers MSL
  compute kernels, threadgroup & grid sizing, MPSMatrixMultiplication (GEMM),
  MPSGraph/MPSNDArray, command-buffer dispatch, CPU↔GPU synchronization, resource storage
  modes, unified memory, fp16/int8 numerics, and Objective-C++ interop.
semantic_id: "9HHwmh88uNwk4rH9Wk5DNmZhlTIbsAAK"
related_ids:
  - "3HD6Cu8-sN6kzLF5Xk5DFiBl146dsAAI"
  - "3P98iM8kgN72r6S4Xs_jE2J1XwQb4AAL"
topic_id: "v2:NOHI"
topic_path: "apple-accelerate/silicon-arch"
---

# Apple Silicon (Metal) reference

Condensed, source-cited notes from Apple's developer documentation. The **API bodies are
repo-agnostic** — that's the ground truth you came for.

Most files then end with a **worked example** section grounding the API in a real codebase. Those
examples come from the **CTranslate2 Metal backend** (`src/metal/`, `-DWITH_METAL=ON`), which is
where this shelf was mined. They are illustrations, not instructions: they show what the API looks
like when a real inference engine leans on it, including the measured numbers and the graveyard of
things that didn't work. **If you are not in CTranslate2, read them as a case study and map the
lesson onto your own code — never onto a `src/metal/` path that doesn't exist in your repo.**

**When working on Metal, read the relevant reference first — these APIs have sharp edges (no `erf`
in MSL, every bound buffer must exist, row-major vs column-major) that are easy to get wrong from
memory.**

## Orienting in a new repo

Find the Metal code before you reason about it. Two layouts you'll meet often:

- **PyTorch / ATen** — MPS operators in `aten/src/ATen/native/mps/operations/`, `.metal` shader
  sources alongside, `MPS:` dispatch keys in `aten/src/ATen/native/native_functions.yaml`. CPU is
  the numeric reference; MPS has real dtype gaps (no fp64 on device). The `metal-kernel` project
  skill owns the ATen conventions — this shelf owns the Apple API truth underneath it.
- **CTranslate2** — `src/metal/` (`device.mm`, `allocator.mm`, `primitives.mm`, `gemm.mm`,
  `kernels_msl.h`); `METAL_BACKEND.md` at the repo root has the design. This is the repo the worked
  examples below describe.

## References

- **[references/op-graduation-playbook.md](../../references/apple-silicon/op-graduation-playbook.md)**
  How to move an op onto a Metal kernel at all: targeted routing, the fp16 real-kernel-vs-bypass decision and its flush nuance, the MSL landmines, parity against a CPU reference; read FIRST when adding or routing any kernel. (The procedure is CT2-shaped; the landmines and the parity discipline are universal.)
- **[references/compute-kernels-and-dispatch.md](../../references/apple-silicon/compute-kernels-and-dispatch.md)**
  The full run-a-compute-kernel chain (device to library to pipeline to encoder to commit), MSL `kernel` basics, and threadgroup/grid sizing incl. `dispatchThreads` vs `dispatchThreadgroups`; read when adding or editing any MSL kernel or its dispatch.
- **[references/simd-group-functions.md](../../references/apple-silicon/simd-group-functions.md)**
  Cross-lane SIMD-group/quad-group functions (`simd_sum`, shuffles, ballot, prefix scans) and the canonical two-level reduction for optimizing row-reduction kernels (softmax/norms); read when writing or optimizing a reduction.
- **[references/math-functions-and-numeric-parity.md](../../references/apple-silicon/math-functions-and-numeric-parity.md)**
  MSL math builtins (no `erf`) and the default-fast-math parity reality (tolerances, the `1.0f/sqrt` spelling, float-accumulated reductions, ULP tables, the `mathMode = Safe` lever); read when a norm, softmax, or reduction kernel must match a CPU reference.

> Transformer **structure** (e.g. norm placement) is CPU orchestration, not Metal. For CT2 that
> lives in the `ct2-internals` skill; in PyTorch it's the model code. Kernel numerics stay here.

- **[references/mps-matrix-multiplication.md](../../references/apple-silicon/mps-matrix-multiplication.md)**
  `MPSMatrixMultiplication` GPU GEMM (initializer params, encode, row-major `MPSMatrixDescriptor`, batched origins) and why operands-at-encode-time enables shape-keyed object caching; read when touching any GEMM routing.
- **[references/storage-and-synchronization.md](../../references/apple-silicon/storage-and-synchronization.md)**
  Storage modes and unified memory (why a backend rides Shared + `contents`) plus the CPU/GPU sync mechanics behind flush/synchronize, and the global-vs-thread-local command-buffer lesson; read when touching allocation, device lifecycle, or stale/garbage GPU reads.
- **[references/dispatch-overlap-and-perf-model.md](../../references/apple-silicon/dispatch-overlap-and-perf-model.md)**
  The perf model: per-op encode floor, CPU/GPU overlap principle, the prefill-wins/decode-loses split — and the graveyard (command-buffer reuse measured -23% on bs8 prefill and was REVERTED); read before chasing any perf change. The numbers are CT2-on-M4-Max; the _shape_ of the argument generalizes.
- **[references/benchmarking-and-profiling.md](../../references/apple-silicon/benchmarking-and-profiling.md)**
  The methodology behind every number here (the benchmark harness, the env-var profiling switches, the probe-isolation trick that found the encode floor); read before measuring a change or claiming a speedup.

### int8 quantized path (worked through end-to-end)

- **[references/int8-gemm-kernel-design.md](../../references/apple-silicon/int8-gemm-kernel-design.md)**
  A hand-tiled int8 GEMM (why no native int8 matmul path exists on the GPU, the tile/micro-tile design, the exactness contract, the shim graveyard, ALU-bound and slower than fp16 MPS at large m but -42% RSS); read before writing an int8 GEMM or expecting a tiling tweak to beat MPS.
- **[references/int8-gemv-simdgroup-decode.md](../../references/apple-silicon/int8-gemv-simdgroup-decode.md)**
  A small-m SIMD-group GEMV (one SIMD-group per output element, the routing and 4-byte-alignment preconditions, why bandwidth-bound int8 beats fp16 MPS at decode); read when touching decode-path GEMMs or anything that could silently break alignment preconditions.
- **[references/quantize-dequantize-kernels.md](../../references/apple-silicon/quantize-dequantize-kernels.md)**
  The three kernels around an int8 GEMM (bit-parity quantize, dequantize, and the epilogue carrying scales+bias+activations); read when touching quantization parity, scales, or fusing a Dense epilogue.

### MSL spec — language & stdlib

- **[references/simdgroup-matrix-functions.md](../../references/apple-silicon/simdgroup-matrix-functions.md)**
  SIMD-group 8x8 matrix matmul and THE §2.4 type table (half/bfloat/float only, NO integer element types — the spec ground truth for why int8 GEMMs get hand-tiled; Metal 2.3+/Apple7+); read before attempting fused attention or an off-MPS fp16 GEMM.
- **[references/conversion-and-packing-functions.md](../../references/apple-silicon/conversion-and-packing-functions.md)**
  Conversion and reinterpretation rules (float-to-int rounds toward zero with no saturation, hence `rint` before the cast; `as_type<T>` vs the pointer-cast `char4` loads; §6.15 norm-pack; Metal 4.1 packed-numeric templates); read when writing quantize/dequantize or packed-load code.
- **[references/integer-functions.md](../../references/apple-silicon/integer-functions.md)**
  The §6.4 integer-builtin lookup table, with the honest inventory that a typical int8 GEMM/GEMV needs none of them (plain int32 math is exact at transformer depths; `clamp`/`mulhi` are the future reach-fors); read when an integer kernel tempts you toward a builtin.
- **[references/atomic-functions.md](../../references/apple-silicon/atomic-functions.md)**
  §6.16 atomics (int/uint/bool/ulong/float only, relaxed-only memory order pre-Metal-4.1, fences and scopes) and why a well-shaped kernel set can stay deliberately atomics-free; read before adding any cross-threadgroup accumulation.
- **[references/threadgroup-and-simdgroup-synchronization.md](../../references/apple-silicon/threadgroup-and-simdgroup-synchronization.md)**
  `threadgroup_barrier`/`simdgroup_barrier` and the `mem_flags` variants, the all-threads-must-reach-it divergence rule, and when SIMD-group functions need no barrier; read when adding a barrier, a row guard, or any threadgroup-memory phase.
- **[references/msl-address-spaces.md](../../references/apple-silicon/msl-address-spaces.md)**
  device/constant/threadgroup/thread access rules (no address-space casts, program-scope-must-be-constant, `device T*` arrays vs `constant T&` setBytes scalars, the in-space `char4` trick); read when declaring kernel signatures or staging tiles.
- **[references/msl-data-types-and-alignment.md](../../references/apple-silicon/msl-data-types-and-alignment.md)**
  §2 size/alignment tables (no `double`, `bfloat` needs Metal 3.1+, the vec3-pads-to-vec4 trap, `packed_` types for byte-tight host-shared layouts); read before sharing a struct with the host or reinterpreting buffer element types.
- **[references/common-functions.md](../../references/apple-silicon/common-functions.md)**
  §6.3 clamp/mix/saturate/step semantics (float/half ONLY; home of the Gemma2 tanh-overflow clamp, and the note that a bit-parity quantize deliberately does NOT clamp to ±127); lookup card for kernels leaning on clamp/saturate semantics near NaNs.
- **[references/relational-and-select-functions.md](../../references/apple-silicon/relational-and-select-functions.md)**
  §6.5 isnan/isinf/`select` semantics plus the fast-math caveat that in-kernel `isnan` tripwires need `math_mode(safe)` (the Gemma2 NaN hunt only worked because the checks ran on the host); lookup card for NaN tripwires or branchless vector guards.

### Metal API surface

- **[references/mtlbuffer-api.md](../../references/apple-silicon/mtlbuffer-api.md)**
  The MTLBuffer/MTLDevice allocation lookup card (the three `makeBuffer` variants, `.contents`, purgeable state, `label`) and the fact Metal guarantees NO base alignment — so alignment-sensitive kernels must check offsets themselves; read when touching allocation.
- **[references/resource-storage-modes-and-options.md](../../references/apple-silicon/resource-storage-modes-and-options.md)**
  The `MTLResourceOptions` bitmask lookup card (storage modes, `defaultCache` vs `writeCombined`, hazard-tracking modes, `bytesNoCopy`); read when creating a buffer with anything but the obvious combination.
- **[references/mtlheap.md](../../references/apple-silicon/mtlheap.md)**
  `MTLHeap` suballocation (`makeAliasable` reuse, the untracked-by-default fence trap); the evaluated answer if allocator churn ever shows on a profile, so read before reaching for a buffer pool.
- **[references/mtlevent-and-mtlfence.md](../../references/apple-silicon/mtlevent-and-mtlfence.md)**
  The three explicit sync primitives (MTLFence/MTLEvent/MTLSharedEvent) — and the concrete triggers (a second queue, an untracked resource) that are the only reasons you'd need them; read before adding any of them.
- **[references/mtlgpufamily-and-feature-availability.md](../../references/apple-silicon/mtlgpufamily-and-feature-availability.md)**
  `MTLGPUFamily`/`supportsFamily` (M1=apple7, M2=apple8, M3/M4=apple9, `maxBufferLength`); read before using a per-family feature or porting off an M-series dev box.
- **[references/argument-buffers.md](../../references/apple-silicon/argument-buffers.md)**
  Argument buffers and the residency rules (tier1 encoder vs tier2 bindless); relevant only when binding many buffers per dispatch, or batching tiny decode ops via ICBs.
- **[references/pipeline-and-library-compilation.md](../../references/apple-silicon/pipeline-and-library-compilation.md)**
  Runtime MSL-to-pipeline compilation (`newLibraryWithSource`, `mathMode` where relaxed is the Apple-silicon default, function constants, the ~493 ms first-MPS-GEMM warmup, the measured-dead `.metallib` receipt); read before touching shader compilation or proposing precompiled shaders.
- **[references/gpu-counters-and-timestamps.md](../../references/apple-silicon/gpu-counters-and-timestamps.md)**
  GPU-side timing in three tiers (`gpuStartTime`/`gpuEndTime` free whole-buffer timing, `sampleTimestamps` clock correlation, counter sample buffers as the per-kernel scalpel); read before adding GPU-side measurement.
- **[references/gpu-capture-and-shader-validation.md](../../references/apple-silicon/gpu-capture-and-shader-validation.md)**
  The misplaced-pointer toolkit (programmatic `.gputrace` capture, `MTL_SHADER_VALIDATION`, `MTL_DEBUG_LAYER`) for MEMORY bugs, NOT numeric ones like a fp16 overflow NaN; read when a kernel scribbles, hangs, or reads garbage.
- **[references/memory-footprint-and-residency.md](../../references/apple-silicon/memory-footprint-and-residency.md)**
  Measuring and bounding GPU memory on unified memory (`recommendedMaxWorkingSetSize` preflight, purgeable state as the cache lever), carrying the int8 -42% RSS headline; read when chasing footprint or before claiming a memory win.

### MPS beyond GEMM

- **[references/mps-matrix-vector-multiplication.md](../../references/apple-silicon/mps-matrix-vector-multiplication.md)**
  `MPSMatrixVectorMultiplication` (cacheable init/encode split, strided-batch vectors, no integer GEMV documented anywhere); the MPS-native option for fp16 decode m=1 GEMMs.
- **[references/mps-softmax-and-topk.md](../../references/apple-silicon/mps-softmax-and-topk.md)**
  `MPSMatrixSoftMax` (fp32/fp16 only, NO masking — why a custom kernel usually wins) and `MPSMatrixFindTopK` (k ≤ 16 or UB); read when graduating sampling ops onto the GPU.
- **[references/mpsndarray.md](../../references/apple-silicon/mpsndarray.md)**
  `MPSNDArray` matmul and THE load-bearing find that macOS 15+ ships `MPSNDArrayQuantizedMatrixMultiplication` (int8/int4, zero-copy buffer init) — a benchmark candidate against any hand-written int8 GEMM; read before any int8-GEMM rework.
- **[references/mpsgraph-for-inference.md](../../references/apple-silicon/mpsgraph-for-inference.md)**
  MPSGraph in one card (placeholders, cached executable, encode into an existing command buffer; has quantize/dequantize ops but NO quantized matmul); read before wrapping any op in MPSGraph.
- **[references/mps-convolution-options.md](../../references/apple-silicon/mps-convolution-options.md)**
  The three routes for getting a Conv1D off the CPU (MPSCNNConvolution poor fit, MPSGraph `convolution2D` via height-1, custom MSL kernel as the recommended first prototype); read when scoping a conv.

### Objective-C++ runtime, debugging & profiling

- **[references/autoreleasepool-in-long-loops.md](../../references/apple-silicon/autoreleasepool-in-long-loops.md)**
  THE memory lesson: autoreleased Metal/MPS temporaries never drain on run-loop-less C++ worker threads (a real SIGKILL), and the per-op thread-local pool fix, plus the diagnostic signature; read before adding any Metal path called from a long-running C++ thread.
- **[references/objcpp-interop-for-mm-files.md](../../references/apple-silicon/objcpp-interop-for-mm-files.md)**
  Objective-C++ survival card: the split-header discipline, the three ownership patterns for holding ObjC objects from C++, bridge casts, nil-messaging semantics. NOTE the examples come from an MRC (non-ARC) backend — check your own project's memory model before copying a pattern.
- **[references/occupancy-and-threadgroup-memory.md](../../references/apple-silicon/occupancy-and-threadgroup-memory.md)**
  The occupancy levers (PSO `maxTotalThreadsPerThreadgroup` under register pressure, `threadExecutionWidth`, the 32 KB threadgroup-memory budget) with worked arithmetic; read when sizing a tile or chasing low occupancy.
- **[references/instruments-gpu-profiling.md](../../references/apple-silicon/instruments-gpu-profiling.md)**
  Metal System Trace overlap lanes, the GPU Counters limiter view, os_signpost labeling, headless `xctrace` recipes; read before the first profiling session.
- **[references/command-buffer-errors-and-hangs.md](../../references/apple-silicon/command-buffer-errors-and-hangs.md)**
  Failure diagnosis (status lifecycle, the real `MTLCommandBufferError` codes, per-encoder blame) and the punchline that if nothing checks command-buffer status, a GPU fault reads back as silent garbage; read when output is wrong and you don't yet know which kind of wrong.

### Hardware & future surfaces

- **[references/apple-gpu-architecture-for-compute.md](../../references/apple-silicon/apple-gpu-architecture-for-compute.md)**
  The calibrate-your-mental-model card, every claim provenance-labeled (32-wide SIMD, marketing vs measured bandwidth, NO int8 matrix hardware, the measured fp16-vs-fp32 GEMM ratio); read before reasoning about what the GPU can do.
- **[references/fp16-numerics-on-gpu.md](../../references/apple-silicon/fp16-numerics-on-gpu.md)**
  Half-precision survival card (65504 limit, THE Gemma2 tanh-overflow NaN case and its clamp fix, the store-half/compute-float rule, literal suffixes, rounding); read before writing any fp16 kernel.
- **[references/indirect-command-buffers.md](../../references/apple-silicon/indirect-command-buffers.md)**
  ICBs for compute (NO `setBytes` — scalars must move to buffers), with the honest verdict that encode-once-replay-per-token likely loses the way command-buffer reuse did; measure first.
- **[references/metal4-tensors-and-mpp.md](../../references/apple-silicon/metal4-tensors-and-mpp.md)**
  The Metal 4 (macOS 26) ML surface and THE find that MPP `matmul2d` supports char×char→int at base Metal 4 — a documented int8 matmul path — with all the unstated flags; read alongside mpsndarray.md before any int8-GEMM rework.

### Copies, layouts & version index

- **[references/gemm-layouts-and-transpose-conventions.md](../../references/apple-silicon/gemm-layouts-and-transpose-conventions.md)**
  THE row/column-major Rosetta stone (MPS maps directly to row-major, so do NOT replicate the cuBLAS A/B swap); read whenever a transpose flag or leading dimension is in play. Essential when porting a CUDA kernel to Metal.
- **[references/blit-command-encoder.md](../../references/apple-silicon/blit-command-encoder.md)**
  `MTLBlitCommandEncoder` buffer ops, and when a blit beats a CPU `std::copy` through `contents` (big contiguous device copies) vs a custom kernel (strided/gather); read before adding any copy path.
- **[references/concurrent-dispatch-and-encoder-semantics.md](../../references/apple-silicon/concurrent-dispatch-and-encoder-semantics.md)**
  Serial vs `.concurrent` encoder semantics and cross-encoder hazard tracking; read before any encoder-fusion or barrier idea.
- **[references/metal-os-feature-matrix.md](../../references/apple-silicon/metal-os-feature-matrix.md)**
  The feature/MSL-version/macOS-floor index across every reference here; read before using anything version-gated.
- **[references/mtlio-command-queue.md](../../references/apple-silicon/mtlio-command-queue.md)**
  Metal 3 fast resource loading, whose headline win is already free on unified memory (interesting only with compressed weights); read before proposing load-time GPU streaming.
- **[references/binary-archives-and-pso-caching.md](../../references/apple-silicon/binary-archives-and-pso-caching.md)**
  Graveyard: `MTLBinaryArchive` PSO caching, and why the system shader cache usually already warms your PSOs; read before re-proposing precompiled shaders.

## Conventions & maintenance

- **The `file:line` anchors in the worked-example sections point at CTranslate2, and they drift.**
  Run `bash scripts/audit-citations.sh` (`-q` for problems-only) from the CT2 repo before trusting
  one; a "verified on DATE" stamp dies the moment the file changes. **From any other repo, those
  anchors are illustrative only — they are not describing your code.**
- Adding a worked example from a new repo? Append a **new** `### Worked example: <repo> <backend>`
  section; don't overwrite the existing one. The shelf is machine-wide and read from many projects,
  so every example must name its repo.
- See the shelf README (`../../references/apple-silicon/README.md`) for the add-a-topic recipes
  (DocC JSON, the MSL spec PDF), the crosslink conventions, and the TODO list of MSL spec sections
  still worth mining.
