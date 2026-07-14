---
topic_id: "v2:KCJP"
topic_path: "cuda-gpu"
semantic_id: "-njdZsc1wbC30Lm-nDEhaHEwt9zikAAO"
related_ids:
  - "enk0fq4US4C077zyvNeCdXFQmRzqkAAP"
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
---
# Thrust — device containers & parallel algorithms

**Sources:**

- https://nvidia.github.io/cccl/thrust/ (Thrust docs, part of CCCL)
- https://github.com/NVIDIA/cccl/blob/main/thrust/examples/cuda/explicit_cuda_stream.cu
  **Fetched:** 2026-06-29 (Thrust / CCCL main)

**What it's for:** Thrust is a CUDA C++ parallel-algorithms library resembling the C++ STL. It ships
in the CUDA Toolkit (and as part of CCCL — CUDA Core Compute Libraries, alongside CUB and
libcu++). CT2 uses it for fills, copies, reductions and elementwise transforms so it doesn't
hand-roll those kernels.

## Containers

- `thrust::device_vector<T>` — STL-like vector backed by device memory.
- `thrust::host_vector<T>` — host-side counterpart; assignment between the two does the H2D/D2H copy.

## Key algorithms (header `<thrust/...>`)

```cpp
thrust::fill(policy, first, last, value);
thrust::copy(policy, first, last, result);
thrust::sequence(policy, first, last);
thrust::for_each(policy, first, last, unary_function);
thrust::transform(policy, first, last, result, unary_op);                 // unary
thrust::transform(policy, first1, last1, first2, result, binary_op);      // binary
T   thrust::reduce(policy, first, last, init, binary_op);
T   thrust::transform_reduce(policy, first, last, unary_op, init, binary_op);
Iter thrust::max_element(policy, first, last);   // also min_element
thrust::sort(policy, first, last);
```

All take an execution policy as the first argument (or default to the iterator's system).

## Execution policies & streams

- `thrust::host`, `thrust::device` — pick the backend system.
- `thrust::cuda::par` — explicit CUDA backend.
- `thrust::cuda::par_nosync` — hint that Thrust should **skip non-essential internal
  synchronizations**; the caller promises to synchronize before reading results. Lower overhead for
  pipelined/async use.
- Run on a specific stream: **`thrust::cuda::par.on(stream)`** (and `par_nosync.on(stream)`). Note
  it is `.on(stream)`, not `par(stream)`.

```cpp
// from explicit_cuda_stream.cu
cudaStream_t s; cudaStreamCreate(&s);
thrust::for_each(thrust::cuda::par.on(s), d_vec.begin(), d_vec.end(), op);
cudaStreamSynchronize(s);
```

- Functors are device-callable (`__host__ __device__`); prefer fancy iterators
  (`counting_iterator`, `transform_iterator`, `zip_iterator`) over temporary buffers.

### Worked example: the CTranslate2 CUDA backend

CT2 wraps every Thrust call in `THRUST_CALL(FUN, ...)` (`src/cuda/utils.h:136-141`), which invokes
the algorithm on the calling thread's stream with **`par_nosync`** — matching CT2's per-thread-stream
model (`runtime-streams-events.md`) and letting CT2 control synchronization. Usage points
(`cuda-backend-structure.md` §4):

- fill / copy / reduce / `max_element` in `src/cuda/primitives.cu:51-133`.
- the `unary_transform` / `binary_transform` / `permute` helpers in `src/cuda/helpers.h:75-107`
  (Thrust `transform` under the hood) — used by elementwise ops.
- gather/scatter-style ops: `src/ops/gather_gpu.cu:49`, `tile_gpu.cu:50-60`,
  `concat_split_slide_gpu.cu:91`.
  Headers come from the vendored `third_party/thrust` (NVIDIA CCCL) submodule. Separately, **CUB**
  (also CCCL) is used directly for `cub::BlockReduce` inside hand-written reduction kernels and for
  `cub::CachingDeviceAllocator` in `src/cuda/allocator.cc:55-58`. **Metal mirror:** no Thrust on
  Apple GPUs — those fills/copies/reductions are hand-written MSL kernels or fall back to the CPU
  reference path.

### See also

- [[apple-silicon:mps-softmax-and-topk]] — no single Metal twin for Thrust; the MPS op families are the nearest equivalents, hand-rolled kernels cover the rest.
- [[gpu-rosetta]] — CUDA↔Metal concept map.
