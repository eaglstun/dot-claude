---
topic_id: "v2:HJBM"
topic_path: "mixed"
semantic_id: "g9EnQhMLFvAdNhZuJizE7faaqzouUAAE"
related_ids:
  - "S05HSldIThUYdhlyoOTexxM8Q7ymUAAJ"
  - "wt8NLD84RaELFl7-JW-KQQXa6xaVQAAN"
---
# Residual connections

**Residual connections** (also called **skip connections**) are a wiring trick that lets you
stack a neural network very deep without the signal falling apart on the way through. The idea
is almost embarrassingly simple: instead of making each layer rebuild its output from scratch,
you let the layer's _input_ skip past it and get added back onto its output. So the layer only
has to learn the **change** (the "residual") rather than reproduce everything that was already
there and then some.

Picture an edit getting passed down a long row of desks. Without a skip connection, each desk
has to redraw the entire picture from memory before handing it on, and after fifty desks the
thing is unrecognizable. With a skip connection, the original gets passed straight through and
each desk just clips on a sticky note of _what to change_. The signal survives the trip, and so
do the [[gelu]]/[[relu]]-style gradients flowing backward during training: they get a clear
highway straight through the stack instead of fading to nothing in a deep pile of layers (the
vanishing-gradient problem). This is the trick that unlocked very deep networks (ResNet first,
in vision), and every [[transformer]] block is built around it: attention and feed-forward
sublayers are each wrapped in one. Mechanically it's just element-wise addition of two
[[tensor]]s of the same shape (input plus transformed-input), which costs almost nothing.

**See also:** [[transformer]]: every block wraps its sublayers in residual connections;
[[relu]]: residuals and good activations together solved the vanishing-gradient problem that
once capped network depth; [[tensor]]: a residual connection is element-wise addition of two
same-shaped tensors.
