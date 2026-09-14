---
semantic_id: "zf4FC1bnb4NbGpzCUAuA07_aIR7kUAAE"
related_ids:
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
  - "z5aFmVRzaAQbbp-6BCmx0BreJzXdEAAG"
---
# Hallucination

A **hallucination** is when a model states something false with the same fluent confidence it uses
for something true - a made-up citation, a plausible wrong date, a function that doesn't exist, a
biography of a person who never lived. The unsettling part isn't that it's wrong; all software is
sometimes wrong. It's that nothing in the output _looks_ wrong. The model has no separate "I'm not
sure" voice; the lie and the fact come out in the same tone.

It helps to remember what the model is actually doing. A [[gpt]]-style model predicts the next
[[token]] over and over, and "predict the most plausible continuation" is not the same job as "say
only true things." Most of the time plausible and true point the same way, because true statements
were the bulk of what it read. But when the model doesn't know - a fact that wasn't in its training
data, a detail too specific to have a stored answer - it doesn't stop. It has no _off_ switch for
uncertainty; it produces the most likely-sounding continuation anyway, and a confident fabrication
is often more likely-sounding than an admission of ignorance. [[temperature]] can turn the dice up
or down, but the behavior is baked into the objective, not just the sampling.

This is why "hallucination" is a slightly generous word - it frames a bug as a lapse, when really
it's the machine working exactly as designed, just pointed at a question it can't answer from
memory. The practical fixes don't try to make the model _know_ more; they try to keep it from
having to guess: give it the source text in-context so the answer is in front of it (retrieval),
make it show work it can check, or wire it to tools that can look things up. None of that cures it.
It just narrows the gap between "sounds right" and "is right," which is the gap hallucination lives
in.

**See also:** [[gpt]]: the next-token predictor whose objective this falls out of; [[token]]: the
unit being predicted; [[temperature]]: the knob that makes guessing bolder or safer; [[alignment]]:
the broader problem of getting a model to do what you meant; [[attention]]: part of how the model
decides what to say next.
