---
name: apple-accelerate
description: Apple Accelerate reference for BLAS/LAPACK, vDSP, vForce, simd, BNNS, Sparse Solvers, vImage, and Quadrature. Use when writing or debugging Accelerate code on Apple platforms, or choosing between Accelerate CPU work and Metal/MPS/Core ML.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: 8m1kxju-EV6Cw2MfCrwBpAxTz79UwAAC
  related_ids: '["8_1kxm84mVCyhuKeB4aZ9wx5jd9V4AAG","9qtYzd8uCRK2ymeWLe0J7wRf354MoAAB"]'
  topic_id: v2:NKJH
  topic_path: apple-accelerate/dense-linear
---

# Apple Accelerate reference

Condensed, source-cited notes grounded in Apple's developer documentation. Each page cites
its source URLs at the top and ends with a **Gotchas** section of the sharp edges that
memory gets wrong (split-complex FFT layout, column-major LAPACK, the `rowBytes` stride,
the `ACCELERATE_NEW_LAPACK` macro, pointer lifetimes at the C boundary).

This is a standalone framework shelf, not tied to one repo. A project's own CLAUDE.md and
existing conventions override anything here. Accelerate is **CPU** math — for GPU compute
see the `apple-silicon` (Metal) skill; for on-device ML across CPU/GPU/ANE, Core ML is the
higher-level front door.

## References — load on demand

Detail lives in `references/`. One pointer per page:

- **[overview.md](references/overview.md)**
  - The module map (BLAS/LAPACK/vDSP/vForce/simd/BNNS/Sparse/vImage/Quadrature), one-framework
    linking (`-framework Accelerate`, `import Accelerate`), C-ABI vs Swift-overlay split, and
    the CPU-vs-GPU-vs-ANE tool choice. _Read first, or when unsure which module owns a task._

- **[blas-and-lapack.md](references/blas-and-lapack.md)**
  - CBLAS levels 1–3 (`cblas_sgemm`), LAPACK solvers/factorizations (LU/QR/Cholesky/SVD/eig),
    row-major CBLAS vs column-major LAPACK, and the **`ACCELERATE_NEW_LAPACK` / ILP64**
    migration. _Read before any dense linear algebra or a gemm/solve._

- **[vdsp-signal-processing.md](references/vdsp-signal-processing.md)**
  - FFT/DFT/DCT (cache the setup!), split-complex `DSPSplitComplex` layout, convolution,
    biquad filters, windowing, and the big element-wise vector-arithmetic library.
    _Read for FFTs, filtering, or fast array arithmetic._

- **[vforce-and-veclib.md](references/vforce-and-veclib.md)**
  - vForce `vv*` transcendentals over whole arrays (`vvexpf`/`vvlog`/`vvsin`, count-by-pointer,
    the `f`=Float/no-`f`=Double naming), and the vecLib umbrella (vBasicOps/vfp/vBigNum).
    _Read for exp/log/trig over arrays._

- **[simd-vectors-and-matrices.md](references/simd-vectors-and-matrices.md)**
  - `<simd/simd.h>` fixed-size vectors/matrices (≤4×4)/quaternions, column-major layout, the
    `simd_float3`-pads-to-16-bytes trap, and Metal/ARKit interop. _Read for geometry/graphics
    math or any 2×2…4×4 matrix — NOT big arrays (that's BLAS/vDSP)._

- **[bnns-neural-networks.md](references/bnns-neural-networks.md)**
  - CPU neural nets: **BNNSGraph** (modern) vs the deprecated per-layer `BNNS.*Layer` API,
    tensors/descriptors, int8/fp16 inference, and BNNS-vs-Core-ML-vs-MPS. _Read before any
    BNNS work or CPU on-device inference._

- **[sparse-solvers.md](references/sparse-solvers.md)**
  - Sparse BLAS + direct/iterative sparse solvers (Cholesky/LDLT/QR, CG/GMRES), CSC format,
    `sparse_commit`, reuse-the-factorization. _Read when the matrix is mostly zeros._

- **[vimage.md](references/vimage.md)**
  - Image processing: the `vImage_Buffer`/`rowBytes` model, convolution & morphology (edge
    flags!), resampling, format/colorspace conversion, histogram/tone, premultiplied alpha,
    Core Video interop. _Read for any pixel-level image work._

- **[quadrature.md](references/quadrature.md)**
  - Numerical definite integration: the batched `x → y` callback, QNG/QAGS/QAG integrators,
    tolerances & status. _Read when integrating a function numerically._

- **[swift-vs-c-usage.md](references/swift-vs-c-usage.md)**
  - The cross-cutting contract: Swift overlays vs C symbols, `withUnsafe*` pointer-lifetime
    rules, precision-suffix decoders, amortizing setup objects, realtime-thread & threading
    discipline. _Read at the C boundary or when a call returns plausible garbage._

## Conventions for this skill

- Each reference cites its Apple **source URLs** at the top; prefer the un-versioned
  `developer.apple.com/documentation/accelerate/...` doc URLs so links don't rot with OS
  releases. The human doc pages are JS SPAs — to re-verify a page, fetch its DocC JSON:
  `https://developer.apple.com/tutorials/data/documentation/accelerate/<path>.json`.
- Keep SKILL.md lean: one/two-line pointers only. Detail lives on the shelf.
- To add a topic: write `references/<topic>.md` in the same format
  (Source block up top, a `### Gotchas` section at the end, `### See also` crosslinks as
  `[[file]]`), then add a pointer above. Facts come from the docs, not memory — the whole
  point of the skill.
