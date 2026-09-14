---
semantic_id: "bc7M_KZda1KxeyiEYoGB0WgP_Tx3wAAA"
related_ids:
  - "bYXMHKZFq6AaysiC7pER1W_P_L93wAAK"
  - "aX5GkKZR4zmy-4iW7pEJ3W9-rV72wAAK"
---
# IO, evaluation, and mutable state

Source:

- https://hackage.haskell.org/package/base/docs/System-IO.html
- https://hackage.haskell.org/package/base/docs/Data-IORef.html
- https://hackage.haskell.org/package/base/docs/Control-Monad-ST.html
- https://hackage.haskell.org/package/base/docs/System-IO-Unsafe.html
- https://hackage.haskell.org/package/base/docs/Control-Exception.html#v:evaluate

## 1. What `IO` is

`IO a` is a **value describing an effect**, not an executed effect. `main` is
the one such value the runtime runs. This is why:

```haskell
xs = [putStrLn "a", putStrLn "b"]     -- nothing printed; a list of two actions
main = sequence_ xs                    -- now it prints
```

and why `let x = launchMissiles` is safe but `x <- launchMissiles` is not.

Operationally, `IO a` is `State# RealWorld -> (# State# RealWorld, a #)` — a
token-threading state monad — which is where the ordering guarantee comes from.
You never see that type unless you're reading Core or `GHC.IO`.

## 2. Evaluation vs execution

Two independent axes, and conflating them causes real bugs:

```haskell
let x = error "boom"      -- neither evaluated nor executed
x `seq` ()                -- evaluated → throws
print (length [x])        -- not evaluated (length doesn't force elements)
```

```haskell
r <- try (return (error "boom"))    -- catches NOTHING: return doesn't force
r <- try (evaluate (error "boom"))  -- catches it
```

`return`/`pure` wraps a thunk. `evaluate :: a -> IO a` forces to WHNF _inside_
`IO`, with well-defined exception ordering. When catching exceptions from pure
code, `evaluate` (or `evaluate . force`) is mandatory. See
`exceptions-and-resources.md`.

## 3. Handles, buffering, and encoding

```haskell
import System.IO
main = do
  hSetBuffering stdout LineBuffering    -- or NoBuffering for interactive prompts
  hSetEncoding  stdout utf8             -- do not trust the locale
  ...
```

Two defaults that cause "it works on my machine" bugs:

- **stdout is line-buffered to a terminal and block-buffered to a pipe.** Output
  that appears interactively vanishes when piped and the program crashes.
- **The default encoding comes from the locale.** On a machine with `LANG=C`,
  `putStrLn` on non-ASCII throws `invalid argument (invalid character)`. Set
  `hSetEncoding` explicitly, or use `utf8` + `hSetEncoding stderr utf8` at
  startup. `mkTextEncoding "UTF-8//TRANSLIT"` for lenient output.

`withFile` over `openFile` — it closes on exception:

```haskell
withFile path ReadMode $ \h -> do
  contents <- hGetContents' h        -- base 4.15+: strict, safe
  ...
```

## 4. Lazy IO — the trap

`readFile`, `hGetContents`, and `getContents` return a **lazily** produced
`String`. The handle stays open until the string is fully consumed, and the read
happens at unpredictable times relative to other effects.

```haskell
main = do
  s <- readFile "f.txt"
  writeFile "f.txt" (map toUpper s)   -- ERROR or corruption: still reading it
```

The correct tools:

```haskell
import qualified Data.Text.IO as T
t <- T.readFile path                  -- strict
b <- BS.readFile path                 -- strict ByteString
s <- hGetContents' h                  -- strict String (base 4.15+)
```

or a streaming library (`conduit`, `streamly`) when the file doesn't fit in
memory. See `parsing-and-streaming.md`. **`Data.Text.Lazy.IO.readFile` is also
lazy IO** — the "lazy" in the module name is the same hazard.

## 5. `IORef`

```haskell
import Data.IORef
ref <- newIORef (0 :: Int)
modifyIORef' ref (+1)        -- STRICT version; plain modifyIORef leaks thunks
v   <- readIORef ref
writeIORef ref 42
atomicModifyIORef' ref (\x -> (x+1, ()))   -- atomic w.r.t. other threads
```

