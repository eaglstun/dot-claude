---
topic_id: "v2:HPEF"
topic_path: "mixed"
semantic_id: "z1esuJaXhSLYOhQI-A005_TG4s3FQAAH"
related_ids:
  - "X0o8WM6VzxjIFn1WPGgc52PeZw7EQAAN"
  - "DT66WEb8QXjJDj9MOEwG0nXaY97tUAAB"
---
# Epsilon gate

An **epsilon gate** is a pass/fail check built around a number that's supposed to be _almost_
zero. Many iterative algorithms stop when some error measure drops below a tiny threshold called
**epsilon** (often written `eps`, a value like `0.002`): close enough, declare success, hand back
the answer. The trouble starts when the code treats that threshold as a hard gate, returning a
result _only_ if the error makes it under epsilon. Anything that lands a hair short gets thrown
away, even when it's a perfectly good answer.

That's fine until the arithmetic shifts underneath it. The same computation run on a different
backend, [[cuda]] versus [[mps]] versus the CPU, will not produce bit-identical numbers, because
[[precision]] and the order of operations differ from one machine to the next. A search that used
[[gradient-descent]] to reach `0.0019` on the GPU it was tuned for might settle at `0.0021`
somewhere else: the same quality of answer, missing the gate by a rounding error. If epsilon was
hardcoded for one machine, the program can silently produce _nothing_ on another. No crash, no
warning, just an empty output folder and a confusing afternoon.

The fix is to stop treating epsilon as a _publication gate_ and treat it as a _stopping hint_:
keep going until the error is under the threshold _or_ you run out of steps, then always return
the best result the run actually found. Epsilon decides when to _stop looking_, not whether the
answer is allowed to exist. A hardcoded convergence threshold is a close cousin of any magic
number tuned on one setup, the kind of buried assumption that turns into a silent failure the
moment the ground moves: a new GPU, a different [[precision]], a fresh library version.

**See also:** [[gradient-descent]]: the iterative loop whose error an epsilon gate is usually
checking; [[precision]]: why the same math lands on different last digits across machines, which
is exactly what trips the gate; [[mps]]: the Apple-silicon backend where a CUDA-tuned threshold
most often goes quietly dark; [[val-loss]]: another spot where a loss threshold decides when to
stop.
