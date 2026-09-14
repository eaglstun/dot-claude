# Browser and JavaScript embedding

Sources:

- https://webassembly.github.io/spec/js-api/
- https://webassembly.github.io/spec/web-api/
- https://developer.mozilla.org/en-US/docs/WebAssembly/Guides/Using_the_JavaScript_API
- https://developer.mozilla.org/en-US/docs/WebAssembly/Reference/JavaScript_interface/instantiateStreaming_static
- https://web.dev/articles/coop-coep

## 1. Loading

Prefer `WebAssembly.instantiateStreaming(fetch(url), imports)` when the server
sends `Content-Type: application/wasm`. It can compile while bytes arrive.
Fallback to `fetch` + `arrayBuffer` + `instantiate` when response rewriting or a
misconfigured server makes streaming unavailable.

Compile a `WebAssembly.Module` once and instantiate it repeatedly when instances
need separate state. Use module/compiled-code caching appropriate to the host;
do not build a handwritten persistent cache around engine-internal formats.

## 2. Boundary types

Imports are nested by module and name. Missing or type-incompatible imports cause
link errors. Exported functions are JS-callable. Numeric conversion follows the
JS API: `i64` uses `BigInt`, not Number. Linear-memory structures require typed
arrays/DataView and an explicit ABI; use little-endian DataView operations.

For strings, generated glue usually manages allocation, UTF encoding, pointer/
length passing, result lifting, and cleanup. Manual glue must do all five.

## 3. Errors and policies

Distinguish `CompileError` (decode/validate), `LinkError` (imports), and
`RuntimeError` (trap). A rejected fetch is an ordinary network/HTTP failure.

Strict Content Security Policy can require an appropriate Wasm execution source
policy. Threaded modules require shared memory, atomics, Workers, and cross-origin
isolation (COOP/COEP); feature-detect and provide a non-threaded build when needed.

## 4. Boundary design

Batch work across JS↔Wasm rather than calling once per scalar in a hot loop.
Keep authoritative ownership of buffers clear. When JS and Wasm share a memory,
pass offsets/lengths, refresh views after growth, and avoid retaining a view
across a call that can allocate.

## Gotchas

- `instantiate(bytes)` and `instantiate(module)` return differently shaped
  results in JavaScript APIs; destructure only after checking which overload ran.
- Streaming compilation fails without the Wasm MIME type.
- `i64` exports require `BigInt`.
- A typed-array view may be detached after Wasm grows memory during a call.
- Shared-memory support in the engine is not enough; browser isolation headers
  are also required.

