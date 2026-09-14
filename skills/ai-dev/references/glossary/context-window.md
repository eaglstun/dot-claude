---
semantic_id: "L9QNRwzQy7FTNtz7McFU6WNSIXngEAAL"
related_ids:
  - "zf4FC1bnb4NbGpzCUAuA07_aIR7kUAAE"
  - "SQaeEHTSr7wrDhxgJOpVw3PII9zoUAAF"
---
# Context window

A model's **context window** is the amount of text it can hold in view at once - everything it's
currently "thinking about," measured in [[token]]s. It's the sum of what you put in _and_ what it
writes back: the system prompt, your question, any documents you pasted, the conversation so far,
and the reply it's generating all have to fit inside the same budget. Run past it and the oldest
material falls out of view; the model doesn't remember the start of a long chat, it just no longer
sees it.

The window exists because of how [[attention]] works. In a [[transformer]], every token attends to
every other token in view, so the cost of the mechanism grows with the _square_ of the window -
double the context and you roughly quadruple the work. That quadratic wall is why context length
was small for years (a couple thousand tokens) and why stretching it to the hundreds-of-thousands
or millions you see advertised now took real engineering, not just a bigger number in a config
file. It's also why a long context is slower and more expensive per query: you're paying for all
that all-pairs comparison.

A big window is genuinely useful - you can drop a whole codebase or a long document in and ask
about it - but "fits in the window" and "actually used well" aren't the same thing. Models famously
attend unevenly across a long context, gripping the beginning and end and going vague in the middle
(the "lost in the middle" problem), so a fact buried at token 400,000 may be technically present
and effectively ignored. The window is how much the model _can_ see at once; it says nothing about
how evenly it looks.

**See also:** [[token]]: the unit the window is measured in; [[attention]]: the mechanism whose
cost sets the window's price; [[transformer]]: where that all-pairs comparison happens;
[[embeddings]]: what each in-window token becomes internally.
