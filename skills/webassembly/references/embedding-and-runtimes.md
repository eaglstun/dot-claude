# Embedding and runtimes

Sources:

- https://docs.wasmtime.dev/
- https://docs.wasmtime.dev/security.html
- https://wasmer.io/docs
- https://bytecodealliance.github.io/wasm-micro-runtime/
- https://github.com/wasm3/wasm3
- https://v8.dev/docs/wasm-compilation-pipeline

## 1. Choose by constraints

Wasmtime is a strong default for server/desktop embedding and Component Model/
WASI work. Wasmer provides multiple engines and broad language integrations.
WAMR targets embedded/IoT footprints. wasm3 is an interpreter useful where JITs
are unavailable or simplicity matters. Browser/Node/Deno/Bun hosts use their JS
engine APIs and policies. Verify maintenance, target architecture, proposal
support, licensing, and bindings for the deployed version.

## 2. Compilation modes

JIT/tiered compilation favors startup plus peak throughput; ahead-of-time
compilation can improve predictable startup and environments that forbid
runtime code generation; interpretation minimizes compiler footprint but costs
throughput. Serialized compiled artifacts are generally runtime-version/target
specific and untrusted cache entries must be handled per runtime guidance.

## 3. Host contract

Create an engine/configuration, compile a module/component, link imports, create
a store/context, instantiate, then invoke typed exports. Keep stores and guest
values within the runtime's lifetime/threading rules. Host callbacks must not
retain borrowed guest pointers across calls or memory growth.

For untrusted work configure memory/table/instance limits, stack limits, fuel or
epoch interruption, deadlines, and allowed WASI resources. Reuse compiled code;
use instance pooling only when reset/isolation semantics are understood.

## 4. Failure classes

Separate compile/validation errors, missing imports, instantiation/start traps,
guest traps, host callback failures, resource-limit interruption, and host
process failure. Preserve the trap backtrace and producer debug metadata in
diagnostic builds.

## Gotchas

- Runtime APIs and serialized artifacts are not a stable cross-version ABI.
- Fuel counts implementation-defined units, not milliseconds.
- Interrupting execution does not automatically roll back host side effects.
- A runtime's sandbox cannot constrain an overpowered host import.
- Reusing an instance can leak guest state between tenants.

