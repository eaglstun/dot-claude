---
name: ct2-internals
version: 1.0.0
public: true
description: >-
  CTranslate2 engine internals — the device/dtype-agnostic architecture below any compute
  backend. Use when working in src/ops, src/layers, src/models, the dispatch machinery,
  StorageView, or the Python specs/converters import pipeline: how an op is structured and
  dispatched, how tensors are represented, how transformer blocks are wired (norm
  placement etc.), and how external checkpoints become CT2 models.
semantic_id: "IVLTyoiEBuS8Iw2IWE5tzLMxpznH4AAL"
related_ids:
  - "AwLfy4gBBu48O87IcGdtrDUrrjFDMAAJ"
  - "JQryQhiEHqS8Y92JQkQ1aDMm5nFv8AAO"
topic_id: "v2:BNAO"
topic_path: "ct2-internals/device-runtime"
---

# CTranslate2 internals

Deep-dive references for the CTranslate2 engine's architecture — the parts that are true
regardless of CPU/CUDA/Metal. `CLAUDE.md` has the one-paragraph layer map (kernels →
primitives → ops → layers → models → replicas); this skill is the next level down, with
verified file:line citations into the real code.

**This is engine structure, not a compute backend.** Backend-specific material lives
elsewhere: the Apple **Metal** GPU backend is the `apple-silicon` skill (MSL kernels,
MPS, the op-graduation procedure). When a task is "how does CT2 do X" → here; when it's
"how do I make X run on the GPU" → `apple-silicon`.

## References

- **[references/dispatch-and-op-implementation.md](../../references/ct2-internals/dispatch-and-op-implementation.md)**
  The 4-file op pattern (flag-free header, checks+dispatch `.cc`, `_cpu.cc`, `_gpu.cu`) and the `DEVICE/TYPE_DISPATCH` macro family that resolves `<D, T>` at runtime, with the SoftMax walkthrough; read when adding or editing an op or tracing device+dtype selection.
- **[references/storageview.md](../../references/ct2-internals/storageview.md)**
  `StorageView`, the core row-major buffer-with-shape (no math semantics, runtime dtype/device) and the resize/reserve allocation contract where churn is a bug; read when touching tensor storage, allocation, or anything perf-sensitive about buffers.
- **[references/norm-placement-in-transformers.md](../../references/ct2-internals/norm-placement-in-transformers.md)**
  Where a norm sits in a transformer block (pre, post, four-norm sandwich auto-detect, parallel-residual) traced across specs, converters, and `transformer.cc`; read for block-structure norm tasks, the kernel/numerics side is the `apple-silicon` skill.
- **[references/attention-and-kv-cache.md](../../references/ct2-internals/attention-and-kv-cache.md)**
  `MultiHeadAttention` structure (fused QKV + Split, head layout transforms, GQA/MQA via Tile, RoPE apply with the offset trick, the KV cache grown one step per token by Concat plus Slide); read for decode-step data flow, GQA/RoPE, or before touching the cache.
- **[references/specs-and-converters.md](../../references/ct2-internals/specs-and-converters.md)**
  The import pipeline from external checkpoint through converter and spec to serialized model and the `model_factory.cc` loader, with the add-a-new-architecture checklist; read when adding model support or tracing how weights load.

### Quantization & model loading (int8 project, 2026-06)

- **[references/quantization-scheme-and-ops.md](../../references/ct2-internals/quantization-scheme-and-ops.md)**
  CT2's int8 scheme (symmetric per-row 127/amax, no zero-point, the `_qzero`/AWQ path scoped out; dynamic vs static scales; the Quantize ctor options and the TWO Dequantize overloads); read before touching anything quantized.
- **[references/gemm-op-and-dtype-dispatch.md](../../references/ct2-internals/gemm-op-and-dtype-dispatch.md)**
  `ops::Gemm` end-to-end (the dtype switch, the unconditional bias+activation epilogue, per-backend `primitives<D>::gemm`, the integer alpha/beta convention that is NOT an assert, the MKL u8-shift compensation story); read before touching any matmul path.
