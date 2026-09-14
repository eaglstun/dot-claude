---
name: webassembly
description: >-
  WebAssembly reference for core modules, WAT/binary format, memory, browser embedding,
  WASI, components/WIT, toolchains, interop, testing, performance, and security. Use when
  writing, compiling, hosting, debugging, optimizing, or choosing a Wasm deployment model.
---

# WebAssembly reference

Condensed, source-cited notes grounded in the WebAssembly specifications and the
toolchains' and runtimes' own documentation. Each page cites source URLs at the
top and ends with a Gotchas section for sharp edges that memory gets wrong.

This is a standalone reference shelf, not tied to one repo. Project conventions,
the chosen producer, the embedding runtime, and its feature flags override this
shelf. **Identify the target environment before recommending an ABI or feature:**
browser JavaScript, a raw core-module embedder, WASI, and the Component Model are
different contracts.

WebAssembly 3.0 is the current core specification baseline for this shelf, but
deployment support may lag. Older or proposal-gated features are labeled inline.

## References — load on demand

Detail lives in `references/`. One pointer per page:

### Core format and runtime

- **[execution-and-validation.md](references/execution-and-validation.md)**
  — stack-machine execution, module lifecycle, types, imports/exports, traps,
  validation, start functions, determinism. _Read when explaining runtime
  behavior, a validation error, or a trap._

- **[wat-and-binary.md](references/wat-and-binary.md)**
  — WAT syntax, folded vs linear instructions, indices and names, sections,
  LEB128, custom/name/source-map sections, and WABT/Binaryen inspection tools.
  _Read when hand-writing WAT or inspecting a `.wasm` file._

- **[memory-tables-and-gc.md](references/memory-tables-and-gc.md)**
  — linear memory, pages and growth, pointers, tables and indirect calls,
  references, multi-memory, memory64, threads/shared memory, and GC types.
  _Read for pointer bugs, stale host views, callbacks, large memories, or
  managed-language targets._

### Hosts and interfaces

- **[browser-and-javascript.md](references/browser-and-javascript.md)**
  — streaming compilation, imports/exports, Memory and typed arrays, strings,
  exceptions, workers/threads, CSP and MIME requirements. _Read whenever Wasm
  runs in a browser or JavaScript host._

- **[wasi-and-components.md](references/wasi-and-components.md)**
  — WASI capability-based interfaces, Preview 1 vs WASI 0.2/0.3, core modules
  vs components, WIT worlds/interfaces/resources, canonical ABI, adapters and
  composition. _Read before targeting server/CLI Wasm or designing a portable
  cross-language interface._

- **[embedding-and-runtimes.md](references/embedding-and-runtimes.md)**
  — choosing Wasmtime/Wasmer/WAMR/wasm3/V8-family hosts, compilation modes,
  linking imports, fuel/epoch limits, resource limits, pooling and caching.
  _Read when embedding Wasm or selecting a runtime._

### Building and shipping

- **[toolchains-and-builds.md](references/toolchains-and-builds.md)**
  — Clang/LLVM, Emscripten, wasi-sdk, wasm-tools, WABT, Binaryen, component
  tooling, exports/imports, reactor vs command, reproducible build checks.
  _Read when setting up or fixing a build._

- **[language-interop.md](references/language-interop.md)**
  — C/C++, Rust, Go/TinyGo, AssemblyScript, .NET, and language-neutral ABI
  choices; ownership, strings, callbacks, exceptions, and bindings. _Read
  before crossing a language boundary._

- **[testing-and-debugging.md](references/testing-and-debugging.md)**
  — validation, host-side tests, spec tests, DWARF/source maps, browser tools,
  wasmtime/wabt tooling, fuzzing and differential testing. _Read for build
  failures, traps, wrong results, or test strategy._

- **[performance-and-size.md](references/performance-and-size.md)**
  — measurement, startup vs steady state, boundary costs, allocation/copies,
  SIMD, threads, optimization/LTO, wasm-opt and size budgets. _Read before
  optimizing or shrinking a module._

- **[security-and-portability.md](references/security-and-portability.md)**
  — sandbox boundaries, capabilities, limits, untrusted modules, side channels,
  browser isolation, supply chain, numeric portability and feature detection.
  _Read when running untrusted Wasm or making a portability claim._

- **[standards-and-features.md](references/standards-and-features.md)**
  — core 1.0/2.0/3.0 landmarks, proposal phases, feature detection, compatibility
  strategy, WASI/Component Model maturity. _Read before using a recent feature
  or choosing a deployment baseline._

## Working rules for WebAssembly in this shelf

1. **Name the execution contract first.** Browser JS, WASI Preview 1, a WASI
   component, and a custom embedder can run the same instruction format but do
   not expose the same world.
2. **Check the producer and consumer versions.** Inspect build flags and run
   `wasm-tools validate --features ...` (or the runtime's equivalent) before
   recommending a proposal-gated instruction or component feature.
3. **Treat the boundary as an ABI.** Specify ownership, encoding, allocation,
   errors, and lifetime. A pointer and length are not a string contract.
4. **A Wasm sandbox is not an authorization policy.** The host decides which
   imports, directories, sockets, clocks, and limits exist.
5. **Measure in the real host.** Startup, compilation cache, JS↔Wasm crossings,
   memory copies, and runtime tiering can dominate the function being optimized.
6. **Prefer generated bindings or WIT over an invented ABI** when more than one
   language or runtime must implement the boundary.

## Conventions for this skill

- Each reference cites primary or maintainer documentation at the top.
- Keep `SKILL.md` as a router; conditional detail belongs on the shelf.
- Add topics as `references/<topic>.md`, with sources first and Gotchas last.
