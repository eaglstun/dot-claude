---
semantic_id: "bYXMHKZFq6AaysiC7pER1W_P_L93wAAK"
related_ids:
  - "bc7M_KZda1KxeyiEYoGB0WgP_Tx3wAAA"
  - "bR3iBSDJo6iY44yOrpON1W5vz383EAAE"
---
# Testing and debugging

Source:

- https://hackage.haskell.org/package/hspec
- https://hackage.haskell.org/package/tasty
- https://hackage.haskell.org/package/QuickCheck
- https://hackage.haskell.org/package/hedgehog
- https://downloads.haskell.org/ghc/latest/docs/users_guide/ghci.html#the-ghci-debugger

## 1. Frameworks

**hspec** — RSpec-style, the most common choice for applications:

```haskell
-- test/Spec.hs
{-# OPTIONS_GHC -F -pgmF hspec-discover #-}
```

```haskell
-- test/MyApp/ParserSpec.hs
module MyApp.ParserSpec (spec) where
import Test.Hspec
import Test.Hspec.QuickCheck (prop)

spec :: Spec
spec = do
  describe "parseConfig" $ do
    it "parses a minimal config" $
      parseConfig "port = 80" `shouldBe` Right (Config 80)

    it "rejects a negative port" $
      parseConfig "port = -1" `shouldSatisfy` isLeft

    prop "round-trips" $ \c -> parseConfig (renderConfig c) === Right c
```

`hspec-discover` finds every `*Spec.hs` and builds the suite — add
`build-tool-depends: hspec-discover:hspec-discover` to the test stanza.
Matchers: `shouldBe`, `shouldSatisfy`, `shouldContain`, `shouldThrow`,
`shouldReturn`, `shouldMatchList`.

**tasty** — a test _aggregator_: combine QuickCheck, HUnit, golden, and
benchmark providers under one runner with a shared CLI
(`--pattern`, `--num-threads`, `--quickcheck-tests`).

```haskell
main = defaultMain $ testGroup "all"
  [ testCase     "unit"  $ f 1 @?= 2
  , testProperty "prop"  $ \x -> f x >= x
  , goldenVsString "render" "test/golden/out.txt" (pure (render sample))
  ]
```

Both are good. hspec reads better for example-heavy suites; tasty is nicer when
you have several kinds of test.

## 2. Property testing — QuickCheck

```haskell
import Test.QuickCheck

prop_reverseInvolutive :: [Int] -> Bool
prop_reverseInvolutive xs = reverse (reverse xs) == xs

prop_sortOrdered :: [Int] -> Property
prop_sortOrdered xs = classify (null xs) "empty" $
  isSorted (sort xs)

quickCheck prop_reverseInvolutive
quickCheckWith stdArgs{maxSuccess = 10000} prop_sortOrdered
verboseCheck prop           -- print every case
```

Combinators: `==>` (conditional, but discards — prefer a custom generator),
`.&&.`, `.||.`, `===` (shows both sides on failure — always prefer over `==`),
`counterexample`, `label`/`classify`/`collect` (check your generator actually
covers interesting cases), `withMaxSuccess`, `forAll` (explicit generator),
`shrinking`.

Custom generators:

```haskell
instance Arbitrary User where
  arbitrary = User <$> arbitrary <*> genName <*> choose (0, 120)
  shrink = genericShrink        -- from Generic; give it one, or failures are unreadable

genName :: Gen Text
genName = T.pack <$> listOf1 (elements ['a'..'z'])
```

**Write `shrink`.** Without shrinking, a failing property reports a random
300-element list instead of the two-element case that actually breaks.
`genericShrink` is usually enough.

Use `Gen`'s `sized`/`scale`/`resize` for recursive types, or you'll generate
trees that take a year to evaluate:

```haskell
arbitrary = sized go
  where go 0 = Leaf <$> arbitrary
        go n = oneof [Leaf <$> arbitrary, Node <$> go (n `div` 2) <*> go (n `div` 2)]
```

## 3. Hedgehog — the alternative

```haskell
import Hedgehog
import qualified Hedgehog.Gen   as Gen
import qualified Hedgehog.Range as Range

prop_roundtrip :: Property
prop_roundtrip = property $ do
  u <- forAll genUser
  tripping u encode decode
```

Differences that matter: generators carry their own shrinking (no separate
`shrink`, no `Arbitrary` orphan problem), ranges are explicit, and the failure
output shows the shrunk value with source context. `tripping` is a built-in
round-trip property. Hedgehog's state-machine testing
(`Hedgehog.Internal.State`) is the best tool in the ecosystem for testing
stateful APIs.