- **[references/dense-layer-and-quantized-linear.md](../../references/ct2-internals/dense-layer-and-quantized-linear.md)**
  `Dense::operator()` orchestration of quantize/gemm/dequantize vs plain GEMM vs AWQ, resolved from model variables and device-agnostic by construction (the int8-Metal project shipped with zero diff here); read before touching any linear layer.
- **[references/compute-type-resolution.md](../../references/ct2-internals/compute-type-resolution.md)**
  How requested `compute_type` becomes effective per-weight dtypes (the saved/requested/effective triple, the `mayiuse` capability queries, the AUTO fallback table where plain "int8" never silently un-quantizes, the Python surface); read before touching types.cc resolution or capability flags.
- **[references/weight-loading-and-conversion.md](../../references/ct2-internals/weight-loading-and-conversion.md)**
  The model-load weight pipeline in `src/models/model.cc` (register, quantize/dequantize/cast with scale pairing, device move), centered on the conv-weight float guard and the int8-Whisper load crash it prevents (commit 351b1990); read before changing load-time conversion or capability flags.
- **[references/model-binary-format.md](../../references/ct2-internals/model-binary-format.md)**
  The serialized model directory documented from both writer and reader ends (model.bin record layout, binary version 6 vs per-spec revision, the backward-compat STABLE SURFACE, alias dedup, config.json vs vocabulary files); read before touching serialization.

### Runtime core

- **[references/allocators-and-caching.md](../../references/ct2-internals/allocators-and-caching.md)**
  The `Allocator` abstraction behind `get_allocator(device)` (64-byte-aligned CPU allocator, the two CUDA allocators and their env knobs, StorageView owns the pointer); read before touching allocation or memory-churn perf.
- **[references/devices-and-device-management.md](../../references/ct2-internals/devices-and-device-management.md)**
  `Device` plumbing ("auto" resolution, per-backend device index incl. thread-global `cudaSetDevice`, `ScopedDeviceSetter`, `synchronize_device` vs `synchronize_stream`, how `device:index` reaches each replica); read for device plumbing or sync semantics.
- **[references/primitives-layer.md](../../references/ct2-internals/primitives-layer.md)**
  The `primitives<Device>` BLAS-like interface surveyed family-by-family, explicit instantiation per device (why a new Device case is expensive), and the CPU orchestration-vs-kernels.cc split; read when deciding where new array math belongs.
- **[references/cpu-isa-dispatch-and-kernels.md](../../references/ct2-internals/cpu-isa-dispatch-and-kernels.md)**
  Runtime ISA selection (`CT2_FORCE_CPU_ISA`, the per-ISA kernels.cc compile trick, `Vec<T,ISA>` widths) and the separate GEMM-backend priority chain (MKL→DNNL→Accelerate→OpenBLAS→Ruy); read before touching CPU kernels or vec headers.
- **[references/parallelism-and-thread-config.md](../../references/ct2-internals/parallelism-and-thread-config.md)**
  inter_threads (replica ThreadPool + queue backpressure) vs intra_threads (`parallel_for`, GRAIN_SIZE, the no-nesting rule), the OpenMP-vs-BS::thread_pool runtimes, and `set_num_threads` plumbing; read for any thread-count or CPU-perf question.

### Op families

- **[references/activation-ops.md](../../references/ct2-internals/activation-ops.md)**
  `ActivationType` (enum order is FIXED: serialized and reused as kernel selectors), the exact GELU/silu formulas, the three application sites that make fusion possible, and the converter mapping per model family; read before touching activations or their fusion path.
- **[references/softmax-and-masking.md](../../references/ct2-internals/softmax-and-masking.md)**
  SoftMax/LogSoftMax (always last-dim, the int32 lengths mask writing padding as exact 0, in-place forms) and where the 1/√d scale actually lives (the QK^T MatMul alpha, never a SoftMax param); read for attention masking or softmax numerics.
