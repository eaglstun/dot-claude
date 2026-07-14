---
topic_id: "v2:JPGJ"
topic_path: "ai-concepts/experimental-methods"
semantic_id: "5D40CfdXf_3S3s7e_ZBb8pvRKx5KcAAM"
related_ids:
  - "JLyDFXR566f7isIczYDU2emULCpuQAAM"
  - "vuSYYOfQOrEb5t4BuqFT05nalb7KMAAB"
---
# Dimensions

**Dimensions** are independent axes of variation, each one a separate thing you can change
without affecting the others. A dimension doesn't have to be spatial, or even start out as a
number: **color** can be a dimension, and so can price, temperature, or sweetness, each is
its own independent knob. (To actually compute with them, ML turns each knob into a number, so
a single data point becomes a list of numbers.)

A point on a line takes 1 number to pin down,
on a map 2, in a room 3. In ML a data point is usually a list of hundreds or thousands of
numbers, one per feature: word [[embeddings]] might live in 768 of them, an image in many
thousands.

The number of dimensions of a [[tensor]] is called its _rank_, and the rich
geometry of [[latent-space]] is exactly this idea: meaning encoded as a position in a
high-dimensional space.

**How to imagine more than 3 or 4.** The honest answer: you don't picture it, you stop
trying to _see_ it and start reasoning about it. A few tricks that actually work:

- **It's just a longer list.** A 100-D point isn't a mysterious shape; it's a list of 100
  numbers. "Add a dimension" = "track one more independent number." Most operations
  (distance, dot product, averaging) are just the 2-D/3-D formulas with more terms summed.
- **Reason by analogy, then generalize.** Work out what's true in 2-D and 3-D (a sphere,
  the corners of a cube, the distance between two points) and trust the algebra to carry
  it to N-D, even when the mental picture gives out. Hinton's half-joke captures the spirit:
  "to deal with a 14-dimensional space, visualize a 3-D space and say 'fourteen' to yourself
  very loudly."
- **Expect high-D to be weird.** Intuition built in 3-D actively misleads you up there.
  Almost all of a high-dimensional cube's volume sits in its corners, randomly chosen points
  are nearly all the same distance apart, and volume concentrates near the surface of a
  sphere. This bundle of surprises is the **curse of dimensionality**, and it's why
  reasoning beats visualizing.

**See also:** [[tensor]], whose rank is its number of dimensions; [[latent-space]], the
high-dimensional space where geometry encodes meaning; [[embeddings]], vectors whose length
is a dimension count (e.g. 768-D).
