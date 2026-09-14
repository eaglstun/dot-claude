---
topic_id: "v2:KMKN"
topic_path: "cuda-gpu/warp-primitives"
semantic_id: "ahwaEeJKV9jmIJzAspO1WXUsqVTpkAAK"
related_ids:
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
  - "uRQVFGAIhoD_Ix3q4IO9V39PStm1sAAK"
---
# CUDA Runtime API — streams & events

**Sources:**

- https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__STREAM.html
- https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EVENT.html
  **Fetched:** 2026-06-29 (CUDA Runtime API, Toolkit 13.x)

**What it's for:** Streams are ordered queues of device work; operations in one stream are serialized,
operations in different streams may overlap. Events are markers recorded into a stream, used for
cross-stream dependencies and for host-side timing. This is the handle/stream model CT2 caches
per-thread.

## Streams

```c
__host__            cudaError_t cudaStreamCreate(cudaStream_t *pStream);
__host__ __device__ cudaError_t cudaStreamCreateWithFlags(cudaStream_t *pStream, unsigned int flags);
__host__ __device__ cudaError_t cudaStreamDestroy(cudaStream_t stream);
__host__            cudaError_t cudaStreamSynchronize(cudaStream_t stream);
__host__ __device__ cudaError_t cudaStreamWaitEvent(cudaStream_t stream, cudaEvent_t event,
                                                    unsigned int flags = 0);
__host__            cudaError_t cudaStreamQuery(cudaStream_t stream);   // cudaSuccess | cudaErrorNotReady
```

- `cudaStreamCreate` creates an async stream on the context current to the **calling host thread**.
- Flags for `cudaStreamCreateWithFlags`:
  - `cudaStreamDefault` (0) — implicitly synchronizes with the NULL/default stream.
  - `cudaStreamNonBlocking` — "work in the created stream may run concurrently with work in stream 0
    (the NULL stream)… no implicit synchronization with stream 0."
- `cudaStreamSynchronize` blocks the host until all work in the stream completes; `cudaStreamQuery`
  is the non-blocking poll.
- `cudaStreamWaitEvent` makes a stream wait on an event recorded (possibly) in another stream — the
  primitive for cross-stream ordering without a host sync.

### Default stream semantics

- **Legacy default stream** (stream 0 / NULL): a single, process-wide stream that implicitly
  synchronizes with all other (blocking) streams.
- **Per-thread default stream**: each host thread gets its own implicit default stream that does
  **not** serialize against other threads' default streams. Selected by the nvcc flag
  `--default-stream per-thread` or by defining `CUDA_API_PER_THREAD_DEFAULT_STREAM` before including
  CUDA headers. The explicit handle is `cudaStreamPerThread`. Available since **CUDA 7.0**.

## Events

```c
__host__            cudaError_t cudaEventCreate(cudaEvent_t *event);              // uses cudaEventDefault
__host__ __device__ cudaError_t cudaEventCreateWithFlags(cudaEvent_t *event, unsigned int flags);
__host__ __device__ cudaError_t cudaEventDestroy(cudaEvent_t event);
__host__ __device__ cudaError_t cudaEventRecord(cudaEvent_t event, cudaStream_t stream = 0);
__host__            cudaError_t cudaEventSynchronize(cudaEvent_t event);
__host__            cudaError_t cudaEventQuery(cudaEvent_t event);                // cudaSuccess | cudaErrorNotReady
__host__            cudaError_t cudaEventElapsedTime(float *ms, cudaEvent_t start, cudaEvent_t end);
```

- `cudaEventRecord` "captures in event the contents of stream at the time of this call."
- `cudaEventSynchronize` waits until all work captured in the event completes.
- `cudaEventElapsedTime` gives ms between two recorded events, **resolution ~0.5 µs**. Both events
  must have completed and must have been created **with timing enabled** (i.e. not
  `cudaEventDisableTiming`).
- Flags:
  - `cudaEventDefault` — standard, timing enabled.
  - `cudaEventBlockingSync` — host thread waiting via `cudaEventSynchronize` blocks (yields CPU)
    instead of spin-waiting.
  - `cudaEventDisableTiming` — no timing data; best perf for pure stream-wait/sync use.
  - `cudaEventInterprocess` — IPC event (requires `cudaEventDisableTiming`).

### Worked example: the CTranslate2 CUDA backend

CT2 runs **one stream + one cuBLAS/cuDNN handle per host thread**, created lazily and cached
`thread_local` (`src/cuda/utils.cc:119-120`, `cuda-backend-structure.md` §2):

- `get_cuda_stream()` (`utils.cc:122-125`) — `static thread_local CudaStream`. The **main thread
  uses the default stream** (it loads replicas across devices); every other thread gets its own
  `cudaStreamCreate`d stream bound to its current device (`utils.cc:70-98`). Because each replica
  worker is its own thread, this yields independent streams with zero locking — the per-thread-default
  pattern, just done explicitly with named streams rather than `--default-stream per-thread`.
- `get_cublas_handle()`/`get_cudnn_handle()` (`utils.cc:127-155`) bind the handle to that thread's
  stream via `cublasSetStream`. Stream/handle destruction re-enters the creating device via
  `ScopedDeviceSetter` (`include/ctranslate2/devices.h:33-54`) since the current device is
  thread-global state.
- All runtime calls are wrapped by `CUDA_CHECK` (`utils.h:68-90`). `THRUST_CALL` runs Thrust on the
  calling thread's stream (`utils.h:136-141`). **Metal mirror:** per-thread `MTLCommandQueue` /
  `MTLCommandBuffer` plays the role of the stream; the cached-handle pattern is the same.

### See also

- [[apple-silicon:concurrent-dispatch-and-encoder-semantics]] — Metal twin of streams: serial command queues + explicitly committed command buffers (no implicit current stream).
- [[apple-silicon:mtlevent-and-mtlfence]] — Metal twin of CUDA events for cross-queue/encoder sync.
- [[gpu-rosetta]] — CUDA↔Metal concept map.
