---
name: cuda
description: CUDA and NVIDIA GPU-compute reference for PyTorch/ATen, CTranslate2, and standalone kernels. Use for CUDA C++, cuBLAS/cuBLASLt, streams, events, Tensor-Core feature gating, memory/coalescing, Thrust, warp primitives, atomics, or dtype and compute-capability choices.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: -nlSWq6W0cSlQPD7EHOTEfXQqTTz0AAC
  related_ids: '["_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO","5mvyFquWmY6l0ca6mjPDa_X1m7350AAK"]'
---

# CUDA reference

Condensed, source-cited notes from NVIDIA's developer documentation
(`docs.nvidia.com`). The API bodies are repo-agnostic and usable from any CUDA
codebase; most pages then end with a worked example grounding the API in real
code, currently drawn from the CTranslate2 CUDA backend.

Those examples are illustrations, not instructions. If you are not in CT2, read
them as a case study and do not map a `src/cuda/` path onto a repo that has no
such file.

This shelf is written and consulted by the **`cuda-references`** agent, which
pulls new pages on demand from docs.nvidia.com. Prefer reading what is here
before re-fetching.

## References - load on demand

Detail lives in `references/`. One pointer per page:

- **[cublas-gemm.md](references/cublas-gemm.md)**
  - the cuBLAS GEMM surface: `cublasGemmEx`, `cublasComputeType_t` /
    `cublasGemmAlgo_t`, the int8/fp16/bf16/tf32 dtype combos, and cuBLASLt
    (`cublasLtMatmul`). _Read when picking or debugging a GEMM path._

- **[runtime-streams-events.md](references/runtime-streams-events.md)**
  - streams and events: create/destroy/sync/wait, the per-thread default stream
    model, event timing. _Read for concurrency, overlap, or "why is this
    serialising"._

- **[compute-capability-tensor-cores.md](references/compute-capability-tensor-cores.md)**
  - the CC-to-arch map and DP4A/HMMA/IMMA/bf16/TF32 gating. _Read before
    assuming a dtype or Tensor-Core path exists on the target GPU._

- **[memory-model-kernels.md](references/memory-model-kernels.md)**
  - global-memory coalescing, shared-memory banks and conflicts, the memory
    hierarchy, async global-to-shared copy (CC 8.0+). _Read when writing or
    tuning a kernel._

- **[thrust.md](references/thrust.md)**
  - device containers plus transform/reduce/fill/copy/max*element and
    `par_nosync.on(stream)`. \_Read for the high-level primitives instead of
    hand-rolling a kernel.*

- **[warp-primitives-atomics.md](references/warp-primitives-atomics.md)**
  - `__shfl_*_sync`, warp vote, `__syncwarp`, and atomics with their arch
    gating. _Read for reductions, scans, and softmax kernels._

## Siblings

- The Apple-GPU twin is the **`apple-silicon`** skill; `references/gpu-rosetta.md`
  at the repo root maps every CUDA concept here to its Metal counterpart.
- Engine structure ("how does CT2 do X", including `cuda-backend-structure.md`)
  lives in **`ct2-internals`**.

## Conventions for this shelf

- Each page starts with its NVIDIA source URL(s) and fetch date, keeps
  signatures, and records the CUDA-version / compute-capability availability.
- Each page ends with a `### Worked example: <repo> <backend>` section mapping
  the API to specific files in a **named** codebase. The shelf is machine-wide
  and read from many projects, so every example must name its repo. Append a new
  section rather than overwriting an existing one.
- Pull on demand. Do not pre-build the shelf speculatively.
