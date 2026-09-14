# Testing, fuzzing, and debugging

Sources:

- https://pkg.go.dev/testing
- https://go.dev/doc/tutorial/add-a-test
- https://go.dev/doc/tutorial/fuzz
- https://go.dev/doc/build-cover
- https://go.dev/doc/articles/race_detector

## Tests

Keep tests deterministic, isolated and behavior-focused. Table tests work well when failures name the case;
subtests allow selection and parallelism. `t.Helper()` fixes blame lines in assertion helpers. `t.Cleanup`
ties cleanup to test lifetime. Use `t.TempDir` and `t.Setenv` rather than shared machine state.

Parallel tests must not share mutable globals, fixed ports, process-wide environment changes, or loop-case
variables incorrectly. Prefer injectable clocks/random/readers over sleeps. The test cache reuses successful
package results; use `-count=1` when rerunning nondeterministic behavior, not as a permanent substitute for isolation.

## Fuzzing and benchmarks

Fuzz functions start with seed corpus entries and assert invariants—no panic, round-trip, parser equivalence,
canonicalization, bounds. Keep them deterministic and fast; committed corpus regressions belong under
`testdata/fuzz`.

Benchmark with realistic inputs, `b.ResetTimer`, `b.ReportAllocs`, and results consumed so work cannot disappear.
Compare with `benchstat`; one run is not evidence. Check CPU scaling and setup costs separately.

## Debugging commands

Use `go test -run`, `-count`, `-shuffle`, `-race`, `-coverprofile`, and `go tool cover`. Delve (`dlv test`,
`dlv debug`) handles source debugging; preserve optimized-release reproduction for optimizer/timing bugs.

## Gotchas

- Coverage measures executed statements, not assertion quality.
- `t.Parallel` changes ordering and exposes hidden process-global coupling.
- A race detector run only covers executed paths.
- Golden files need an explicit opt-in update flag and reviewable diffs.
- Benchmarks run under dynamic CPU/thermal conditions; report environment and variance.

