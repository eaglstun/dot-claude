---
name: golang
description: >-
  Go language and tooling reference. Use when writing, reviewing, debugging, testing,
  profiling, or organizing Go code; resolving races, interface-nil bugs, module failures,
  or goroutine leaks; or choosing standard-library and ecosystem packages.
---

# Go reference

Condensed, source-cited notes grounded in primary Go documentation: the language
specification, memory model, standard-library docs, command documentation, release
notes, and official Go blog. Each reference ends with the sharp edges most often
misremembered.

This is a standalone language shelf. Repository conventions, the `go` directive,
the selected toolchain, existing package boundaries, and local lint policy override
general advice here. **Inspect `go.mod`, `go.work`, `go env GOWORK`, and `go version`
before relying on a recent feature or changing dependencies.**

The shelf tracks Go 1.26 as its current language baseline. Maintain compatibility
with the module's declared minimum Go version unless the user requests an upgrade.

## References — load on demand

### Language and design

- **[types-and-values.md](references/types-and-values.md)** — declarations, zero
  values, arrays/slices/maps/strings, conversions, constants, range and control
  flow. _Read when choosing a representation or debugging aliasing/range behavior._
- **[functions-errors-and-resources.md](references/functions-errors-and-resources.md)**
  — multiple returns, closures, defer/panic/recover, wrapped/joined errors, cleanup
  and ownership. _Read for API failure design or leaked files/bodies/rows._
- **[methods-interfaces-and-embedding.md](references/methods-interfaces-and-embedding.md)**
  — method sets, pointer receivers, implicit interfaces, typed nil, embedding,
  assertions and type switches. _Read on interface satisfaction or nil surprises._
- **[generics.md](references/generics.md)** — type parameters, constraints, `~`,
  unions, inference, generic containers and when an interface is simpler. _Read
  before introducing or debugging generic code._
- **[memory-and-allocation.md](references/memory-and-allocation.md)** — pointers,
  escape analysis, stack/heap, slice backing arrays, maps, GC, finalizers and unsafe.
  _Read for ownership, retention, allocation, or unsafe questions._

### Concurrency

- **[goroutines-and-channels.md](references/goroutines-and-channels.md)** — goroutine
  lifecycle, channel ownership, select, cancellation, fan-out/fan-in, closure and
  leak patterns. _Read before spawning work or designing a pipeline._
- **[synchronization-and-memory-model.md](references/synchronization-and-memory-model.md)**
  — happens-before, mutexes, atomics, once, condition variables, race detector and
  common race shapes. _Read whenever state is shared across goroutines._
- **[context-and-structured-concurrency.md](references/context-and-structured-concurrency.md)**
  — context propagation, deadlines, cancellation causes, errgroup and shutdown.
  _Read for request-scoped work, worker trees, or goroutine leaks._

### Practice and tooling

- **[modules-workspaces-and-toolchains.md](references/modules-workspaces-and-toolchains.md)**
  — `go.mod`, MVS, major versions, `go get` vs `go install`, replace/retract, private
  modules, workspaces and automatic toolchain selection. _Read for build/dependency failures._
- **[testing-fuzzing-and-debugging.md](references/testing-fuzzing-and-debugging.md)**
  — table tests, subtests, examples, fuzzing, benchmarks, race/coverage, test caches
  and Delve. _Read when adding tests or chasing nondeterminism._
- **[performance-and-observability.md](references/performance-and-observability.md)**
  — benchmark discipline, pprof, trace, metrics, logging, allocation and GC tuning,
  PGO. _Read before optimizing or investigating production behavior._

### Boundaries and ecosystem

- **[http-services-and-networking.md](references/http-services-and-networking.md)**
  — `net/http`, server/client timeouts, transports, middleware, graceful shutdown,
  TLS and service layout. _Read when building or reviewing a network service._
- **[data-encoding-and-databases.md](references/data-encoding-and-databases.md)**
  — JSON, text/bytes, time, SQL pools/transactions/nulls and streaming. _Read at
  serialization, filesystem, or database boundaries._
- **[cgo-interop-and-portability.md](references/cgo-interop-and-portability.md)**
  — cgo pointer rules, callbacks, build constraints, cross compilation, plugins,
  WebAssembly and `unsafe`. _Read before crossing an ABI or OS boundary._
- **[ecosystem-and-versions.md](references/ecosystem-and-versions.md)** — standard
  library first, package-selection criteria, common maintained choices, Go 1.18–1.26
  landmarks and compatibility. _Read for package or minimum-version decisions._

## Working rules for Go in this shelf

1. **Check the module and toolchain first.** The `go` line is a minimum language/toolchain
   requirement, and automatic toolchain switching can make `go version` differ by module.
2. **Make goroutine ownership explicit.** Every goroutine needs a stopping condition,
   a party responsible for cancellation, and a plan for errors and cleanup.
3. **Run `go test -race ./...` for concurrency changes.** Passing ordinary tests says
   nothing about unsynchronized shared state.
4. **Wrap errors with useful operation context, preserve identity, and inspect with
   `errors.Is`/`errors.As`.** Do not parse error strings for control flow.
5. **Use the standard library until a dependency earns its cost.** Compare maintenance,
   compatibility, transitive graph, API surface, and escape hatch—not GitHub stars alone.
6. **Profile before optimizing.** Use representative benchmarks and pprof; do not infer
   allocation or inlining behavior from source aesthetics.

## Shelf conventions

- Sources appear at the top of every reference; prefer stable `go.dev` and `pkg.go.dev` URLs.
- Keep this file a router. Put conditional detail in `references/`.
- Label features newer than the repository's likely baseline and verify the `go` directive.
