# Toolchains and builds

Sources:

- https://clang.llvm.org/docs/CrossCompilation.html
- https://emscripten.org/docs/compiling/Building-Projects.html
- https://github.com/WebAssembly/wasi-sdk
- https://github.com/bytecodealliance/wasm-tools
- https://github.com/WebAssembly/wabt
- https://github.com/WebAssembly/binaryen

## 1. Pick target and host contract together

- `wasm32-unknown-unknown`: freestanding/core-module style; supply imports and
  libc/runtime pieces yourself.
- Emscripten: C/C++ to browser/JS or compatible hosts, with generated JS glue,
  libc, filesystem shims, and optional pthread support.
- `wasm32-wasi`/versioned WASI targets: command/reactor-style WASI modules,
  depending on compiler era and target naming.
- Component targets: compile a core guest, generate language bindings from WIT,
  and componentize/adapt with current component tooling.

Never infer ABI from the `wasm32` architecture alone.

## 2. Exports and imports

Dead-code elimination removes functions that are neither roots nor exports.
Declare the actual entry points and runtime helpers (allocator/deallocator,
indirect-function table, memory) required by the host glue. Inspect the final
artifact rather than trusting source visibility.

With Emscripten, shell quoting of list-valued settings and the distinction
between exported native functions and exported runtime methods are common build
failures. Keep compiler/linker settings in the build system rather than a README
command that silently diverges.

## 3. Build pipeline

A practical release pipeline:

1. Compile/link with an explicit target, CPU/features, sysroot, and export set.
2. Validate with the intended feature baseline.
3. Inspect imports/exports and artifact kind.
4. Optimize/strip deliberately; retain a symbolized diagnostic artifact.
5. Test in the oldest supported engine and the production host configuration.
6. Serve browser artifacts with `application/wasm` and correct isolation/CSP
   headers where relevant.

`wasm-opt` transforms may require enabling the same feature set as the input and
consumer. LTO can improve whole-program size/speed but makes debug attribution
harder; preserve a non-stripped map/build.

## Gotchas

- `wasm32` is an ISA target, not a libc or host API.
- Link-time DCE can remove a function the host expected to call.
- A module can validate yet import an ABI unavailable in the chosen runtime.
- Running `wasm-opt` with the wrong feature flags can reject or rewrite a module
  incompatibly.
- Browser deployment needs headers and glue assets, not just the `.wasm` file.

