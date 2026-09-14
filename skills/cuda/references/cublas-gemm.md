---
topic_id: "v2:KGOA"
topic_path: "cuda-gpu"
semantic_id: "9DmanK-d-bnvzMKUi9D7S_tgoMUjsAAE"
related_ids:
  - "-nhW1t8U_Zkt9M6eGjST57VRuZBj0AAM"
  - "0mnR7stG7fNg3LIWD1BqB5blqlwSMAAF"
---
# cuBLAS GEMM surface — `cublasGemmEx` & cuBLASLt `cublasLtMatmul`

**Source:** https://docs.nvidia.com/cuda/cublas/index.html
**Fetched:** 2026-06-29 (cuBLAS docs, CUDA Toolkit 13.x)

**What it's for:** The mixed-precision GEMM entry points CT2 leans on. `cublasGemmEx` is the
single-call, explicit-dtype GEMM (operands + output + accumulation type chosen independently);
cuBLASLt (`cublasLtMatmul`) is the newer descriptor-based GEMM with epilogue fusion and explicit
algorithm/heuristic selection.

## `cublasGemmEx`

```c
cublasStatus_t cublasGemmEx(cublasHandle_t handle,
                            cublasOperation_t transa,
                            cublasOperation_t transb,
                            int m, int n, int k,
                            const void *alpha,
                            const void *A, cudaDataType_t Atype, int lda,
                            const void *B, cudaDataType_t Btype, int ldb,
                            const void *beta,
                            void *C, cudaDataType_t Ctype, int ldc,
                            cublasComputeType_t computeType,
                            cublasGemmAlgo_t algo)
```

Computes `C = alpha * op(A) * op(B) + beta * C`. `alpha`/`beta` are pointers whose pointee type
follows `computeType` (e.g. `float` for `CUBLAS_COMPUTE_32F`, `int32_t` for `CUBLAS_COMPUTE_32I`,
`__half` for `CUBLAS_COMPUTE_16F`). cuBLAS is **column-major**, so a row-major C = A·B is issued as
a swapped B·A (this is exactly what CT2 does).

### `cublasComputeType_t` (CUDA 11.0+; replaced the old `cudaDataType` compute arg)

- `CUBLAS_COMPUTE_16F` — half-precision accumulate (default for fp16 ops).
- `CUBLAS_COMPUTE_32F` — fp32 accumulate.
- `CUBLAS_COMPUTE_32F_FAST_16F` — fp32 I/O, Tensor Cores w/ down-convert to fp16 compute.
- `CUBLAS_COMPUTE_32F_FAST_TF32` — TF32 Tensor-Core path (round-to-nearest-even on input convert);
  needs SM 8.0+ (Ampere).
- `CUBLAS_COMPUTE_32I` — int32 accumulate (the int8 path).
- `CUBLAS_COMPUTE_64F` — double accumulate.

### `cublasGemmAlgo_t`

- `CUBLAS_GEMM_DEFAULT` — heuristic selection (use this on modern arch).
- `CUBLAS_GEMM_DEFAULT_TENSOR_OP` — heuristic, prefer Tensor Cores (now largely folded into DEFAULT).
- `CUBLAS_GEMM_ALGO0`..`ALGO23` — explicit algo IDs; **no effect on sm_80+** (ignored, heuristic used).

### Data-type combos (the ones CT2 uses)

| Atype/Btype          | Ctype                      | computeType                      | Arch needed                                      |
| -------------------- | -------------------------- | -------------------------------- | ------------------------------------------------ |
| `CUDA_R_8I` (s8)     | `CUDA_R_32I` (s32)         | `CUBLAS_COMPUTE_32I`             | int8 IMMA Tensor Cores SM 7.2+/7.5; DP4A SM 6.1+ |
| `CUDA_R_16F` (fp16)  | `CUDA_R_16F`/`CUDA_R_32F`  | `CUBLAS_COMPUTE_16F`/`32F`       | HMMA Tensor Cores SM 7.0+                        |
| `CUDA_R_16BF` (bf16) | `CUDA_R_16BF`/`CUDA_R_32F` | `CUBLAS_COMPUTE_32F`             | bf16 Tensor Cores SM 8.0+                        |
| `CUDA_R_32F`         | `CUDA_R_32F`               | `CUBLAS_COMPUTE_32F[_FAST_TF32]` | TF32 path SM 8.0+                                |

