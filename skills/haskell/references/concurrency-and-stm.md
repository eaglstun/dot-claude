---
semantic_id: "6fTGTKLpyeCY-s2SIpADEWRrt14jQAAH"
related_ids:
  - "4ZjGjKBZy7Saw4iSq4EVQWtrFVwzwAAB"
  - "aYz2IabZa9AS79yCbqOD0WpuhdwzQAAK"
---
# Concurrency, STM, and parallelism

Source:

- https://hackage.haskell.org/package/base/docs/Control-Concurrent.html
- https://hackage.haskell.org/package/async/docs/Control-Concurrent-Async.html
- https://hackage.haskell.org/package/stm/docs/Control-Concurrent-STM.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/using-concurrent.html
- https://hackage.haskell.org/package/parallel/docs/Control-Parallel-Strategies.html

## 1. Green threads

`forkIO` creates a Haskell thread: a few hundred bytes, scheduled by the RTS
onto OS capabilities. Spawning tens of thousands is normal and cheap.

```haskell
import Control.Concurrent
tid <- forkIO (forever (worker q))
threadDelay 1_000_000     -- microseconds
killThread tid            -- throws ThreadKilled to it
myThreadId
```

Build and run flags:

```
ghc-options: -threaded -rtsopts "-with-rtsopts=-N"
./prog +RTS -N4 -RTS             # 4 capabilities
```

Without `-threaded` you get a single OS thread: concurrency still works, but a
blocking FFI call blocks _everything_, and `-N` does nothing. Use `-threaded`
for anything real.

**The main thread is special**: when it finishes, the program exits and all
other threads are killed without cleanup. And an exception in a `forkIO` thread
is printed to stderr and otherwise ignored — nothing propagates to the parent.
That alone is why you should use `async` instead of raw `forkIO`.

## 2. `async` — use this

```haskell
import Control.Concurrent.Async

a  <- async (fetch url)          -- start
r  <- wait a                     -- rethrows the child's exception here
withAsync (fetch url) $ \a -> …  -- cancelled when the block exits ← prefer this

(x, y)  <- concurrently  actA actB     -- both, both results
r       <- race          actA actB     -- first to finish; loser cancelled
rs      <- mapConcurrently  fetch urls
_       <- mapConcurrently_ notify ids
rs      <- forConcurrently urls fetch
r       <- replicateConcurrently n act
```

`Concurrently` is a newtype whose `Applicative` runs in parallel — so
`runConcurrently ((,) <$> Concurrently a <*> Concurrently b)` is `concurrently`
generalized, and `Alternative` gives you `race`.

`withAsync` over `async`: it guarantees the child is cancelled if the parent
dies. Bare `async` without a `wait` leaks a thread.

Bounded concurrency: `mapConcurrently` on 10,000 URLs opens 10,000 sockets. Use
a `QSem`/`TSem`, `pooledMapConcurrentlyN` (from `unliftio`), or a worker pool
over a `TBQueue`.

## 3. `MVar`

A one-slot box: full or empty.

```haskell
mv <- newMVar 0
modifyMVar_ mv (pure . (+1))          -- exception-safe take/put
v  <- readMVar mv
x  <- takeMVar mv                     -- blocks if empty; leaves it empty
putMVar mv x                          -- blocks if full
```

Uses: mutex (`modifyMVar_`), single-slot channel, "one worker at a time",
completion signal (`newEmptyMVar` + `putMVar` + `takeMVar`).

Always `modifyMVar_`/`withMVar` rather than `takeMVar` + `putMVar` — the
combinators mask exceptions so an interrupt can't leave the `MVar` permanently
empty (which deadlocks every other thread).

The RTS can detect _some_ deadlocks and throws `BlockedIndefinitelyOnMVar`, but
only when no other thread can possibly reach the `MVar`. Real deadlocks between
live threads just hang.

`Chan` is an unbounded FIFO built on `MVar`s — unbounded means a slow consumer
grows the heap without limit. Prefer `TBQueue`.

## 4. STM — composable atomicity

```haskell
import Control.Concurrent.STM

atomically :: STM a -> IO a
newTVarIO  :: a -> IO (TVar a)
readTVar   :: TVar a -> STM a
writeTVar  :: TVar a -> a -> STM ()
modifyTVar':: TVar a -> (a -> a) -> STM ()     -- STRICT; use this one
retry      :: STM a                            -- abort and re-run when a read TVar changes
orElse     :: STM a -> STM a -> STM a          -- try the first, else the second
check      :: Bool -> STM ()                   -- guard: retry unless True
```

The killer feature is **composability**: two correct atomic operations combine
into one correct atomic operation, which is exactly what locks can't do.

