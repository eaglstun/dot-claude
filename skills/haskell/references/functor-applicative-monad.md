---
semantic_id: "aV5mabYh7fIS0uCEL4EQ1Smqr1wnQAAP"
related_ids:
  - "bUx2tPbx6ySS-gCm6wED1S_69lxH0AAK"
  - "ad1WwIYJbKQb-yqCLoAB1e3s58wjkAAD"
---
# Functor, Applicative, Monad — and the rest of the hierarchy

Source:

- https://hackage.haskell.org/package/base/docs/Data-Functor.html
- https://hackage.haskell.org/package/base/docs/Control-Applicative.html
- https://hackage.haskell.org/package/base/docs/Control-Monad.html
- https://hackage.haskell.org/package/base/docs/Data-Traversable.html
- https://hackage.haskell.org/package/base/docs/Data-Semigroup.html

## 1. The hierarchy

```
Functor  ──▶  Applicative  ──▶  Monad
                   │                │
                   ▼                ▼
              Alternative       MonadPlus
Foldable ──▶ Traversable  (Traversable also requires Functor)
Semigroup ──▶ Monoid
```

Each arrow is a superclass constraint: every `Monad` is an `Applicative` is a
`Functor`. Since GHC 7.10 this is enforced (the "AMP" change), and since GHC 8.8
`fail` lives in `MonadFail`, not `Monad`.

| Class         | Core method                                | Intuition                            |
| ------------- | ------------------------------------------ | ------------------------------------ | -------------------------------- |
| `Functor`     | `fmap :: (a -> b) -> f a -> f b`           | map inside a structure, shape fixed  |
| `Applicative` | `pure`, `(<*>) :: f (a->b) -> f a -> f b`  | combine independent effects          |
| `Monad`       | `(>>=) :: m a -> (a -> m b) -> m b`        | next effect _depends on_ last result |
| `Semigroup`   | `(<>) :: a -> a -> a`                      | combine two values associatively     |
| `Monoid`      | `mempty`                                   | plus an identity                     |
| `Foldable`    | `foldr` / `foldMap`                        | consume a structure into a summary   |
| `Traversable` | `traverse :: (a -> f b) -> t a -> f (t b)` | effectful map preserving shape       |
| `Alternative` | `empty`, `(<                               | >)`                                  | choice/failure for `Applicative` |

**The dividing line that matters**: `Applicative` combines effects whose
_structure is known up front_; `Monad` lets the structure depend on a value.
`(,) <$> readLine <*> readLine` fixes two reads; `readLine >>= \n -> replicateM n readLine`
cannot be written applicatively. If you don't need the dependency, use
`Applicative` — more instances exist (validation, concurrency, static analysis
of parsers) precisely because it promises less.

## 2. The operator vocabulary

```haskell
(<$>)   :: Functor f     => (a -> b) -> f a -> f b        -- infix fmap
(<&>)   :: Functor f     => f a -> (a -> b) -> f b        -- flipped <$>
(<$)    :: Functor f     => a -> f b -> f a               -- replace contents
($>)    :: Functor f     => f a -> b -> f b
void    :: Functor f     => f a -> f ()

(<*>)   :: Applicative f => f (a -> b) -> f a -> f b
(*>)    :: Applicative f => f a -> f b -> f b             -- run both, keep right
(<*)    :: Applicative f => f a -> f b -> f a             -- run both, keep left
liftA2  :: Applicative f => (a -> b -> c) -> f a -> f b -> f c

(>>=)   :: Monad m => m a -> (a -> m b) -> m b
(=<<)   :: Monad m => (a -> m b) -> m a -> m b
(>=>)   :: Monad m => (a -> m b) -> (b -> m c) -> a -> m c   -- Kleisli compose
join    :: Monad m => m (m a) -> m a
```

`f <$> a <*> b <*> c` is the idiom for "apply an n-ary pure function to n
effectful arguments". Reach for it before `do`.

`traverse`/`mapM` and their `_` variants are the most-underused functions in
`base`:

```haskell
traverse  :: (Traversable t, Applicative f) => (a -> f b) -> t a -> f (t b)
traverse_ ::  (Foldable t,   Applicative f) => (a -> f b) -> t a -> f ()
sequenceA :: (Traversable t, Applicative f) => t (f a) -> f (t a)
for       :: ... -> t a -> (a -> f b) -> f (t b)     -- flipped traverse
```

`traverse` at `Maybe`/`Either` is validation; at `IO` it's a loop; at `[]` it's
a cartesian product. `sequenceA [Just 1, Just 2] == Just [1,2]`;
`sequenceA [Just 1, Nothing] == Nothing`.

## 3. The laws

**Functor**

```
fmap id      = id
fmap (g . h) = fmap g . fmap h      -- follows from the first, by parametricity
```

**Applicative**

```
pure id <*> v            = v                        -- identity
pure f <*> pure x        = pure (f x)               -- homomorphism
u <*> pure y             = pure ($ y) <*> u         -- interchange
pure (.) <*> u <*> v <*> w = u <*> (v <*> w)        -- composition
```

**Monad**

```
return x >>= f  = f x                   -- left identity
m >>= return    = m                     -- right identity
(m >>= f) >>= g = m >>= (\x -> f x >>= g)   -- associativity
```

