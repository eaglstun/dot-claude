---
topic_id: "v2:JKFB"
topic_path: "ai-concepts/architecture-types"
semantic_id: "S05HSldIThUYdhlyoOTexxM8Q7ymUAAJ"
related_ids:
  - "S9bfTF9Jr7QdZjFwsNie2TE-ATzmQAAP"
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
---
# Transformer

**Transformer** is the neural-network design behind virtually all modern large language models
(and much more). Introduced in the 2017 paper _"Attention Is All You Need,"_ its key idea is
**self-[[attention]]**: for each word in a sequence, the model weighs how much every other word
should influence it, so it can connect distant words directly instead of marching through them
one at a time like older "recurrent" networks did. Because those weighings happen in parallel
across the whole sequence, transformers train efficiently on GPUs and scale up to enormous
models and datasets, the practical reason they won out. They come in three flavors:
**encoder-only** (e.g. BERT, good at understanding and classifying text), **decoder-only**
(e.g. the [[gpt]] family, good at generating text), and **encoder-decoder** (e.g. T5, good at
tasks like translation that turn one sequence into another). It all runs on [[tensor]]
operations stacked into repeated attention and feed-forward layers.

**See also:** [[attention]] (the mechanism at its core); [[gpt]] (the decoder-only branch);
[[tensor]] (the data it all runs on); [[lora]] (the efficient way to fine-tune a
transformer's attention weights); [[qwen]] (a widely-run open-weight transformer LLM family).
