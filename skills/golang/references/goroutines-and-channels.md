# Goroutines and channels

Sources:

- https://go.dev/ref/spec#Go_statements
- https://go.dev/ref/spec#Channel_types
- https://go.dev/blog/pipelines
- https://go.dev/blog/share-memory-by-communicating

## Lifecycle first

`go f()` starts concurrent work but provides no automatic join, cancellation, error propagation,
or panic containment. Before spawning, identify who waits, who cancels, what unblocks sends/
receives, and how errors return. A goroutine blocked forever still retains its stack and reachable data.

Channels communicate values and synchronize. The sender that knows no more values will arrive
normally owns closing. Receivers generally should not close a channel; sending or closing twice
panics. Receiving from a closed channel yields buffered values then zero values with `ok=false`.
A nil channel blocks forever, useful for disabling a select case but dangerous accidentally.

## Select and pipelines

`select` chooses a ready case pseudo-randomly; a `default` makes it non-blocking and can create
a busy loop. Cancellation must participate in every potentially blocking stage:

```go
select {
case out <- value:
case <-ctx.Done():
    return ctx.Err()
}
```

Bound concurrency with a worker pool, semaphore, or errgroup limit rather than spawning per
untrusted item. Buffer size encodes a backpressure policy; it is not a generic race/deadlock fix.

## Gotchas

- Closing broadcasts readiness; it does not interrupt arbitrary work unless code selects on it.
- Only a sender/owner with complete lifecycle knowledge should close.
- A send to a closed channel panics; a receive from one does not.
- An unbounded goroutine-per-request pattern can exhaust memory before CPU saturates.
- Timeouts made with repeated `time.After` in a hot loop allocate timers; manage a timer explicitly.

