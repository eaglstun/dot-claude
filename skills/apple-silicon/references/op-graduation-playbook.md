---
topic_id: "v2:MOHL"
topic_path: "metal-compute"
semantic_id: "FkPbloqmsOx0qnW_VO6jGsbh2jqToAAB"
related_ids:
  - "9HHwmh88uNwk4rH9Wk5DNmZhlTIbsAAK"
  - "2ldQ3s42mHJkVvG33nwgi-LHGNs_oAAC"
---

# Op-graduation playbook (CT2 → Metal GPU kernel)

How to correctly move a CTranslate2 op from the CPU-reference binding onto a real Metal
GPU kernel — the repo procedure and its sharp edges. Unlike the other references here,
this is not an Apple-API topic: it is the CT2-specific "how to make this change" companion
to `compute-kernels-and-dispatch.md` (MSL/dispatch), `mps-matrix-multiplication.md` (GEMM),
and `storage-and-synchronization.md` (the flush model). Read those for the API; read this
for the pattern.

## STEP ZERO (any repo): is it still slow, and does it still matter?

Two measurements, both cheap, both capable of cancelling the whole project. Do them before
writing a line of MSL. Added 2026-08-10 after they killed a day-long kernel plan in the
`image-gen` repo — see the worked example at the bottom.

**1. Is the op still slow?** Framework backends get fixed. Re-measure on the _exact_
toolchain you will ship against, not the one your notes were written on. A stale benchmark
is worse than no benchmark, because it comes with false confidence. Two specific traps:

- **Check for a shipped kernel first.** For PyTorch, look in
  `<site-packages>/torch/include/ATen/native/mps/kernels/` — a header named after your op
  means a dedicated Metal shader exists. Absence from the `operations/*.mm` file does NOT
  mean absence overall; group norm lives only in `kernels/GroupNorm.h`.
- **Measure against an in-run reference op, never a bare millisecond.** Run a trivial
  read+write on the _same tensor in the same process_ and express your op as a multiple of
  its achievable bandwidth. Absolute timings on a loaded machine moved by **up to 10x**
  between sessions in the case below; the ratio to an in-run reference stayed stable.
  A kernel that is a fixed ~30 GB/s regardless of shape is genuinely broken; one within
  ~2x of the elementwise roofline is close to done.
- **Take the BEST of several trivial ops as the reference, and carry a control row.**
  A single elementwise op can sit on its own slow path and silently understate the
  machine — measured on MPS 2026-08-10, `torch.add(x, 1, out=)` gets **211 GB/s** on a
  10 MB fp16 tensor where `copy_` gets **863** and `neg` **828** (the integer scalar drags
  it through a promotion path; `add(x, 1.0)` only recovers to 274). Used as the reference
  it understated the roofline 4x and made GroupNorm score _better_ than theoretically
  possible. So: reference = max over `copy_`/`neg`/`abs`, and always include a control row
  whose correct answer you know in advance (a plain elementwise op, which must land near
  1.0x). **A sub-1.0x roofline ratio is not a fast kernel, it is a broken harness** — and
  without the control row you will read it as good news.
- **Take min-of-repeats, not mean-of-iterations.** Under load the timing distribution has
  a hard floor (the hardware) and an unbounded tail (everything else). The minimum is the
  statistic that reproduces; the mean measures your other browser tabs.

**2. Does it matter — measured hook-free?** Profiler hooks that synchronize per module
destroy CPU/GPU overlap and can inflate a category several-fold (observed: 2.78x on a
loaded box vs 1.15x on an idle one). Prefer the **no-op substitution**: time the real
workload, replace every instance of the op with a passthrough, time again. The difference
is the op's true contribution and sets a hard ceiling on any kernel you could write.

```python
mods = [m for m in net.modules() if isinstance(m, TargetOp)]
saved = [m.forward for m in mods]
for m in mods: m.forward = (lambda x: x)     # shapes preserved, work removed
...time again, restore...
# base - noop == the most an infinitely fast kernel can ever save
```

If that number is small, stop. An infinitely fast kernel saving 3% is not a project.

## Mental model: route, don't switch

`Device::METAL` is bound to the CPU implementation in `src/device_dispatch.h`
(`METAL_DEVICE_CASE` → `constexpr Device D = Device::CPU`). So by default every op already
"works" on Metal data via the CPU kernel over unified memory — correct but not GPU-fast.
You graduate ONE op at a time by adding a **targeted route**: an `if (device == METAL)`
branch that calls a `metal::` entry point and returns, placed BEFORE the generic dispatch.
You never add `Device::METAL` as a real `DEVICE_CASE` (that breaks the link — see
`METAL_BACKEND.md`).

