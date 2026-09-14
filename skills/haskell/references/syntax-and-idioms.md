---
semantic_id: "aYz2IabZa9AS79yCbqOD0WpuhdwzQAAK"
related_ids:
  - "4Z5uMOBZxySy24SA5qEH0W9v9dx1UAAF"
  - "ae5-RBY5S8mw65iQLpOI1Wt_115nwAAC"
---
# Syntax, pattern matching, and idioms

Source:

- https://www.haskell.org/onlinereport/haskell2010/haskellch3.html (expressions)
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/syntax.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/lambda_case.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/view_patterns.html
- https://hackage.haskell.org/package/base/docs/Data-Function.html

## 1. Pattern matching

Patterns match top-to-bottom, left-to-right, and **force only as far as the
pattern demands**.

```haskell
describe :: [Int] -> String
describe []          = "empty"
describe [x]         = "one: " <> show x
describe (x:y:_)     | x == y    = "starts with a pair"
                     | x <  y    = "ascending"
                     | otherwise = "other"
```

Useful pattern forms:

```haskell
f all@(x:xs)      = ...          -- as-pattern: name the whole and the parts
f ~(a, b)         = ...          -- irrefutable/lazy: doesn't force until a or b is used
f _               = ...          -- wildcard, binds nothing
g (Point{x = px}) = px           -- record pattern
g Point{..}       = x + y        -- RecordWildCards: brings all fields into scope
h (Just !v)       = v            -- BangPatterns: force the payload
```

`RecordWildCards` is divisive — it's excellent for constructing/destructuring at
a boundary (config, JSON) and awful in long functions where a reader can't tell
where `x` came from. `NamedFieldPuns` (`Point{x, y}`) is the middle ground and
usually the better default.

**View patterns** apply a function before matching:

```haskell
{-# LANGUAGE ViewPatterns #-}
f (Map.lookup k -> Just v) = v
f _                        = defaultV
```

**Pattern synonyms** give an abstract type a constructor-like interface:

```haskell
{-# LANGUAGE PatternSynonyms #-}
pattern Head :: a -> [a]
pattern Head x <- (x:_)
```

Bidirectional synonyms (`pattern P x = ...`) can also be used to _construct_.
They're the polite way to keep a representation abstract while allowing
matching — and to add `COMPLETE` pragmas so GHC stops warning about
"incomplete" matches on your synonyms.

## 2. Guards and `case`

```haskell
classify n
  | n < 0     = "neg"
  | n == 0    = "zero"
  | otherwise = "pos"
```

**Pattern guards** (Haskell 2010, no extension) bind and match inside a guard,
and `,` chains them:

```haskell
lookupUser env name
  | Just uid  <- Map.lookup name (users env)
  , Just user <- Map.lookup uid  (byId  env)
  , active user
  = Just user
  | otherwise = Nothing
```

This is the idiomatic replacement for a nested `case` pyramid, and it's often
clearer than a `MaybeT` stack for two or three steps.

`LambdaCase` (GHC2021) removes the throwaway binder:

```haskell
handle = \case
  Left  e -> logError e
  Right v -> use v
```

`MultiWayIf` gives guards in expression position:

```haskell
{-# LANGUAGE MultiWayIf #-}
x = if | n < 0 -> "neg" | n == 0 -> "zero" | otherwise -> "pos"
```

## 3. `let`, `where`, and layout

`where` attaches to a _declaration_ (and is visible across all its guards);
`let` is an expression and works anywhere. Prefer `where` for helpers that
several guards share, `let` for a value used once inside a `do` block.

The layout rule: a block opens at the column of its first token, and continues
while lines are indented further. A line at the same column starts a new item; a
line indented less closes the block. Explicit braces and semicolons are always
legal and occasionally worth it in generated code.

