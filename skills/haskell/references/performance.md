---
semantic_id: "ae5-RBY5S8mw65iQLpOI1Wt_115nwAAC"
related_ids:
  - "aX5GkKZR4zmy-4iW7pEJ3W9-rV72wAAK"
  - "Ya1y2QAJy4U4-9zSIIHQzGN__V5jAAAE"
---
# Performance: profiling, optimization, and Core

Source:

- https://downloads.haskell.org/ghc/latest/docs/users_guide/profiling.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/runtime_control.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/pragmas.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/rewrite_rules.html
- https://hackage.haskell.org/package/tasty-bench

## 1. Order of operations

1. **Measure.** `+RTS -s` first: it takes ten seconds and tells you whether the
   problem is allocation, GC, or actual work.
2. **Check the algorithm and the data structure.** A `Map` instead of a list
   lookup beats every micro-optimization below.
3. **Check for space leaks** (`laziness-and-strictness.md`). Most "slow" Haskell
   is a leak: GC time dominates because the heap is full of thunks.
4. **Check the string and container types.** `String` in a hot loop, boxed
   vectors of `Int`, `Data.Map` (lazy) accumulators.
5. **Then** reach for strictness annotations, `INLINE`, `SPECIALIZE`, unboxing.
6. **Then** read the Core.

Never benchmark a `-O0` build, and never benchmark a profiling build for timing
(profiling adds cost centres that inhibit optimization).

## 2. `+RTS -s`

```
   3,507,048,928 bytes allocated in the heap
      42,180,864 bytes copied during GC
       1,048,576 bytes maximum residency (3 sample(s))     ← the leak indicator
  Productivity  87.3% of total user
```

- **Total allocation** is usually irrelevant — GHC allocates constantly and the
  nursery is a bump allocator.
- **Maximum residency** growing with input size when it shouldn't = space leak.
- **Productivity below ~80%** = GC-bound; either you're leaking or you need a
  bigger allocation area (`-A32m`/`-A64m`).

## 3. Cost-centre profiling

```bash
cabal build --enable-profiling
cabal run --enable-profiling myapp -- +RTS -p -RTS      # writes myapp.prof
```