- **[references/norm-ops.md](../../references/ct2-internals/norm-ops.md)**
  LayerNorm vs RMSNorm numerics (eps defaults and eps inside the sqrt, beta-presence selects the op at load, Gemma's (1+gamma) as a runtime flag not baked weights); read for norm numerics/parity, placement is norm-placement-in-transformers.md.
- **[references/shape-manipulation-ops.md](../../references/ct2-internals/shape-manipulation-ops.md)**
  The decode-loop data movers (Concat, Split with `no_copy` views, Transpose, Tile, Slide, Gather with its strictly-increasing in-place fast path, metadata-only Squeeze/Unsqueeze); read for decode-step plumbing.
- **[references/elementwise-and-bias-ops.md](../../references/ct2-internals/elementwise-and-bias-ops.md)**
  Add/Sub/Mul/Min/Max broadcasting (scalar-b or same-size flat, nothing else, caller's contract) and `BiasAdd` as the separate axis-broadcast op carrying bias+residual+activation for fusion; read before touching elementwise or the bias path.

### Decode machinery

- **[references/decoding-loop-and-beam-search.md](../../references/ct2-internals/decoding-loop-and-beam-search.md)**
  The token-generation driver in `src/decoding.cc` (the per-step sequence, beam bookkeeping and cache reorder, batch shrinking as hypotheses finish, hard-prefix vs `BiasedDecoder`); read before touching the decode driver, per-op perf lives in `apple-silicon`.
- **[references/sampling-and-topk.md](../../references/ct2-internals/sampling-and-topk.md)**
  The sampler filter-pipeline order (top-k, temperature, `TopPMask`, Multinomial/GumbelMax), the TopK op contract, and the thread-local RNG story; sampling runs CPU-side on Metal over unified memory.
- **[references/logits-processing.md](../../references/ct2-internals/logits-processing.md)**
  The `LogitsProcessor` machinery (the `DisableTokens` collector, the five built-ins, the fixed ordering, Whisper's `ApplyTimestampRules`); note min_length is NOT a processor, it is `apply_min_length` in decoding.cc.
- **[references/batching-and-length-sorting.md](../../references/ct2-internals/batching-and-length-sorting.md)**
  `rebatch_input` longest-first sorting, tokens-vs-examples fill, promise-order restoration in `ReplicaPool::post_examples`, and the `Padder` gather-based padding removal (never for fp16 off-CPU); read before touching batching, pool plumbing, or padded shapes.
- **[references/position-encodings.md](../../references/ct2-internals/position-encodings.md)**
  The position-encoding family (additive Sinusoidal/learned, ALiBi, T5 relative bias vs Shaw-style, the full RoPE option table incl. "longrope"→Su); RoPE apply mechanics stay in attention-and-kv-cache.md.

### Models

- **[references/transformer-model-wiring.md](../../references/ct2-internals/transformer-model-wiring.md)**
  From spec config to constructed layer graph (the sequence factories, ctors resolving everything from scoped variables, tied embeddings via converter alias dedup with zero tying logic in C++, the spec-attribute defaults table); read before wiring or tracing model assembly.
- **[references/whisper-model-internals.md](../../references/ct2-internals/whisper-model-internals.md)**
  The Whisper surface (encode/generate/detect_language/align, the 2xConv1D+GELU stem, the `forward_prompt` prefill/decode split, no_speech, the align-to-DTW pipeline); ApplyTimestampRules mechanics stay in logits-processing.md.
- **[references/generator-and-language-model.md](../../references/ct2-internals/generator-and-language-model.md)**
  Decoder-only runtime (`Generator` pool with an async-only C++ surface, the two prefill paths incl. the cached static_prompt, scoring as a teacher-forced forward); the Qwen downstream driver is the canonical consumer.
- **[references/translator-and-seq2seq.md](../../references/ct2-internals/translator-and-seq2seq.md)**
  The seq2seq practical card (`translate_batch` flow, encode-to-decode handoff via `state["memory"]`, prefix vs scoring modes, the full options enforcement table, when attention is populated); the NLLB downstream driver is the enc-dec proof.

### Infrastructure, tests & bindings

- **[references/replica-pools-and-async-api.md](../../references/ct2-internals/replica-pools-and-async-api.md)**
  The header-only `ReplicaPool<Replica>` template (Job/JobQueue/Worker mechanics, `BatchJob`'s promise-per-result + exception fan-out contract, `ModelLoader` same-device model sharing, the greedy-only streaming callback); read for pool lifecycle.
- **[references/python-bindings-architecture.md](../../references/ct2-internals/python-bindings-architecture.md)**
  `python/cpp/*.cc` (the pool-config mapping, the three GIL release points, StorageView via `__array_interface__` not DLPack and no metal in the Python Device enum, the CTRANSLATE2_ROOT rebuild-then-wheel rule); read before touching bindings or wheel builds.
- **[references/vocabulary-and-tokenization-boundary.md](../../references/ct2-internals/vocabulary-and-tokenization-boundary.md)**
  `Vocabulary` (unk auto-appended, EOS-preserving truncation) and the tokens-in/tokens-out boundary (CT2 never tokenizes), plus vmap target-vocab restriction physically shrinking the output projection; read for vocab plumbing or the vmap feature.
- **[references/profiling-infrastructure.md](../../references/ct2-internals/profiling-infrastructure.md)**
  `ENABLE_PROFILING`/`PROFILE()` scoped timers (cross-thread aggregation, self-time subtraction, the stream sync at every scope boundary that distorts async backends, `--log_throughput`; `init_profiling` THROWS on a non-profiling build); read before perf-gating a change.
- **[references/logging-and-env-config.md](../../references/ct2-internals/logging-and-env-config.md)**
  spdlog wiring (`CT2_VERBOSE`) and the complete grepped env-var table, the operational debugging card; read before reaching for an env knob since several folklore vars don't exist (`CT2_NO_MPS_ACT` was removed with the Gemma2 fix).
- **[references/ops-test-suite-structure.md](../../references/ct2-internals/ops-test-suite-structure.md)**
  The C++ test suite (value-parameterized device/dtype fixtures with per-backend tolerances, METAL fp32-only + skips, `expect_storage_eq`, the 5-step recipe for an op test covering all devices free); the oracle, read before adding or judging tests.
- **[references/cuda-backend-structure.md](../../references/ct2-internals/cuda-backend-structure.md)**
  The CUDA backend as the reference GPU backend (shared infra vs per-op `_gpu.cu` layout, thread-local stream/handles, the `cublasGemmEx` dtype table, CUDA as a real `DEVICE_CASE`, the three properties int8-Metal mirrored); read before structuring any new backend work.

### Weights & projections

- **[references/embeddings-and-output-projection.md](../../references/ct2-internals/embeddings-and-output-projection.md)**
  The bookends: `Embeddings` as Gather (the table CAN be int8, with gathered-scale Dequantize), the √d scale applied by the model not the layer, `Dense` as lm_head in embedding layout so tying needs no transpose, and vocab restriction; temperature is sampling, not here.
- **[references/conv1d-op.md](../../references/ct2-internals/conv1d-op.md)**
  Conv1D (ctor options, CPU im2col+GEMM vs DNNL direct vs cuDNN) and the dtype matrix where exactly ONE backend runs int8 conv (CPU-without-DNNL), with the Whisper stem and wav2vec2 as the only users; the Metal graduation bridge is mps-convolution-options.md.
- **[references/converter-quantization-and-fusion.md](../../references/ct2-internals/converter-quantization-and-fusion.md)**
  What converters do to weights beyond layout (`_quantize` eligibility where embeddings/conv ARE quantizable but norms/biases never, the AWQ bypass, `fuse_linear` QKV concat while gate+up stays unfused, alias-before-quantize ordering); cross-refs compute-type-resolution + weight-loading.

### Layers, features & tooling

- **[references/feed-forward-network-layer.md](../../references/ct2-internals/feed-forward-network-layer.md)**
  `FeedForwardNetwork` (standard 2-linear vs GLU where weight presence IS the flag, the residual fused into `_ff2` only when the FFN owns its norm, the converter gate/up mapping); activation formulas stay in activation-ops.md, placement in norm-placement.
- **[references/decoder-state-contract.md](../../references/ct2-internals/decoder-state-contract.md)**
  The `DecoderState` map contract (per-layer key/value entries created empty as the first-step signal, the `memory` handoff and post-step-0 erase, why `memory*` keys are never beam-replicated, the dim-0-is-batch Gather contract); update mechanics in decoding-loop, growth in attention-and-kv-cache.
- **[references/encoder-models-and-wav2vec2.md](../../references/ct2-internals/encoder-models-and-wav2vec2.md)**
  The encoder-only surface (`Encoder` pool, forward output with optional CLS-gather pooler, the BERT/XLM-R/Roberta loaders, and the two audio encoders Wav2Vec2 and Wav2Vec2Bert); pool machinery is replica-pools.
- **[references/flash-attention-integration.md](../../references/ct2-internals/flash-attention-integration.md)**
  `WITH_FLASH_ATTN` vendored FA2 (self-attention ONLY, the structural deltas like heads-last layout and preallocated cache chunks, and what's unsupported); CUDA-only, Metal's attention stays op-composed.
- **[references/tensor-parallel.md](../../references/ct2-internals/tensor-parallel.md)**
  `WITH_TENSOR_PARALLEL` (one MPI process per rank, load-time name-classified weight sharding with NO spec markers, the per-sublayer allreduce points, and the rename-a-spec-weight silent-missharding trap); CUDA-only, throws off-CUDA.
- **[references/transformers-converter-loaders.md](../../references/ct2-internals/transformers-converter-loaders.md)**
  Inside the HF converter (the `@register_loader` registry keyed by HF config class name, the loader hook order, the stale-install Qwen2 trap, and `Qwen2Loader` walked end-to-end); read before adding or extending an HF loader.
- **[references/cli-clients-and-perf-gating.md](../../references/ct2-internals/cli-clients-and-perf-gating.md)**
  `ct2-translator`, the only CLI (the full flag surface incl. --device accepting "metal" despite the help text, the streaming read-ahead loop, the worked --log_throughput gating recipe); the operator card, flag mechanics live in profiling-infrastructure.md.
- **[references/python-high-level-extensions.md](../../references/ct2-internals/python-high-level-extensions.md)**
  `extensions.py`, the complete is-it-C++-or-Python card (the seven monkey-patched methods, the callback-to-queue generator bridge with forced greedy, the 16x prefetch); read before touching token streaming or batch iterables.
- **[references/model-reader-abstraction.md](../../references/ct2-internals/model-reader-abstraction.md)**
  `ModelReader` (the filename-to-istream contract, `ModelFileReader` vs the zero-copy `ModelMemoryReader` embed-in-app path, the exact file request sequence); short card, contents of those files are model-binary-format.md.
- **[references/downstream-validation-harness.md](../../references/ct2-internals/downstream-validation-harness.md)**
  The OTHER oracle: `scripts/validate-downstream.sh` builds, installs, and wheels into 4 consumer venvs and diffs against fp16-on-Metal goldens (the 2026-06-11 int8 run went 4/4 and caught the conv guard); the loose end-to-end gate.

## Conventions & maintenance

- **Pull the matching reference before reasoning about engine structure — do not
  answer from memory.** The dispatch machinery and layer wiring are exactly the
  places where a plausible-sounding recollection is wrong.
- **Line numbers here cite a snapshot and DRIFT.** Run `bash scripts/audit-citations.sh`
  (`-q` for problems-only) before trusting any file:line, and re-grep the symbol rather
  than the line; a "verified on DATE" note is worthless once the file is touched again.
- See the shelf README (`../../references/ct2-internals/README.md`) for the
  add-a-reference recipe and the citation/crosslink conventions moved out of this index.
