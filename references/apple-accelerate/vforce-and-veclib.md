---
topic_id: "v2:NCHM"
topic_path: "apple-accelerate/vector-math"
semantic_id: "2m9Jg7YZA5rQauuEzrQdN34HGhXEgAAF"
related_ids:
  - "tk7RAPZ_0drq5HO2TqSR8X5bnxZEcAAD"
  - "9-_ohzE9PdqiUeOKQqwBOA5m3ldc4AAM"
---
# vForce & vecLib — transcendental math over arrays

Source:

- https://developer.apple.com/documentation/accelerate/vforce (Swift `vForce` namespace)
- https://developer.apple.com/documentation/accelerate/vforce-library (C `vv*` functions)
- https://developer.apple.com/documentation/accelerate/veclib (the vecLib umbrella)

## vForce

vForce applies `<math.h>`-style functions to **whole arrays** at once, far faster than a
scalar loop. C symbols are the `vv*` family; every function takes **pointers + a count
pointer** and processes `*count` elements:

```c
int n = 1024;
vvexpf(out, in, &n);     // out[i] = expf(in[i]) for i in 0..<n   (Float)
vvlog(outD, inD, &nl);   // Double variant: vvlog / vvexp / vvsin …
```

Naming: single-precision functions end in `f` (`vvexpf`, `vvsinf`, `vvsqrtf`); the
double-precision names drop it (`vvexp`, `vvsin`, `vvsqrt`). Note the **count is passed by
pointer** (`&n`), a Fortran-ism that trips up first-timers.

Swift overlay — the `vForce` enum, generic and buffer-based:

```swift
vForce.exp(input, result: &output)
let s = vForce.sin(anglesArray)          // returns [Float]
vForce.sincos(x, sinResult: &s, cosResult: &c)
```

### Function families

- **Trig:** `sin cos tan asin acos atan atan2`, plus `sinPi/cosPi/tanPi` (compute of π·x).
- **Hyperbolic:** `sinh cosh tanh asinh acosh atanh`.
- **Exp/log:** `exp exp2 expm1 log log1p log2 log10 logb`.
- **Power/root:** `pow sqrt rsqrt (1/√x) reciprocal`.
- **Rounding:** `ceil floor trunc nearestInteger (rint)`.
- **Misc:** `copysign remainder truncatingRemainder`.

## vecLib (the umbrella)

vForce lives under **vecLib**, the historical umbrella that also contains BLAS, LAPACK,
vDSP and these lower-level 128-bit-vector libraries (rarely needed directly, but good to
recognize):

- **vBasicOps** — basic arithmetic/logical ops on 128-bit vectors.
- **vfp** — floating-point / transcendental / trig on 128-bit vectors.
- **vectorOps** — vector & matrix BLAS-style ops on arrays of 128-bit vectors.
- **vBigNum** — arithmetic on large (128/256/512/1024-bit) integers.

For almost all modern work you want **vForce** (any-length arrays) or **simd**
(fixed small vectors), not the raw 128-bit-vector libraries.

## Gotchas

- **Count is a pointer.** `vvexpf(out, in, &n)` — forgetting the `&` (or passing a literal)
  won't compile in C but the mistake surfaces when porting from `expf` habits. The Swift
  overlay hides this.
- **`f`-suffix = Float, no suffix = Double.** `vvexp` is _double_; `vvexpf` is _float_.
  Mixing a Float buffer into `vvexp` reads twice the bytes and returns garbage. Easy to
  fumble because it's the opposite of the libm convention people half-remember.
- **vForce trades a few ULPs for speed.** These are fast approximations, not
  correctly-rounded libm. Great for signals/graphics/ML; if you need bit-exact IEEE results
  (financial/reproducibility), call scalar `libm` or check tolerances.
- **In-place is allowed but aliasing rules apply.** `out == in` is fine for the elementwise
  functions; _partial_ overlap (shifted pointers into the same buffer) is not — results are
  undefined.
- **Don't loop it yourself.** Calling `vvexpf` per element in a loop defeats the entire
  point; hand it the whole array once.

### See also

- [[vdsp-signal-processing]] — vDSP does the +/−/×/÷ and reductions; vForce does the
  transcendentals. They compose on the same buffers.
- [[simd-vectors-and-matrices]] — for a single `simd_float4` of angles, `simd` has inline
  `sin`/`cos`; vForce only pays off across long arrays.
