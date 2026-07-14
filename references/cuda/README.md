---
topic_id: "v2:KIFF"
topic_path: "cuda-gpu"
semantic_id: "rGpSEL-X8YyFwLt6FJeRUPHwr7Tp0AAM"
related_ids:
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
  - "5mvyFquWmY6l0ca6mjPDa_X1m7350AAK"
---
# CUDA / NVIDIA GPU references

Condensed, source-cited notes from NVIDIA's developer documentation (`docs.nvidia.com`). The **API
bodies are repo-agnostic** — usable from any CUDA codebase (PyTorch/ATen, CTranslate2, standalone
kernels).

Most files then end with a **worked example** section grounding the API in real code. Those examples
currently come from the **CTranslate2 CUDA backend** (`src/cuda/` + `src/ops/*_gpu.cu`,
`-DWITH_CUDA=ON`), which is where this shelf was mined — CT2's reference GPU implementation, the
template its Metal backend mirrors. **They are illustrations, not instructions.** If you are not in
CT2, read them as a case study; do not map a `src/cuda/` path onto a repo that has no such file.

Written and consulted by the **`cuda-references`** agent. Convention (matching the `apple-silicon`
and `arkit` shelves): each file **starts with its NVIDIA source URL(s) + fetch date**, keeps
signatures and the **CUDA-version / compute-capability availability**, and **ends with a
`### Worked example: <repo> <backend>` section** mapping the API to specific files/usage in a named
codebase. The shelf is machine-wide and read from many projects, so every example must name its
repo; append a new section rather than overwriting an existing one. Pull on demand — don't pre-build
speculatively — and reuse before re-fetching.

Siblings: the Apple-GPU twin is the `apple-silicon` skill (`references/apple-silicon/`); engine
structure ("how does CT2 do X", including `cuda-backend-structure.md`) lives in `ct2-internals`
(`references/ct2-internals/`).

## Index

- **cublas-gemm.md** — the cuBLAS GEMM surface: `cublasGemmEx` signature, `cublasComputeType_t` /
  `cublasGemmAlgo_t`, the int8/fp16/bf16/tf32 dtype combos, and cuBLASLt (`cublasLtMatmul`); core of
  CT2's `primitives.cu` GEMM wrappers.
- **runtime-streams-events.md** — CUDA Runtime streams & events: create/destroy/sync/wait, the
  per-thread default stream model, and event timing — CT2's per-thread cached stream/handle model.
- **compute-capability-tensor-cores.md** — CC→arch map and the DP4A/HMMA/IMMA/bf16/TF32 gating;
  maps to `gpu_supports_int8` (≥6.1), `gpu_has_fp16_tensor_cores` (≥7.0), `gpu_has_int8_tensor_cores` (≥7.2).
- **memory-model-kernels.md** — global-memory coalescing, shared-memory banks/conflicts, the memory
  hierarchy, and async global→shared copy (CC 8.0+) for writing `src/ops/*_gpu.cu` kernels.
- **thrust.md** — Thrust device containers + transform/reduce/fill/copy/max_element and
  `par_nosync.on(stream)`; the fill/copy/reduce primitives behind `THRUST_CALL` in `primitives.cu`.
- **warp-primitives-atomics.md** — `__shfl_*_sync`, warp vote, `__syncwarp`, and atomics with their
  arch gating; the building blocks under `cub::BlockReduce` in the reduction/softmax kernels.

Cross-shelf: [[gpu-rosetta]] (repo root) maps every CUDA concept here to its Metal twin file.
