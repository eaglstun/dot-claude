# Performance and observability

Sources:

- https://go.dev/doc/diagnostics
- https://go.dev/blog/pprof
- https://pkg.go.dev/runtime/pprof
- https://pkg.go.dev/net/http/pprof
- https://go.dev/doc/pgo
- https://pkg.go.dev/log/slog

## Observe before changing

Choose the right evidence: CPU profiles for on-CPU time, heap profiles for live allocation/retention,
alloc profiles for allocation sites, block/mutex profiles for contention, goroutine dumps for stuck work,
and runtime trace for scheduling/latency interactions. Production-like load and symbol-matched binaries matter.

Expose pprof only on an authenticated/private administrative listener. Capture bounded profiles during the
problem; an idle profile answers a different question. Use labels to separate workloads when helpful.

## Optimization workflow

Establish a representative benchmark, profile, change one thing, compare statistics, and keep readability
unless the gain matters. Common wins are algorithm/data-layout changes, removing avoidable conversions,
batching I/O, preallocating known sizes, and reducing retention—not hand inlining.

PGO consumes representative CPU profiles and can improve hot code while preserving source semantics; keep
profiles current enough to represent production. Verify binary/toolchain compatibility and measure rollout.

GC knobs (`GOGC`, memory limit) trade CPU, memory and latency. Set a memory limit with container/headroom
awareness; it is a soft runtime target, not protection from all memory exhaustion.

Use structured `slog` records with stable keys and request correlation. Metrics should be bounded-cardinality;
traces should propagate context. Logs are not a synchronization primitive or a substitute for metrics.

## Gotchas

- Heap “alloc_space” and “inuse_space” answer different questions.
- Benchmarking only micro-operations can miss boundary/I/O/GC costs.
- High-cardinality labels can take down observability systems.
- Enabling every contention profile continuously has overhead.
- `-gcflags=-m` diagnostics change across compiler versions and are not performance measurements.

