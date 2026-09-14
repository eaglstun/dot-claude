---
semantic_id: "SeckjN5UD6EK__HiIVQEx7laFf4tUAAO"
related_ids:
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
  - "fnwODJ9cb2gNXrBaOGYOx3MS9zaF0AAL"
---
# Mixture of experts

**Mixture of experts** (MoE) is a way of building a [[transformer]] so that only a fraction of it
runs on any given [[token]]. Instead of one big feed-forward block that every token passes through,
an MoE layer holds many smaller blocks - the "experts" - plus a little **router** that looks at
each token and picks a handful of experts to actually use. A model might hold 128 experts but
activate only 8 of them per token, so a model with hundreds of billions of total [[parameters]]
does the compute of a much smaller one.

The payoff is that you get to separate two things that are normally welded together: how much a
model _knows_ and how much it _costs to run_. Total parameters set the first; the number of
_active_ parameters per token sets the second. That's why you see MoE models advertised with two
numbers, like "235B total, 22B active" - the big number is the library, the small number is how
much of it gets pulled off the shelf for any one word. The router learns to send, say, code-ish
tokens to experts that got good at code and prose-ish tokens elsewhere, though the specializations
are rarely as tidy as the name suggests.

The catch is that all those experts still have to _fit in memory_ even though only a few run at a
time, so an MoE model is cheap in compute but expensive in RAM - which is exactly backwards from
what fits on a laptop. That's why the giant open-weight releases (many [[qwen]] models, Mixtral,
DeepSeek) are MoE: it's the trick that lets a model be enormous and still affordable to serve, as
long as you have the memory to hold the whole bench of experts even while most of them sit idle.

**See also:** [[transformer]]: the architecture MoE modifies; [[parameters]]: total vs active is
the whole point; [[attention]]: the part of the block MoE leaves alone, since it replaces the
feed-forward part; [[qwen]]: a family with large MoE models; [[open-weights]]: MoE is common in the
biggest open releases.
