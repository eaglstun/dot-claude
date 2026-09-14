---
semantic_id: "bR5WEaJd7wST-8SCa5NC0W9-vhxP8AAM"
related_ids:
  - "bUx2tPbx6ySS-gCm6wED1S_69lxH0AAK"
  - "4Z5uMOBZxySy24SA5qEH0W9v9dx1UAAF"
---
# Types and data declarations

Source:

- https://www.haskell.org/onlinereport/haskell2010/haskellch4.html (declarations and bindings)
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/newtypes.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/gadt_syntax.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/strict.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/pragmas.html#unpack-pragma

## 1. The three declaration forms

| Form      | Runtime cost       | Pattern match forces? | Can be recursive | Use for                         |
| --------- | ------------------ | --------------------- | ---------------- | ------------------------------- |
| `data`    | heap-allocated box | yes                   | yes              | real sum/product types          |
| `newtype` | **zero** (erased)  | **no**                | yes (rarely)     | wrapping one field to add types |
| `type`    | none (alias only)  | n/a                   | no               | shortening a long type          |

```haskell
data    Meters = Meters Double   -- boxed; Meters undefined /= undefined
newtype Feet   = Feet   Double   -- erased; Feet undefined == undefined at runtime
type    Name   = Text            -- no new type; Name and Text are interchangeable
```

`type` gives you **no** type safety — a `Name` is a `Text` and any function
taking `Text` accepts it. If you want the compiler to catch a swapped argument,
you want `newtype`.

The `newtype`/`data` semantic difference is real and occasionally bites:

```haskell
newtype N = N Int; data D = D Int
f (N _) = "ok"   -- f undefined      == "ok"   (the pattern is irrefutable)
g (D _) = "ok"   -- g undefined      == ⊥      (matching forces the constructor)
```

## 2. Algebraic data types

A `data` declaration is a **sum of products**:

```haskell
data Shape
  = Circle Double            -- product of 1
  | Rect   Double Double     -- product of 2
  | Empty                    -- product of 0
  deriving (Show, Eq)
```

Cardinality is literal arithmetic: `|Either a b| = |a| + |b|`, `|(a,b)| = |a| * |b|`,
`|a -> b| = |b| ^ |a|`. `Void` has 0 inhabitants, `()` has 1. This is worth
knowing because it tells you when a type admits states you don't want — the
classic being `(Bool, Maybe User)` (6 states) where `data Session = Anon | LoggedIn User`
(1 + n) is what you meant. **Make illegal states unrepresentable** is the whole
game.

Records add field selectors:

```haskell
data User = User
  { userId    :: !UserId
  , userName  :: !Text
  , userEmail :: Maybe Text
  } deriving (Show, Eq)
```

Field selectors are just functions (`userId :: User -> UserId`), which is why
two records in the same module can't share a field name without
`DuplicateRecordFields`. See `records-and-optics.md` for the modern extension
set.

## 3. GADT syntax (without the GADT power)

`GADTSyntax` (on in GHC2021) lets you write constructors with type signatures.
Even for ordinary types it reads better once there are many fields:

```haskell
data Shape where
  Circle :: Double -> Shape
  Rect   :: Double -> Double -> Shape
```

This is _syntax only_ until a constructor's return type is refined
(`Expr Int` rather than `Expr a`) — that's a real GADT, covered in
`advanced-types.md`.

## 4. Strictness annotations and UNPACK

A `!` on a constructor field means the field is forced to WHNF when the
constructor is built:

```haskell
data P = P !Int !Int          -- both fields are evaluated on construction
```

`{-# UNPACK #-}` goes further and stores the contents inline, removing the
pointer and the box:

```haskell
data P = P {-# UNPACK #-} !Int {-# UNPACK #-} !Int   -- two raw Int#s in the P closure
```

Rules of thumb:

