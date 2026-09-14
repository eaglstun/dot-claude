# cgo, interop, and portability

Sources:

- https://pkg.go.dev/cmd/cgo
- https://go.dev/wiki/cgo
- https://pkg.go.dev/unsafe
- https://pkg.go.dev/cmd/go#hdr-Build_constraints
- https://go.dev/doc/install/source#environment
- https://go.dev/wiki/WebAssembly

## cgo boundary

cgo binds C through `import "C"` and generated wrappers. Keep the boundary small, expose a C-shaped API, translate
errors/ownership immediately, and benchmark crossings. Build/link flags and platform libraries become deployment
requirements. Pure-Go builds are easier to cross-compile and ship, but correctness/library availability may justify cgo.

Go pointer passing is constrained so the GC never loses track of Go memory containing Go pointers. C must not retain
Go pointers after the call unless the documented pinning/handle rules permit it. Use `runtime/cgo.Handle` for opaque
callback state rather than smuggling Go pointers through integers. C allocations require matching C frees.

Callbacks cross threads/runtimes and can deadlock or violate reentrancy assumptions. Document which side owns threads,
memory and cancellation. Panics must not escape as an undefined foreign exception.

## Portability

Use build constraints plus filename suffixes for OS/architecture implementations, with a portable package API and CI
matrix. Check `CGO_ENABLED`, `GOOS`, `GOARCH`, tags and external linker requirements. Build tags require exact syntax and
blank-line placement.

Go WebAssembly targets have host-specific APIs: browser `js/wasm` uses `syscall/js`; WASI targets expose a different
environment. Check the current toolchain/runtime support rather than treating all `.wasm` artifacts alike.

## Gotchas

- `C.CString` allocates C memory and must be freed.
- C retaining a Go pointer beyond a call commonly violates pointer rules.
- Cross compilation with cgo needs a target C compiler/sysroot.
- `unsafe` assumptions can fail under GC/compiler/architecture changes.
- Go plugins have strict toolchain/dependency identity constraints and limited platform support; subprocess/RPC is often safer.

