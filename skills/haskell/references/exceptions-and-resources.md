---
semantic_id: "7a3G1aZZ78Sa-0jj6hM7U8JuNV9VQAAM"
related_ids:
  - "LZ5GmZAZayGY-8yG6oEfVcp-7V6WwAAO"
  - "aYz2IabZa9AS79yCbqOD0WpuhdwzQAAK"
---
# Exceptions, async exceptions, and resource safety

Source:

- https://hackage.haskell.org/package/base/docs/Control-Exception.html
- https://hackage.haskell.org/package/safe-exceptions/docs/Control-Exception-Safe.html
- https://hackage.haskell.org/package/unliftio/docs/UnliftIO-Exception.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/exception_backtraces.html
- https://hackage.haskell.org/package/resourcet

## 1. The three ways a Haskell program fails

| Mechanism              | Visible in the type? | Use for                                      |
| ---------------------- | -------------------- | -------------------------------------------- |
| `Maybe` / `Either e`   | yes                  | expected failure the caller must handle      |
| `throwIO` / exceptions | no                   | exceptional failure, IO errors, cancellation |
| `error` / `undefined`  | no                   | programmer errors — bugs, not conditions     |

**Rule of thumb**: if the caller can reasonably recover _and_ the failure is
part of the function's contract, return `Either`. If it's an environmental
failure (disk, socket, out of memory) or a cancellation, an exception is right.
`error` is for invariants that should be impossible.

## 2. The exception hierarchy

```haskell
class (Typeable e, Show e) => Exception e where
  toException   :: e -> SomeException
  fromException :: SomeException -> Maybe e
  displayException :: e -> String       -- override this; Show is for debugging
```

```haskell
data AppError = NotFound Text | Invalid Text
  deriving stock (Show)
  deriving anyclass (Exception)         -- default methods are fine here
```

`SomeException` is the existential root. `ErrorCall` (from `error`),
`IOException`, `ArithException`, `ArrayException`, `AsyncException`,
`SomeAsyncException`, and `ExitCode` are the built-ins worth recognizing.

GHC 9.10+ adds exception _backtraces_ (`HasCallStack`-based annotations,
`displayExceptionWithInfo`), which finally makes an uncaught `error` locatable.
On older GHCs, `HasCallStack` on your own throwing functions is the workaround.

## 3. Throwing

```haskell
throwIO :: Exception e => e -> IO a       -- precise: ordered w.r.t. other IO
throw   :: Exception e => e -> a          -- IMPRECISE: a pure value that throws when forced
throwTo :: Exception e => ThreadId -> e -> IO ()   -- async, to another thread
ioError :: IOError -> IO a
error   :: HasCallStack => String -> a
```

**Always `throwIO` in `IO`.** `throw` creates a value whose evaluation throws,
so _when_ it fires depends on evaluation order, and GHC may pick among several
possible exceptions in a pure expression (the "imprecise exceptions" semantics).
That's a real hazard: `throw A + throw B` may throw either.

## 4. Catching

```haskell
try     :: Exception e => IO a -> IO (Either e a)
catch   :: Exception e => IO a -> (e -> IO a) -> IO a
handle  :: Exception e => (e -> IO a) -> IO a -> IO a   -- flipped catch
catches :: IO a -> [Handler a] -> IO a
```

The type of the handler decides what gets caught:

```haskell
r <- try @IOException (readFile p)          -- only IO errors
r <- try @SomeException action              -- everything, including async ⚠
```

**Do not `catch @SomeException` casually.** It swallows `ThreadKilled`,
`UserInterrupt` (Ctrl-C), timeouts, and `async`'s cancellation, turning a clean
shutdown into a hang. If you must catch broadly, either use
`safe-exceptions`/`unliftio` (which rethrow async exceptions automatically) or
check `fromException @SomeAsyncException` yourself.

Catching from pure code requires forcing inside the `try`:

```haskell
r <- try (evaluate (force expr))     -- needs NFData; evaluate alone is WHNF-only
```

## 5. Async exceptions and `mask`

