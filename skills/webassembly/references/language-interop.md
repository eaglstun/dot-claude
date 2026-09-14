# Language interop

Sources:

- https://emscripten.org/docs/porting/connecting_cpp_and_javascript/Interacting-with-code.html
- https://rustwasm.github.io/docs/wasm-bindgen/
- https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html
- https://tinygo.org/docs/guides/webassembly/
- https://component-model.bytecodealliance.org/language-support.html
- https://learn.microsoft.com/dotnet/architecture/blazor-for-web-forms-developers/architecture

## 1. Select an ABI level

Use raw core signatures for a tiny, controlled boundary. Use generated
language-specific glue (`wasm-bindgen`, Emscripten bindings, etc.) when one host
language dominates. Use WIT/components when multiple languages/runtimes must
share a portable contract. Do not publish compiler-internal struct layout as an
API unless producer, consumer, compiler, flags, and lifetime are locked together.

## 2. Raw ABI checklist

For every value specify:

- scalar representation and signedness;
- byte encoding and pointer/length/capacity layout;
- which side allocates and which function frees;
- whether memory may grow during the call;
- callback/table lifetime and reentrancy;
- errors: result code, tagged payload, trap, or host exception;
- thread ownership and synchronization.

Never let a host keep a guest pointer after the guest may free or relocate it.

## 3. Language notes

- **C/C++:** Clang/Emscripten/wasi-sdk are mature. C++ names/classes/exceptions
  need C wrappers, Embind/WebIDL glue, or component bindings. Avoid exposing STL
  layout.
- **Rust:** `wasm-bindgen` is browser/JS-oriented; `wasm32-wasip*` targets and
  component binding generators serve WASI/components. `#[no_mangle] extern "C"`
  alone does not define string ownership.
- **Go:** standard Go's Wasm runtime/glue and target support differ from TinyGo;
  output size, GC/runtime imports, and host API are not interchangeable.
- **AssemblyScript:** TypeScript-like syntax compiles to Wasm but has its own
  runtime/managed-memory conventions; it is not TypeScript running directly.
- **.NET:** browser Wasm typically ships a managed runtime plus assemblies;
  NativeAOT/WASI scenarios have different constraints and maturity.

## 4. Components

Generate bindings from one WIT contract. Records/variants/results/lists/strings
are lifted and lowered via the canonical ABI; resource handles model stateful
objects. Pin the WIT package/interface version and regenerate both sides
together when it changes.

## Gotchas

- Source-language type similarity does not imply ABI compatibility.
- C++ exceptions and Rust panics must not unwind through an unspecified boundary.
- Host strings are not automatically guest strings.
- Two toolchains targeting `wasm32` may require completely different imports.
- Generated glue is part of the deployed ABI and must be versioned with the
  module.

