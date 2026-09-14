---
semantic_id: "ad1WwIYJbKQb-yqCLoAB1e3s58wjkAAD"
related_ids:
  - "aV5mabYh7fIS0uCEL4EQ1Smqr1wnQAAP"
  - "KfsGhKYZ7-3585ySy4ELUe1urU9yAAAC"
---
# Monad transformers and effect systems

Source:

- https://hackage.haskell.org/package/transformers
- https://hackage.haskell.org/package/mtl
- https://hackage.haskell.org/package/unliftio-core/docs/Control-Monad-IO-Unlift.html
- https://hackage.haskell.org/package/effectful
- https://www.fpcomplete.com/blog/2017/06/readert-design-pattern/

## 1. The transformer idea

A transformer adds one capability to an existing monad:

```haskell
newtype StateT  s m a = StateT  { runStateT  :: s -> m (a, s) }
newtype ReaderT r m a = ReaderT { runReaderT :: r -> m a }
newtype ExceptT e m a = ExceptT { runExceptT :: m (Either e a) }
newtype WriterT w m a = WriterT { runWriterT :: m (a, w) }
newtype MaybeT    m a = MaybeT  { runMaybeT  :: m (Maybe a) }
```

`lift :: (MonadTrans t, Monad m) => m a -> t m a` raises an action one layer;
`liftIO :: MonadIO m => IO a -> m a` raises all the way from the bottom.

Running unwinds outside-in:

```haskell
type App = ReaderT Env (StateT Counter (ExceptT AppError IO))

runApp :: Env -> Counter -> App a -> IO (Either AppError (a, Counter))
runApp env s = runExceptT . flip runStateT s . flip runReaderT env
```

## 2. `transformers` vs `mtl`

`transformers` gives the types and explicit `lift`. `mtl` adds the classes —
`MonadState s m`, `MonadReader r m`, `MonadError e m`, `MonadWriter w m` — with
instances that thread through every other transformer, so you write `get` and
`throwError` without counting `lift`s:

```haskell
step :: (MonadReader Env m, MonadState Int m, MonadError AppError m) => m ()
step = do
  env <- ask
  n   <- get
  when (n > limit env) (throwError TooMany)
  put (n + 1)
```

This is _capability-based_ typing: the signature says what the function may do,
and it works in any stack providing those. The cost is O(n²) instances (which is
why `mtl` needs `FunctionalDependencies` and why adding your own transformer
means writing pass-through instances for every class).

## 3. Stack order changes semantics — this is the part people get wrong

`StateT` over `ExceptT` and `ExceptT` over `StateT` are different programs:

```haskell
StateT s (ExceptT e m) a   ≡  s -> m (Either e (a, s))   -- error DISCARDS state
ExceptT e (StateT s m) a   ≡  s -> m (Either e a, s)     -- state SURVIVES the error
```

Same for `WriterT`: an error above a writer discards the log; below it, the log
survives. If you've ever lost your accumulated output on an exception path, this
was it.

`ReaderT` commutes with everything, which is one reason the `ReaderT` pattern
is popular.

## 4. `MonadUnliftIO` and the lifting problem

Functions like `bracket`, `catch`, `withFile`, `forkIO`, and `timeout` take an
`IO a` _argument_. To use them in a transformer stack you must run the inner
monad — which is only possible when the monad is isomorphic to `ReaderT env IO`:

```haskell
class MonadIO m => MonadUnliftIO m where
  withRunInIO :: ((forall a. m a -> IO a) -> IO b) -> m b
```

`ReaderT r IO` and `IdentityT IO` have instances. **`StateT`, `ExceptT`, and
`WriterT` cannot** — there's no way to produce the final state if the action is
run twice or not at all, so `bracket` over `StateT` either loses state updates
in the cleanup or duplicates them. `monad-control`/`lifted-base` do provide
instances for these, at the cost of exactly those surprising semantics (state
changes silently discarded in a handler).

This is the strongest practical argument for the `ReaderT` pattern.

## 5. The `ReaderT` pattern

```haskell
data Env = Env
  { envConfig  :: Config
  , envLogger  :: Text -> IO ()
  , envDbPool  :: Pool Connection
  , envCounter :: IORef Int          -- mutable state lives in a ref, not StateT
  }

newtype App a = App { unApp :: ReaderT Env IO a }
  deriving newtype (Functor, Applicative, Monad, MonadIO, MonadReader Env, MonadUnliftIO)

runApp :: Env -> App a -> IO a
runApp env = flip runReaderT env . unApp
```

