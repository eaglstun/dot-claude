# Standards and features

Sources:

- https://webassembly.github.io/spec/core/
- https://www.w3.org/TR/wasm-core-2/
- https://github.com/WebAssembly/proposals
- https://webassembly.org/features/
- https://github.com/WebAssembly/component-model
- https://wasi.dev/

## 1. Layered standards

Core WebAssembly specifies instruction semantics, validation, binary/text
formats, and abstract embedding. Separate JS and Web APIs define browsers.
WASI defines portable host interfaces. The Component Model defines components,
WIT-facing types, canonical ABI, and composition. A version number in one layer
does not imply support for a version in another.

Core 1.0 established MVP numeric code, one linear memory/table model and basic
JS embedding. Later standardized releases incorporate mature additions in
bundles; WebAssembly 3.0 is the current specification baseline as of this
shelf's August 2026 creation. Engines may ship individual proposals before or
after their inclusion in a numbered spec.

## 2. Proposal maturity is not deployment support

The proposals repository tracks phases, but a phase is a standards-process
signal, not a browser/runtime compatibility table. Check:

1. the exact producer feature flags and emitted instructions/types;
2. the oldest deployed consumer's documented support and defaults;
3. whether validation requires an opt-in flag;
4. host API/policy requirements (CSP, isolation, WASI interfaces);
5. a real validation/instantiation test in CI.

Representative feature families include SIMD/relaxed SIMD, threads, tail calls,
exception handling, reference/typed function references, GC, multi-memory,
memory64, extended constant expressions, and component-model features. Never
collapse these to one boolean `supportsWasm`.

## 3. Compatibility strategy

Choose a conservative required baseline, then build optional variants only when
the performance/functionality gain justifies delivery complexity. Validate each
variant and select with reliable feature detection or server-side targeting.
For libraries, document core/WASI/component ABI and feature requirements in
machine-readable metadata where the ecosystem supports it.

Pin component tooling and WIT dependencies. WASI Preview 1, WASI 0.2, and WASI
0.3 are materially different contracts; adapters can bridge selected cases but
are not a reason to leave the target unspecified.

## Gotchas

- Specification release date and ubiquitous engine support date differ.
- Proposal phase does not guarantee a feature is enabled by default.
- A runtime can support a core instruction but not the corresponding language
  toolchain, debugger, or host API.
- “WASI support” without a version is incomplete.
- Feature detection must test the actual construct, not parse a user-agent or
  runtime version string when validation is available.
