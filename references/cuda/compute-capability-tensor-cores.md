---
topic_id: "v2:KJLG"
topic_path: "cuda-gpu/tensor-parallelism"
semantic_id: "enk0fq4US4C077zyvNeCdXFQmRzqkAAP"
related_ids:
  - "Zik2asZFTCSP7_neJMQO9XFwuz7ikAAN"
  - "_nlTTvsU1Uis4LDSENewQfVQuZbh0AAO"
---
# Compute capability & Tensor-Core feature matrix

**Sources:**

- https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/compute-capabilities.html
- https://github.com/NVIDIA/cutlass/blob/main/media/docs/cpp/functionality.md (arch→opclass→dtype table)
  **Fetched:** 2026-06-29 (CUDA C++ Programming Guide 13.3; CUTLASS main)

**What it's for:** Compute capability (CC) "major.minor" identifies the SM architecture and gates
which dtypes and Tensor-Core instructions a GPU supports. CT2 turns CC into the boolean feature
gates that drive GEMM compute-type resolution.

## Querying compute capability

- Runtime: `cudaGetDeviceProperties(&prop, dev)` → `prop.major`, `prop.minor`; or
  `cudaDeviceGetAttribute(&v, cudaDevAttrComputeCapabilityMajor, dev)` /
  `cudaDevAttrComputeCapabilityMinor`.
- Driver: `cuDeviceGetAttribute(...)`. NVML: `nvmlDeviceGetCudaComputeCapability`.

## CC → architecture

| CC              | Architecture |
| --------------- | ------------ |
| 6.0 / 6.1 / 6.2 | Pascal       |
| 7.0 / 7.2       | Volta        |
| 7.5             | Turing       |
| 8.0 / 8.6 / 8.7 | Ampere       |
| 8.9             | Ada Lovelace |
| 9.0             | Hopper       |
| 10.x / 12.x     | Blackwell    |

(The 13.3 appendix narrative explicitly names 7.x Volta, 8.x Ampere, 9.0 Hopper, 10.x/12.x
Blackwell; the older-arch names above are the long-standing NVIDIA mapping and the CUTLASS SM tags.)

## Math-instruction / dtype gating (from the CUTLASS SM table)

| SM (CC)                        | Opclass                 | Operation                                       | Meaning                             |
| ------------------------------ | ----------------------- | ----------------------------------------------- | ----------------------------------- |
| SM50/60+                       | Simt                    | `f32*f32+f32`, `f64*f64+f64`                    | baseline FMA                        |
| SM60+                          | Simt                    | `f16*f16+f16`                                   | fp16 SIMT (no Tensor Cores)         |
| **SM61+ (6.1)**                | Simt                    | `s8*s8+s32`                                     | **DP4A** 8-bit integer dot product  |
| **SM70+ (7.0 Volta)**          | TensorOp / WmmaTensorOp | `f16*f16+{f16,f32}`                             | **HMMA** fp16 Tensor Cores          |
| **SM72/SM75 (7.2/7.5 Turing)** | TensorOp / WmmaTensorOp | `s8*s8+s32`                                     | **IMMA** int8 Tensor Cores          |
| **SM80+ (8.0 Ampere)**         | TensorOp                | `bf16*bf16+f32`, `tf32*tf32+f32`, `f64*f64+f64` | bf16 / **TF32** / fp64 Tensor Cores |
| SM90a+ (9.0 Hopper)            | TensorOp                | wgmma incl. FP8 (e4m3/e5m2)                     | 4th-gen Tensor Cores                |

CUTLASS lists CUDA Toolkit **11.4+** for the SM70–SM80 Tensor-Core paths and **12.0+** for SM90a.
DP4A int8 (SM61) predates Tensor Cores — it accelerates int8 dot products on CUDA cores, which is
why int8 GEMM "works" (just slower) from 6.1 even without IMMA. The Programming Guide notes the
architecture-specific Tensor-Core feature set "is strongly recommended" to be used through CUDA-X
libraries (cuBLAS, cuDNN), not raw MMA.

## The three thresholds that matter for CT2

- **int8 supported at all** → CC ≥ 6.1 (DP4A).
- **fp16 Tensor Cores (HMMA)** → CC ≥ 7.0.
- **int8 Tensor Cores (IMMA)** → CC ≥ 7.2 (and 7.5 Turing).
- **bf16 / TF32 Tensor Cores** → CC ≥ 8.0.

### Worked example: the CTranslate2 CUDA backend

These thresholds are coded verbatim in `src/cuda/utils.cc` as capability queries
(`cuda-backend-structure.md` §1):

- `gpu_supports_int8` = CC ≥ **6.1** (`utils.cc:225-228`) — DP4A row above.
- `gpu_has_int8_tensor_cores` = CC ≥ **7.2** (`utils.cc:230-233`) — IMMA row above.
- `gpu_has_fp16_tensor_cores` = CC ≥ **7.0** (`utils.cc:235-238`) — HMMA row above.
  These feed `mayiuse_*` in compute-type resolution, choosing the `cublasComputeType_t` and whether a
  Tensor-Core GEMM path is taken in `primitives.cu` (see `cublas-gemm.md`). CC is read from the
  `thread_local` per-device cache `get_device_properties` (`utils.cc:187-203`). **Metal mirror:** the
  Apple-GPU backend has no CC; it gates on `MTLGPUFamily` / `supportsFamily` and its own
  `gpu_has_*`-style checks — the int8-Metal work mirrored these three boolean gates conceptually.

### See also

- [[apple-silicon:mtlgpufamily-and-feature-availability]] — Metal twin of compute-capability gating (MTLGPUFamily instead of sm_XX).
- [[apple-silicon:simdgroup-matrix-functions]] — Metal twin of Tensor Core matrix ops (simdgroup_matrix; see also metal4-tensors-and-mpp there).
- [[gpu-rosetta]] — CUDA↔Metal concept map.
