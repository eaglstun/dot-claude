# Memory, tables, references, and GC

Sources:

- https://webassembly.github.io/spec/core/syntax/modules.html
- https://webassembly.github.io/spec/core/exec/instructions.html
- https://developer.mozilla.org/en-US/docs/WebAssembly/Reference/JavaScript_interface/Memory
- https://github.com/WebAssembly/gc/blob/main/proposals/gc/Overview.md
- https://github.com/WebAssembly/memory64

## 1. Linear memory

Linear memory is a growable byte array. Loads/stores provide explicit widths,
offsets, signedness, and alignment hints; addresses are bounds-checked. Wasm is
little-endian. A page is 65,536 bytes. `memory.grow` returns the previous page
count or `-1` in Wasm on failure (the JS method throws).

Core Wasm has no intrinsic allocator or object layout. Producers conventionally
export `malloc`/`free`, use a bump allocator, or define a generated ABI. Pointer
validity and ownership remain language/toolchain contracts even though accesses
cannot escape the memory's bounds.

Memory64 changes address/index types to 64-bit; it does not guarantee the host
can allocate an enormous memory. Multi-memory permits more than one memory, but
both features require deployment support.

## 2. Host views and growth

Hosts expose linear memory through their own API. In JavaScript, create typed
views over `memory.buffer`. After a grow, reacquire the buffer/view: non-shared
buffers can be detached and shared-buffer lengths can become stale.

Strings conventionally cross as `(pointer, byteLength)` plus an encoding (often
UTF-8). Never infer NUL termination, ownership, or capacity without the ABI.

## 3. Tables and references

Tables hold references, historically function references for indirect calls.
They support dynamic linking and callbacks but retain runtime bounds/type checks.
Reference-types and typed-function-reference features broaden what can be stored
and reduce some indirect-call ambiguity; check target support.

## 4. Shared memory and GC

Threaded Wasm uses shared linear memory plus atomic instructions. Browser use
also requires cross-origin isolation. Data races remain source-language bugs.

The Wasm GC proposal/standard features struct and array types plus managed
references for language runtimes. These are distinct from storing a tracing GC's
heap in linear memory. A GC-targeting producer needs a compatible engine; it
does not make raw linear-memory pointers managed.

## Gotchas

- Bounds safety does not prevent use-after-free or corruption inside one linear
  memory.
- `memory.grow` invalidates cached host views.
- The alignment immediate is a hint/validation constraint, not permission for
  an out-of-bounds access.
- Table indices are not native code addresses.
- `memory64` and GC support cannot be assumed from “supports WebAssembly.”

