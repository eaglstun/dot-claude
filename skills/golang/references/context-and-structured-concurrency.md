# Context and structured concurrency

Sources:

- https://pkg.go.dev/context
- https://go.dev/blog/context
- https://pkg.go.dev/golang.org/x/sync/errgroup
- https://go.dev/doc/database/cancel-operations

## Context contract

Pass `context.Context` as the first parameter to operations whose work may outlive a call or be
cancelled. Do not store it in structs for ordinary APIs, pass nil, or use values for optional
parameters. Context values carry request-scoped metadata across process/API boundaries; keys should
be private typed values.

Derived contexts must be cancelled to release timers and parent references. Use deadline/timeout
at an ownership boundary and propagate inward. Preserve cancellation identity with `context.Cause`
when the reason matters; callers should still handle `Canceled` and `DeadlineExceeded`.

## Structured worker trees

`errgroup.WithContext` ties sibling failure to cancellation and joins completion. Set a concurrency
limit before work starts when input size is untrusted. Every worker must select/check cancellation
around blocking channel, network and retry operations; context cannot stop code that ignores it.

Graceful shutdown normally stops admission, cancels background work, asks servers to shut down with
a bounded context, waits for owned goroutines, then forces exit if the bound expires. Keep process
signals at `main`; pass cancellation down rather than teaching packages about signals.

## Gotchas

- Forgetting the returned cancel function retains resources until the parent ends.
- Context cancellation does not roll back already committed external effects.
- A timeout per retry attempt and a total operation deadline solve different problems.
- Detached background work from a request context dies when the request ends; give it explicit ownership.
- `errgroup` returns one error; preserve multiple errors separately when the application requires them.

