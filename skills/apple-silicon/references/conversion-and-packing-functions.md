---
topic_id: "v2:PBOO"
topic_path: "msl-math/msl-types-and-utils"
semantic_id: "5d-8s5m-ehRjzyKEy3F3q57tXImVMAAM"
related_ids:
  - "5J_80_k-eFxgjSawq2VBO5blWYwVMAAH"
  - "9P_804G8-NxijSa0n0VLso70nIwdsAAK"
---
# Conversions, `as_type` reinterpretation, and pack/unpack

Source (Apple): Metal Shading Language Specification, §2.23–2.24 (conversions, `as_type`),
§8.6 (float↔int conversion rules), §6.15 (pack/unpack), §2.21 (packed numeric types,
Metal 4.1) (v4.1, 2026-06-04).
PDF: <https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf>
(The MSL standard-library functions are only in the spec PDF — there is no DocC HTML/JSON
page for them, so this was extracted from the PDF, not the usual DocC-JSON endpoint.)

## Value conversions: `static_cast` / constructor syntax (§2.23, §8.6)

`static_cast<T>(x)` (and the equivalent `T(x)` constructor spelling) converts scalar↔scalar
and vector↔vector "using the default rounding mode with **no saturation**":

| direction             | rounding (§2.23, §8.6)                                        |
| --------------------- | ------------------------------------------------------------- |
| float → integer       | **round toward zero** (truncation)                            |
| float/int → float     | round ties to even                                            |
| float → half / bfloat | ties to even; half↔float and bfloat→float are lossless upward |
| bool → numeric        | false → 0, true → 1                                           |
| float NaN → integer   | **0** (§8.6)                                                  |

§8.6 also notes: "fast math does not change the accuracy of conversion operations."

**The toward-zero trap:** a bare `(char)v` on a positive float drops the fraction — `(char)4.9f
== 4`. Round-to-nearest must be **explicit and precede the cast** (`rint` = ties-to-even, the
match for CPU `nearbyintf`; see `math-functions-and-numeric-parity.md`).

**Out-of-range float → int is NOT saturated.** §2.23 says "no saturation" and §8.6 defines only
the NaN case; nothing promises a clamped result, so treat overflow as undefined (C++ inherits).
The only `convert_*_saturate` spellings in the whole spec are **texture-write conversion rules**
(§8.7.6, e.g. `convert_char_saturate`) — they are not callable stdlib functions in compute code.
To saturate in a kernel, `clamp()` (or `min`/`max`) **before** the cast; integer-side `addsat`/
`madsat` etc. exist for integer arithmetic only (see `integer-functions.md`).

Vector notes (§2.24): implicit vector→vector conversion is a compile error (`float4 f = i4;`
fails); explicit `static_cast`/constructor does componentwise value conversion — `int4(c4)`
**sign-extends** each `char` lane to `int`. Scalar→vector implicitly splats. `bfloat` implicitly
converts only upward to `float`, never to/from `half`.

## Bit reinterpretation: `as_type<T>(x)` (§2.23)

```metal
uint u   = as_type<uint>(1.0f);     // 0x3f800000 — bits unchanged, new type
int  i   = as_type<int>(c4);        // char4 -> one 32-bit lane (same size: OK)
short2 j = as_type<short2>(i);      // int -> short2 (same size: OK)
float4 g = as_type<float4>(h4);     // ERROR: half4 (8B) -> float4 (16B), sizes differ
```

Any non-pointer scalar/vector → same-**size** scalar/vector; bits pass through unmodified, no
argument promotion. Different byte count = compile error. `as_type` operates on **values**;
to reinterpret _memory_ (e.g. read 4 packed int8 as one vector load), cast the address-space
pointer instead — `*(const threadgroup char4*)(&tile[i])` — which is what the int8 kernels do.
Alignment is on you: the compiler "assumes that the object referenced by the pointer is always
appropriately aligned as required by the data type" (§2.5), so a `char4*` load needs a
4-aligned address.

## Pack/unpack functions (§6.15, header `<metal_pack>`)

`unpack_{u,s}norm{4x8,2x16}_to_{float,half}(uint)` and `pack_{float,half}_to_{u,s}norm…` convert
between packed 8/16-bit integers and **normalized** floats ([0,1] / [-1,1] — snorm divides by
127). These are graphics color-data helpers: an snorm unpack of quantized weights would bake in
a 1/127 factor, so the int8 path does **not** use them — it wants raw integer values
(`int4(char4)`), with scales applied separately.

Metal 4.1 adds general packed-numeric templates (§2.21): `pack<Format, rounding_mode,
saturation_mode>(vec<T,N>)` / `unpack<T, Format, N>` over formats including `char` (N = 4, 8)
and `int4b_format` (N = 8, 16), with explicit `rounding_mode` (`to_nearest_even`, `toward_zero`,
…) and `saturation_mode` (`none`, `saturate`, `symmetric_saturate`) — defaults for `char` are
toward_zero + saturate (Table 2.20). This is the spec-level path to int4 packing if the backend
ever goes below 8 bits; not used today.

---

### Worked example: the CTranslate2 Metal backend

- **`ct2_quantize_s8_*`** (`src/metal/kernels/kernels_msl.h`): the quantize store is
  `y[j] = (char)(round_before_cast != 0u ? rint(v) : v)` — `rint` (ties-to-even, matching CPU
  `nearbyintf`/`vrndnq_f32`) runs **before** the cast precisely because the cast itself rounds
  toward zero; the legacy `round_before_cast=false` path _wants_ the C-style truncation.
  The kernel needs **no saturating cast**: `scale = 127/amax(row)` bounds `|v| ≤ 127` by
  construction. If the scheme ever changes (zero-point, clipped amax, per-tensor scale), add an
  explicit `clamp(v, -127.0f, 127.0f)` — the plain `(char)` cast will not saturate for you.
- **`ct2_gemm_s8` / `ct2_gemv_s8`**: the packed-int8 fast path is pointer reinterpretation +
  value conversion — `int4(*(const threadgroup char4*)(&As[kk][tid.y * 4u]))` loads 4 weights
  in one 4-byte access and sign-extends to `int4` for exact int32 MACs. The GEMM tile rows are
  64-byte aligned and `tid.{x,y}*4` keeps the 4-alignment; the GEMV host
  (`gemm_s8` in `src/metal/primitives.mm`) only routes to `ct2_gemv_s8` "when k and the operand
  alignments allow the char4 reinterpretation" — that guard exists because of the §2.5
  alignment assumption above.
- **`ct2_dequantize_s8_*` / `ct2_dequant_gemm_out_*`**: `(float)char` and `(float)int` widenings
  are exact (every int8/int32-in-range value is representable in float up to 2^24), and the
  final `(T)` store to `half` rounds ties-to-even — same rounding the fp32→fp16 CPU path uses,
  which is what keeps the int8_float16 parity tests honest.
- Byte-level kernels (`ct2_strided_copy_bytes`, `ct2_gather_bytes`) sidestep conversion
  entirely by copying `uchar` — the type-agnostic alternative when bits must move unmodified.
