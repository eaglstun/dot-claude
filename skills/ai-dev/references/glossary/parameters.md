---
topic_id: "v2:JFNF"
topic_path: "ai-concepts/vector-representation"
semantic_id: "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
related_ids:
  - "718sDU7GXzjMVg1OzHwc5eWBpT7mIAAG"
  - "DT66WEb8QXjJDj9MOEwG0nXaY97tUAAB"
---
# Parameters (7B, etc.)

**Parameters** are the learned numbers inside a model: the weights (and biases) that training
adjusts, and that together store everything the model "knows." A label like **7B** means
roughly 7 billion of them; common sizes run 1B, 3B, 7B, 8B, 13B, 70B, on up to the hundreds of
billions for the biggest models. The count is the usual shorthand for how capable, and how
expensive, a model is: more parameters generally means more ability, but also more compute to
train and more memory to run. Those numbers are stored as [[tensor]] weight grids, most of them
in a [[transformer]]'s attention and feed-forward layers.

The figure that matters in practice is **parameters × bytes-per-parameter = memory**. At full
precision each parameter takes 2 bytes, so a 7B model needs about 14 GB just for its weights;
squeezing each one down to 4 bits (see [[gguf]]) cuts that to roughly 3.5 GB, exactly how big
models fit onto consumer hardware. Two distinctions worth keeping straight: _parameters_ (the
model's fixed learned weights) are not _tokens_ (the chunks of text it reads and writes), and
they're not _hyperparameters_ (settings like learning rate or batch size that you pick before
training). And note [[lora]] fine-tunes a model by training a tiny batch of _extra_ parameters
while leaving the billions of original ones frozen.

**See also:** [[tensor]]: what parameters are stored as; [[transformer]]: where most of
them live; [[gguf]]: quantization, which shrinks the bytes-per-parameter; [[lora]]:
parameter-efficient fine-tuning.
