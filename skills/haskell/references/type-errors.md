---
semantic_id: "LXdSEJLN7yAQywS36oGuUe7qxf4XUAAK"
related_ids:
  - "bV5SmLLN_aEwy-2QaoGOUO_77O0_8AAK"
  - "bW5GcJLN76ZQ20SHI9ECwE_L5X6XQAAH"
---
# Reading GHC type errors

Source:

- https://downloads.haskell.org/ghc/latest/docs/users_guide/using-warnings.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/typed_holes.html
- https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/defer_type_errors.html
- https://www.haskell.org/onlinereport/haskell2010/haskellch4.html#x10-880004.5.5 (monomorphism restriction)

## 1. Read the error bottom-up, and only the first one

GHC reports errors in source order, and later errors are usually _consequences_
of the first. Fix error #1, recompile, ignore the rest. In a long message the
useful parts are:

```
    • Couldn't match expected type ‘Int’ with actual type ‘Text’
      ^ the actual mismatch
    • In the first argument of ‘f’, ...
      ^ where; read this to locate it
      Relevant bindings include
        x :: Text  (bound at Foo.hs:12:5)
      ^ often the smoking gun
```

"Expected" is what the _context_ demands; "actual" is what the _expression_
supplies.

## 2. Rigid type variables

```
Couldn't match expected type ‘a’ with actual type ‘Int’
  ‘a’ is a rigid type variable bound by
      the type signature for: f :: forall a. a -> a
```

**"Rigid" means the caller chose it, not you.** The signature promises to work
for _every_ `a`, and the body is trying to use one specific type. Either the
signature is too general (add a constraint: `Num a => a -> a`), or the body is
wrong.

The other common source: a `where` helper whose signature reuses a type
variable name without the parent having an explicit `forall`. See
`advanced-types.md` §1.

## 3. Ambiguity

```
Ambiguous type variable ‘a0’ arising from a use of ‘read’
  prevents the constraint ‘(Read a0)’ from being solved.
```

Nothing in the expression determines the type. Fixes, best first:

```haskell
read @Int s              -- TypeApplications
(read s :: Int)          -- annotation
let n :: Int; n = read s
```

If the variable appears only in constraints (never in the argument or result
types), you need `AllowAmbiguousTypes` on the definition plus
`TypeApplications` at every call site — a deliberate API decision, not an
accident to paper over.

`Ambiguous occurrence` is a different error entirely: two imports export the
same name. Qualify the import.

## 4. The monomorphism restriction

```haskell
-- module scope, no signature, no arguments on the left
n = 5                    -- MR forces a single monomorphic type
f = (+)                  -- ditto
```

A binding with **no arguments to the left of `=`** and **no type signature**
gets a single monomorphic type rather than being generalized. Symptoms: "No
instance for (Num a) arising from...", or a value that works at `Int` in one
use and then fails at `Double` in another, or the dreaded
`Defaulting the following constraint(s)` warning with `-Wtype-defaults`.

Fixes: write the type signature (right answer), add an argument (eta-expand),
or `{-# LANGUAGE NoMonomorphismRestriction #-}` (module-wide sledgehammer; GHCi
already has it off). **Top-level signatures fix this and a dozen other
problems** — `-Wmissing-signatures` is worth enabling.

## 5. `No instance for`

```
No instance for (Show (Int -> Int)) arising from a use of ‘print’
```

Three flavours, distinguishable by what's inside the parens:

- **A function type** — you forgot an argument, or applied one too few. This is
  the single most common Haskell beginner error and it stays common.
- **A concrete type you own** — write or derive the instance.
- **A type variable** (`No instance for (Show a)`) — add the constraint to the
  enclosing signature.

```
No instance for (MonadIO m) arising from a use of 'liftIO'
```

in transformer code usually means a missing `lift` or a stack that doesn't
include `IO` at the bottom.

## 6. Kind errors

```
Expected a type, but ‘Maybe’ has kind ‘Type -> Type’
```

You applied a type constructor to the wrong number of arguments —
`Show Maybe` instead of `Show (Maybe a)`, or a class expecting `Type -> Type`
(like `Functor`) given a saturated type. `:kind` in GHCi is the fastest check.

