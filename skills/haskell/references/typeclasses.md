---
semantic_id: "LZ5GmZAZayGY-8yG6oEfVcp-7V6WwAAO"
related_ids:
  - "aX5GkKZR4zmy-4iW7pEJ3W9-rV72wAAK"
  - "LXdSEJLN7yAQywS36oGuUe7qxf4XUAAK"
---
# Type classes, instances, and deriving

Source:

- https://www.haskell.org/onlinereport/haskell2010/haskellch4.html#x10-770004.3
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/instances.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/deriving.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/deriving_via.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/type_class_extensions.html

## 1. What a class actually compiles to

A class is a record of functions (a **dictionary**); an instance is a value of
that record; a constraint `Show a =>` is an extra hidden argument.

```haskell
class Show a where show :: a -> String
-- ≈ data ShowDict a = ShowDict { show :: a -> String }
f :: Show a => a -> String        -- ≈ f :: ShowDict a -> a -> String
```

Three consequences that explain most confusing behaviour:

1. **Instance selection is by type, at compile time.** There is no runtime
   dispatch on a value. If the type isn't known at the call site, you get an
   ambiguity error, not a runtime failure.
2. **Dictionaries are passed, so polymorphic code can be slower.** `SPECIALIZE`
   and `INLINABLE` exist to remove that indirection (see `performance.md`).
3. **A class must be _globally coherent_** — one instance per type per class,
   across the whole program, or two modules can disagree about what `Map`
   ordering means and corrupt data structures.

## 2. Writing a class

```haskell
class Container f where
  empty  :: f a
  insert :: a -> f a -> f a
  toList :: f a -> [a]

  -- default method, defined in terms of the others
  fromList :: [a] -> f a
  fromList = foldr insert empty

  {-# MINIMAL empty, insert, toList #-}
```

`{-# MINIMAL #-}` documents which methods must be defined; GHC warns when an
instance under-defines. Write it whenever there are default methods — otherwise
a missing method becomes a runtime `undefined method` error instead of a
compile-time warning.

Superclasses are constraints on the class head:

```haskell
class Eq a => Ord a where compare :: a -> a -> Ordering
```

A superclass is a _requirement_, not inheritance: `Ord a` implies `Eq a` is
available, and every `Ord` instance needs an `Eq` instance to exist.

## 3. Class extension flags

| Extension                 | Enables                         | In GHC2021 |
| ------------------------- | ------------------------------- | ---------- |
| `MultiParamTypeClasses`   | `class Convert a b where ...`   | yes        |
| `FlexibleInstances`       | `instance C (Maybe Int)`        | yes        |
| `FlexibleContexts`        | `f :: C (Maybe a) => ...`       | yes        |
| `ConstrainedClassMethods` | extra constraints on a method   | yes        |
| `FunctionalDependencies`  | `class C a b \| a -> b`         | no         |
| `UndecidableInstances`    | turns off the termination check | no         |
| `DefaultSignatures`       | generic default method bodies   | no         |
| `QuantifiedConstraints`   | `forall x. Show (f x) => ...`   | no         |

`UndecidableInstances` is not evil — it's usually needed for perfectly sane
instances that GHC's conservative check can't see terminate. It only risks a
looping _compiler_, never a looping program.

Functional dependencies (`| a -> b`) say "`a` determines `b`", which lets
inference resolve `b`. Modern code more often reaches for an associated type
family instead (see `advanced-types.md`), but `mtl` is built on fundeps and
they're still the right tool for a two-parameter class with a determined result.

## 4. Instances, coherence, and orphans

```haskell
instance Show Shape where
  show (Circle r) = "Circle " <> show r
  show Rect{}     = "Rect"
```

An **orphan instance** is one defined in a module that owns neither the class
nor the type. GHC warns (`-Worphans`). They break the coherence guarantee in
practice: two packages can each define `instance ToJSON UTCTime`, and which one
you get depends on the import graph — with no error, just different output.

If you need behaviour the upstream instance doesn't give you, the answer is a
`newtype`, not an orphan:

```haskell
newtype UnixTime = UnixTime UTCTime
instance ToJSON UnixTime where toJSON (UnixTime t) = toJSON (utcTimeToPOSIXSeconds t)
```

