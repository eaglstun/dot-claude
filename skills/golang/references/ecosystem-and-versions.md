# Ecosystem and versions

Sources:

- https://pkg.go.dev/std
- https://go.dev/doc/devel/release
- https://go.dev/doc/go1.26
- https://go.dev/doc/go1compat
- https://go.dev/wiki/CodeReviewComments
- https://go.dev/doc/effective_go

## Choosing packages

Start with the standard library: `net/http`, `encoding/*`, `database/sql`, `log/slog`, `testing`, `context`, `crypto/*`
cover more than many ecosystems expect. Add a dependency when it materially improves correctness, protocol coverage,
maintainability or delivery speed.

Evaluate ownership/activity, compatibility policy, security history, API size, transitive graph, build tags/cgo,
observability hooks, context support, cancellation/resource behavior, and exit strategy. Prefer narrow interoperable
packages over frameworks that replace standard interfaces without a measured benefit.

Common official/extended modules include `golang.org/x/sync`, `x/time`, `x/text`, `x/crypto`, `x/net`, `x/tools` and
`x/exp` (experimental—pin and expect churn). For CLIs, routers, RPC, databases, validation and telemetry, match the
existing repository first and verify current maintenance/docs before recommending a new library.

## Version landmarks

- Go 1.18: generics, fuzzing, workspace mode.
- Go 1.19–1.20: memory-model-era typed atomics and multi-error wrapping/`errors.Join`.
- Go 1.21: stronger `go` version requirement, toolchain management, `slog`, new built-ins/packages.
- Go 1.22: range-loop semantics changes by language version and integer range.
- Go 1.23–1.25: iterators/range-over-function and continuing runtime/tool improvements; verify exact release notes.
- Go 1.26: current shelf baseline; `new(expression)` and current library/toolchain changes. Verify module minimum first.

Go 1 compatibility protects source compatibility broadly, not identical performance, diagnostics, scheduling, undocumented
behavior, or every unsafe/linkname trick. Read every intervening release note for an upgrade.

## Gotchas

- “Latest Go installed” does not mean the module opts into latest language semantics.
- `x/exp` is not a stability promise.
- Effective Go is foundational but not a complete guide to newer language/library features.
- A dependency's major-version module path is part of its import path.
- Security/maintenance status changes; verify package recommendations rather than relying on memory.
