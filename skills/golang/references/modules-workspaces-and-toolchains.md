# Modules, workspaces, and toolchains

Sources:

- https://go.dev/ref/mod
- https://go.dev/doc/modules/gomod-ref
- https://go.dev/doc/toolchain
- https://go.dev/doc/tutorial/workspaces
- https://go.dev/ref/mod#private-modules

## Module graph

`go.mod` declares the module path, minimum Go version, direct/indirect requirements, and optional
replace/retract/toolchain configuration. Minimal version selection chooses the highest required
version of each module in the graph—not the newest available version. Major versions v2+ normally
live at paths ending `/v2`, `/v3`, etc.

Use `go mod tidy` to align requirements/sums with packages and tests. Inspect changes rather than
blindly accepting graph churn. `go mod why -m`, `go mod graph`, `go list -m -u all`, and
`go mod download -json` answer different dependency questions.

`go get` edits dependencies/toolchain requirements in the current module. `go install cmd@version`
installs a tool without adding it to the current module. Pin tool versions in reproducible workflows.
Use `replace` for local/fork testing deliberately; it changes provenance and should not leak into a
published module accidentally.

## Workspaces and toolchains

`go.work` combines local modules for development. Check `go env GOWORK`; an unexpected parent
workspace can make builds pass locally but fail in CI. Test modules outside workspace mode when publishing.

Since Go 1.21, the `go` and `toolchain` directives participate in toolchain selection and the go command
may download a newer verified toolchain. Inspect `GOTOOLCHAIN` when behavior is surprising.

Configure `GOPRIVATE` (and related proxy/sumdb settings when necessary) for private module paths; avoid
leaking private paths to public proxies.

## Gotchas

- The `go` directive is a required minimum, not merely formatting metadata in modern Go.
- `go.work` should often remain local and uncommitted unless the repository intentionally owns a workspace.
- `replace` applies only in main modules/workspaces, not to consumers of a dependency's `go.mod`.
- A v2 module without `/v2` is usually a path/versioning error.
- Automatic toolchain download can surprise locked-down/offline CI.

