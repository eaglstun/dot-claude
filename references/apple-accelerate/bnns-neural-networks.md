---
topic_id: "v2:NHNB"
topic_path: "apple-accelerate/cpu-neural"
semantic_id: "-tdtQkOHtdu8Yd52gq6X1T5LVK-S0AAC"
related_ids:
  - "_-bsBuV9l9rySMOYA7aN4ChjXm7U8AAI"
  - "_u-ph617kVLoE8ckwq61QYhHXlcRYAAI"
---
# BNNS & BNNSGraph — neural networks on the CPU

Source:

- https://developer.apple.com/documentation/accelerate/bnns (Swift `BNNS` namespace)
- https://developer.apple.com/documentation/accelerate/bnnsgraph (the modern graph API)
- https://developer.apple.com/documentation/accelerate/bnns/bnnsgraph (types)

BNNS = **Basic Neural Network Subroutines**: Apple's CPU-side neural-network runtime inside
Accelerate. It runs inference (and some training) on the CPU with low latency and low energy
— the right tool for small models, realtime audio/sensor nets, or when you specifically want
to stay off the GPU/ANE. For large models on Apple silicon, **Core ML** (which can target
CPU **and** GPU **and** the Apple Neural Engine) is usually the better front door.

## Two generations — use BNNSGraph

- **`BNNSGraph` (modern, recommended).** You compile a whole graph (typically from a Core ML
  `.mlmodel`/`.mlpackage` or an authored graph) into a `BNNSGraph.Context` and execute it.
  Graph-level view lets Accelerate fuse and schedule ops. This is the entry point for new code.
- **Per-layer `BNNS.*Layer` API (legacy, largely `@deprecated`).** The older style where you
  hand-build `ConvolutionLayer`, `FullyConnectedLayer`, `PoolingLayer`, `ActivationLayer`,
  `NormalizationLayer`, chain them, and manage tensors yourself. Nearly all of these layer
  classes, the optimizer structs (`AdamOptimizer`, `SGDMomentumOptimizer`, `RMSPropOptimizer`,
  `AdamWOptimizer`), and helper enums are now deprecated. **Don't start new work here.**

## Core concepts

- **Tensors / descriptors:** data is described by `BNNSNDArrayDescriptor` (shape, `DataLayout`,
  dtype, stride). `BNNS.Shape` and `BNNS.DataLayout` name the dimensions.
- **Dtypes:** float32, float16, and quantized int8/int16 paths — a big reason to use BNNS is
  cheap low-precision CPU inference.
- **Activations & ops:** `BNNS.ActivationFunction` (ReLU, sigmoid, tanh, GELU, …),
  arithmetic unary/binary/ternary functions, pooling/normalization/convolution types.
- **Training bits (legacy):** `LearningPhase`, gradient/`*Backward` calls, loss functions,
  and the optimizers — present but deprecated; use a real training framework and deploy the
  result via Core ML → BNNSGraph.

## Typical modern flow

1. Author/convert your model (usually via Core ML Tools) to a Core ML package.
2. Load/compile it into a `BNNSGraph.Context`.
3. Bind input/output tensors (`BNNSNDArrayDescriptor`s over your buffers).
4. Execute; read outputs. Reuse the context across calls.

## Gotchas

- **Prefer BNNSGraph; the per-layer API is a deprecation minefield.** If you find yourself
  instantiating `ConvolutionLayer`, you're on the old path — expect `@deprecated` warnings
  and no new features. Route new work through BNNSGraph (or Core ML).
- **BNNS is CPU-only.** It does _not_ use the GPU or the Neural Engine. If you want the ANE,
  that's Core ML's job — BNNS is deliberately the CPU path (predictable latency, no GPU
  contention, good for realtime threads).
- **Descriptor layout must match your buffer exactly.** `BNNSNDArrayDescriptor` shape/stride/
  layout mismatches don't crash — they read wrong memory and produce plausible-but-wrong
  tensors. Double-check row-major vs the layout enum and the stride math.
- **Don't hand-write a training loop in BNNS in 2025+.** The optimizers are deprecated; train
  in PyTorch/JAX/MLX, convert, and _deploy_ on-device. BNNS's sweet spot is inference.
- **Not the same as MPS / MLCompute.** BNNS (CPU, Accelerate) ≠ MPSGraph (GPU) ≠ Core ML
  (dispatcher over all three). Choose by target hardware.

### See also

- [[overview]] — where BNNS sits among the Accelerate modules and vs. Core ML / MPS.
- [[blas-and-lapack]] — BNNS's dense layers ultimately ride the same BLAS gemm machinery.
