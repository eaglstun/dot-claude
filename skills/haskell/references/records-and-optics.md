---
semantic_id: "KfsGhKYZ7-3585ySy4ELUe1urU9yAAAC"
related_ids:
  - "aX5GkKZR4zmy-4iW7pEJ3W9-rV72wAAK"
  - "LZ5GmZAZayGY-8yG6oEfVcp-7V6WwAAO"
---
# Records, field access, and optics

Source:

- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/records.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/field_selectors.html
- https://hackage.haskell.org/package/lens
- https://hackage.haskell.org/package/optics
- https://hackage.haskell.org/package/generic-lens

## 1. Plain records and their two historical problems

```haskell
data User = User { userId :: UserId, userName :: Text, userAge :: Int }

u2 = u { userAge = userAge u + 1 }        -- update syntax
```

Problem 1: **field selectors are top-level functions**, so two records in a
module can't share a field name. The traditional workaround was prefixing
(`userName`, `postName`), which is noisy and leaks the type name into every use.

Problem 2: **nested update is miserable**.

```haskell
c { cfgServer = (cfgServer c) { srvPort = 8080 } }
```

Modern GHC fixes both, mostly.

## 2. The modern extension set (GHC 9.2+)

```haskell
{-# LANGUAGE DuplicateRecordFields, OverloadedRecordDot, NoFieldSelectors #-}

data User = User { id :: UserId, name :: Text }
data Post = Post { id :: PostId, name :: Text }   -- same field names: fine

f :: User -> Text
f u = u.name                       -- OverloadedRecordDot
```

- **`DuplicateRecordFields`** (GHC 8.0) — allows the duplicate declarations.
  Selectors become ambiguous, so you can't call `name u` without disambiguation.
- **`OverloadedRecordDot`** (GHC 9.2) — `u.name` desugars via `HasField`, and
  resolves by the type of `u`. This is what makes duplicate fields usable.
  Note: `.` is now context-sensitive — `f . g` still composes (spaces matter),
  but `f.g` is now field access.
- **`NoFieldSelectors`** (GHC 9.2) — stops generating the top-level functions
  entirely, so the names stay free for your own use and dot-access is the only
  route.
- **`OverloadedRecordUpdate`** — the update half (`u{name = x}` polymorphically,
  `u.a.b = c`). Still experimental and tied to `RebindableSyntax`; not yet the
  thing to build on.

`GHC.Records.HasField` is the class underneath:

```haskell
class HasField (x :: Symbol) r a | x r -> a where getField :: r -> a
```

Instances are solved by the compiler for real record fields; you can write your
own for virtual fields.

## 3. Optics, in one screen

An optic is a first-class, composable accessor. The hierarchy (subtyping goes
_up_: every `Lens` is a `Getter` and a `Traversal`):

| Optic        | Focuses              | Read   | Write             |
| ------------ | -------------------- | ------ | ----------------- |
| `Lens'`      | exactly one          | always | yes               |
| `Prism'`     | zero or one (a case) | maybe  | yes (+ construct) |
| `Traversal'` | zero or more         | list   | yes               |
| `Iso'`       | isomorphic view      | always | yes (both ways)   |
| `Getter`     | one, read-only       | always | no                |
| `Fold`       | many, read-only      | list   | no                |
| `Setter'`    | many, write-only     | no     | yes               |

```haskell
import Control.Lens

view    lens s          -- s ^. lens
set     lens b s        -- s &  lens .~ b
over    lens f s        -- s &  lens %~ f
preview prism s         -- s ^? prism      (Maybe)
toListOf fold s         -- s ^.. fold
has     fold s
```

The operators, decoded: `^.` view, `^?` preview, `^..` toList, `.~` set,
`%~` modify, `?~` set to `Just`, `+~`/`-~`/`<>~` arithmetic/append modify,
`&` reverse application (so chains read left-to-right), `.=`/`%=` the `State`
versions.

```haskell
config & server . port .~ 8080
       & server . host %~ T.toLower
       & tags %~ ("prod":)
```