- Unpacking works for single-constructor, single-field types with a strict
  field: `Int`, `Double`, `Word`, a `newtype` over those. It does **not** work
  for sum types (GHC 9.x can unpack sums in some cases, but don't rely on it).
- `-funbox-small-strict-fields` is **on by default**, so small strict fields are
  already unpacked; the pragma matters mostly for larger ones.
- An `UNPACK`ed field must be strict — `{-# UNPACK #-}` without `!` is silently
  ignored (with `-Wall`, warned about).
- Unpacking a field you frequently pass _whole_ to something expecting the boxed
  type causes re-boxing. Measure.

`StrictData` makes every field in the module strict by default, with `~` to opt
out. It is the single highest-value extension for numeric/record-heavy code.
See `laziness-and-strictness.md`.

## 5. Deriving

```haskell
data Color = Red | Green | Blue
  deriving stock (Show, Read, Eq, Ord, Enum, Bounded, Ix)
```

Stock-derivable classes: `Eq`, `Ord`, `Enum` (nullary constructors only),
`Bounded`, `Show`, `Read`, `Ix`, `Functor`/`Foldable`/`Traversable` (with
`DeriveFunctor` etc., all in GHC2021), `Generic` (`DeriveGeneric`),
`Data`/`Typeable`, `Lift` (Template Haskell).

`deriving` strategies (`stock` / `newtype` / `anyclass` / `via`) matter as soon
as a class is derivable more than one way — see `typeclasses.md` §5. Write the
strategy explicitly; `-Wmissing-deriving-strategies` will nag you into it.

`Enum` deriving only works when every constructor is nullary. `Ord` derives
lexicographically **in constructor declaration order**, so reordering
constructors silently changes comparison and any `Map` built on it.

## 6. Parameters, phantoms, and roles

```haskell
newtype Tagged tag a = Tagged a          -- tag is a phantom: appears in no field
data Proxy a = Proxy                     -- from Data.Proxy
```

Phantom parameters let you tag values without runtime cost: `Tagged "utc" Int`
vs `Tagged "local" Int` are different types with identical representations.

**Roles** control whether `coerce` may change a parameter. A phantom parameter
gets role `phantom`, most parameters get `representational`, and anything used
at the type level or under a type family gets `nominal`. The practical effect:

```haskell
import Data.Coerce (coerce)
newtype Age = Age Int
coerce (xs :: [Int]) :: [Age]      -- free, no traversal, no allocation
coerce (m :: Map Int v) :: Map Age v  -- REJECTED if Age's Ord differs in meaning
```

`Data.Map`'s key parameter is nominal precisely because coercing the key type
could change the `Ord` instance and break the invariant. If you need a
role-restricted API, `type role T nominal` (with `RoleAnnotations`) is how.

## 7. Existentials and GADT-lite packing

```haskell
{-# LANGUAGE ExistentialQuantification #-}
data Showable = forall a. Show a => MkShowable a

render :: [Showable] -> [String]
render = map (\(MkShowable a) -> show a)
```

The type variable is bound by the constructor, not the type, so `Showable`
holds "some `a` I can `show`" — a dictionary plus a value. This is
object-orientation in Haskell, and it is usually the wrong reach: the caller
loses all information except what the constraint gives back. Prefer a record of
functions or a plain sum type unless the set of cases is genuinely open.

## 8. Kinds, briefly

`Type` (formerly `*`) is the kind of types that have values. A type
constructor's kind shows its arity:

```
Int            :: Type
Maybe          :: Type -> Type
Either         :: Type -> Type -> Type
StateT         :: Type -> (Type -> Type) -> Type -> Type
```

`ghci> :kind Either Int` → `Type -> Type`. Partial application at the type level
is how `Functor (Either e)` works, and why you can't write `Functor (Either _ b)` —
type constructors are curried and only the _last_ parameter can be abstracted
over. When that's the parameter you don't want, you need a `newtype` flip
(`Data.Bifunctor`, or `Flip`).

## Gotchas

- **`type` is not a new type.** It catches nothing. If a bug would come from
  passing the wrong `Text`, you need `newtype`.
- **Deriving `Ord` locks your constructor order into your data.** Reordering
  constructors changes `Map` layout, `sort` results, and serialized output.
- **`{-# UNPACK #-}` without `!` does nothing.** And unpacking a sum type
  usually does nothing.
- **Record field selectors are partial on sum types.** `data T = A {x :: Int} | B`
  gives you `x :: T -> Int` that throws at runtime on `B`. GHC warns only with
  `-Wincomplete-record-selectors` (GHC 9.10+); before that it's silent.
- **Record update syntax is partial too**, for the same reason, and
  `-Wall` says nothing about it in older GHCs.
- **A lazy field in a long-lived record is a leak waiting to happen.** Default
  to `!` on fields, or turn on `StrictData` module-wide.
- **`newtype` pattern matches don't force.** If you rely on a match to trigger
  evaluation (e.g. to catch an error early), a `newtype` won't do it.
- **Phantom parameters are erased, so `Coercible` can convert between tags.**
  If the tag is a security boundary, give the type a nominal role annotation.