Any thread can be interrupted at almost any allocation point by `throwTo`
(that's how `timeout`, `killThread`, and `race` work). Two consequences:

1. A resource acquired between "allocate" and "install the cleanup handler" can
   leak.
2. A cleanup action can itself be interrupted.

`mask` blocks async delivery for a region and hands you a `restore` to re-enable
it around the interruptible part:

```haskell
mask $ \restore -> do
  r <- acquire
  result <- restore (use r) `onException` release r
  release r
  pure result
```

That's `bracket`, essentially. **Use the combinators; don't hand-roll `mask`.**

`uninterruptibleMask` blocks even interruptible operations (`takeMVar`,
`throwTo`, `hClose` on a blocked handle). It can hang your program forever —
reserve it for very short, guaranteed-terminating cleanups.

## 6. The bracket family — the actual API you want

```haskell
bracket    :: IO a -> (a -> IO b) -> (a -> IO c) -> IO c   -- acquire, release, use
bracket_   :: IO a -> IO b -> IO c -> IO c
bracketOnError :: IO a -> (a -> IO b) -> (a -> IO c) -> IO c  -- release only on failure
finally    :: IO a -> IO b -> IO a
onException:: IO a -> IO b -> IO a                        -- no cleanup on success
```

```haskell
withDatabase :: Config -> (Conn -> IO a) -> IO a
withDatabase cfg = bracket (connect cfg) close
```

Every `with*` function in every library is this pattern. Prefer providing a
`withFoo` over exporting `openFoo`/`closeFoo` — it makes leaks impossible for
callers.

Ordering rule: **acquire and release must be in `mask`ed positions, use must
not be.** `bracket` gets this right; `do { r <- acquire; ...; release r }` does
not.

## 7. `safe-exceptions` vs `unliftio` vs `Control.Exception`

- **`Control.Exception`** — base. Correct, but `catch`/`try` at
  `SomeException` catch async exceptions too, and `bracket`'s cleanup is
  interruptible in a couple of places.
- **`safe-exceptions`** (`Control.Exception.Safe`) — same API, but
  synchronous-only catching by default (`catchAny` still rethrows async),
  `bracket` with uninterruptible cleanup, and `throwString` for quick cases.
  Drop-in; a good default for applications.
- **`unliftio`** (`UnliftIO.Exception`) — the same safety plus generalization
  over any `MonadUnliftIO`, so it works in `ReaderT env IO` without `lift`.

Pick one per project and stick to it — mixing produces subtly different
catching semantics in different modules.

## 8. Resource scopes beyond one function

`bracket` is lexical. When a resource's lifetime doesn't nest neatly —
streaming, dynamic acquisition — use **`resourcet`**:

```haskell
runResourceT $ do
  (key, h) <- allocate (openFile p ReadMode) hClose
  ...                                   -- released at runResourceT, or via release key
```

`conduit` is built on it. The trade: cleanup order is registration order
(reverse), and everything must run inside `runResourceT`.

## 9. `ExitCode` and top-level handling

`exitWith`/`exitFailure` throw `ExitCode` — which means a broad `catch` in
`main` will swallow your exit. The default top-level handler prints
`displayException` to stderr and exits 1.

```haskell
main :: IO ()
main = do
  hSetBuffering stdout LineBuffering
  run `catch` \(e :: AppError) -> do
    hPutStrLn stderr (displayException e)
    exitWith (ExitFailure 2)
```

`bracket`-installed cleanups do **not** run on `exitWith` from another thread
unless the main thread is the one exiting — and no cleanup runs on
`System.Posix.Process.exitImmediately` or a SIGKILL.

## Gotchas

- **`try (return (error "x"))` catches nothing.** Force with `evaluate`, and
  `force` if you need more than WHNF.
- **`throw` in `IO` is a bug.** Use `throwIO`; `throw` has imprecise ordering.
- **`catch @SomeException` swallows Ctrl-C, timeouts, and thread cancellation.**
  Use `safe-exceptions`/`unliftio`, or filter `SomeAsyncException`.
- **`catch` only catches exceptions from the action, not from the handler.**
- **The handler's exception type is what selects it** — `try` with an
  unconstrained result type is an ambiguity error, and `try @SomeException` at
  the wrong spot silently catches more than you meant.
- **`bracket`'s release runs under `mask`, but is still interruptible** in
  base; `safe-exceptions` makes it uninterruptible.
- **`uninterruptibleMask` can deadlock permanently.** Only for short cleanups.
- **`hClose` can throw** (flush failure), which in a `finally` will mask the
  original exception.
- **Pure exceptions (`error`) inside a lazily-returned value escape the
  `bracket`** — the thunk is forced after the handle is closed. Force before
  returning.
- **`ExitCode` is an exception**; a catch-all in `main` will trap your own
  `exitFailure`.
