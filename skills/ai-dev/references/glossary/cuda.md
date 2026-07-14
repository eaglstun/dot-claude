---
topic_id: "v2:KNLF"
topic_path: "cuda-gpu/memory-model"
semantic_id: "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
related_ids:
  - "rGpSEL-X8YyFwLt6FJeRUPHwr7Tp0AAM"
  - "-nhW1t8U_Zkt9M6eGjST57VRuZBj0AAM"
---
# CUDA

**CUDA** (Compute Unified Device Architecture) is NVIDIA's software platform for running
general-purpose number-crunching, not just graphics, on NVIDIA GPUs. It's the default
engine for machine learning: rather than write low-level GPU code yourself, you almost always
lean on libraries like cuDNN and cuBLAS (see [[cudnn-cublas]]) and the CUDA-powered builds of
PyTorch and TensorFlow, which spread the work across the GPU's thousands of cores. NVIDIA's
grip on the field comes less from the chips than from this software head start, the mature
ecosystem everyone targets first. The catch: CUDA is NVIDIA-only. It won't run on Apple, AMD,
or Intel GPUs, which is exactly the gap [[metal]] and [[vulkan]] fill on other hardware. In
the local-inference world, [[ggml]] ships a CUDA backend so `.gguf` models can hand work to an
NVIDIA GPU instead of grinding away on the CPU.

**See also:** [[metal]]: Apple's equivalent; [[vulkan]]: the cross-vendor alternative;
[[ggml]]: uses CUDA as one of its GPU backends; [[cudnn-cublas]]: the optimized math/DL
libraries on top of CUDA.
