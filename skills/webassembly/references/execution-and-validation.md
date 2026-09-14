# Execution and validation

Sources:

- https://webassembly.github.io/spec/core/
- https://webassembly.github.io/spec/core/valid/index.html
- https://webassembly.github.io/spec/core/exec/index.html

## 1. Module lifecycle

A core module is decoded, validated, instantiated with matching imports, then
invoked through exports. Validation is static and type-directed; it rejects
ill-typed stacks, invalid indices, inconsistent limits, and feature use the
engine has not enabled. Instantiation allocates module state, initializes
memories/tables/globals, evaluates element and data segments, and runs the
optional start function. Start-function traps make instantiation fail.

Imports are matched by module/name and exact external type. A function with the
right language-level meaning but a different Wasm signature is not compatible.

## 2. Stack machine and structured control

Instructions consume and produce typed operand-stack values. Control flow is
structured: `block`, `loop`, `if`, `br`, `br_if`, `br_table`, `return`; there is
no arbitrary jump. Branch labels name structured constructs by depth or WAT
identifier. A branch to a `loop` continues at its header; a branch to a `block`
exits the block.

Locals are per-call mutable slots. Globals are module-instance state and may be
mutable only when declared so. Core numeric values include integers and IEEE
floating point; newer standards add richer reference/vector/value types.

## 3. Calls and traps

`call` targets a known function index. `call_indirect` reads a table element and
checks its runtime type before calling; null, out-of-range, or type mismatch
traps. Tail-call instructions require corresponding engine support.

Traps abort the current Wasm computation: examples include unreachable,
out-of-bounds memory/table access, integer division by zero, invalid integer
conversion, and exhausted implementation resources. Traps are not ordinary
language exceptions unless the host/toolchain maps them into one.

## 4. Determinism boundaries

Core execution has specified numeric behavior, including wrapping integer
arithmetic. NaN payload details and host imports can introduce observable
variation. Time, randomness, files, networks, scheduling, and environment access
come from imports and are only as deterministic as the host implementation.

## Gotchas

- Validation success does not imply imports can be linked or instantiation will
  succeed.
- The start function runs during instantiation, before the host receives an
  instance.
- `br 0` means different things inside a `loop` and a `block`.
- A trap cannot generally be caught by Wasm code as if it were a source-language
  exception.

