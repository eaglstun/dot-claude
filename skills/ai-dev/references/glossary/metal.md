---
topic_id: "v2:NLGD"
topic_path: "apple-accelerate/compute-apis"
semantic_id: "3nN0TN88O9zsrjAZitSwI9JwW5qMsAAO"
related_ids:
  - "2tX8QsIoeZ7GIjF4y5eQlhLkUgGtsAAD"
  - "3vc2au8qe7-q5zKtwpVQttjKAQGKMAAP"
---
# Metal

**Metal** is Apple's low-level interface for graphics and GPU computing, its answer to
[[cuda]] and [[vulkan]], but exclusive to Apple hardware (Mac, iPhone, iPad). For ML it matters
because Apple-silicon chips share one pool of memory between CPU and GPU (unified memory), so
Metal lets models use the GPU without copying their weights across the slow link that
separates the CPU and GPU on a typical PC. The compute side is exposed through **[[mps]]**
(Metal Performance Shaders) and the higher-level MPS Graph; PyTorch's `mps` device and [[mlx]]
both sit on top of it. In local inference, [[ggml]] ships a Metal backend, which is how
llama.cpp and Ollama speed up `.gguf` models on a Mac instead of falling back to the CPU.

**See also:** [[cuda]]: the NVIDIA counterpart; [[vulkan]]: the cross-vendor alternative;
[[mlx]]: Apple's ML framework built on Metal; [[mps]]: the optimized kernel library on
top of Metal; [[ggml]]: uses Metal as a GPU backend.
