---
topic_id: "v2:JOIA"
topic_path: "ai-concepts/mixed"
semantic_id: "byPeHHb12QkF9_OYRxXCBatQ4_I2EAAJ"
related_ids:
  - "TQDbGF_lWQUd5pFwK02S1X9ww_5EUAAE"
  - "Zn7ezDKtmagPr1H2CxeKDLdD0bEXEAAC"
---
# GGUF

**GGUF** (GPT-Generated Unified Format) is a single-file format from the
[llama.cpp](https://github.com/ggml-org/llama.cpp) project for sharing and running quantized
large language models, models whose numbers have been shrunk to save space (see
[[parameters]]). It replaced the older [[ggml]] format. One `.gguf` file packs everything
needed to run the model: the weights, the tokenizer, and metadata like the architecture,
context length, and chat template, so there are no loose config files to juggle. It's built
to load fast and comes in a range of [[quantization]] levels (e.g. `Q4_K_M`, `Q5_K_M`, `Q8_0`)
that trade a little accuracy for smaller size and lower memory use, which is how big models
fit on everyday hardware. It's the native format for llama.cpp, Ollama, and LM Studio.

**See also:** [[quantization]]: what those `Q4_K_M` names actually encode, and what the
squashing costs; [[mlx]]: the Apple-silicon counterpart in the local-inference world;
[[ggml]]: the tensor library that actually loads and runs `.gguf` files; [[parameters]]:
quantization shrinks the bytes-per-parameter, which is what makes `.gguf` files small;
[[qwen]]: a model family people very commonly download and run in this format.