Why it wins in applications:

- `MonadUnliftIO` works, so `bracket`/`catch`/`async` behave normally.
- State in `IORef`/`TVar` is thread-safe; `StateT` over a concurrent program is
  not (each thread would get its own copy).
- Errors are exceptions, which propagate uniformly across threads and FFI.
- The stack is one layer deep, so error messages stay readable.

Keep the _capability classes_ for testability: write
`MonadReader Env m, MonadIO m => m ()` signatures, and swap `Env` fields
(`envLogger`, a `DbOps` record) for fakes in tests.

## 6. When `StateT`/`ExceptT` _are_ right

Pure, single-threaded, bounded computations: interpreters, parsers, simulation
steps, compiler passes. `State`/`Except` over `Identity` are excellent there —
no IO, no unlifting problem, and the purity buys you testability for free.

`WriterT` is the exception to the exception: it leaks in every variant
(lazy accumulates thunks, strict still builds the whole log in memory before
you can see it). Use `StateT` with `modify'`, an `IORef`, or
`Control.Monad.RWS.CPS`/`Writer.CPS` (from `transformers` 0.5.6+), which fixes
the classic leak.

## 7. The effect-system landscape

When a `ReaderT` record of functions stops scaling, the alternatives:

| Library           | Approach                       | Notes                                                       |
| ----------------- | ------------------------------ | ----------------------------------------------------------- |
| **effectful**     | `Eff es a` over `ReaderT`+`IO` | fast, good errors, `IOE` at the bottom; the current default |
| **cleff**         | similar, `IORef`-based         | close cousin of effectful                                   |
| **fused-effects** | algebraic, carrier-based       | fast, but heavy type machinery                              |
| **polysemy**      | free-monad-ish, TH-friendly    | lovely API; needs plugin + optimizations for speed          |
| **freer-simple**  | free monad + open union        | simple, slower                                              |
| **rio**           | `ReaderT` with a standard env  | not an effect system — a batteries-included prelude+pattern |
| **mtl**           | classes                        | still fine, and everyone can read it                        |

Honest summary: effect systems buy you fine-grained, swappable capabilities and
better testing seams; they cost compile time, type-error legibility, and team
onboarding. **`ReaderT env IO` + records of functions covers most applications**,
and `effectful` is the one to reach for when it doesn't.

## 8. Practical patterns

```haskell
-- constrain to the capability, not the concrete monad
fetchUser :: (MonadReader Env m, MonadIO m) => UserId -> m (Maybe User)

-- a handle/record of operations, swappable in tests
data UserStore m = UserStore
  { getUser  :: UserId -> m (Maybe User)
  , putUser  :: User   -> m ()
  }

-- natural transformation to change the base monad
hoistUserStore :: (forall x. m x -> n x) -> UserStore m -> UserStore n
```

The "handle pattern" (a record of functions in `Env`) gets you 90% of an effect
system's testability with zero extra type machinery.

## Gotchas

- **Stack order changes behaviour.** `StateT` over `ExceptT` loses state on
  error; `ExceptT` over `StateT` keeps it.
- **`StateT` is per-thread.** `forkIO` inside a `StateT` gives the child its own
  state, and updates never come back.
- **No `MonadUnliftIO` for `StateT`/`ExceptT`/`WriterT`** — and the
  `monad-control` versions silently discard state changes made in a handler.
- **`ExceptT` over `IO` gives you two error channels.** Exceptions still exist;
  now callers must handle both. Pick one — usually exceptions at the top level,
  `Either` in pure functions.
- **`WriterT` leaks in all flavours.** Use `CPS` variants or `StateT`+`modify'`.
- **`Control.Monad.State` is the lazy `State`.** Import `.Strict`.
- **`liftIO` is not free in a deep stack** — each layer is a wrapper; hot loops
  in a 5-layer stack pay for it. `INLINE`/`SPECIALIZE` on small monadic helpers
  helps more than you'd think.
- **`mtl` classes need `FlexibleContexts`** (in GHC2021) and produce ambiguity
  errors when a stack has two of the same capability (two `StateT`s) —
  disambiguate by `newtype`ing.
- **A `deriving newtype` block for a `newtype App` needs
  `GeneralizedNewtypeDeriving`** and gives you every class the inner type has,
  including ones you may not want exposed (`MonadIO` in a "pure" layer).