## Steps to graduate an op

1. **Write the MSL kernel** in `src/metal/kernels/kernels_msl.h` (inline raw string). MSL
   supports C++ templates: write a templated `device` function body + concrete `[[kernel]]`
   wrappers per dtype (e.g. `ct2_softmax_float` / `ct2_softmax_half` both calling a shared
   `template <typename T>` impl). This is confirmed working.

2. **Add a `metal::` entry point** — declare in `src/metal/primitives.h`, implement in
   `src/metal/primitives.mm`. Provide fp32 and fp16 overloads. In the encoder, bind buffers
   at indices matching the MSL arg order (from 0). Resolve each StorageView pointer to its
   `(MTLBuffer, offset)` via `buffer_and_offset(ptr)` — this handles sub-views and
   strided-batch operands (the allocator side table is an address-ordered `std::map`).

3. **Route the op** at the `operator()` level in `src/ops/<op>.cc`:

   ```cpp
   #ifdef CT2_WITH_METAL
   #  include "metal/primitives.h"   // or metal/utils.h for synchronize() only
   #endif
   ...
   #ifdef CT2_WITH_METAL
     if (x.device() == Device::METAL && /* supported dtype/shape */) {
       metal::my_op(...);   // a.device() is the REAL device even though the binding makes D=CPU
       return;
     }
   #endif
     // ...generic dispatch follows (unchanged)
   ```

   Route at `operator()` level (not inside `compute`) so it sits before the dispatch that
   throws on fp16 in a non-CUDA build. Partial coverage is fine: route only the common case
   (e.g. LayerNorm routes axis==rank-1 && gamma && beta; general-axis falls through to CPU).

4. **Verify parity** (see below) and check the full suite is still at baseline.

## fp16: two paths

The CPU-reference binding CANNOT do fp16 (CPU has no half compute) — so an fp16 model needs
a real half kernel for every op it touches. Two ways to satisfy a given op:

- **Real half kernel** (preferred for hot/compute ops): add the `_half` MSL wrapper + fp16
  `metal::` overload, route fp16 alongside fp32. Compute in `float`, cast back, so half has
  the same rounding as the fp32 path.

- **Direct-instantiation bypass** (for cold, comparison/copy/RNG-based ops — sampling, etc.):
  call the already-instantiated fp16 CPU `compute` directly, bypassing the throwing dispatch.
  Two requirements:
  1. Instantiate the fp16 CPU path — add `DECLARE_IMPL(float16_t)` in the op's `_cpu.cc`
     (its kernel body must compile for `half`: comparisons, `std::discrete_distribution`
     from half, etc. all work).
  2. **Call `metal::synchronize()` FIRST.** This is the easy-to-miss correctness bug: the
     direct `compute<Device::CPU,...>` call SKIPS the `metal::flush()` that
     `METAL_DEVICE_CASE` performs before every normal CPU-reference op. Without the flush,
     the CPU reads GPU-produced data (e.g. softmax output, prior-op logits) over unified
     memory before the async command buffer has completed → stale/garbage. Pattern:

     ```cpp
     #ifdef CT2_WITH_METAL
       if (device == Device::METAL && dtype == DataType::FLOAT16) {
         metal::synchronize();
         compute<Device::CPU, float16_t>(input, output);
         return;
       }
     #endif
     ```

     (Confirmed: `topk.cc`, `topp_mask.cc`, `multinomial.cc` use exactly this. TopK
     originally omitted the `synchronize()` and survived only on a beam-search timing race —
     fixed 2026-06-09.)

Also flip `mayiuse_float16(Device::METAL)` → true in `src/types.cc` so FLOAT16 resolves on
Metal (AUTO stays CPU-like, so fp16 is explicit opt-in). Output StorageView must be
pre-typed FLOAT16 for the op to write half — caller's responsibility.

## MSL landmines (each cost real debugging)

- **No `erf` in MSL** — any language version, no `precise::erf` either. Exact GELU needs a
  hand-rolled Abramowitz-Stegun 7.1.26 approximation (`ct2_erf`, ~1.5e-7 max error).
