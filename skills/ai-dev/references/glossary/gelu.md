---
topic_id: "v2:JGFN"
topic_path: "ai-concepts"
semantic_id: "Tx_m_pOEW1Q7rjtwOSmaTfXa46iwwAAF"
related_ids:
  - "29vkbpdUwtzcdDs6uAuZxfSY6CjE8AAD"
  - "Sxrn4J6EGuTZIt21l20t3bc44annwAAL"
---
# GELU

**GELU** (Gaussian Error Linear Unit) is the little nonlinear gate that sits between the
layers of most modern [[transformer]] models, deciding how much of each signal to pass
forward. You need a gate like this because without one, stacking layers is pointless,
a pile of plain linear steps just collapses back into a single linear step, so no matter
how deep the network got, it could only ever draw straight lines. The gate is what lets it
bend.

The old standby gate was ReLU, a hard bouncer: anything negative gets slammed to exactly
zero, anything positive walks through untouched. GELU is the same idea with better manners.
Instead of a hard cutoff it uses the bell curve (the _Gaussian_ in the name) to weight each
input by how likely it is to matter, so small negative values aren't thrown out, they're
quietly turned down. That smoothness gives the model gentler slopes to learn from during
training, which tends to train more stably. It runs element-wise across a [[tensor]], and
it's the default activation inside [[gpt]]-style models and BERT.

**See also:** [[transformer]]: GELU lives in the feed-forward sublayer of every
transformer block; [[gpt]]: GPT-family models use GELU as their activation; [[tensor]]:
GELU is applied element-wise to the tensors flowing between layers.
