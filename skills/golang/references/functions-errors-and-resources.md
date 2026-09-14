# Functions, errors, and resources

Sources:

- https://go.dev/ref/spec
- https://go.dev/blog/error-handling-and-go
- https://pkg.go.dev/errors
- https://go.dev/blog/defer-panic-and-recover

## Errors as values

Return an error when callers can reasonably handle or report failure. Add concise
operation/context while preserving identity:

```go
if err != nil {
    return fmt.Errorf("load account %q: %w", id, err)
}
```

Use `errors.Is` for sentinel identity through wrapping and `errors.As` for typed detail.
`errors.Join` represents multiple concurrent/cleanup failures. Avoid exported sentinel
errors when a predicate or typed error gives a more stable API. Error text is for humans;
do not branch on it.

## Defer, panic, and cleanup

Deferred calls execute LIFO when the surrounding function returns or panics; arguments
are evaluated when `defer` executes. Defer cleanup immediately after successful acquisition.
In loops, extract an iteration into a helper when resources should close each iteration
instead of at function return.

Panic is suitable for broken internal invariants or initialization that cannot continue,
not ordinary input, network, or storage failure. Recover only in the same goroutine's
deferred call, normally at a process/framework boundary that can restore a valid state.

Functions and closures capture variables, not frozen values. Named results can be useful
for deferred error combination but become obscure when mutated casually.

## Resource checklist

Close response bodies, rows, files, compressors and other owned resources on all paths.
For HTTP, close the body and usually drain/reuse appropriately. Check `rows.Err()` after
iteration. Decide whether cleanup errors matter; writes, flushes and file closes can fail.

## Gotchas

- `defer f(x)` evaluates `x` immediately.
- A deferred close in a large loop retains every resource until the outer return.
- `%v` adds text; `%w` adds an unwrap relationship.
- Recover in another goroutine cannot catch the panic.
- Logging and returning the same error at every layer produces duplicate noise.

