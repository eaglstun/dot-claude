---
topic_id: "v2:NCCI"
topic_path: "apple-accelerate/vector-math"
semantic_id: "2r0NQtMtUhCqaTuFKuiN3n7-Sz_DwAAH"
related_ids:
  - "--0lTj89Q9OCaLOHo46M8mo2H04CkAAH"
  - "2m9Jg7YZA5rQauuEzrQdN34HGhXEgAAF"
---
# vDSP — signal processing, FFT, vector arithmetic

Source:

- https://developer.apple.com/documentation/accelerate/vdsp (Swift `vDSP` namespace)
- https://developer.apple.com/documentation/accelerate/vdsp-library (C `vDSP_*` functions)
- https://developer.apple.com/documentation/accelerate/fast_fourier_transforms
- https://developer.apple.com/documentation/accelerate/dspsplitcomplex

vDSP is the digital-signal-processing engine: FFT/DFT/DCT, convolution & correlation,
biquad filtering, windowing, ramps, statistics, type conversion, and a large library of
element-wise vector/matrix arithmetic. Two faces:

- **C:** `vDSP_*` (single precision) and `vDSP_*D` (double). e.g. `vDSP_vadd`, `vDSP_dotpr`,
  `vDSP_fft_zrip`. Every function takes explicit **strides** (usually `1`) and a **length**.
- **Swift:** the `vDSP` enum — `vDSP.add`, `vDSP.multiply`, `vDSP.convolve`, `vDSP.FFT`,
  `vDSP.DCT`, `vDSP.Biquad`, `vDSP.window(ofType:count:)`. Generic over `Float`/`Double`,
  works on any `AccelerateBuffer`/`AccelerateMutableBuffer` (arrays, slices, pointers).

## FFT

Modern Swift path — build a reusable setup object once, run it many times:

```swift
let log2n = vDSP_Length(log2(Float(n)))
let fft = vDSP.FFT(log2n: log2n, radix: .radix2, ofType: DSPSplitComplex.self)!
fft.forward(input: inputSplitComplex, output: &outputSplitComplex)
```

C path: `vDSP_create_fftsetup(log2n, kFFTRadix2)` once (expensive — cache it),
then `vDSP_fft_zrip` (real→complex, in-place) / `vDSP_fft_zip` (complex-complex) per call,
then `vDSP_destroy_fftsetup` at teardown.

**Split-complex layout.** vDSP does not use interleaved `[re, im, re, im, …]`; it uses
`DSPSplitComplex { realp, imagp }` — two separate arrays. Convert interleaved audio into
split-complex with `vDSP_ctoz` before an FFT and back with `vDSP_ztoc`. A real→complex
`zrip` FFT packs `N` real inputs into `N/2` complex outputs, with DC in `realp[0]` and
Nyquist smuggled into `imagp[0]` — a classic source of off-by-one magnitude bugs.

Setup size is chosen for the **largest** transform you'll run; you can run any smaller
power-of-two length with the same setup. `n` must be a power of two for the radix-2 FFT;
use the DFT (`vDSP.DiscreteFourierTransform` / `vDSP_DFT_zop_CreateSetup`) for other sizes.

## Vector arithmetic (the bread and butter)

`vDSP.add/subtract/multiply/divide`, fused `vDSP.add(multiplication:_:)` (a·b+c),
`vDSP.dot`, `vDSP.sum`, `vDSP.mean`, `vDSP.rootMeanSquare`, `vDSP.maximum`, running
`vDSP.slidingWindowSum`, `vDSP.clip`/`threshold`/`limit`, `vDSP.ramp`, `vDSP.reverse`,
`vDSP.sort`. Element-wise ops are where vDSP quietly beats a hand-written loop by a lot on
long arrays.

## Filtering, windowing, conversion

- **Biquad IIR:** `vDSP.Biquad` (Swift) / `vDSP_biquad` — cascaded second-order sections,
  the standard building block for EQ/lowpass/highpass. Keep the delay state between calls.
- **Windows:** `vDSP.window(ofType: .hanningNormalized, count: n, isHalfWindow: false)` —
  Hann/Hamming/Blackman; multiply your frame before FFT to cut spectral leakage.
- **Type conversion:** `vDSP.convertElements`, `vDSP.floatToDouble`, `vDSP.floatToInteger`,
  and the fast `float16`↔`float` pair — much faster than per-element casts.
- **Convolution/correlation:** `vDSP.convolve` (1D and 3×3/5×5 2D kernels), `vDSP.correlate`.

## Gotchas

- **Split-complex, not interleaved.** The #1 vDSP bug: feeding an interleaved `[re,im,…]`
  buffer straight into an FFT. Convert with `vDSP_ctoz`/`vDSP_ztoc` (or hand vDSP a
  `DSPSplitComplex` with separate `realp`/`imagp`).
- **Cache the FFT setup.** `vDSP_create_fftsetup` / `vDSP.FFT(...)` allocates and precomputes
  twiddles — build it once and reuse. Creating one per frame in an audio callback tanks
  performance and may allocate on the realtime thread (forbidden).
- **The real-FFT Nyquist packing.** After `vDSP_fft_zrip`, `imagp[0]` is the Nyquist bin,
  not the imaginary part of DC. And Apple's real FFT returns results scaled by 2 — you
  typically multiply by `0.5` (or `1/n`) to get true magnitudes. Read the scaling notes.
- **Everything takes a stride.** The C API's stride arg is almost always `1`; passing `0`
  or a wrong stride reads the same element repeatedly or strides off the end. The Swift
  overlay hides this for whole buffers but exposes it for strided views.
- **Lengths are `vDSP_Length` (unsigned).** Passing a negative/`-1` int wraps to a giant
  length and walks off the array.
- **Don't reach for a 2×2 FFT-of-a-matrix.** vDSP is for long signals; tiny fixed math is
  [[simd-vectors-and-matrices]]'s job.

### See also

- [[vforce-and-veclib]] — vForce for `exp`/`log`/`sin` over the same arrays; vDSP does the
  arithmetic, vForce the transcendentals.
- [[vimage]] — 2D convolution on _images_ (with edge modes) is vImage's territory, not vDSP's.
