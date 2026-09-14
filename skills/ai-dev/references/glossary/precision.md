---
topic_id: "v2:HGAD"
topic_path: "mixed"
semantic_id: "ygM9ZUYWTzhARCTe_nSQs1PSBwv1QAAP"
related_ids:
  - "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
  - "718sDU7GXzjMVg1OzHwc5eWBpT7mIAAG"
---
# Floating-point precision

**Precision** is how many bits you spend storing each number in a model. The default for
training is **fp32** (32-bit floating point, "full" or "single" precision); the common
inference-time halving is **fp16** (16-bit, "half" precision); and its cousin **bf16**
(bfloat16) keeps fp32's full dynamic range while using 16 bits, by spending its bits on
exponent rather than mantissa. All three are _floating point_: a sign bit, an exponent, and a
mantissa: the same number system, just carrying more or fewer significant digits and range.
Dropping fp32 to fp16 roughly halves a model's footprint (the thing an [[rss-sampler]] watches)
and, on hardware with native half-precision units, often runs faster too, for very little
accuracy loss at inference time. That's why "use fp16" is the cheap first move when a run won't
fit.

Here's the part people blur together: **going fp32 to fp16 is not quantizing.** Quantization
throws out the floating-point system _for storage_ entirely. It takes the continuous range of
weight values, slices it into a small set of buckets, and stores each weight as a low-bit
_integer_ index (int8, int4, sometimes lower) alongside a shared scale factor (and sometimes
a zero-point) per block that maps those integers back to approximate floats at compute time.
That's the machinery behind [[gguf]]'s `Q4_K_M`-style formats: 4 bits per weight is roughly an
8x shrink over fp32, not 2x. But it's lossier, and it's a genuine _encoding_ rather than just
fewer digits, which is why quantized formats come with calibration choices, per-block scales,
and the habit of leaving a few sensitive layers in higher precision.

So the mental model: **precision (fp32/fp16/bf16) is the same ruler with coarser tick marks;
quantization is throwing away the ruler and sorting everything into a handful of labeled bins.**
Both shrink the [[parameters]] and the memory bill, both cost some accuracy, but fp16 is the
nearly-free 2x that keeps the float math intact and the hardware happy, while [[quantization]] is
the aggressive 4-8x that swaps float storage for an integer lookup table. One is turning down
the resolution; the other is changing the medium.

**See also:** [[quantization]], the other move, in full: buckets, per-block scales, and what the
shrink costs you; [[gguf]], where integer quantization actually ships; [[parameters]], the
weights being stored at whatever precision; [[rss-sampler]], how you measure the footprint each
choice buys; [[tensor]], the arrays whose dtype this all describes; [[epsilon-gate]], why the
same math landing on different last digits across machines can silently trip a hardcoded threshold.
