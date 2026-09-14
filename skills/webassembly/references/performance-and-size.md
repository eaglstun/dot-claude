# Performance and code size

Sources:

- https://v8.dev/docs/wasm-compilation-pipeline
- https://emscripten.org/docs/optimizing/Optimizing-Code.html
- https://github.com/WebAssembly/binaryen/wiki/wasm-opt
- https://docs.wasmtime.dev/examples-profiling.html
- https://github.com/WebAssembly/simd

## 1. Measure the deployed path

Separate download/decompression, decode/validation, compile, instantiate/start,
warmup/tiering, steady-state execution, and host-boundary costs. Cache state and
runtime tiering make first and later runs incomparable. Benchmark the production
runtime, CPU class, feature flags, input sizes, and glue.

Profile before changing source. Browser performance tools, runtime profiling,
native perf maps, and producer source maps/DWARF each expose different layers.

## 2. Common dominant costs

- Too many fine-grained host↔guest calls.
- Copying/encoding strings and buffers across the boundary.
- Allocator churn or memory growth.
- Shipping a language runtime/unused library code.
- Missed inlining/vectorization due to ABI boundaries or indirect calls.
- Compilation startup for short-lived instances.

Batch operations, reuse guest buffers, and keep hot loops on one side of the
boundary. Confirm ownership and memory-growth safety before eliminating copies.

## 3. Compiler and binary optimization

Use release optimization and LTO where measured. `-O3` can increase code size;
`-Os`/`-Oz` may improve download and instruction-cache behavior. Binaryen's
`wasm-opt` can run post-link passes; use the intended feature set and test after
transformations. Compress for transport, but report both wire size and decoded
size.

SIMD can deliver large wins for suitable data-parallel loops when producer and
consumer enable it. Threads help only after accounting for worker startup,
cross-origin isolation, contention, and shared-memory limits.

## 4. Size accounting

Use section-level tools to find code, data, debug/custom metadata, and embedded
runtime costs. Strip symbols only from delivery artifacts. Lazy-load secondary
modules/components if latency and caching improve in the actual app.

## Gotchas

- A microbenchmark omitting JS glue and copies can invert the real result.
- `-O3` is not always faster and is often larger.
- `wasm-opt` output still needs full integration tests.
- Memory reservation and committed memory are not the same metric.
- SIMD/threads require a compatibility baseline and fallback strategy.