- **Library compilation is LAZY** (`ensure_library()` on first `pipeline()` call), NOT eager
  in the MetalContext constructor. Keep it that way: a single kernel that fails to compile
  must not take down device setup / allocation / MPS GEMM (it did, once, when erf broke the
  eager compile and bricked the whole backend including the allocator).
- **Use `1.0f/sqrt(x)`, not `rsqrt(x)`**, in norms — `rsqrt` diverges from the CPU reference
  and breaks bit-for-bit parity.
- **Row-reduction kernels use a fixed 256-thread threadgroup** (tree reduction for max/sum).
  Keep threadgroup sizes a multiple of `threadExecutionWidth` (32 on Apple GPUs).
- **Every referenced buffer must be bound.** If an optional operand (`lengths`, a scalar) is
  absent, bind a dummy buffer at its index anyway, or the dispatch fails.
- **Scalar operands live on the HOST.** For e.g. `MulScalar`, the scalar `b` is CPU memory —
  `buffer_and_offset(b)` will fail. Read it on the host (unified) and pass it to the kernel
  BY VALUE as a uniform; bind the unused operand as the dummy buffer.

## Verification strategy

- **Parity comes free from the existing op suite.** `tests/ops_test.cc` / `layers_test.cc`
  are parameterized over `Device::METAL`, so once an op is routed, its existing fp32 tests
  run on the GPU and compare against the CPU reference automatically.
- **fp16 has no op-suite coverage** — add an explicit parity test in `tests/metal_test.cc`
  (`Float16<Op>MatchesFloat32`, tolerance ~2e-2), following the existing ones. For RNG ops
  (Multinomial) exact parity is meaningless — assert runs-without-throw + valid output
  instead. fp16 mask/sentinel values must be representable (a large-negative mask saturates
  to fp16 -inf; use 0 in a TopPMask parity test).
- **Full-suite baseline:** all pass except the pre-existing `Conv1DGroupNoBiasQuantized`
  CPU int8 failure (MKL-less build artifact, not Metal). Confirm the count went UP by your
  new tests and the only failure is that known one.

## What is NOT worth a GPU kernel

Sampling (TopK/TopPMask/Multinomial) runs once per token on a vocab-sized vector — not a
bottleneck, selection/sort/RNG-heavy. Leave it on the CPU reference; only close the fp16
dispatch gap via the bypass above. Conv1D and concat/split are also fine on the reference
for the tiny model (concat was graduated to GPU for KV-cache residency but did NOT move the
e2e needle). See the perf graveyard in `SKILL.md` / `METAL_BENCHMARKS.md` before optimizing.

### Worked example: image-gen (PyTorch MPS) — the GroupNorm kernel that wasn't written

2026-08-10, M4 Max / macOS 26.5.2. A well-measured plan to write a fused Metal GroupNorm,
cancelled by Step Zero in under an hour.

- **The premise** (recorded against torch 2.12.1): MPS GroupNorm ran at 1.9 GB/s on a
  10 MB tensor, lost 3.2x to a naive multi-pass Python reimplementation, and was 31% of an
  SD 1.5 UNet step. Upstream issue #28201 diagnosed exactly this pathology in 2019 and
  shipped a fused kernel for CPU and CUDA; Metal never got it. Genuinely good analysis.
- **Check 1 killed it.** torch 2.13 ships `ATen/native/mps/kernels/GroupNorm.h`
  ("blocks of 4 elements at a time in unrolled loops"). Measured against in-run GELU:
  2.12.1 sits **8-18x** off the 2-reads-1-write roofline and is pinned at ~30 GB/s at every
  shape; 2.13 is **1.2-1.9x** off, at 84-492 GB/s. The naive Python that used to win now
  loses to the builtin by 6.3x.
- **Check 2 buried it.** No-op substitution on SDXL 1024px, torch 2.13, 46 GroupNorm
  modules: 1414.1 ms/step normal vs 1422.5 ms/step with GroupNorm removed entirely —
  **-0.6%, i.e. noise.** The ceiling on the entire project was zero.
- **The reproducibility lesson, which is the durable one.** The original 11.34 ms
  measurement re-ran at **1.087 ms** on the same torch and same machine months later; hook
  inflation was 2.78x where it had been 1.15x. Nothing was wrong with the original method
  except that it recorded bare milliseconds. Ratios against an in-run reference reproduced
  fine. **Record ratios, not milliseconds.**
- Sibling negative result: MPP `matmul2d` ties MPS on float GEMM
  (`metal4-tensors-and-mpp.md`). Same shape of lesson — verify the gap still exists before
  building for it.
