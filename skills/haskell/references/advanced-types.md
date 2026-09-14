---
semantic_id: "bUx2tPbx6ySS-gCm6wED1S_69lxH0AAK"
related_ids:
  - "bR5WEaJd7wST-8SCa5NC0W9-vhxP8AAM"
  - "aX5GkKZR4zmy-4iW7pEJ3W9-rV72wAAK"
---
# Advanced types: GADTs, families, kinds, and quantifiers

Source:

- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/gadt.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/type_families.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/data_kinds.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/rank_polymorphism.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/type_applications.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/scoped_type_variables.html

## 1. ScopedTypeVariables and explicit forall

In GHC2021 `ScopedTypeVariables` is on. An explicit `forall` brings the variable
into scope in the body, which is what lets you annotate local bindings:

```haskell
f :: forall a. Num a => [a] -> a
f xs = go 0 xs
  where
    go :: a -> [a] -> a     -- 'a' here is the SAME a, only because of the forall
    go acc []     = acc
    go acc (y:ys) = go (acc + y) ys
```

Without the `forall`, the `where` signature's `a` is a _fresh_ variable and you
get a rigid-type-variable error. When a local helper's signature fights you,
this is almost always the cause.

## 2. TypeApplications

`@` supplies a type argument in the order the `forall` binds them (and for
inferred/unannotated functions, in a compiler-determined order — so annotate
anything whose `@` order is part of its API):

```haskell
read @Int "42"
show @Double 1.0
fromIntegral @Int @Double n
maxBound @Word8
```

This is the modern replacement for `(undefined :: Proxy a)` tricks and for
annotation gymnastics. `AllowAmbiguousTypes` + `TypeApplications` is a common
pair for functions whose type variable appears only in a constraint:

```haskell
{-# LANGUAGE AllowAmbiguousTypes, TypeApplications, ScopedTypeVariables #-}
typeName :: forall a. Typeable a => String
typeName = show (typeRep @a)
```

## 3. GADTs

A GADT constructor may _refine_ the result type, which means matching on it
brings a type equality into scope:

```haskell
{-# LANGUAGE GADTs #-}
data Expr a where
  IntE  :: Int  -> Expr Int
  BoolE :: Bool -> Expr Bool
  Add   :: Expr Int -> Expr Int -> Expr Int
  If    :: Expr Bool -> Expr a -> Expr a -> Expr a

eval :: Expr a -> a
eval (IntE n)   = n            -- here, GHC knows a ~ Int
eval (BoolE b)  = b            -- here, a ~ Bool
eval (Add x y)  = eval x + eval y
eval (If c t e) = if eval c then eval t else eval e
```

That's the payoff: a well-typed interpreter with no `Maybe`, no partiality.

Costs to weigh before reaching for GADTs:

- **Type inference stops.** Functions consuming a GADT nearly always need an
  explicit signature; GHC will tell you so in a long message.
- Constraints captured in a constructor (`Show a => MkT :: a -> T`) make the
  constructor an existential package — see `types-and-data.md` §7.
- `deriving` gets restricted (use `StandaloneDeriving`).

## 4. Type families

**Closed type family** — a function on types, defined once, matched in order:

```haskell
{-# LANGUAGE TypeFamilies, DataKinds #-}
type family Elem c where
  Elem [a]      = a
  Elem Text     = Char
  Elem (Set a)  = a
```

**Open type family** — extensible, instances anywhere (with the same orphan
hazards as classes):

```haskell
type family Key m
type instance Key (Map k v) = k
```

**Associated type family** — an open family scoped to a class. This is the
modern alternative to functional dependencies:

```haskell
class Collection c where
  type Item c
  cinsert :: Item c -> c -> c
  ctoList :: c -> [Item c]

instance Collection [a] where
  type Item [a] = a
  cinsert = (:)
  ctoList = id
```

**Data families** produce a fresh, injective data type per instance, which
sidesteps the biggest problem with type families:

```haskell
data family Vec a
data instance Vec Int    = VecInt    (UV.Vector Int)
data instance Vec Double = VecDouble (UV.Vector Double)
```

**Type families are not injective.** From `Elem c ~ Int` GHC cannot deduce `c`.
This is the source of most "could not deduce" walls in type-family code. If
your family really is injective, say so:

```haskell
type family F a = r | r -> a       -- injective type family (GHC 8.0+)
```

## 5. DataKinds and type-level literals

`DataKinds` promotes data constructors to types and types to kinds:

