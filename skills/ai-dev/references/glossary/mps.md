---
topic_id: "v2:NGOP"
topic_path: "apple-accelerate/mps-inference"
semantic_id: "2PRzjH4-edggp5gVHt0Tpb1gFR_QIAAM"
related_ids:
  - "kPRVrE08SbgkovIUv_yBp37AFzTCoAAO"
  - "wWUprU8jbbAA66pVl10GtCVUFl6LIAAD"
---
# MPS

**MPS** (Metal Performance Shaders) is Apple's set of hand-optimized GPU building blocks built
on top of [[metal]]: ready-made routines for things like matrix multiply, convolution, and
other neural-network operations, plus a higher-level graph API (**MPS Graph**) that schedules
and combines them efficiently. It's roughly Apple's answer to NVIDIA's [[cudnn-cublas]]: the
optimized pieces frameworks call instead of writing raw GPU code themselves. In day-to-day use
you meet MPS as **PyTorch's `mps` device** (`torch.device("mps")`), which is how PyTorch runs
on Apple-silicon GPUs instead of falling back to the CPU; Apple's [[mlx]] leans on the same
Metal foundation. Note the name collision: "MPS" here means Metal Performance Shaders, not
"model-parallel" anything.

**See also:** [[metal]]: the GPU API MPS is built on; [[mlx]]: Apple's ML framework over
the same stack; [[cuda]]: the platform underneath; [[cudnn-cublas]]: the NVIDIA libraries
that play the equivalent role; [[epsilon-gate]]: a CUDA-tuned convergence threshold often goes
quietly dark when the same code runs here.
