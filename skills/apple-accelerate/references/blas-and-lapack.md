---
topic_id: "v2:NKOH"
topic_path: "apple-accelerate/dense-linear"
semantic_id: "8_1kxm84mVCyhuKeB4aZ9wx5jd9V4AAG"
related_ids:
  - "8m1kxju-EV6Cw2MfCrwBpAxTz79UwAAC"
  - "-32KV6078ViqxPMfh7ab2QR3VtZc4AAI"
---
# BLAS & LAPACK — dense linear algebra

Source:

- <https://developer.apple.com/documentation/accelerate/blas> (Swift `BLAS` namespace, threading)
- <https://developer.apple.com/documentation/accelerate/lapack>
- <https://developer.apple.com/documentation/accelerate/veclib> (cblas.h / clapack.h are Apple's impls)
- macOS 13.3+ release notes & `<Accelerate/Accelerate.h>` SDK headers (the `ACCELERATE_NEW_LAPACK` / ILP64 macros — not on the DocC pages)
- Reference standard: <https://www.netlib.org/blas/> , <https://www.netlib.org/lapack/>

## BLAS: the three levels

Apple ships the standard **CBLAS** C interface (`cblas.h`). Symbols are
`cblas_<precision><operation>`, precision ∈ {`s` float, `d` double, `c` complex-float,
`z` complex-double}:

- **Level 1** — vector-vector: `cblas_sdot`, `cblas_saxpy`, `cblas_snrm2`, `cblas_sscal`.
- **Level 2** — matrix-vector: `cblas_sgemv`, `cblas_ssymv`, `cblas_strsv`.
- **Level 3** — matrix-matrix: `cblas_sgemm` (the workhorse), `cblas_ssyrk`, `cblas_strsm`.

CBLAS takes an explicit `CBLAS_ORDER` (`CblasRowMajor` / `CblasColMajor`) as the first
argument, so you are **not** forced into Fortran column-major — pass `CblasRowMajor` and
your C 2D arrays work directly. Transpose flags are `CblasNoTrans` / `CblasTrans` /
`CblasConjTrans`. `sgemm` computes `C = alpha·op(A)·op(B) + beta·C`; leading dimensions
(`lda`/`ldb`/`ldc`) are the _stride between rows/cols in memory_, ≥ the corresponding
matrix dimension.

## LAPACK: solvers & factorizations

Higher-level routines built on BLAS. Named `<precision><matrix-type><operation>`:

- **Linear solve:** `sgesv` (general, LU), `sposv` (symmetric positive-definite, Cholesky).
- **Factorizations:** `sgetrf` (LU) + `sgetrs` (solve with it), `spotrf` (Cholesky),
  `sgeqrf` (QR), `sgesdd`/`sgesvd` (SVD).
- **Eigenproblems:** `ssyev`/`ssyevd` (symmetric), `sgeev` (general).
- **Least squares:** `sgels`, `sgelsd`.

LAPACK is **column-major** (Fortran heritage) and takes arguments by **pointer**
(`&n`, `&lda`) — including the workspace-query idiom where you call once with `lwork = -1`
to have it write the optimal workspace size into `work[0]`, allocate that, and call again.

## The new LAPACK interface — `ACCELERATE_NEW_LAPACK`

This is the sharpest edge in the whole framework. Apple's **legacy** BLAS/LAPACK interface
(`clapack.h`, the old `<Accelerate/…>` symbols) is frozen at an old LAPACK version and is
**deprecated**. The modern interface (LAPACK 3.9.1-compatible, matching the Netlib standard
signatures) is **opt-in** via preprocessor macros defined _before_ including Accelerate:

```c
#define ACCELERATE_NEW_LAPACK 1     // use the modern LAPACK 3.9.1 interface
#define ACCELERATE_LAPACK_ILP64 1   // OPTIONAL: 64-bit integer dimensions (ILP64)
#include <Accelerate/Accelerate.h>
```

Or as build flags: `-DACCELERATE_NEW_LAPACK=1 -DACCELERATE_LAPACK_ILP64=1`.

- **LP64** (default) — 32-bit `int` matrix dimensions. Fine below ~2.1-billion-element limits.
- **ILP64** — 64-bit integer dimensions, for very large matrices. Selecting it changes the
  integer type in every signature; you cannot mix ILP64 and LP64 object files.
- On recent SDKs the **new interface is on by default for Swift** and for the Swift `BLAS`/
  LAPACK overlays; the macros matter mostly for C/Obj-C/Fortran call sites.

## Swift overlay

The `BLAS` Swift `struct` is currently a thin namespace exposing the **threading model**
(`BLAS.threadingModel`, `BLASSetThreading(_:)`, `BLASGetThreading()`,
`BLAS.ThreadingModel`), not typed gemm wrappers — for actual gemm/solve in Swift you still
call the `cblas_*` / LAPACK C symbols (import Accelerate makes them visible) or use `simd`
for tiny fixed matrices. `BLAS.threadingModel` controls BLAS **and** LAPACK threading.

## Gotchas

- **CBLAS lets you pick row-major; raw LAPACK does not.** `cblas_*` has a `CBLAS_ORDER`
  arg — use `CblasRowMajor` and skip transposes. Bare LAPACK (`sgesv`) is column-major,
  full stop; feed it column-major or transpose first, or the result is silently wrong.
- **The `ACCELERATE_NEW_LAPACK` macro must be set before the include**, and consistently
  across your whole build. Half your objects on the legacy interface and half on the new
  one is a link-time / silent-ABI-mismatch trap.
- **ILP64 is all-or-nothing.** One ILP64 translation unit calling an LP64-compiled library
  passes 64-bit ints where 32 are expected → garbage dimensions → heap corruption. Don't mix.
- **The legacy interface is deprecated, not gone.** Old code keeps compiling with warnings;
  new code should define `ACCELERATE_NEW_LAPACK=1`. Don't cargo-cult old sample code that
  omits it.
- **Workspace queries (`lwork = -1`) are mandatory for the sizing-sensitive routines**
  (`sgeqrf`, `sgesdd`, eigen). Guessing `lwork` under the optimum silently kills performance
  or overflows; over-guessing wastes memory. Query, allocate, call.
- **Leading dimension ≠ matrix dimension** when a matrix is a sub-block of a larger buffer.
  `ldc` is the memory stride, not `n`. Passing `n` for a strided view corrupts neighbors.

### See also

- [[simd-vectors-and-matrices]] — for 2×2…4×4 matrices, use `simd` (`matrix_multiply`,
  `simd_inverse`), NOT BLAS; the fixed-size path has zero call overhead.
- [[sparse-solvers]] — when the matrix is mostly zeros, dense LAPACK is the wrong tool.
