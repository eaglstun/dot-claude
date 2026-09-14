---
semantic_id: "5f_mrAIRo5G61hiGqJOg1V1LNFxxQAAP"
related_ids:
  - "4ZjGjKBZy7Saw4iSq4EVQWtrFVwzwAAB"
  - "aX5GkKZR4zmy-4iW7pEJ3W9-rV72wAAK"
---
# Laziness, strictness, and space leaks

Source:

- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/strict.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/bang_patterns.html
- https://hackage.haskell.org/package/base/docs/Prelude.html#v:seq
- https://hackage.haskell.org/package/deepseq/docs/Control-DeepSeq.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/profiling.html

## 1. Thunks and WHNF

Every unevaluated expression is a **thunk**: a heap object holding a code
pointer and its free variables. Evaluating a thunk to **weak head normal form
(WHNF)** means reducing until the outermost constructor or lambda is exposed —
and no further.

```haskell
xs = map (+1) [1..10]     -- one thunk
xs `seq` ()               -- forces to (_ : _) — the first cons cell only
length xs                 -- forces the spine, not the elements
sum xs                    -- forces the spine AND every element
```

WHNF vs NF is the distinction behind most confusion:

| Expression        | WHNF?          | Note                               |
| ----------------- | -------------- | ---------------------------------- |
| `(1+2, 3+4)`      | already WHNF   | the tuple constructor is outermost |
| `\x -> undefined` | already WHNF   | it's a lambda                      |
| `1 + 2`           | not WHNF → `3` |                                    |
| `Just undefined`  | already WHNF   | `seq` on it does _not_ explode     |
| `undefined`       | ⊥              |                                    |

`seq :: a -> b -> b` forces its first argument to WHNF when the result is
forced. `x \`seq\` y`does **not** guarantee an evaluation *order* — it
guarantees that if`y`is forced,`x`is too.`pseq`(from`parallel`) is the
ordered one.

Derived tools: `($!)` (strict application), `evaluate` (forces in `IO`, with
proper exception ordering), `force`/`deepseq`/`NFData` (full normal form),
`rnf`.

## 2. What laziness buys

- **Control structures as functions**: `if'`, `&&`, `||`, `bool`, short-circuit
  everything.
- **Infinite and circular data**: `iterate`, `cycle`, `fix`, knot-tying,
  `take 5 primes`.
- **Fusion**: `sum (map f [1..n])` runs in constant space with no intermediate
  list, because GHC's rewrite rules can fuse the producer/consumer pair.
- **Separation of generation from selection**: `head . sort` costs O(n) with a
  lazy merge sort, not O(n log n).

Don't turn laziness off wholesale — turn it off where it accumulates.

## 3. The leak catalogue

**a) Lazy left folds.** `foldl (+) 0 [1..10^7]` builds a 10-million-deep thunk
chain and then blows the stack when forced.

```haskell
sum'  = foldl' (+) 0                  -- Data.List / Data.Foldable, strict accumulator
```

`foldl'` is exported from `Prelude` since `base` 4.20 (GHC 9.10); before that,
import `Data.List` or `Data.Foldable`. `sum`/`product` are strict for `Int`-like
types in recent `base`, but `foldl'` is the one to reach for by reflex.

**b) Lazy accumulators in records and tuples.**

```haskell
data Stats = Stats { count :: Int, total :: Int }      -- lazy fields
step (Stats c t) x = Stats (c+1) (t+x)                 -- both fields are thunks
```

Fix: `data Stats = Stats { count :: !Int, total :: !Int }`, or `StrictData` for
the module.

**c) `Control.Monad.State` (the lazy one).** `Control.Monad.State` re-exports
the **lazy** `State`. `modify` builds thunks; `modify'` forces. Use
`Control.Monad.State.Strict` and `modify'`. Note that even "strict" `State` is
strict only in the _pair_, not the state value — `modify'` is still required.

**d) Lazy `Map` insertion.** `Data.Map.Lazy.insertWith (+) k 1 m` keeps a thunk
chain per key. Use `Data.Map.Strict`. **`Data.Map.Strict` is strict in values on
insert but the keys were always strict**; `Data.Map` (unqualified) is the lazy
one.