Always `modifyIORef'`. Plain `modifyIORef` builds a thunk chain and is a
top-three source of space leaks.

`IORef` is _not_ a synchronization primitive: `readIORef` then `writeIORef` from
two threads races. `atomicModifyIORef'` is a CAS loop and is safe, but only for
one ref at a time. For anything more, use `MVar` or `TVar` (see
`concurrency-and-stm.md`).

## 6. `MVar` in one line

A `MVar a` is a box that is full or empty; `takeMVar` blocks while empty,
`putMVar` blocks while full. It doubles as a mutex (`modifyMVar_`), a one-shot
channel, and a signal. Details in `concurrency-and-stm.md`.

## 7. The `ST` monad

`ST s` gives real mutable state with **no** observable effects — you can run it
from pure code:

```haskell
import Control.Monad.ST
import Data.STRef

sumST :: [Int] -> Int
sumST xs = runST $ do
  ref <- newSTRef 0
  mapM_ (\x -> modifySTRef' ref (+x)) xs
  readSTRef ref
```

`runST :: (forall s. ST s a) -> a`. The rank-2 `forall s.` is what stops an
`STRef` leaking out of the computation — if you try, you get a rigid-type-
variable error about `s` escaping its scope.

`ST` is the right home for in-place algorithms: mutable vectors
(`Data.Vector.Mutable`, `Data.Vector.Unboxed.Mutable`), union-find, sorting,
dynamic programming tables, hash building. `Data.Array.ST`/`STUArray` too.
`stToIO` lifts it when you need it inside `IO`.

## 8. `unsafePerformIO` and friends

```haskell
import System.IO.Unsafe (unsafePerformIO)

{-# NOINLINE globalCache #-}
globalCache :: IORef (Map Text Value)
globalCache = unsafePerformIO (newIORef mempty)
```

Legitimate uses are narrow: a global mutable variable (with `NOINLINE`),
memoization of a genuinely pure function, and wrapping a C function that is
pure but lives in `IO`. Everything else is a bug.

The hazards are all about the optimizer, which assumes purity:

- **Without `{-# NOINLINE #-}` the effect can be duplicated** — you get two
  caches, or none.
- The effect can be **floated out of a lambda** (run once instead of each call)
  or **eliminated entirely** (result unused).
- The effect can be **reordered** relative to other `IO`.
- `unsafeDupablePerformIO` explicitly permits duplication (cheaper, no thread
  safety); `unsafeInterleaveIO` is the primitive lazy IO is built on and
  produces the same hazards on purpose.

## 9. Getting out of `IO` — the design rule

Push effects to the edges. A function that does file IO _and_ parsing _and_
business logic can't be tested; split it:

```haskell
loadConfig :: FilePath -> IO (Either ConfigError Config)
loadConfig p = parseConfig <$> BS.readFile p     -- IO here

parseConfig :: ByteString -> Either ConfigError Config   -- pure, testable
```

For code that needs _some_ effects, the ReaderT-over-IO pattern with a record of
capabilities beats a deep transformer stack — see
`monad-transformers-and-effects.md`.

## Gotchas

- **`return`/`pure` doesn't force anything.** `try (return (error "x"))`
  catches nothing; use `evaluate`.
- **`modifyIORef` is lazy.** Use `modifyIORef'`. Same for `modifySTRef'`.
- **`readFile`/`hGetContents` are lazy IO** and hold the handle open; combining
  them with a write to the same file corrupts or errors.
- **`hClose` on a lazily-read handle truncates the string you already have** —
  the remaining reads return nothing rather than failing loudly.
- **stdout buffering changes when you pipe.** Crash-with-no-output almost always
  means block buffering plus an uncaught exception; `hSetBuffering stdout
LineBuffering` or `hFlush`.
- **Text encoding comes from the locale.** Set it explicitly at startup or your
  program breaks in a Docker container with no `LANG`.
- **`unsafePerformIO` without `NOINLINE` gives you N copies of your "global".**
- **`IORef` is not thread-safe** for read-modify-write; use `atomicModifyIORef'`
  or an `MVar`/`TVar`.
- **`ST` can't do IO**, and that's the point — reaching for `unsafeIOToST` means
  you wanted `IO`.