cuBLAS Tensor-Core paths require **compute capability 7.0+** and benefit from 16-byte-aligned
pointers and leading dimensions (`lda`/`ldb`/`ldc` × element size divisible by 16).

## cuBLASLt — `cublasLtMatmul`

cuBLASLt is "a lightweight library dedicated to GEMM operations with a new flexible API" — matrix
layouts, input/compute types, and algorithm choice are all expressed via descriptor objects
(`cublasLtMatmulDesc_t`, `cublasLtMatrixLayout_t`, `cublasLtMatmulAlgo_t`) that can be cached and
reused. It is the recommended surface for fused epilogues (bias + activation) and for the IMMA int8
GEMM with the `CUBLASLT_ORDER_COL32` / IMMA-specific layouts. Available since CUDA 10.1.
`cublasLtMatmul()` takes a preference + heuristic result and runs the configured matmul. CT2's
current GEMM wrappers use the simpler `cublasGemmEx` rather than cuBLASLt; epilogue fusion is done
in CT2's own `dequantize_gpu.cu` kernel instead.

## Legacy / deprecation note

The typed `cublasSgemm`/`cublasHgemm` calls still exist (CT2 uses `cublasSgemm` for the f32→f32
path), but mixed-precision and Tensor-Core control should go through `cublasGemmEx`/cuBLASLt. The
old `cublasGemmEx` signature that took a `cudaDataType` compute arg was superseded by
`cublasComputeType_t` in CUDA 11.0.

### Worked example: the CTranslate2 CUDA backend

This is the exact core of `primitives<Device::CUDA>::gemm` in `src/cuda/primitives.cu`, one explicit
specialization per dtype combo (`cuda-backend-structure.md` §3):

- **f32→f32** → `cublasSgemm` (`primitives.cu:487-506`).
- **f16→f16** → `cublasGemmEx` with `CUDA_R_16F` + `CUBLAS_COMPUTE_16F`, or `_32F` with float
  alpha/beta when `use_true_fp16_gemm()` is off (`CT2_CUDA_TRUE_FP16_GEMM`, `utils.cc:260`;
  `primitives.cu:510-544`).
- **bf16→bf16** → `cublasGemmEx`, `CUDA_R_16BF` + `CUBLAS_COMPUTE_32F` (`primitives.cu:548-569`).
- **int8→int32** → `cublasGemmEx`, operands `CUDA_R_8I`, output `CUDA_R_32I`, `CUBLAS_COMPUTE_32I`,
  alpha/beta truncated to int32 (`primitives.cu:573-597`). cuBLAS is natively signed s8s8s32, so the
  `a_shift_compensation` param is unnamed/ignored (`primitives.cu:581`) — no u8-shift. Scale+bias+
  activation run **after** the GEMM in the fused epilogue kernel `dequantize_gpu.cu:40-52`.
  All calls swap A/B for column-major (comment `primitives.cu:496`) and go through `CUBLAS_CHECK`
  (`utils.h:68-90`) on the thread's cached `get_cublas_handle()`. Compute-type resolution is gated by
  `gpu_has_fp16_tensor_cores`/`gpu_has_int8_tensor_cores`/`gpu_supports_int8` (see
  `compute-capability-tensor-cores.md`). **Metal mirror:** `metal::gemm_s8` (signed s8, int32 accum,
  `src/ops/gemm.cc:113`) + `dequantize_gemm_output_s8` epilogue.

### See also

- [[apple-silicon:mps-matrix-multiplication]] — Metal twin: MPS GEMM the CT2 Metal backend calls where CUDA calls cuBLAS.
- [[apple-silicon:gemm-layouts-and-transpose-conventions]] — layout gotcha across the pair: cuBLAS is column-major by convention, MPS descriptors are row-major.
- [[gpu-rosetta]] — CUDA↔Metal concept map.