```haskell
{-# LANGUAGE DataKinds, KindSignatures #-}
data Access = Public | Private          -- also gives kinds 'Public, 'Private :: Access

newtype Doc (a :: Access) = Doc Text

publish :: Doc 'Private -> Doc 'Public
```

`GHC.TypeLits` gives type-level `Nat` and `Symbol` with `KnownNat`/`KnownSymbol`
to reflect them back to values:

```haskell
import GHC.TypeLits
newtype Tagged (name :: Symbol) a = Tagged a
label :: forall n a. KnownSymbol n => Tagged n a -> String
label _ = symbolVal (Proxy @n)
```

`TypeError` (from `GHC.TypeLits`) lets you produce a _custom_ compile error from
a type family or an instance — the polite way to say "this combination is
unsupported" instead of leaking internals:

```haskell
instance TypeError ('Text "Cannot JSON-encode a function") => ToJSON (a -> b)
```

## 6. Higher-rank types

```haskell
{-# LANGUAGE RankNTypes #-}
applyToBoth :: (forall a. a -> a) -> (Int, String) -> (Int, String)
applyToBoth f (n, s) = (f n, f s)
```

Rank-1 (ordinary) polymorphism means _the caller_ picks the type. Rank-2 means
the _function_ gets a polymorphic argument it may use at several types. The
canonical uses: `runST`'s `forall s.` trick that prevents an `STRef` escaping,
lens/optics types, and "run this callback with a resource you can't keep"
patterns (`withFile`-style, `MonadUnliftIO`).

Higher-rank types kill inference: an argument of rank ≥ 2 must be annotated.
Impredicativity (putting a `forall` inside a type constructor, e.g.
`Maybe (forall a. a -> a)`) needs `ImpredicativeTypes` and is still an area with
sharp edges — avoid unless you know why you're there.

`QuantifiedConstraints` allows a `forall` in a constraint, mostly for
transformer stacks:

```haskell
{-# LANGUAGE QuantifiedConstraints #-}
f :: (forall x. Show x => Show (t x)) => t Int -> String
```

## 7. Standalone kind signatures and `Type`

```haskell
{-# LANGUAGE StandaloneKindSignatures, DataKinds #-}
import Data.Kind (Type, Constraint)

type Vec :: Nat -> Type -> Type
data Vec n a where
  VNil  :: Vec 0 a
  VCons :: a -> Vec n a -> Vec (n + 1) a
```

Since GHC 8.10, a standalone kind signature is the clearest way to state a
type's kind, and it makes the type's arity and dependency explicit. `Type` is
the modern spelling of `*` (`StarIsType` is still on by default but `*` conflicts
with type-level multiplication).

`Constraint` is the kind of constraints; `type C = (Show a, Eq a) :: Constraint`
requires `ConstraintKinds` and lets you alias constraint bundles.

## 8. When _not_ to do this

Type-level programming is real engineering leverage in a library and real
liability in an application. Before reaching for it, check whether the problem
is solved by:

- a `newtype` and a smart constructor (unrepresentable illegal states),
- a plain sum type (a closed set of cases),
- a runtime check at the boundary with a parsed, trusted type inside
  ("parse, don't validate"),
- a record of functions instead of a class.

The tells that you've gone too far: error messages nobody on the team can read,
`UndecidableInstances` plus `AllowAmbiguousTypes` plus a wall of `Proxy`,
inference gone entirely so every call site needs annotations, and compile times
measured in minutes.

## Gotchas

- **A `where` helper's type variables are fresh unless the parent signature has
  an explicit `forall`.** This causes most "rigid type variable" errors.
- **Type families aren't injective.** `F a ~ F b` does not give `a ~ b`, and
  GHC cannot solve backwards from a family's result.
- **GADT matches need signatures.** Inference for a function that scrutinizes a
  GADT is effectively off; write the type.
- **`TypeApplications` order depends on the `forall` order** — and for
  signatureless bindings, on GHC's inference order, which can change between
  versions. Annotate anything whose `@` arguments are public API.
- **`DataKinds` promoted constructors need a tick** when ambiguous with a type
  of the same name (`'True` vs `True`), and GHC 9.x warns about missing ticks
  in some positions.
- **Custom `TypeError`s fire when the constraint is _solved_, not when it's
  written** — an unused instance won't complain.
- **`ImpredicativeTypes` is still a rough edge.** If a `forall` needs to live
  inside `Maybe`/`[]`, wrap it in a `newtype` instead.
- **Existential + GADT means you can't get the type back out.** If you need a
  runtime type test, you need `Typeable` and `eqT`, not a clever GADT.