Composition is just `.` (in `lens`) and reads outside-in, like a path.

## 4. Generating lenses

```haskell
{-# LANGUAGE TemplateHaskell #-}
data Server = Server { _srvHost :: Text, _srvPort :: Int }
makeLenses ''Server            -- generates srvHost, srvPort (drops the underscore)

-- or, without the underscore convention:
makeFieldsNoPrefix ''Server    -- generates classy HasHost/HasPort classes
```

Or skip TH entirely with `generic-lens` / `optics`' generic support:

```haskell
{-# LANGUAGE DeriveGeneric, DataKinds, TypeApplications, OverloadedLabels #-}
data Server = Server { host :: Text, port :: Int } deriving (Generic)

view (field @"port") srv
srv ^. #port                  -- OverloadedLabels
```

No Template Haskell, no underscore convention, no generated names to export.
Costs a `Generic` instance and some compile time.

## 5. `lens` vs `optics` vs `microlens`

- **`lens`** — the original. Enormous (pulls in a big dependency tree),
  van Laarhoven encoding, optics compose with `.`, error messages are famously
  bad because everything is a rank-2 type synonym.
- **`optics`** — profunctor-ish encoding behind an _abstract_ `Optic` type.
  Composition is `%`, subtyping is explicit and checked, and error messages are
  dramatically better ("a Lens is required but you supplied a Traversal"). Newer,
  smaller ecosystem.
- **`microlens`** — a compatible subset with almost no dependencies. If you just
  want `^.`, `.~`, `%~` in a library, this is the polite choice.
- **`lens-family`** — another minimal option.

For a _library_, prefer `microlens` or no optics at all — don't force a
dependency tree on your users. For an _application_, pick one and standardize.

## 6. Prisms and sum types

```haskell
data Shape = Circle Double | Rect Double Double
makePrisms ''Shape            -- _Circle, _Rect

s ^? _Circle                  -- Maybe Double
review _Circle 3.0            -- Circle 3.0   (prisms construct too)
over (_Rect . _1) (*2) s
```

Prisms are the sum-type counterpart to lenses, and they're what makes
`aeson-lens`-style JSON traversal (`json . key "a" . _Integer`) work.

## 7. When _not_ to use optics

- A single flat record with `OverloadedRecordDot` needs no optic at all.
- One-level updates: `u { field = x }` is clearer than `u & field .~ x`.
- A library API: exposing `Lens'` in a signature commits your users to the
  encoding.
- Deeply lens-ified code becomes unreadable to anyone who hasn't memorized the
  operator table. Two levels of composition is fine; six is a code smell.

The genuine wins: deep nested updates, traversing every element matching a
pattern (`traverse . filtered p . field`), `zoom`/`use` in `State`-based code,
and JSON/XML poking without defining types.

## Gotchas

- **`OverloadedRecordDot` changes what `.` means.** `f.g` is field access;
  function composition needs spaces (`f . g`). Formatters will bite you here.
- **`DuplicateRecordFields` without `OverloadedRecordDot` is painful** —
  selectors become ambiguous and need type annotations at every use.
- **Record update syntax is partial on sum types**, and `-Wall` alone doesn't
  warn (`-Wincomplete-record-updates` does).
- **Record selectors on sum types are partial too** — `-Wpartial-fields` and,
  in GHC 9.10+, `-Wincomplete-record-selectors`.
- **`makeLenses` requires the underscore prefix** and silently generates nothing
  for fields without it.
- **TH lens generation forces a module split** for anything used in the same
  module before it's defined (stage restriction).
- **`lens` composes with `.`, `optics` with `%`.** Mixing the two in one file is
  a rite of passage nobody enjoys.
- **A `Traversal` used where you assumed a `Lens` silently does nothing** when
  it targets zero elements — `^?` returns `Nothing`, `.~` is a no-op.
- **`lens` is a heavy dependency.** For a library, `microlens` or plain
  functions.