## 4. Property patterns worth reaching for

- **Round-trip**: `decode . encode == Right`. Catches most serialization bugs.
- **Invariant**: the output of every operation satisfies the data structure's
  invariant.
- **Model/oracle**: compare an optimized implementation against an obviously
  correct slow one (`Map` vs association list).
- **Metamorphic**: `sort (xs ++ ys) == sort (ys ++ xs)` when you can't state the
  full spec.
- **Idempotence**: `normalize . normalize == normalize`.
- **Algebraic laws**: associativity, identity, functor laws —
  `quickcheck-classes` / `hedgehog-classes` package the standard ones for your
  instances.

## 5. Golden tests

`tasty-golden` / `hspec-golden`: compare output against a checked-in file,
regenerate with a flag. Ideal for pretty-printers, generated SQL, CLI help text,
and API responses. Keep golden files small and reviewable, and make the
regeneration command obvious in the README, or people will `--accept`
everything without reading it.

## 6. Testing `IO` code

- Keep the pure core pure and test _that_ (see `io-and-mutable-state.md` §9).
- For the effectful shell, pass capabilities in a record (`Env`) and substitute
  fakes — the handle pattern from `monad-transformers-and-effects.md` §8.
- `temporary`'s `withSystemTempDirectory` for anything touching the filesystem.
- `hspec-wai` for WAI apps; `warp` on a random port plus a real client for
  integration tests.
- `testcontainers-hs` or a docker-compose fixture for a real database; `tmp-postgres`
  spins a throwaway Postgres per suite.
- `shouldThrow` with a selector for expected exceptions:
  `action \`shouldThrow\` (== NotFound)`.

## 7. `doctest`

```haskell
-- | Add two numbers.
--
-- >>> add 2 3
-- 5
add :: Int -> Int -> Int
```

`doctest` runs the examples in your haddocks, so documentation can't drift.
Cheap to add, catches the "the example in the docs doesn't compile" class of
bug. Note it must be run with the same package environment
(`cabal repl --with-ghc=doctest`, or the `doctest-parallel` driver).

## 8. Debugging

```haskell
import Debug.Trace
trace ("x = " <> show x) expr        -- prints when the expr is forced
traceShow x expr
traceM  ("here")                     -- in a monad
traceShowId x                        -- prints and returns
```

`trace` output timing is governed by _evaluation_, not program order — a trace
can appear far from where you expected, or not at all if the value is never
forced. That's information too: a missing trace means dead/unforced code.

GHCi debugger:

```
:break MyModule 42          -- break at a line
:break myFunction
:trace main                 -- record the evaluation history
:step / :steplocal / :continue
:history                    -- where did we come from (after an exception)
:force x / :print x         -- :print shows thunks without forcing
:show bindings
```

`:print` is the one people don't know: it shows the structure of a value with
`_` for unevaluated thunks, which makes laziness bugs visible.

Other tools: `-xc` (with a profiling build) prints a cost-centre stack on an
uncaught exception — the closest thing to a stack trace; `HasCallStack`
constraints for your own errors; GHC 9.10+ exception backtraces.

## 9. Assertions and invariants

```haskell
import Control.Exception (assert)
assert (n >= 0) (compute n)         -- removed by -O (via -fignore-asserts)
```

For invariants you want kept in production, use an explicit `error`/`throwIO`
with a message, or `nothunks` in tests to assert that a long-lived structure has
no thunks — the only reliable regression test for a space leak.

## Gotchas

- **`shouldBe` on `Double` fails on rounding.** Use an epsilon comparison or
  `Test.Hspec.Expectations` with a custom predicate.
- **A property with no `shrink` reports an unusable counterexample.**
- **`==>` discards cases**, and QuickCheck gives up after too many discards —
  the property then "passes" while testing almost nothing. Watch the discard
  count, or write a generator.
- **Recursive `Arbitrary` without `sized` generates exponential structures**
  and hangs the suite.
- **`===` shows both sides; `==` shows nothing.** Always `===`.
- **`trace` fires on evaluation, not execution** — misleading order, or silence.
- **`assert` is compiled away with `-O`**; don't rely on it for production
  checks.
- **Tests that share a temp directory or a fixed port race** under tasty/hspec
  parallelism. Randomize or serialize (`--num-threads 1`, `sequential`).
- **`hspec-discover` needs the pragma at the top of `Spec.hs` and the
  build-tool-depends entry**; without either it silently runs zero tests.
- **A test suite that always exits 0** because it never `exitFailure`s — check
  `type: exitcode-stdio-1.0` and that CI actually fails on a broken test.