## 7. Overlap and coherence errors

```
Overlapping instances for Show [Char]
  Matching instances: instance Show a => Show [a]
                      instance Show MyType  -- via FlexibleInstances
```

Either mark one instance `{-# OVERLAPPING #-}` / the other `{-# OVERLAPPABLE #-}`,
or (better) `newtype` your way out. See `typeclasses.md` §4.

```
Could not deduce (Eq b) from the context (Eq a)
```

The instance head needs a constraint. `instance Eq a => Eq (Tree a)`.

## 8. Type-family walls

```
Could not deduce: Elem c ~ Int from the context ...
```

Type families are not injective — GHC can't work backwards from a result. See
`advanced-types.md` §4. Practical escapes: add the equality as a constraint
(`(Elem c ~ Int) =>`), use an injectivity annotation, or switch to a **data**
family, which is injective by construction.

## 9. Typed holes — the debugging superpower

Leave a `_` where you don't know what goes:

```haskell
f :: [Int] -> Int
f xs = _ (map (*2) xs)
```

```
Found hole: _ :: [Int] -> Int
  Valid hole fits include
    sum :: forall (t :: * -> *) a. (Foldable t, Num a) => t a -> a
    product, maximum, minimum, head, last, length ...
```

Named holes (`_acc`) let you have several. Flags worth knowing:
`-fdefer-typed-holes` (compile and fail at runtime instead),
`-frefinement-level-hole-fits=2` (suggest fits that themselves take arguments),
`-fno-show-valid-hole-fits` (when the suggestion list is enormous and slow).

This is the intended workflow: write the type, punch a hole, let GHC enumerate
what fits.

## 10. Deferred errors and iterative development

```
{-# OPTIONS_GHC -fdefer-type-errors #-}
```

Turns type errors into _warnings_ plus a runtime exception at the offending
expression. Useful when refactoring a large module and you want to run the
tests for the parts that already type-check. Never commit it.

Related: `-fdefer-typed-holes`, `-fdefer-out-of-scope-variables`.

## 11. Warnings that prevent errors

```
-Wall                          -- the baseline
-Wcompat                       -- warns about upcoming breaking changes
-Wincomplete-uni-patterns      -- `let Just x = ...` and lambda patterns
-Wincomplete-record-updates
-Wpartial-fields               -- record selectors that are partial
-Wredundant-constraints
-Wmissing-export-lists
-Wmissing-signatures / -Wmissing-local-signatures
-Wunused-packages              -- build-depends you don't use
-Widentities                   -- fromIntegral :: Int -> Int and friends
-Werror=incomplete-patterns    -- promote the one that actually crashes
```

`-Wall` does **not** include `-Wincomplete-uni-patterns` or `-Wcompat`. Add
them.

## 12. Making the messages readable

- `-fprint-explicit-foralls`, `-fprint-explicit-kinds` when a kind error is
  opaque.
- `-fmax-relevant-binds=N`, `-fmax-valid-hole-fits=N` to control message size.
- `-freverse-errors` prints errors bottom-up so the first one stays on screen.
- `-fdiagnostics-color=always` when piping through `less -R`.
- For a monstrous transformer error, add explicit signatures to intermediate
  bindings; GHC then blames the actual line instead of the whole `do` block.

## Gotchas

- **Fix only the first error.** Cascades are noise.
- **"Rigid type variable" means your signature is more general than your
  implementation** — the fix is usually in the signature.
- **A missing argument shows up as `No instance for (Show (a -> b))`,** not as
  an arity error.
- **The monomorphism restriction only affects bindings with no arguments and no
  signature** — which is exactly the shape of most top-level constants.
- **GHCi has `ExtendedDefaultRules` and no monomorphism restriction**, so code
  that works there can fail in a module.
- **`Couldn't match type ‘Text’ with ‘[Char]’`** with `OverloadedStrings` on
  usually means a literal was pinned by an annotation somewhere upstream.
- **Type-family errors that say "could not deduce" are usually injectivity**,
  not a missing instance.
- **`-Wall` isn't all.** `-Wcompat -Wincomplete-uni-patterns` are the two most
  valuable omissions.
