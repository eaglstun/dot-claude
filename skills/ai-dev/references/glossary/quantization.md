---
topic_id: "v2:IGBC"
semantic_id: "718sDU7GXzjMVg1OzHwc5eWBpT7mIAAG"
related_ids:
  - "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
  - "KlN6zMhjHzNkdw-PxWQYrKaQqpnnoAAN"
---
# Quantization

**Quantization** is storing each of a model's weights as a small integer instead of a
float. You take the continuous spread of values in a chunk of a [[tensor]], slice that
range into a handful of buckets, and write down only which bucket each weight fell into,
plus one shared **scale** (and often a **zero-point**) that maps the bucket numbers back
to approximate floats when it's time to do the math. Four bits per weight means sixteen
buckets. That's an 8x shrink over fp32, which is the whole reason a model with 70 billion
[[parameters]] can sit on a laptop instead of a rack.

This is a different move from dropping fp32 to fp16. That one keeps the floating-point
number system and just carries fewer significant digits: same ruler, coarser ticks (see
[[precision]], which draws the line in detail). Quantization throws the ruler out. The
stored value is no longer a number in any meaningful sense, it's an _index_, a pointer
into a tiny lookup table that gets rebuilt for every block of weights. Closer to saving a
photograph as a 16-color GIF than to rounding it off.

## Why the scale is per-block, and not per-model

The obvious version of this fails, and it fails in an instructive way. Take one scale for
an entire weight matrix and you have to stretch it to cover the largest value in there.
Neural networks are full of **outliers**, a few coefficients hundreds of times larger than
their neighbors, and those outliers hold a lot of the model's behavior. One monster value
sets the scale for everybody, all the ordinary weights get crushed into the bottom two or
three buckets, and the model comes out lobotomized.

So real schemes quantize in **blocks**, usually 32 or 64 weights at a time, each with its
own scale. Now a block containing an outlier can spend its range on that outlier without
flattening a block on the other side of the matrix. This is why the honest cost of "4-bit"
is never exactly 4 bits per weight: you're also paying for a scale per block, and the
K-quant formats go a step further and quantize the _scales_ themselves. Hence the file
names in [[gguf]]. `Q4_K_M` reads as: quantized, 4 bits, K-quant block structure, Medium,
where "medium" means which of the sensitive tensors got left at higher precision.
Attention layers and embeddings frequently get the good silverware while the bulk of the
feed-forward weights eat off paper plates.

## What it actually costs

Not gibberish. That's the thing people brace for and it's not what happens. A well-quantized
model doesn't break, it gets **duller**. It holds up fine on the things it knew cold and
gets vaguer at the edges: the obscure fact, the rare name, the long chain of reasoning where
a small wrongness at step three compounds by step nine. The loss is real and it is
frustratingly hard to see in a demo, which is exactly why "it seems fine to me" is not an
evaluation.

The rough shape of the tradeoff, on today's formats:

- **Q8** is close enough to lossless that measuring the difference is a research project, but it only halves the file, so it's rarely worth the disk.
- **Q4_K_M** is the default for a reason. It's the knee of the curve: 4x-ish smaller, and the damage is small enough that most people never notice it.
- **Below 4 bits**, quality falls off a cliff face rather than a ramp. 3-bit and 2-bit exist, they run, and they will lie to you with total confidence.

And the rule that surprises people: for a fixed memory budget, **a bigger model quantized
harder usually beats a smaller model quantized gently.** A 13B at 4-bit tends to outrun a
7B at 8-bit at the same footprint. Capacity is worth more than fidelity, up to a point.
(Watch the actual number with an [[rss-sampler]] rather than trusting the file size, because
the weights are only part of what lands in RAM.)

## Two ways to do it

**Post-training quantization** is the common one: take a finished model and squash it,
usually with a small **calibration** set run through it to see which activation ranges
actually occur, so the buckets get placed where the values really live instead of where
they theoretically could. This is what the `.gguf` files you download have had done to them.

**Quantization-aware training** does it the other way around, simulating the rounding during
training so the model learns weights that survive being squashed. Better results, much more
expensive, so it's mostly for models being shipped to phones. The hybrid worth knowing is
**QLoRA**, which keeps a frozen 4-bit base model in memory and trains a small [[lora]]
adapter at full precision on top of it. That combination is the reason fine-tuning a large
model on one consumer GPU stopped being a joke.

**See also:** [[precision]]: the fp32/fp16/bf16 distinction this is constantly confused with,
and the sharpest statement of the difference; [[gguf]]: where quantization actually ships, and
where those `Q4_K_M` names come from; [[ggml]]: the library that has to implement the math for
every one of these formats; [[parameters]]: the weights being bucketed, and the count that sets
the bill; [[lora]]: QLoRA, fine-tuning on top of a frozen quantized base; [[tensor]]: the arrays
being carved into blocks; [[rss-sampler]]: how you check what the shrink actually bought you.
