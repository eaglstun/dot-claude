---
topic_id: "v2:KNKM"
topic_path: "cuda-gpu/memory-model"
semantic_id: "fGxTPoZ29dR3KvS72tGzU_vyuRJq0AAO"
related_ids:
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
  - "OAr6HAfO4Ib79pSpuJHyWXtZM1ppIAAC"
---
# CUDA memory model essentials for `*_gpu.cu` kernels

**Sources:**

- https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html (Memory Optimizations)
- https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/async-copies.html
  **Fetched:** 2026-06-29 (CUDA C++ Best Practices Guide 13.3; CUDA Programming Guide 13.3)

**What it's for:** The memory hierarchy and access rules a kernel author must respect when writing
per-op CUDA kernels — coalescing, shared-memory banking, and (on Ampere+) async global→shared copy.

## Memory hierarchy (fastest → slowest)

Registers (per-thread, on-chip) → Shared / L1 (on-chip, per-SM/per-block) → L2 (on-chip,
device-wide) → Global (off-chip DRAM, largest) → Constant & Texture (off-chip, read-only, cached).
High-priority rule: minimize host↔device transfer; keep data resident on the device.

## Global memory coalescing

- "Global memory loads and stores by threads of a warp are coalesced by the device into as few as
  possible transactions."
- On **CC 6.0+** the access unit is **32 bytes** (L1 caching default, but unit is 32B regardless).
  A warp's accesses coalesce into the number of 32-byte transactions needed to cover the addresses
  touched.
- `cudaMalloc()` is aligned to ≥ 256 bytes, so a stride-1, base-aligned array gives ideal
  coalescing: sequential threads → adjacent 4-byte words in a 32-byte-aligned span.
- Penalties: stride-2 ≈ 50% efficiency; large strides degrade toward one transaction per thread.
  A misaligned sequential access needs 5 segments instead of 4 (≈ 20% loss, partly hidden by cache).
- Best-practice framing: maximize the ratio of bytes used to bytes transferred.

## Shared memory

- On-chip; "much higher bandwidth and lower latency than local and global memory." Declared with
  `__shared__`; scoped per thread block.
- Organized into **32 banks** (CC 5.x+), each serving 32 bits per clock; successive 32-bit words map
  to successive banks.
- **Bank conflict:** multiple threads of a warp hitting different addresses in the same bank
  serialize (throughput / N for an N-way conflict). **Exception:** all threads reading the _same_
  address broadcasts/multicasts with no conflict.
- Canonical use: stage a coalesced global load into shared memory, then reorder/reuse from shared
  (e.g. transpose, reductions, GEMM tiles) to avoid uncoalesced or repeated global traffic.

## Asynchronous global→shared copy (CC 8.0+)

- Starting at **CC 8.0 (Ampere)**, `memcpy_async` / the `cp.async` (LDGSTS) instruction transfers
  global→shared **bypassing the register file and L1**, overlapping the copy with compute. On
  pre-8.0 it falls back to a synchronous load-then-store through registers.
- APIs:
  ```cpp
  // collective, per block
  cg::memcpy_async(block, dst, src, num_bytes);   cg::wait(block);
  // with a barrier
  cuda::memcpy_async(dst, src, cuda::aligned_size_t<4>(size), barrier);
  barrier.arrive_and_wait();
  // pipelined (multi-stage prefetch)
  cuda::pipeline<cuda::thread_scope_thread> p = cuda::make_pipeline();
  p.producer_acquire(); cuda::memcpy_async(dst, src, size, p); p.producer_commit();
  p.consumer_wait(); /* use dst */ p.consumer_release();
  ```
- Directions: global→shared (primary), shared→distributed-shared (clusters, CC 9.0), shared→global
  via TMA (CC 9.0+).

### Worked example: the CTranslate2 CUDA backend

This is the rulebook for the hand-written kernels in `src/ops/*_gpu.cu`:

- **Coalescing** governs the elementwise / transpose / gather-scatter kernels — e.g. transpose
  kernels in `primitives.cu`, `gather_gpu.cu`, `tile_gpu.cu`, `concat_split_slide_gpu.cu`. The
  `index_t` is deliberately 32-bit for addressing perf (`helpers.h:39`).
- **Shared memory + bank-conflict-free staging** underlies the block-reduction kernels:
  `layer_norm_gpu.cu:180`, `rms_norm_gpu.cu:26`, `mean_gpu.cu:26`, `topk_gpu.cu:187` use
  `cub::BlockReduce`, which manages shared-memory scratch for the reduction.
- Launch bounds come from `helpers.h`: `max_threads = 1024`, `max_blocks` (`helpers.h:41-42`).
- Most fill/copy/transform paths defer to Thrust (`THRUST_CALL`, `helpers.h:75-107`) rather than
  raw shared-memory kernels (see `thrust.md`); async-copy/`cp.async` is an available optimization
  for SM 8.0+ targets but is not required by the current op kernels. **Metal mirror:** the same
  coalescing + threadgroup-memory (= shared memory) discipline applies to the MSL kernels in the
  Apple-silicon backend.

### See also

- [[apple-silicon:msl-address-spaces]] — Metal twin of the device/shared/local memory spaces (device/threadgroup/thread).
- [[apple-silicon:occupancy-and-threadgroup-memory]] — occupancy math on the Metal side; gotcha: threadgroup memory caps at 32 KB vs CUDA's configurable shared memory.
- [[apple-silicon:resource-storage-modes-and-options]] — unified memory is the default reality on Apple silicon, not an opt-in abstraction.
- [[apple-silicon:compute-kernels-and-dispatch]] — launch-config twin; Metal dispatchThreads needs no tail bounds check.
- [[gpu-rosetta]] — CUDA↔Metal concept map.
