---
topic_id: "v2:JOIA"
topic_path: "ai-concepts/mixed"
semantic_id: "Zn7ezDKtmagPr1H2CxeKDLdD0bEXEAAC"
related_ids:
  - "byPeHHb12QkF9_OYRxXCBatQ4_I2EAAJ"
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
---
# GGML

**GGML** is a C/C++ library, written by Georgi Gerganov, for _running_ machine-learning models
(as opposed to training them), with a deliberate focus on getting good performance out of
ordinary CPUs and consumer hardware, though it also supports GPU backends like [[cuda]],
[[metal]], and [[vulkan]]. It's the engine under
[llama.cpp](https://github.com/ggml-org/llama.cpp) and
[whisper.cpp](https://github.com/ggml-org/whisper.cpp): it defines the math operations, the
order they run in, and (crucially) the **quantization** schemes that shrink the model's
numbers to fewer bits so large models fit in limited memory. One confusing wrinkle: "GGML"
was also the name of an early single-file model format from the same project. That _format_
was retired and replaced by [[gguf]], but the _library_ lives on and is what actually crunches
the numbers when you run a `.gguf` model. So today: GGML = the engine, GGUF = the file it
loads.

**See also:** [[gguf]]: the file format that replaced the old GGML format and runs on
this library; [[tensor]]: the core data structure GGML operates on; [[cuda]], [[metal]],
[[vulkan]]: the GPU backends it can offload to.
