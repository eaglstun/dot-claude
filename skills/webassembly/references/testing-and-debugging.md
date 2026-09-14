# Testing and debugging

Sources:

- https://github.com/WebAssembly/spec/tree/main/test
- https://github.com/WebAssembly/wabt
- https://github.com/bytecodealliance/wasm-tools
- https://emscripten.org/docs/porting/Debugging.html
- https://docs.wasmtime.dev/examples-debugging-wasm.html
- https://github.com/WebAssembly/tool-conventions/blob/main/Debugging.md

## 1. Shrink the failure class

Start with validation, then inspect imports/exports and artifact kind. Reproduce
with the smallest host and deterministic imports. Classify: producer compile or
link failure; Wasm validation; host linking; instantiation/start trap; runtime
trap; wrong result; performance regression.

For a trap, retain the Wasm program counter/backtrace, symbol/name/DWARF data,
runtime version and flags, module hash, and host inputs. `wasm-tools print`,
`wasm-objdump -x`, and runtime backtrace settings answer different questions.

## 2. Debug metadata

Native-language producers can emit DWARF in custom sections. Browser toolchains
may use source maps and developer-tool integrations. Keep a debug artifact with
symbols even if production delivery strips it; archive the exact source map and
build ID/hash alongside release artifacts.

Optimization changes inlining, variable availability, and stack shape. Confirm
a correctness failure in a low-optimization debug build, but reproduce release-
only failures under the release optimizer too.

## 3. Tests

- Unit-test pure source code before crossing the boundary.
- Contract-test imports/exports, malformed lengths, ownership, errors, growth,
  and reentrant callbacks in the real host.
- Run integration tests in every supported browser/runtime family and oldest
  baseline, not only a CLI simulator.
- Fuzz decoders and guest APIs with hard memory/time limits. Differential tests
  across engines can expose producer and engine bugs, but first normalize NaNs,
  imports, feature flags, and limits.

The official spec test suite is for engine conformance; application tests still
need the application's ABI and host behavior.

## Gotchas

- Stripping the name/DWARF sections turns actionable traces into offsets.
- A module working in Wasmtime does not prove browser JS glue or headers work.
- Debug and release may target different feature sets or import lists.
- A host exception raised from an import may appear as a guest trap/backtrace.
- Fuzzing untrusted code without execution limits can hang the test runner.

