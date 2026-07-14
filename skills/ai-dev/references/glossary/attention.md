---
topic_id: "v2:JDBP"
topic_path: "ai-concepts/mixed"
semantic_id: "S9bfTF9Jr7QdZjFwsNie2TE-ATzmQAAP"
related_ids:
  - "S05HSldIThUYdhlyoOTexxM8Q7ymUAAJ"
  - "TQDbGF_lWQUd5pFwK02S1X9ww_5EUAAE"
---
# Attention

**Attention** is the mechanism at the heart of the [[transformer]]. For each word, more
precisely each _token_, it lets the model decide how much every other token should
influence it, so meaning can jump straight between distant words instead of being passed
along one step at a time.

Here's the idea. Every token is turned into three vectors with
nicknames: a **query** (what am I looking for?), a **key** (what do I offer?), and a
**value** (what I'll actually contribute). The model compares one token's query against every
token's key to score how relevant each other token is, turns those scores into weights that
add up to 1 (a step called _softmax_), and then blends the value vectors in those
proportions. That's **scaled dot-product attention**: in shorthand,
`softmax(QKᵀ / √dₖ)·V`. Models run many of these comparisons in parallel
(**multi-head attention**) so different "heads" can focus on different kinds of relationships
(grammar, what a pronoun refers to, position, and so on).

When the queries, keys, and values
all come from the same sentence it's **self-attention** (a token reading its own context);
when the queries come from one sequence and the keys/values from another it's
**cross-attention** (for example, a translator's output attending to the input).

The catch is
cost: comparing every token to every other grows with the _square_ of the length, which is
why long context windows get expensive and why so much research chases cheaper versions. Under
the hood the query/key/value steps are just [[tensor]] matrix multiplications, and they're
exactly the weights [[lora]] usually adjusts when fine-tuning.

**See also:** [[transformer]]: the architecture built around attention; [[tensor]]: what
Q/K/V are; [[lora]]: fine-tunes the attention projection matrices.
