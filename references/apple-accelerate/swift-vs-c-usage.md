---
topic_id: "v2:NCPF"
topic_path: "apple-accelerate/vector-math"
semantic_id: "_u-ph617kVLoE8ckwq61QYhHXlcRYAAI"
related_ids:
  - "9-_ohzE9PdqiUeOKQqwBOA5m3ldc4AAM"
  - "_-bsBuV9l9rySMOYA7aN4ChjXm7U8AAI"
---
# Swift overlays vs the C ABI — calling Accelerate safely

Source:

- https://developer.apple.com/documentation/accelerate (the Swift overlays: `vDSP`, `vForce`, `BLAS`, `BNNS`, `Sparse…`)
- https://developer.apple.com/documentation/accelerate/using_accelerate_and_simd
- https://developer.apple.com/documentation/swift/using-imported-c-functions-in-swift (pointer/withUnsafe rules)

Every Accelerate module has two faces. Picking the right one — and getting the memory rules
right at the boundary — is most of what goes wrong for newcomers.

## Which face to use

- **New Swift code → the Swift overlay** where one exists: `vDSP.*`, `vForce.*`, `BLAS.*`,
  `BNNS`/`BNNSGraph`, `Sparse…`, `vImage.PixelBuffer`, `simd`. They're typed, generic over
  `Float`/`Double`, take `AccelerateBuffer`/collections instead of raw pointers, manage
  lengths/strides for you, and are much harder to misuse.
- **C / Obj-C, or a routine with no overlay → the C ABI:** `cblas_*`, LAPACK (`sgesv`…),
  `vDSP_*`, `vv*` (vForce), `sparse_*`, `vImage*_*`, `quadrature_integrate`. Also the fallback
  in Swift when the overlay doesn't cover what you need (e.g. an exotic LAPACK solve) — the C
  symbols are all visible after `import Accelerate`.

## Memory rules at the C boundary (Swift)

The C functions want raw pointers + counts. From Swift:

- Use `withUnsafeBufferPointer` / `withUnsafeMutableBufferPointer` to hand an array's storage
  to a `vDSP_*` / `cblas_*` call. **Do not** let the pointer escape the closure — it's only
  valid inside.
- Don't pass `&array` for a whole buffer where a base pointer is expected across a length;
  `&array[0]` or the buffer-pointer closure is correct. `&scalar` for genuine scalar-by-ref
  args (LAPACK's `&n`, vForce's `&count`) is fine.
- **Output arrays must be pre-sized.** The C API writes into memory you own; it does not
  allocate. Allocate the result (`[Float](repeating: 0, count: n)`) before the call.
- Prefer the overlays precisely because they encapsulate all of the above.

## Precision & naming decoder

- **BLAS/LAPACK/vDSP:** `s` = Float, `d` = Double, `c`/`z` = complex float/double. `vDSP_vadd`
  (Float) vs `vDSP_vaddD` (Double).
- **vForce:** trailing `f` = Float (`vvexpf`), no `f` = Double (`vvexp`). Opposite feel to the
  BLAS `s`/`d` scheme — easy to cross up.
- **simd:** `simd_float4` etc.; Swift `SIMD4<Float>`.

## Performance & threading discipline

- **Amortize setup objects.** `vDSP.FFT`, `vDSP_create_fftsetup`, `SparseFactor`,
  `BNNSGraph.Context`, DFT setups — create once, reuse across calls. Building them per
  iteration (or per audio callback) is the most common self-inflicted slowdown.
- **No allocation on realtime threads.** In an audio render callback, all Accelerate setup
  objects and result buffers must be pre-allocated; the per-call functions themselves are
  realtime-safe, the _setup_ is not.
- **Don't wrap Accelerate in your own parallel-for.** It parallelizes internally
  (tune via `BLASSetThreading`); nesting GCD around it oversubscribes cores and slows down.
- **Operate on whole arrays.** The entire value proposition is one call over N elements.
  Calling a vDSP/vForce function inside a per-element loop is strictly worse than scalar libm.

## Gotchas

- **Pointer lifetime.** A pointer from `withUnsafeMutableBufferPointer` is dead the instant
  the closure returns — stashing it for a later Accelerate call is a use-after-free that
  "works" until it corrupts. Keep the whole call inside the closure.
- **Length/stride mismatches don't crash, they lie.** Off-by-N lengths or wrong strides read
  adjacent memory and return plausible garbage. The overlays remove most of this risk.
- **Overlay availability varies by OS.** Newer overlay methods have deployment-target floors
  (`@available`); the underlying C symbol is usually older. If an overlay method is unavailable
  on your target, drop to the C symbol.
- **`import Accelerate` gives you everything** — you don't import `vDSP`/`BLAS` separately.
  The module + `-framework Accelerate` link is the whole setup.

### See also

- [[overview]] — the module map and the one-framework linking story.
- Every other page here — this page is the memory/naming contract they all assume.
