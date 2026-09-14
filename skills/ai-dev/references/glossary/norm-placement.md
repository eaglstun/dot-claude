---
topic_id: "v2:JLHI"
topic_path: "ai-concepts"
semantic_id: "R5AkSF6BDEVZH37nrGgPxaWi4D-CAAAL"
related_ids:
  - "BhKCyZ-lDGAdE9-vPWAp7bGi5L2DAAAL"
  - "BxLjwoyEDOFYD_fvHWBrvb2i5CsDwAAB"
---
# Norm placement

**Norm placement** is the question of _where_ you put the normalization step inside a
[[transformer]] block, and it sounds like a plumbing detail until you realize it's the
difference between a model that trains and one that quietly falls apart. Normalization
(usually **LayerNorm**) is the leveling stage that re-centers and re-scales the numbers
flowing through the network so they don't blow up to infinity or shrink to nothing as they
pass through layer after layer. Every block has two moving parts wrapped in
[[residual-connections]]: the attention sublayer and the feed-forward sublayer, and norm
placement is just: do you level the signal _before_ each part, _after_ it, or _both_?

Picture a long chain of guitar pedals with a leveling box that keeps the signal from
clipping or fading. **Post-norm** (the original 2017 setup) puts the leveler _after_ the
pedal, right on the main signal path, downstream of the residual add. It works, but the
unnormalized residual highway lets the signal swell as the chain gets long, so deep
post-norm models are touchy: they need careful learning-rate warmup or they diverge.

**Pre-norm** (the modern default from [[gpt]]-2 onward) moves the leveler _inside_ the
pedal's own branch, so the residual highway stays clean and untouched all the way through.
That clean highway is exactly what lets you stack dozens of layers and still train stably,
because the [[gradient-descent]] signal flows straight back through it without fading. The tradeoff: pre-norm can
get a little lazy in its deepest layers.

**Sandwich-norm** is the belt-and-suspenders move:
a leveler both before _and_ after each branch, used in some very large or very deep models
(CogView, a few big ones since) to keep the numbers tame when even pre-norm starts to wobble.
Mechanically all three are the same cheap [[tensor]] operation; only the wiring around the
residual add changes, and that wiring decides whether the thing learns.

**See also:** [[residual-connections]], norm placement is defined entirely by where the
norm sits relative to the residual add; [[transformer]], every block carries two of these
norms, around its attention and feed-forward sublayers; [[gradient-descent]], pre-norm's
clean residual path is what keeps gradients alive in very deep stacks; [[tensor]],
normalization is an element-wise rescale of the tensors flowing between layers.
