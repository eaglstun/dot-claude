---
topic_id: "v2:NHNF"
topic_path: "apple-accelerate/cpu-neural"
semantic_id: "9qtYzd8uCRK2ymeWLe0J7wRf354MoAAB"
related_ids:
  - "8m1kxju-EV6Cw2MfCrwBpAxTz79UwAAC"
  - "xp186_06aFwjzea2q30gL4TEm4wEMAAF"
---
# simd — small vectors, matrices & quaternions

Source:

- https://developer.apple.com/documentation/simd (the `simd` module)
- https://developer.apple.com/documentation/accelerate/simd-library
- Header: `<simd/simd.h>` (C/Obj-C/Metal) — bridged to Swift as the `simd` module

The `simd` library is for **small, fixed-size** vectors and matrices — the geometry math of
graphics, physics, and ARKit/RealityKit — not big arrays. It maps directly onto CPU SIMD
registers, so operations are effectively free (no call overhead, no allocation). Crucially,
the **same types are shared with Metal Shading Language**, so a `simd_float4x4` uniform
struct is laid out identically on CPU and GPU.

## Types

- **Vectors:** `simd_floatN` / `simd_doubleN` / `simd_intN` / `simd_uintN` … for N ∈ {2,3,4}
  (and up to 16 for float, 8 for double). Swift spellings: `SIMD2<Float>`, `SIMD3<Float>`,
  `SIMD4<Float>`, or the aliases `simd_float3` etc. Half-precision `simd_half*` exists too.
- **Matrices:** `simd_floatNxM` up to **4×4**, e.g. `simd_float4x4`, `simd_float3x3`. Swift:
  `simd_float4x4` / `matrix_float4x4`. **Column-major** storage (`columns.0…columns.3`).
- **Quaternions:** `simd_quatf` / `simd_quatd` — rotations, `simd_slerp` spherical interp.

## Operations

- **Arithmetic:** overloaded `+ - * /` element-wise on vectors; `*` between matrices and
  matrix×vector is real linear algebra (`matrix_multiply` / the `*` operator).
- **Geometry:** `simd_dot`, `simd_cross`, `simd_length`, `simd_normalize`, `simd_distance`,
  `simd_reflect`, `simd_mix` (lerp), `simd_clamp`.
- **Linear algebra (tiny):** `simd_inverse`, `simd_transpose`, `simd_determinant`,
  `matrix_multiply`. This is the right tool for 2×2…4×4 — **not** BLAS/LAPACK, which have
  per-call overhead that dwarfs a 4×4 multiply.
- **Element math:** `sin`, `cos`, `sqrt`, `rsqrt`, `abs` etc. are overloaded to apply
  lanewise to a whole `simd_float4`.
- **Swizzling (Swift):** `v.xyz`, `v.xy`, `v[.init(0,2,1,3)]`.

## Interop

- **With Metal:** declare shared structs in a bridging header using `simd_float4x4` /
  `packed_float3`; the CPU and shader see the same bytes. Beware `simd_float3` is **16-byte
  aligned** (padded like a float4) — for tightly-packed vertex data use `packed_float3`.
- **With SceneKit/ARKit/RealityKit:** these APIs expose `simd_float4x4` transforms directly
  (`node.simdTransform`, `anchor.transform`).

## Gotchas

- **Column-major.** `simd_float4x4` is column-major, so `m.columns.3` is the translation
  column of a standard TRS matrix. Building matrices row-by-row (mentally transposed) is the
  classic "my object teleports/mirrors" bug — and it must match your MSL side.
- **`simd_float3` is padded to 16 bytes.** A `SIMD3<Float>` occupies the space of a float4.
  An array of them is _not_ tightly packed — for GPU vertex buffers or file formats use
  `packed_float3`/`MTLPackedFloat3`, or you'll read every 4th value as garbage.
- **Multiplication order is math order, not left-to-right intuition.** `proj * view * model`
  applied to a column vector `M*v`. Reverse it and the transform stack is inverted.
- **Not for large data.** `simd` tops out at 4×4 / 16-lane. A 1000-element dot product is
  [[vdsp-signal-processing]] (`vDSP.dot`); a big matmul is [[blas-and-lapack]]. Using simd in
  a scalar loop over a huge array just reimplements the slow path.
- **Quaternions must be normalized** before use as rotations; `simd_slerp` on unnormalized
  quats drifts. Renormalize after accumulation.

### See also

- [[blas-and-lapack]] — the moment a matrix exceeds 4×4 or a vector op runs over a long
  array, cross over to BLAS; simd's zero-overhead advantage only holds at fixed small sizes.
