---
topic_id: "v2:KHEO"
topic_path: "cuda-gpu/gpu-libraries"
semantic_id: "6L4EauM9QUaUAZEy0F63UvfQq4xA0AAB"
related_ids:
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
  - "rGpSEL-X8YyFwLt6FJeRUPHwr7Tp0AAM"
---
# Vulkan

**Vulkan** is a low-level, cross-platform standard for graphics and GPU computing from the
[Khronos Group](https://www.vulkan.org/), the open, vendor-neutral counterpart to [[cuda]]
and [[metal]]. It's an open, royalty-free _specification_ rather than a single piece of
software: the spec and reference tooling (headers, validation layers, conformance tests) are
published openly, and the actual drivers range from fully open source (AMD and Intel via Mesa)
to proprietary (NVIDIA's).

Its appeal for ML is exactly that neutrality: one Vulkan compute
backend runs on NVIDIA, AMD, Intel, and many mobile and embedded GPUs, so it's the portable
fallback when you can't count on an NVIDIA card (and thus on CUDA). The trade-offs: it's
lower-level and more verbose to work with, and its ML-library ecosystem is much thinner than
CUDA's, so on NVIDIA hardware it usually delivers less peak speed than CUDA does.

In local
inference, [[ggml]] ships a Vulkan backend, which is what lets llama.cpp speed up `.gguf`
models on AMD and Intel GPUs that CUDA and Metal can't touch.

**See also:** [[cuda]], the NVIDIA-only counterpart; [[metal]], Apple's equivalent;
[[ggml]] — uses Vulkan as a cross-vendor GPU backend.
