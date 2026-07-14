---
topic_id: "v2:JIOL"
topic_path: "ai-concepts/training-fundamentals"
semantic_id: "v003DB4QaOhOClVYCGsWxUEy0q6msAAJ"
related_ids:
  - "fnwODJ9cb2gNXrBaOGYOx3MS9zaF0AAL"
  - "718sDU7GXzjMVg1OzHwc5eWBpT7mIAAG"
---
# Gradient descent

**Gradient descent** is the basic algorithm that lets a model _learn_, the optimization engine
underneath almost all modern [[machine-learning]]. Training starts with a model that's wrong,
scores _how_ wrong with a **loss** (a single number measuring error), and then asks, for every
one of the model's [[parameters]]: "which way should I nudge this, and how hard, to make the
loss a little smaller?" That whole bundle of directions-and-magnitudes is the **gradient**: the
slope of the loss. Take one small step downhill along it and the model gets slightly less wrong;
repeat millions of times and the error grinds toward a bottom.

The size of each step is the
**learning rate**: too large and the model overshoots and thrashes, too small and training
crawls. In practice you rarely use the whole dataset for each step, _stochastic gradient
descent_ (SGD) estimates the slope from one small batch at a time, and smarter variants like
_Adam_ adapt the step size per parameter as they go.

One thing worth keeping straight: gradient
descent only ever drives the _training_ loss down. Whether the model is genuinely learning
rather than memorizing is what [[val-loss]] is there to catch.

And the machinery doesn't have to
move a model's weights at all: freeze the model and run the same descent over its _input_
instead, and you can search a [[latent-space]] for the point that produces what you want, which
is exactly how GAN-based upscalers hunt for a face that matches a blurry photo.

**See also:** [[machine-learning]]: gradient descent is the optimization engine underneath most
of it; [[parameters]]: the dials gradient descent actually turns; [[val-loss]]: the held-out
check that says when to stop descending; [[latent-space]]: run the same descent over inputs
instead of weights and you're searching this space; [[epsilon-gate]]: the threshold that decides
when one of these descents is allowed to stop.
