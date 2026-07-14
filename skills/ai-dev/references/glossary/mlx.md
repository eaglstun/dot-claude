---
topic_id: "v2:NLBL"
topic_path: "apple-accelerate/compute-apis"
semantic_id: "cBlcrnfcb9l15OhWENWYB7IRlVmjgAAO"
related_ids:
  - "-nhW1t8U_Zkt9M6eGjST57VRuZBj0AAM"
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
---
# MLX

**MLX** is Apple's open-source framework for machine learning, built specifically for Apple
silicon (M-series chips). Its headline feature is **unified memory**: the CPU and GPU share one
pool of memory, so data doesn't have to be copied back and forth between them the way it does
with [[cuda]].

Under the hood it builds on Apple's [[metal]] GPU stack. The API is deliberately
close to NumPy (with PyTorch-style building blocks for neural networks), and it only does the
actual computing when you ask for a result rather than eagerly along the way (_lazy
evaluation_). It also works out the calculus that training needs automatically, and can shrink
models to smaller number formats right on the device.

For running LLMs locally on a Mac, the
companion library `mlx-lm` loads and runs models in MLX format, the native Apple-silicon
alternative to the GGUF / llama.cpp world (often noticeably faster on a Mac, but Mac-only).

**See also:** [[gguf]], the cross-platform format MLX competes with for local inference;
[[metal]], the Apple GPU API MLX is built on.