```haskell
transfer :: TVar Int -> TVar Int -> Int -> STM ()
transfer from to n = do
  b <- readTVar from
  check (b >= n)                -- blocks (retries) until funds exist
  modifyTVar' from (subtract n)
  modifyTVar' to   (+ n)

atomically (transfer a b 100)
```

`retry` isn't a spin loop: the transaction is aborted and the thread parked
until one of the `TVar`s it read is written. `orElse` gives you "take from
queue A, or B if A is empty" atomically.

Ready-made structures in `stm`: `TVar`, `TMVar`, `TChan`, `TQueue`,
`TBQueue` (bounded — use this for backpressure), `TSem`, `TArray`.
`stm-containers` adds concurrent maps.

**What may not go inside `atomically`**: arbitrary `IO`. The type prevents it,
which is the point. If you need IO decided by a transaction, read the decision
out and act after, or use `TQueue` to hand work to a dedicated thread.

Cost model: STM is optimistic — reads are logged, the commit validates and
retries on conflict. Cheap for small, low-contention transactions; a large
transaction over a hot `TVar` can livelock re-running. Keep transactions short,
and never put a long computation or an `unsafePerformIO` inside one (it will be
re-run, possibly many times).

## 5. Timeouts and cancellation

```haskell
import System.Timeout (timeout)
r <- timeout 5_000_000 action          -- Just a, or Nothing
```

`timeout` throws an async exception into the action. Which means: any
`catch @SomeException` inside will swallow the cancellation and the timeout
won't work. See `exceptions-and-resources.md` §4.

Cancellation is cooperative in exactly one respect: a thread stuck in a
**`unsafe` foreign call** cannot be interrupted, and neither can a tight
non-allocating loop (GHC inserts yield points at allocation). A pure `let go n = go (n+1)`
loop with no allocation is uninterruptible and unkillable.

## 6. Parallelism (different problem from concurrency)

Concurrency is about structure; parallelism is about speed on multiple cores.

```haskell
import Control.Parallel.Strategies
rs = map expensive xs `using` parList rdeepseq
r  = runEval $ do a <- rpar (f x); b <- rpar (f y); rseq a; rseq b; pure (a,b)
```

`par`/`pseq` and `Strategies` express "this may be evaluated in parallel"
without changing results. Requires `-threaded -N`. The usual failure is
**insufficient granularity** (sparks too small, overhead dominates) or
**laziness** (`parList rseq` only forces WHNF, so nothing real happens — use
`rdeepseq`). `+RTS -s` reports sparks converted/overflowed/fizzled; mostly
fizzled means you parallelized nothing.

`Control.Monad.Par` and `monad-par` give a deterministic, `IVar`-based API.
For data parallelism over arrays, `massiv` has parallel strategies built in.

## 7. RTS flags worth knowing

```
-N / -N4          capabilities (cores). -N alone = all.
-qg               disable parallel GC (sometimes faster for low core counts)
-qa               thread affinity
-A32m             bigger allocation area — often a large win for parallel programs
-s / -S           GC and productivity summary
-ls               eventlog for ThreadScope / eventlog2html
```

Parallel GC on many cores with a small `-A` is a classic reason a parallel
program is _slower_ than the serial one. Try `-A64m -qn2` before concluding the
algorithm is at fault.

## Gotchas

- **`forkIO` swallows exceptions** (prints to stderr, parent unaffected) and
  leaks the thread if you forget it. Use `async`/`withAsync`.
- **When `main` returns, all other threads die instantly** — no cleanup, no
  finalizers. Join your workers.
- **Without `-threaded`, a blocking FFI call freezes the whole program**, and
  `-N` is ignored.
- **`modifyTVar` and `modifyIORef` are lazy** — `modifyTVar'` and
  `modifyIORef'` exist for a reason and thunk buildup inside a `TVar` is a
  classic leak.
- **`takeMVar`/`putMVar` pairs are not exception-safe.** Use `modifyMVar_`,
  `withMVar`.
- **`catch @SomeException` breaks `timeout`, `race`, and `cancel`**, because all
  three work by throwing async exceptions.
- **`Chan` and `TQueue` are unbounded.** A fast producer and slow consumer will
  eat all memory. `TBQueue` gives backpressure.
- **A long transaction over a contended `TVar` can livelock**, re-running
  forever. Keep transactions small.
- **Non-allocating loops are uninterruptible** — `killThread` on such a thread
  hangs.
- **`unsafePerformIO` inside `atomically` runs an unknown number of times.**
- **`mapConcurrently` over a large list has no concurrency limit.** Bound it.