If you genuinely must write an orphan (bridging two packages you don't own),
put it in its own module, name it `...Orphans`, and mention it in the haddock.

**Overlapping instances**: `{-# OVERLAPPING #-}` / `{-# OVERLAPPABLE #-}` /
`{-# INCOHERENT #-}` pragmas on the _instance_ (not, since GHC 7.10, on the
module) let a more specific instance win. Overlap is a maintenance hazard —
adding an import can change which instance is picked. `INCOHERENT` gives up on
determinism entirely; treat any use of it as a bug report waiting to happen.

## 5. Deriving strategies

With `DerivingStrategies` (on by default in GHC2024, otherwise enable it), each
`deriving` clause names how:

```haskell
{-# LANGUAGE DerivingStrategies, GeneralizedNewtypeDeriving, DeriveAnyClass, DerivingVia #-}

newtype Age = Age Int
  deriving stock   (Show, Eq, Ord)      -- generated structurally: "Age 3"
  deriving newtype (Num, Enum)          -- reuse Int's instances via coerce
  deriving anyclass (SomeClassWithDefaults)
  deriving (ToJSON) via Int             -- use Int's instance at Age's type
```

- **stock** — GHC's built-in derivation. `Show` prints the constructor.
- **newtype** (GND) — coerces the underlying type's instance. Zero cost. This is
  why `deriving newtype Show` prints `3` and `deriving stock Show` prints
  `Age 3`, a difference that has embarrassed many a log file.
- **anyclass** — uses the class's _default_ method bodies (usually
  `Generic`-based via `DefaultSignatures`). Silently produces a bottoming
  instance if the class has no defaults.
- **via** — `deriving C via T` uses `T`'s instance, requiring `Coercible`. The
  most flexible: define a wrapper with the semantics you want once, then derive
  through it everywhere.

When a class is derivable both stock and newtype, GHC picks by a precedence rule
that has changed across versions. **Always write the strategy.**

## 6. Standalone deriving

```haskell
{-# LANGUAGE StandaloneDeriving #-}
deriving instance Show Shape
deriving instance (Show a) => Show (Tree a)      -- explicit context
deriving newtype instance Num Age
```

Needed when the type is defined elsewhere, when you want a non-obvious context,
or when deriving for a GADT.

## 7. Defaulting and ambiguity

`show (read "3")` is ambiguous — nothing determines the intermediate type.
Haskell's _defaulting rules_ rescue only the numeric case: when an ambiguous
variable's constraints are all from the standard numeric classes plus at least
one numeric class, GHC tries `Integer` then `Double`. That's why `show (2+2)`
works in a file but `show (read "3")` does not.

GHCi turns on `ExtendedDefaultRules`, which additionally defaults to `()` and
`[]` and considers more classes — which is why an expression works in GHCi and
fails when pasted into a module. Add a type annotation or `TypeApplications`
(`read @Int "3"`).

## 8. Class laws

Laws are not checked by the compiler and are not decoration. Code (including
library code you call) relies on them to be correct:

- `Eq`: reflexive, symmetric, transitive; `x == y` implies `x` and `y` are
  substitutable. A `Float`-based `Eq` with `NaN` already violates reflexivity.
- `Ord`: total order consistent with `Eq`. **`Data.Map` and `Data.Set` corrupt
  silently if `compare` is inconsistent** — a "compare only the id field" `Ord`
  with an `Eq` that compares everything is the classic way to lose elements.
- `Semigroup`/`Monoid`: associativity, identity. See
  `functor-applicative-monad.md`.
- `Hashable`: `a == b` must imply `hash a == hash b`.

Test laws with QuickCheck; `quickcheck-classes` packages the standard ones.

## Gotchas

- **`deriving newtype Show` prints the payload, not the wrapper.** Fine for
  `Text` wrappers, terrible for anything you'll grep in a log.
- **`deriving anyclass` on a class with no defaults compiles and then throws at
  runtime.** GHC warns only sometimes (`-Wmissing-methods` catches instances,
  not anyclass derivation, in older versions).
- **Orphans are silent.** No error, no link failure — just different behaviour
  depending on what's imported. `-Worphans` in every project.
- **An `Ord` instance inconsistent with `Eq` corrupts `Map`/`Set`.** No
  exception, no warning; lookups just miss.
- **Overlap resolution depends on what's in scope at the _use_ site**, so
  adding an import can change program behaviour.
- **Constraints on a class method are not the same as on the class.** A
  constraint in the class head is available to all methods and required by all
  instances; putting it on one method keeps instances free of it.
- **GHCi's defaulting is not the file's defaulting.** Anything that "works in
  GHCi" needs a type annotation before it goes in a module.
- **Instance methods can't be given type signatures** (without
  `InstanceSigs`, which is in GHC2021 — use it, it aids readability).
