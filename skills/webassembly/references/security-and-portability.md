# Security and portability

Sources:

- https://webassembly.github.io/spec/core/intro/introduction.html#security-considerations
- https://webassembly.org/docs/security/
- https://docs.wasmtime.dev/security.html
- https://github.com/WebAssembly/WASI/blob/main/wasip2/README.md
- https://web.dev/articles/coop-coep

## 1. What the sandbox guarantees

Validated core code cannot directly address outside its declared memories and
cannot invoke capabilities absent from its imports. Control flow and indirect
calls are type checked. This isolates the guest from arbitrary host memory, but
does not make the guest correct, confidential, terminating, or safe from every
microarchitectural side channel.

Within linear memory, ordinary C/C++ bugs still exist: overflowed lengths,
use-after-free, double free, data races, and application-level corruption.

## 2. The host is the authority boundary

Imports are capabilities. Give each guest the minimum filesystem roots,
network endpoints, environment values, clocks/randomness, and host functions it
needs. Validate every pointer/length and semantic argument in a host callback;
guest-supplied offsets can be valid memory addresses but malicious data.

Configure upper bounds for memories, tables, instances, stacks, compilation,
execution (fuel/deadline/epoch), output, and host resource use. Treat guest traps
as request failures, not host-process crashes. Isolate tenants at a stronger
boundary when engine compromise is in the threat model.

## 3. Portability

Pin or feature-detect the core proposal set, artifact kind, WASI/Component Model
version, ABI, runtime version range, and CPU/runtime options. Integer behavior is
portable; floating-point NaN details, host imports, resource limits, and thread
scheduling may differ. Test big workloads near limits, not only validity.

Browser threads require COOP/COEP and change page integration. CSP can block
compilation. Server runtimes may disable JIT or proposals by policy.

## 4. Supply chain

Record source/toolchain versions, lock dependencies, validate artifacts, and
hash/sign releases where appropriate. A valid module can still contain hostile
logic. Do not deserialize runtime-native compiled caches from untrusted sources
unless the runtime explicitly guarantees safe validation.

## Gotchas

- “Sandboxed” does not mean “may receive all host imports.”
- Fuel/deadlines do not undo filesystem or network side effects already made.
- Linear-memory safety is bounds isolation, not source-language memory safety.
- A valid Wasm file can intentionally consume excessive CPU/memory.
- Cross-engine portability stops at unspecified host behavior and unsupported
  features.

