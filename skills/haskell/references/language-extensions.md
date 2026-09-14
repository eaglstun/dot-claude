---
semantic_id: "4Z5uMOBZxySy24SA5qEH0W9v9dx1UAAF"
related_ids:
  - "YZjGBCDZwwy4_Yiw5KGLU09_4l43UAAO"
  - "4ZjGjKBZy7Saw4iSq4EVQWtrFVwzwAAB"
---
# Language extensions

Source:

- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/control.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/control.html#extension-GHC2021
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/table.html
- https://github.com/ghc-proposals/ghc-proposals/blob/master/proposals/0380-ghc2021.rst

## 1. Where extensions come from

Three places, in increasing scope:

```haskell
{-# LANGUAGE LambdaCase, OverloadedStrings #-}     -- per module, at the very top
```

```cabal
library
  default-language:   GHC2021          -- or Haskell2010
  default-extensions: OverloadedStrings
                    , LambdaCase
                    , DerivingStrategies
  other-extensions:   TemplateHaskell  -- documentation only; used in some modules
```

Per-module pragmas are the norm for anything with semantic weight;
`default-extensions` for the handful you want everywhere and would otherwise
copy into every file. A reader opening one module can't see
`default-extensions`, so keep that list short and boring —
`OverloadedStrings` and `Strict` are the two that most often surprise people
when they're set project-wide.

GHCi: `:set -XOverloadedStrings`. Scripts: `{-# LANGUAGE #-}` at the top works
in `runghc`/`cabal script` files too.

## 2. GHC2021 — the modern default

`default-language: GHC2021` (GHC 9.2+) turns on the extensions that had become
de-facto standard. The ones you no longer need to write:

```
BangPatterns              ConstrainedClassMethods    ConstraintKinds
DeriveDataTypeable        DeriveFoldable             DeriveFunctor
DeriveGeneric             DeriveLift                 DeriveTraversable
DoAndIfThenElse           EmptyCase                  EmptyDataDecls
EmptyDataDeriving         ExistentialQuantification  ExplicitForAll
FieldSelectors            FlexibleContexts           FlexibleInstances
ForeignFunctionInterface  GADTSyntax                 GeneralisedNewtypeDeriving
HexFloatLiterals          ImplicitPrelude            ImportQualifiedPost
InstanceSigs              KindSignatures             MultiParamTypeClasses
NamedFieldPuns            NamedWildCards             NumericUnderscores
PolyKinds                 PostfixOperators           RankNTypes
RelaxedPolyRec            ScopedTypeVariables        StandaloneDeriving
StandaloneKindSignatures  StarIsType                 TupleSections
TypeApplications          TypeOperators              TypeSynonymInstances
```

Notably **absent** from GHC2021 (still opt-in): `LambdaCase`,
`OverloadedStrings`, `DerivingStrategies`, `DerivingVia`, `DeriveAnyClass`,
`RecordWildCards`, `TypeFamilies`, `DataKinds`, `GADTs`, `MultiWayIf`,
`BlockArguments`, `ViewPatterns`, `StrictData`, `TemplateHaskell`,
`UndecidableInstances`, `FunctionalDependencies`, `OverloadedRecordDot`,
`NoFieldSelectors`, `DuplicateRecordFields`.

**GHC2024** (available from GHC 9.10, not the default) adds — among others —
`LambdaCase`, `DerivingStrategies`, `DataKinds`, `GADTs`, `MonoLocalBinds`,
`RoleAnnotations`, `ExplicitNamespaces`, `TypeFamilies` (via `ExplicitNamespaces`
and friends). The one to know about is **`MonoLocalBinds`**, which changes
inference for local bindings and can break code that compiled under GHC2021.
Opting into GHC2024 is a real migration, not a flag flip.

## 3. The everyday set

Enable without much thought in application code:

