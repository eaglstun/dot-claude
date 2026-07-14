---
topic_id: "v2:JKCG"
topic_path: "ai-concepts/architecture-types"
semantic_id: "TQDbGF_lWQUd5pFwK02S1X9ww_5EUAAE"
related_ids:
  - "byPeHHb12QkF9_OYRxXCBatQ4_I2EAAJ"
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
---
# GPT

**GPT** (Generative Pre-trained Transformer) is a family (and by now a whole class) of large
language models built on the "decoder" half of the [[transformer]] architecture. The name
spells out the recipe: _generative_ (it produces text), _pre-trained_ (it first learns broadly
from a huge pile of text before any task-specific tuning), and _transformer_ (the
attention-based network underneath). At its core it's a next-word predictor: given the text so
far, it guesses the most likely next chunk of text (a _token_), adds it, and repeats. At
enough scale, that simple loop yields fluent writing, reasoning, coding, and more. OpenAI's
GPT-2/3/4 and successors popularized the term, but "GPT" now gets used loosely for
decoder-only LLMs in general. One unrelated name collision worth knowing: **GPT** is also
_GUID Partition Table_, a disk-partitioning scheme. Context tells them apart.

**See also:** [[gguf]]: these models are often shipped in GGUF for local inference;
[[qwen]]: an open-weight LLM family cut from the same decoder-only cloth.