**e) Retaining the head of a long list**, or a big structure held alive by a
thunk that closes over it. A `where`-bound value used in only one branch is
still a closure captured by both.

**f) Lazy IO** (`readFile`, `hGetContents`) holding a handle open, or
interleaving unpredictably. See `io-and-mutable-state.md`.

**g) `WriterT`** in any form: the accumulator is a left fold in disguise.
Prefer `StateT` with `modify'`, or accumulate in `IORef`.

## 4. Bang patterns and strict extensions

```haskell
{-# LANGUAGE BangPatterns #-}   -- in GHC2021
go !acc []     = acc
go !acc (x:xs) = go (acc + x) xs

let !x = expensive in ...       -- forces at binding
f (Just !x) = ...               -- forces the payload
```

Module-level extensions:

- **`StrictData`** — every constructor field is strict unless prefixed with `~`.
  Low-risk, high-value; safe to turn on for most application modules.
- **`Strict`** — additionally makes let/where bindings, function arguments, and
  pattern bindings strict. Much more invasive: it changes the semantics of code
  that relied on laziness (including imported code's _use_ of your functions,
  since it changes what the function itself forces). Use deliberately, per
  module, usually only in numeric kernels.

Neither makes your program deeply strict — `!` is still just WHNF.

## 5. Finding a leak

```bash
# build with profiling
cabal build --enable-profiling
# then run with a heap profile
./prog +RTS -hc -p -RTS          # by cost centre  (needs -prof -fprof-auto)
./prog +RTS -hT -RTS             # by closure type — works WITHOUT profiling build
./prog +RTS -s -RTS              # summary: total alloc, max residency, GC time
```

Reading `-s`: **maximum residency** is the number that matters for a leak. High
total allocation with low residency is normal in Haskell (GHC allocates
constantly and the nursery is cheap); high _residency_ growing over time is the
leak.

`-hT` is the quickest first look because it needs no profiling rebuild. A heap
dominated by `THUNK`, `BLACKHOLE`, or a huge count of `Data.Map.Bin`/`(:)` tells
you which of §3 you're in. `eventlog2html` renders `.eventlog` output nicely
(`-l -hT` with `-eventlog`). Info-table profiling (`-hi`, GHC 9.4+) points at
the actual allocation _source line_ without cost centres.

`ghc-debug` can inspect a live heap and find retainers; `weigh` and
`nothunks` are the library-level tools — `nothunks` in particular lets you
assert "this state value contains no thunks" in tests, which is the only
reliable regression test for a leak.

## 6. When strictness is wrong

- **Short-circuiting**: `any p xs` on an infinite list, `find`, `takeWhile`.
  Forcing kills termination.
- **`foldr` with a lazy combining function** is the right fold for
  `map`/`filter`/`++`-style producers and for early exit.
- **Big-record updates where only one field is consumed.** Strictness forces
  work you'd have skipped.
- **`Data.Map.Lazy` on purpose**: memo tables of expensive values keyed by
  input, where you only ever look up a few.

## Gotchas

- **`seq` only forces to WHNF.** `seq (Just undefined) ()` is `()`. To force
  contents you need `deepseq`/`force` (and an `NFData` instance).
- **`foldl'` forces the accumulator to WHNF only.** A strict fold building a
  lazy tuple still leaks: `foldl' (\(a,b) x -> (a+x, b+1))` is a classic. Force
  the components or use a strict-field data type.
- **`Control.Monad.State` is the lazy one**, and `modify` is lazy even in
  `State.Strict`. Reach for `Strict` + `modify'` every time.
- **`Data.Map`'s unqualified module is `Data.Map.Lazy`.** Import
  `Data.Map.Strict` unless you specifically want lazy values.
- **`length` forces the spine, not the elements**; `null` forces almost nothing.
  Using `length xs > 0` on a big or infinite list is both slow and possibly
  divergent.
- **`WriterT` leaks in every flavour.** Strict `WriterT` isn't a fix.
- **`Strict` (the extension) changes semantics of code that reads perfectly
  fine** — including turning terminating programs into non-terminating ones.
  `StrictData` is the safe subset.
- **Total allocation is not a leak.** GHC programs allocate absurd amounts by
  design. Watch maximum residency.
- **A `where` binding used in one branch is still allocated as a thunk captured
  by the whole function**, which can retain more than you think.