`BlockArguments` (GHC2021) removes `$` before a `do`/`\`/`case`:

```haskell
withFile path ReadMode \h -> do ...        -- no $ needed
forM_ xs \x -> print x
```

## 4. Operators, sections, and composition

```haskell
(+ 1)        -- right section:  \x -> x + 1
(1 +)        -- left section:   \x -> 1 + x
(subtract 1) -- because (- 1) is negative one, not a section
(`div` 2)    -- backticks make any function infix
```

Fixity declarations set precedence 0–9 and associativity:

```haskell
infixl 6 <+>      -- left-associative, precedence 6
infixr 5 :|
infix  4 ===      -- non-associative
```

Default for an operator without a fixity declaration is `infixl 9`. Reference
points: `.` is `infixr 9`, `^`/`^^`/`**` are `infixr 8`, `*`/`/` `infixl 7`,
`+`/`-` `infixl 6`, `:`/`++` `infixr 5`, comparisons `infix 4`, `&&` `infixr 3`,
`||` `infixr 2`, `>>=`/`>>` `infixl 1`, `$`/`$!`/`seq` `infixr 0`.

The glue functions:

```haskell
($)  :: (a -> b) -> a -> b        -- application, lowest precedence
(&)  :: a -> (a -> b) -> b        -- reverse application (Data.Function)
(.)  :: (b -> c) -> (a -> b) -> a -> c
on   :: (b -> b -> c) -> (a -> b) -> a -> a -> c   -- sortBy (compare `on` fst)
fix  :: (a -> a) -> a
```

**Point-free style** is good in small doses (`map (f . g)`,
`sortBy (comparing snd)`) and unreadable past two compositions. If you need
`flip . (.) . flip`, write the lambda.

## 5. `do` notation and what it desugars to

```haskell
do { x <- a; f x }        ⇒  a >>= \x -> f x
do { a; b }               ⇒  a >> b
do { let x = e; k }       ⇒  let x = e in k
do { pure x }             ⇒  pure x
```

A **failable pattern** in a bind desugars through `MonadFail`:

```haskell
do Just x <- action       ⇒  action >>= \case Just x -> ...; _ -> fail "..."
```

which is why that line requires `MonadFail m` and why it throws in `IO` rather
than type-erroring. Since GHC 8.6 this is enforced; `Monad` no longer has
`fail`.

`ApplicativeDo` (opt-in) makes GHC desugar independent binds to `<*>` instead
of `>>=`, unlocking parallelism/validation in types where the `Applicative` is
stronger than the `Monad`. It's finicky about what it detects — verify, don't
assume.

## 6. Idioms worth having in the fingers

```haskell
maybe def f m            -- eliminate Maybe
fromMaybe def m
either onLeft onRight e  -- eliminate Either
bool onFalse onTrue b    -- Data.Bool
when cond act            -- Control.Monad; unless is the negation
forM_ / traverse_        -- loop, discard results
foldr / foldl' / foldMap
zipWith3, zip, unzip
sortOn f                 -- decorate-sort-undecorate; better than sortBy (comparing f)
groupBy ((==) `on` key) . sortOn key
nub                      -- O(n²): use Data.List.sort + group, or Set
mapMaybe f               -- filter + map in one
catMaybes, partitionEithers, lefts, rights
iterate, unfoldr, replicate, cycle
interact                 -- whole-stdin-to-stdout, for scripts and code golf
```

`Data.Function.on`, `Data.Ord.comparing`, `Data.Ord.Down` (for descending
sorts) and `Data.List.sortOn` are the sorting toolkit.

## 7. The partial-function blacklist

These throw at runtime and have total replacements:

| Partial             | Use instead                                        |
| ------------------- | -------------------------------------------------- |
| `head` / `tail`     | pattern match, `uncons`, `listToMaybe`, `NonEmpty` |
| `fromJust`          | `maybe`, `fromMaybe`, pattern match                |
| `read`              | `readMaybe` (`Text.Read`)                          |
| `(!!)`              | `lookup`, `Map`, `Vector.!?`                       |
| `maximum`/`minimum` | guard for `null`, or `NonEmpty` versions           |
| `foldr1`/`foldl1`   | `foldr`/`foldl'` with an explicit seed             |
| `Map.!`             | `Map.lookup`, `Map.findWithDefault`                |
| `init`/`last`       | pattern match or `unsnoc` (`base` 4.19+)           |

GHC 9.8+ attaches an `x-partial` warning to `Data.List.head`/`tail`. Turn on
`-Wall` and, in application code, `-Werror=incomplete-patterns`.
`Data.List.NonEmpty` is the type-level fix when a list genuinely can't be empty.

## Gotchas

- **`(- 1)` is negative one, not a section.** Use `subtract 1`.
- **Operator precedence defaults to `infixl 9`** for any operator you define
  without a fixity declaration — usually not what you want.
- **`where` can't see `do`-block bindings**, since it scopes over the whole
  equation, not the expression. `let` can.
- **`$` cannot be used where a higher-rank argument is expected** (e.g.
  `runST $ ...` used to fail); GHC special-cases it now, but the general
  lesson — `$` is a function and can't do what juxtaposition does — still bites
  with impredicativity.
- **A failable pattern bind silently adds a `MonadFail` constraint**, and in
  `IO` "fails" by throwing `userError` with a message nobody will understand.
- **`nub` is quadratic** and `nub` on a big list is a routine accidental
  O(n²). `Data.List.sort`+`group` or a `Set` fold instead.
- **`RecordWildCards` shadows silently.** A field named `id` or `map` will
  quietly capture uses of the Prelude function.
- **Guards fall through to the next _equation_, not the next pattern**, if none
  match — and if no equation matches, it's a runtime pattern-match failure.
