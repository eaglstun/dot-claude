---
topic_id: "v2:JOEP"
topic_path: "ai-concepts/mixed"
semantic_id: "29vkbpdUwtzcdDs6uAuZxfSY6CjE8AAD"
related_ids:
  - "Tx_m_pOEW1Q7rjtwOSmaTfXa46iwwAAF"
  - "x_M0SG8UQreJxDok6QwK95WYS4xEcAAD"
---
# ReLU

**ReLU** (Rectified Linear Unit) is the simplest useful activation function, the little
nonlinear gate that sits between the layers of a neural network and decides how much of each
signal to pass forward. Its whole rule fits in one line: if a number is negative, output
zero; if it's positive, leave it alone. That's it. Negative gets bounced, positive walks
right through.

You need a gate like this because without one, stacking layers is pointless: a pile of
plain linear steps just collapses back into a single linear step, so the network could only
ever draw straight lines. ReLU's hard kink is enough to break that and let the model bend.
It became the default for years because it's dirt cheap to compute and it sidesteps an old
training headache (the "vanishing gradient," signals shrinking to nothing as they pass back
through a deep stack). Its one quirk is that a unit stuck on the negative side outputs zero
forever and stops learning (a "dead" unit), which is part of why smoother successors like
[[gelu]] took over inside big [[transformer]] models. It runs element-wise across a
[[tensor]].

**See also:** [[gelu]]: the smooth, better-mannered successor that replaced ReLU in most
transformers; [[transformer]]: where these activation gates live, in the feed-forward
sublayer; [[tensor]]: ReLU is applied element-wise to the tensors flowing between layers.
