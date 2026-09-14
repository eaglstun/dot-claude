# Memory and allocation

Sources:

- https://go.dev/ref/spec#Pointer_types
- https://go.dev/doc/gc-guide
- https://go.dev/doc/diagnostics
- https://go.dev/blog/pprof
- https://pkg.go.dev/runtime

## Ownership without ownership syntax

Pointers share mutable objects, but slices, maps, channels, functions and interfaces already
contain reference-like state. Copying a struct copies all fields; copying a mutex, once, map
header or slice descriptor has different consequences. Document whether callers may retain
or mutate buffers and whether returned slices alias internal storage.

Escape analysis decides stack versus heap; `new` does not mean heap and a local can escape.
Inspect compiler diagnostics only when profiling identifies allocation cost:
`go build -gcflags=all=-m=2`. Optimizer output is version-sensitive.

## Retention and GC

GC cost is driven by live heap size, allocation rate and pointer density. Reuse only when
measurements justify complexity. `sync.Pool` is a cache whose contents may disappear at any
GC; never use it for required state. Slice capacity and substrings/subslices can retain much
larger objects. Clear removed pointer elements in long-lived backing arrays when retention matters.

Finalizers and cleanup hooks are nondeterministic safety nets, not primary resource management.
Use explicit `Close`. `runtime.KeepAlive` can be required around finalizer-sensitive system
calls; follow the relevant API documentation exactly.

## Unsafe

`unsafe.Pointer` and `uintptr` obey narrow conversion/lifetime rules. A `uintptr` is an integer,
not a GC-tracked pointer. Prefer `unsafe.Slice`/`unsafe.String` where appropriate, keep unsafe
operations tiny, test across architectures, and state lifetime/alignment assumptions.

## Gotchas

- Returning a pointer to a local is safe; escape analysis moves storage as needed.
- Reslicing to zero length does not release the backing array.
- `sync.Pool` may be emptied at any time.
- A zero-copy conversion built with unsafe can violate string immutability or outlive storage.
- `GOGC` tuning without heap/latency profiles commonly trades one problem for another.

