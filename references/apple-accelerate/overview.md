---
topic_id: "v2:NIKF"
topic_path: "apple-accelerate/sparse-solvers"
semantic_id: "_-bsBuV9l9rySMOYA7aN4ChjXm7U8AAI"
related_ids:
  - "9-_ohzE9PdqiUeOKQqwBOA5m3ldc4AAM"
  - "_u-ph617kVLoE8ckwq61QYhHXlcRYAAI"
---
# Accelerate — framework overview & linking

Source:

- <https://developer.apple.com/documentation/accelerate> (framework landing)
- <https://developer.apple.com/documentation/accelerate/veclib> (vecLib umbrella)
- <https://developer.apple.com/documentation/accelerate/blas> (BLAS namespace + threading)

Accelerate is Apple's CPU vectorized-math umbrella framework: hand-tuned, energy-aware
implementations that dispatch to the best SIMD path (NEON/AMX) for the running Apple
silicon or Intel chip. It is **CPU-side** — for GPU compute reach for Metal / MPS, and
for on-device ML the high-level path is Core ML / MPSGraph. Accelerate is the right tool
when you have arrays of numbers and want them crunched fast without writing SIMD by hand.

## The sub-frameworks

One `#include <Accelerate/Accelerate.h>` (C/Obj-C) or `import Accelerate` (Swift) pulls
in all of them. There is one framework to link: `-framework Accelerate`.

| Module               | What it is                                                                                                       | Reference page                |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **BLAS**             | Basic Linear Algebra Subprograms — dot/gemv/gemm dense linear algebra                                            | [[blas-and-lapack]]           |
| **LAPACK**           | Solvers, factorizations (LU/QR/Cholesky/SVD), eigenvalues                                                        | [[blas-and-lapack]]           |
| **vDSP**             | 1D/2D FFT, convolution/correlation, biquad filters, vector & matrix arithmetic, windowing, type conversion       | [[vdsp-signal-processing]]    |
| **vForce**           | Transcendental math over whole arrays (`vvexp`, `vvlog`, `vvsin`, …)                                             | [[vforce-and-veclib]]         |
| **vecLib**           | The umbrella containing BLAS/LAPACK/vDSP/vForce plus `vBasicOps`, `vfp`, `vBigNum`, `vectorOps`                  | [[vforce-and-veclib]]         |
| **simd**             | Small fixed-size vectors/matrices/quaternions (`simd_float4`, `simd_float4x4`, `simd_quatf`) via `<simd/simd.h>` | [[simd-vectors-and-matrices]] |
| **BNNS / BNNSGraph** | Basic Neural Network Subroutines — CPU inference/training; BNNSGraph is the modern entry point                   | [[bnns-neural-networks]]      |
| **Sparse Solvers**   | Sparse & dense factorizations/iterative solvers, Sparse BLAS                                                     | [[sparse-solvers]]            |
| **vImage**           | Image processing — convolution/morphology, format & colorspace conversion, resampling, histogram/tone            | [[vimage]]                    |
| **Quadrature**       | Numerical definite integration of a callback function                                                            | [[quadrature]]                |

Also _reachable through_ the Accelerate landing page but separate frameworks: **Compression**,
**Apple Archive**, and **Spatial** (3D primitives). Those are not covered here.

## C ABI vs the Swift overlays

Almost everything here has two faces (see [[swift-vs-c-usage]] for the full story):

- **C ABI** — the original Fortran/C symbols: `cblas_sgemm`, `vDSP_fft_zrip`, `vvexpf`,
  `sparse_matrix_create…`. Callable from C, Obj-C, and Swift. Stable, terse, pointer-heavy.
- **Swift overlays** — typed, safe namespaces layered on top: `vDSP`, `vForce`, `BLAS`,
  `BNNS`, `BNNSGraph`, `Sparse…`. These are Swift `enum`/`struct` namespaces (e.g.
  `vDSP.FFT`, `vForce.exp(_:result:)`, `BLAS.threadingModel`). Prefer these in new Swift.

## Threading

Accelerate manages its own internal threading and generally should **not** be called from
inside your own parallel loop over the same work — you double-book the cores. Threading is
tunable via `BLASSetThreading(_:)` / `BLAS.threadingModel` (single- vs multi-threaded), which
governs BLAS **and** LAPACK.

## Gotchas

- **It's CPU, not GPU.** A large `gemm` on Accelerate is excellent, but for sustained
  large-matrix ML throughput on Apple silicon the GPU (MPSMatrixMultiplication) or the ANE
  (Core ML / BNNSGraph-compiled) often wins. Benchmark; don't assume Accelerate == fastest.
- **One framework, many headers.** Don't hunt for `-lvDSP` or a `vImage.framework`; there
  is only `-framework Accelerate`. The umbrella header pulls every module.
- **Don't nest your threads inside its threads.** Wrapping `cblas_sgemm` in a GCD
  `concurrentPerform` usually _slows down_ — Accelerate already parallelizes internally.
- **`Accelerate` (CPU) ≠ `MetalPerformanceShaders` (GPU) ≠ `Metal Performance Primitives`.**
  Names rhyme; the hardware doesn't. Pick by where the data lives.

### See also

- [[swift-vs-c-usage]] — the C-symbol ↔ Swift-overlay decision and memory/pointer rules that
  apply to every page here.