| Extension             | Why                                                     |
| --------------------- | ------------------------------------------------------- |
| `OverloadedStrings`   | string literals as `Text`/`ByteString`                  |
| `LambdaCase`          | `\case` — removes throwaway binders                     |
| `DerivingStrategies`  | forces you to say _how_ something derives               |
| `DerivingVia`         | reuse semantics through a wrapper                       |
| `DeriveAnyClass`      | only alongside strategies, never alone                  |
| `StrictData`          | strict record fields by default; kills a class of leaks |
| `NamedFieldPuns`      | `Point{x, y}` — clearer than `RecordWildCards`          |
| `MultiWayIf`          | guards in expression position                           |
| `BlockArguments`      | drops noise `$` before `do`/`\`                         |
| `ImportQualifiedPost` | `import Data.Map qualified as M` (already in GHC2021)   |
| `NumericUnderscores`  | `1_000_000` (already in GHC2021)                        |
| `OverloadedRecordDot` | `user.name` (GHC 9.2+)                                  |

## 4. Extensions that change semantics — enable deliberately

- **`OverloadedStrings`** — literals become `IsString a => a`. Ambiguity errors
  appear where none existed, `show` of a literal may need an annotation, and
  `ByteString`'s `IsString` instance **truncates to 8 bits**, silently mangling
  non-ASCII. Still worth it in `Text`-heavy code.
- **`Strict` / `StrictData`** — `StrictData` is safe and local; `Strict` changes
  the evaluation of every binding in the module and can turn a terminating
  program into a hanging one.
- **`OverloadedLists`** — makes `[1,2,3]` polymorphic. Ambiguity everywhere;
  rarely worth it.
- **`RebindableSyntax`** — `do`, `if`, literals resolve to whatever is in
  scope. Powerful for EDSLs, hostile to every reader. Also implies
  `NoImplicitPrelude`.
- **`NoImplicitPrelude`** — required by alternative preludes (`relude`, `rio`).
  Fine as a project-wide decision, confusing as a per-module one.
- **`MonoLocalBinds`** — restricts generalization of local bindings. Implied by
  `GADTs` and `TypeFamilies`, which is why turning those on can break unrelated
  `where` clauses.
- **`DuplicateRecordFields`** — lets two records share a field name, at the cost
  of ambiguous selectors that need annotations or `OverloadedRecordDot`.
- **`TemplateHaskell`** — real cost: stage restrictions, cross-compilation pain,
  slower builds, and a recompile avalanche. Pays for itself in `persistent`,
  `aeson`'s TH deriving, and `lens`'s `makeLenses`.

## 5. Type-level extensions (see `advanced-types.md`)

`TypeFamilies`, `DataKinds`, `GADTs`, `PolyKinds`, `FunctionalDependencies`,
`QuantifiedConstraints`, `UndecidableInstances`, `AllowAmbiguousTypes`,
`ImpredicativeTypes`, `LinearTypes` (GHC 9.0+, still niche),
`DependentHaskell`-adjacent bits (`RequiredTypeArguments`, GHC 9.10+).

`UndecidableInstances` is fine; `AllowAmbiguousTypes` is fine _with_
`TypeApplications`; `IncoherentInstances` is not fine.

## 6. Deprecated / avoid

- `IncoherentInstances` — nondeterministic instance choice.
- `OverlappingInstances` / `NoMonomorphismRestriction` as _module-wide_ flags —
  use per-instance pragmas and per-binding signatures instead.
- `DatatypeContexts` — removed from the language; it never did what people
  expected.
- `NPlusKPatterns` — gone.
- `TypeInType` — subsumed by `PolyKinds` + `StandaloneKindSignatures`;
  deprecated.
- `CPP` — not deprecated, but every `#if` is a configuration you aren't testing.
  Keep it to version guards (see `ghc-versions.md`).

## 7. A reasonable project default

```cabal
common warnings-and-extensions
  default-language: GHC2021
  default-extensions:
      DerivingStrategies
    , DerivingVia
    , LambdaCase
    , OverloadedStrings
    , StrictData
  ghc-options:
      -Wall -Wcompat -Widentities
      -Wincomplete-record-updates -Wincomplete-uni-patterns
      -Wmissing-export-lists -Wpartial-fields -Wredundant-constraints
      -Wunused-packages
```

`common` stanzas (cabal 2.2+) with `import: warnings-and-extensions` in each
component keep this in one place. See `build-and-tooling.md`.

## Gotchas

- **`default-extensions` is invisible to a reader of the module.** Anything
  semantically surprising belongs in a per-module pragma.
- **`OverloadedStrings` + `ByteString` silently truncates non-ASCII literals**
  to their low 8 bits. Use `Data.Text.Encoding.encodeUtf8` instead.
- **Turning on `TypeFamilies` or `GADTs` implies `MonoLocalBinds`**, which can
  break `where`-bound helpers elsewhere in the module with a confusing error.
- **GHC2024 is not a free upgrade** — `MonoLocalBinds` and the extra
  `DataKinds`/`GADTs` inference changes are real breakage risk.
- **`DeriveAnyClass` without `DerivingStrategies`** changes which derivation
  GHC picks for classes that could be derived two ways, silently.
- **Extensions apply to the module, not the package.** A pragma in `Main.hs`
  does nothing for `Lib.hs`.
- **`{-# LANGUAGE #-}` must precede `module`** — and after a `{-# OPTIONS_GHC #-}`
  block is fine, but after the module header is a parse error.
