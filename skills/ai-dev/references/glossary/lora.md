---
topic_id: "v2:JAHP"
topic_path: "ai-concepts"
semantic_id: "wt8NLD84RaELFl7-JW-KQQXa6xaVQAAN"
related_ids:
  - "fnwODJ9cb2gNXrBaOGYOx3MS9zaF0AAL"
  - "Yg0fKTZS7rmLH2wGBDQc7iyaiz7tEAAA"
---
# LoRA

**LoRA** (Low-Rank Adaptation) is a cheap way to fine-tune a large model. Normally fine-tuning
updates all of a model's weights, billions of numbers, costly in compute and memory. LoRA
instead freezes the original weights and trains a small add-on alongside them. The trick: the
_change_ a fine-tune makes to a big grid of weights turns out to be simple enough to capture
with two much smaller grids multiplied together (`A · B`), which together hold a tiny fraction
of the original numbers (their size is set by a chosen _rank_ `r`, often 8–64). At run time
that product is added back onto the frozen weights, so once merged there's no speed penalty.

The payoff is twofold: you can fine-tune a large model on a single consumer GPU, and the
resulting **LoRA adapter** is a small file (megabytes, not gigabytes) that you swap in and out
on top of one base model.

**QLoRA** goes further by also shrinking the frozen base model to
4-bit (the same quantization idea behind [[gguf]]) while training the adapter at higher
precision, saving even more memory. LoRA is most often applied to the attention weights of a
[[transformer]].

**See also:** [[transformer]]: the architecture whose weight matrices LoRA adapts;
[[tensor]]: the low-rank matrices that make up an adapter; [[gguf]]: the quantization
world QLoRA borrows from; [[parameters]]: the billions of base weights LoRA leaves frozen;
[[qwen]]: a common open-weight base people fine-tune with LoRA.