Requires `-prof -fprof-auto` (cabal's `--enable-profiling` adds them).
`myapp.prof` ranks by `%time` and `%alloc`. Manual cost centres when auto is too
coarse or too noisy:

```haskell
{-# SCC "parsePhase" #-} parse input
```

`-fprof-auto-top` (top-level only) keeps the noise down and the optimizer
happier than full `-fprof-auto`. Be aware that cost centres **change
optimization** — a function that gets inlined in production may not be in a
profiling build, so profile results are directional, not exact.

`-fprof-late` (GHC 9.4+) inserts cost centres _after_ optimization, which gives
you a profile of the program you actually ship. This is the flag to prefer now.

## 4. Heap profiling

```bash
./prog +RTS -hc -RTS        # by cost centre (needs profiling build)
./prog +RTS -hT -RTS        # by closure type — NO profiling build needed
./prog +RTS -hy -RTS        # by type
./prog +RTS -hr -RTS        # by retainer — "who is keeping this alive"
./prog +RTS -hi -RTS        # by info table (GHC 9.4+, -finfo-table-map)
./prog +RTS -l-au -RTS      # eventlog → eventlog2html
hp2ps -c prog.hp && open prog.ps
```

Reading it: a band that grows linearly with input and never shrinks is the leak.
`THUNK`/`BLACKHOLE`-dominated heap → lazy accumulation. Lots of `(:)`/`ARR_WORDS`
→ you're keeping a list/ByteString alive. `-hr` answers "what's holding it",
which is the question you actually have.

`ghc-debug` attaches to a live process for deep heap analysis;
`eventlog2html` renders the profile as an interactive page and is the nicest
front end.

## 5. `INLINE`, `INLINABLE`, `SPECIALIZE`

```haskell
{-# INLINE    smallHelper #-}      -- always inline (make sure it IS small)
{-# INLINABLE polymorphicFn #-}    -- expose the definition for cross-module specialization
{-# SPECIALIZE genericSum :: [Int] -> Int #-}
{-# NOINLINE globalRef #-}         -- required for unsafePerformIO globals
```

- **The real cost of polymorphism is dictionary passing.** A `Num a =>` function
  in a hot loop can't use machine addition until it's specialized. `INLINABLE`
  on the definition lets GHC specialize it at each call site's type in _other_
  modules; `SPECIALIZE` makes a named copy.
- `INLINE` on a large function bloats code and can make things slower.
- GHC inlines small functions automatically within a module; the pragmas matter
  mostly at module boundaries.
- `-fexpose-all-unfoldings -fspecialise-aggressively` is the blunt instrument for
  a library whose users need specialization.

## 6. Strictness and unboxing

Adding `!` to accumulator arguments and record fields is the single
highest-yield optimization in Haskell, because it turns a heap-allocating thunk
chain into a register-resident loop.

```haskell
data Acc = Acc {-# UNPACK #-} !Int {-# UNPACK #-} !Double
```

**Worker/wrapper**: GHC's strictness analysis rewrites a function on boxed
arguments into a worker on unboxed ones plus a thin wrapper. It only fires when
the function is provably strict — which is why `!` unlocks it. `-ddump-simpl`
shows `$wgo` workers when it worked.

`-fllvm` (needs a matching LLVM) can help numeric code by 10–30%; it does
nothing for allocation-bound code.

## 7. Fusion

GHC's rewrite rules eliminate intermediate structures:

```haskell
sum (map (*2) (filter even [1..n]))     -- no lists allocated at all
```

Fusion works for lists (build/foldr), `vector` (stream fusion), and `text`. It
**breaks** when the intermediate is used twice, stored in a data structure,
passed through a non-inlined boundary, or the pipeline crosses a module without
`INLINABLE`. There is no warning when fusion fails; you check with
`-ddump-simpl` (look for whether a list constructor survives) or by benchmarking.

Writing your own rules:

```haskell
{-# RULES "map/map" forall f g xs. map f (map g xs) = map (f . g) xs #-}
```

Rules are unchecked — GHC will not verify that the two sides are equivalent.
A wrong rule silently changes your program's meaning. Add `-Winline-rule-shadowing`
and test both sides.

## 8. Reading Core

```bash
cabal build --ghc-options="-ddump-simpl -ddump-to-file -dsuppress-all -dno-suppress-type-signatures"
# → dist-newstyle/.../MyModule.dump-simpl
```

`-dsuppress-all` makes it readable. What to look for:

- **`case x of` on a boxed type in a loop** — a thunk is being forced each
  iteration; add strictness.
- **`I# `/`D#` boxing and unboxing pairs** — a value is being re-boxed;
  `UNPACK` or worker/wrapper isn't firing.
- **A dictionary argument (`$fNumInt`, `$dNum`) in the inner loop** — not
  specialized; add `SPECIALIZE`/`INLINABLE`.
- **`$wgo` workers** — good, worker/wrapper fired.
- **List constructors surviving a pipeline** — fusion failed.

`-ddump-stg-final` and `-ddump-cmm` for the levels below; rarely needed.

## 9. Benchmarking

```haskell
import Test.Tasty.Bench
main = defaultMain
  [ bench "parse/small" $ nf parseConfig smallInput
  , bench "parse/large" $ nf parseConfig largeInput
  ]
```

`tasty-bench` is a drop-in, dependency-light alternative to `criterion` and
integrates with the rest of a tasty suite; `criterion` gives richer statistics
and HTML reports; `gauge` is a lighter criterion fork.

**`nf` vs `whnf`**: `whnf` on a function returning a lazy structure measures
almost nothing (it builds one constructor). Use `nf` unless you specifically
want WHNF and know why. Pass the function and argument separately
(`nf f x`, not `nf (\_ -> f x) ()`) so the benchmark can't be lifted out of the
loop by the optimizer.

Compare across commits with `tasty-bench`'s `--baseline`/`--fail-if-slower` in
CI to catch regressions.

## 10. RTS tuning

```
-A64m         larger nursery — often the single biggest win for allocation-heavy programs
-n4m          nursery chunks (with -N)
-N            all cores
-qn2          limit parallel GC threads (parallel GC on many cores can hurt)
-c            compacting GC for the old gen — lower residency, more CPU
-I0           disable idle GC (for latency-sensitive servers)
-T            runtime stats readable from GHC.Stats
```

`-with-rtsopts=-A64m -N` in `ghc-options` bakes a default in while still
allowing `+RTS` overrides (with `-rtsopts`).

## Gotchas

- **Never benchmark `-O0` or a profiling build.**
- **Profiling changes optimization**, so a profile can point at a function that
  doesn't exist in the release build. `-fprof-late` avoids most of this.
- **Total allocation is not the problem; residency is.**
- **`whnf` in a benchmark measures nothing** for lazily-produced results.
- **Fusion fails silently.** Check with `-ddump-simpl` or a benchmark, not by
  hope.
- **`INLINE` on a big function makes things worse** — code bloat, worse cache
  behaviour, longer compiles.
- **A `RULES` pragma is not checked for correctness.** A wrong rule is a silent
  miscompilation of your own program.
- **Dictionary passing in a hot polymorphic loop is often the whole problem**,
  and it's invisible in the source.
- **Parallel GC with a small `-A` on many cores can make a program slower than
  single-threaded.** Try `-A64m -qn2`.
- **`-O2` over `-O1` is usually a small win and a large compile-time cost.**
  Measure before making it the default everywhere.
