# Synchronization and the memory model

Sources:

- https://go.dev/ref/mem
- https://pkg.go.dev/sync
- https://pkg.go.dev/sync/atomic
- https://go.dev/doc/articles/race_detector

## Happens-before, not “probably visible”

Race-free Go programs receive sequentially consistent behavior. Coordinate conflicting access
with channel operations, mutexes, or atomics. Goroutine scheduling, sleeps, logging, and “it has
already run on my machine” do not establish happens-before.

Use a mutex to protect an invariant spanning fields or operations. Keep the protected state and
mutex together, document the invariant, and avoid copying the value after first use. `RWMutex`
helps only for measured read-heavy contention; it adds complexity and is not recursive.

Atomics suit small independent state machines/counters with a precisely documented protocol.
Typed atomics reduce mistakes, but atomically loading several fields does not make their combined
invariant atomic. `atomic.Value` requires consistent concrete types.

`sync.Once` publishes initialization to later callers; a panic marks the Once done. `Cond` is
appropriate for condition changes under a lock, but channels are often clearer for one-shot events.

## Race detector

Run `go test -race ./...` and representative integration/load paths. It detects races that execute,
not all possible races, and changes timing/memory. A race report's conflicting stacks and creation
stacks are evidence; fix ownership/synchronization rather than suppressing it.

## Gotchas

- Concurrent map read/write is unsafe and may fail loudly; even when it does not, it is a race.
- `len(ch)` is a momentary observation, not synchronization.
- Copying a struct containing `sync.Mutex`, `Once`, atomic values, or `noCopy` breaks invariants.
- Double-checked locking needs a correct atomic publication protocol; prefer `Once`.
- “Single writer” still needs synchronization for concurrent readers.