Plus the compatibility law `fmap = liftM = (<$>)` and `(<*>) = ap` — an
instance where these disagree is broken, even if it type-checks.

**Semigroup/Monoid**

```
(a <> b) <> c = a <> (b <> c)
mempty <> a = a = a <> mempty
```

**Traversable**: `traverse` must preserve shape and respect applicative
composition; in practice, if your `Traversable` was derived, it's correct.

## 4. Instances worth knowing cold

| Type       | `Functor`/`Monad` meaning                                   |
| ---------- | ----------------------------------------------------------- |
| `Maybe`    | short-circuit on `Nothing`                                  |
| `Either e` | short-circuit on `Left`, keeping the **first** error        |
| `[]`       | nondeterminism — `>>=` is `concatMap`, `<*>` is cartesian   |
| `ZipList`  | `<*>` zips instead (no `Monad`)                             |
| `IO`       | sequencing of real-world effects                            |
| `(->) r`   | the reader: `fmap = (.)`, `f <*> g = \x -> f x (g x)`       |
| `(,) w`    | tags along a `Monoid` (writer-ish); `fmap` hits the **snd** |
| `State s`  | threaded state                                              |
| `Parser`   | sequential consumption                                      |

`Either`'s applicative **stops at the first error**. When you want to accumulate
all errors, use `Validation` (from `validation` or `either`'s `Validation`), whose
`Applicative` collects into a `Semigroup` and which deliberately has **no**
`Monad` instance — because `>>=`'s dependency makes accumulation impossible.

## 5. Alternative and MonadPlus

```haskell
class Applicative f => Alternative f where
  empty :: f a
  (<|>) :: f a -> f a -> f a
  some  :: f a -> f [a]      -- one or more
  many  :: f a -> f [a]      -- zero or more
```

`Maybe`: first `Just` wins. `[]`: concatenation. Parsers: backtracking choice.
`some`/`many` **diverge** on instances where the parser can succeed without
consuming input (`many (pure ())` hangs forever) — a real hazard with
hand-rolled parsers.

`guard :: Alternative f => Bool -> f ()` is the filter in list/`Maybe`
comprehension-style code:

```haskell
pythag = do a <- [1..20]; b <- [a..20]; c <- [b..20]; guard (a*a + b*b == c*c); pure (a,b,c)
```

## 6. Foldable — power and footguns

`Foldable` generalizes `length`, `sum`, `elem`, `maximum`, `null`, `toList`,
`foldr`, `foldMap`, and friends over any container. The cost is that these are
now type-general enough to accept things you didn't mean:

```haskell
length (3, "hi")   == 1      -- (,) a is Foldable over its second component
sum   (Just 3)     == 3
null  (Left "err") == True
```

GHC's `-Wcompat` includes `-Wtype-equality-out-of-scope` etc.; the specific
warning you want here is `-Wall`'s successor to the FTP debate:
`-Wtype-defaults` won't catch it. The pragmatic defence is a linter
(`hlint` flags `length` on tuples) and preferring the monomorphic
`Data.List.length` / `Data.Map.size` when the container is known.

`foldMap` is the good one: pick a `Monoid`, get a fold.

```haskell
foldMap Sum      [1..10]        -- Sum {getSum = 55}
foldMap (\x -> [x,x]) "ab"      -- "aabb"
```

`Data.Monoid` newtype wrappers: `Sum`, `Product`, `Any`, `All`, `First`,
`Last`, `Min`, `Max`, `Endo`, `Dual`.

## 7. Choosing the right abstraction

- Only mapping? `Functor`.
- Independent effects combined at the end? `Applicative` (and you get
  concurrency/validation for free in the right types).
- Later steps depend on earlier results? `Monad`.
- Combining two values of the same type? `Semigroup`, and add `Monoid` if
  there's a genuine identity.
- Want a summary of a container? `Foldable`/`foldMap`.
- Want to keep the container shape but run effects? `Traversable`.

If the code needs `Monad` only to `pure` at the end, it probably wanted
`Applicative`.

## Gotchas

- **`mapM_`/`forM_` over a `Map` iterates values, not pairs.** Use
  `Map.traverseWithKey` or `forM_ (Map.toList m)`.
- **`foldl` is almost never what you want** — `foldl'` for strict accumulation,
  `foldr` for lazy/infinite/short-circuiting. See `laziness-and-strictness.md`.
- **`Either`'s `Applicative` doesn't accumulate errors.** If you wrote
  `(,) <$> validateA <*> validateB` expecting both errors, you got the first.
- **`some`/`many` loop forever** on an `Alternative` that can succeed without
  consuming input.
- **`Foldable` makes nonsense type-check**: `length` of a tuple, `sum` of a
  `Maybe`, `elem` on `Either`.
- **`(,) w`'s `Functor` maps the second component.** Every "why didn't my tuple
  change" bug is this.
- **`mapM` over a large list in `IO` builds the whole result list** — use
  `mapM_`/`traverse_` when you're discarding it, or a streaming library.
- **`return` is just `pure`.** Modern style writes `pure`; `return` remains only
  for compatibility and habit.
