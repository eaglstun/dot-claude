---
name: haskell
description: Haskell language and tooling reference. Use when writing, reviewing, debugging, testing, or profiling Haskell; resolving type errors, laziness or space leaks, concurrency, effects, build failures, and FFI issues; or choosing language extensions and libraries.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: bW5GcJLN76ZQ20SHI9ECwE_L5X6XQAAH
  related_ids: '["LXdSEJLN7yAQywS36oGuUe7qxf4XUAAK","bR5WEaJd7wST-8SCa5NC0W9-vhxP8AAM"]'
---

# Haskell reference

Condensed, source-cited notes grounded in the primary sources (the GHC User's
Guide, the Haskell 2010 Report, Hackage haddocks, the Cabal and Stack docs, and
the libraries' own documentation). Each page cites its source URLs at the top
and ends with a Gotchas section of the sharp edges that memory gets wrong.

This is a standalone language shelf, not tied to one repo. Repo conventions (a
project CLAUDE.md, the `default-extensions` in the cabal file, the surrounding
module) override anything here — including which extensions are on and which
prelude is in scope. **Check the `.cabal` file and the GHC version before
recommending anything.**

Assumed baseline is GHC 9.6+ with `GHC2021`; anything newer or older is labeled
inline.

## References — load on demand

Detail lives in `references/`. One pointer per page:

### Core language

- **[types-and-data.md](references/types-and-data.md)**
  — algebraic data types, records, `newtype` vs `data` vs `type`, strictness
  annotations and `UNPACK`, `deriving` strategies, phantom and existential
  shapes, kinds. _Read when designing a data type, or when a `newtype` and a
  `data` behave differently at runtime._

- **[typeclasses.md](references/typeclasses.md)**
  — class/instance mechanics, dictionary passing, superclasses, default
  methods, `deriving` (stock/newtype/anyclass/via), coherence and orphan
  instances, overlapping/incoherent, defaulting, `MINIMAL`. _Read before
  writing an instance, and always before writing an orphan._

- **[functor-applicative-monad.md](references/functor-applicative-monad.md)**
  — the hierarchy and its laws, `Semigroup`/`Monoid`, `Alternative`,
  `Foldable`/`Traversable`, the operator vocabulary (`<$>`, `<*>`, `>>=`,
  `=<<`, `>=>`, `traverse_`), and which abstraction a problem actually needs.
  _Read when the types nearly line up but not quite._

- **[laziness-and-strictness.md](references/laziness-and-strictness.md)**
  — thunks and WHNF, where laziness pays and where it leaks, `seq`/`$!`/
  `force`, bang patterns, `StrictData` and `Strict`, `foldl'`, the classic leak
  catalogue. _Read on any "why is this using 4 GB" question._

- **[syntax-and-idioms.md](references/syntax-and-idioms.md)**
  — pattern matching and guards, `where` vs `let`, sections and point-free,
  operators and fixity, `do` desugaring, `LambdaCase`/`MultiWayIf`/view
  patterns, layout rule, the partial-function blacklist. _Read when writing
  idiomatic code or reading someone else's `.&.` soup._

- **[advanced-types.md](references/advanced-types.md)**
  — GADTs, type families (open/closed/associated), `DataKinds` and promotion,
  `RankNTypes`, existentials, `TypeApplications`, `ScopedTypeVariables`,
  standalone kind signatures, `QuantifiedConstraints`, when type-level
  programming is the wrong call. _Read before reaching for a type family._

- **[language-extensions.md](references/language-extensions.md)**
  — what `GHC2021`/`GHC2024` turn on, the extensions worth enabling by default,
  the ones that change semantics, the ones to avoid, and where to put them.
  _Read when adding a `{-# LANGUAGE #-}` pragma or setting
  `default-extensions`._

- **[type-errors.md](references/type-errors.md)**
  — decoding GHC messages: rigid type variables, ambiguity, the monomorphism
  restriction, `No instance for`, overlapping instances, missing-`Show`-for-a-
  function, deferred type errors, typed holes as a debugging tool. _Read when
  the error is longer than the function._

### Effects and runtime

- **[io-and-mutable-state.md](references/io-and-mutable-state.md)**
  — what `IO` actually is, ordering and `unsafePerformIO`, `IORef`/`MVar`/
  `STRef`, the `ST` monad and escape analysis, evaluation vs execution, lazy IO
  and why it bites, `interact`. _Read before mixing pure code with effects._

- **[exceptions-and-resources.md](references/exceptions-and-resources.md)**
  — the exception hierarchy, `throwIO` vs `throw` vs `error`, imprecise
  exceptions, `bracket`/`finally`/`onException`, async exceptions and `mask`,
  `safe-exceptions` vs `unliftio`, when to use `Either` instead. _Read whenever
  a resource must be released, or a `catch` swallows more than intended._

- **[concurrency-and-stm.md](references/concurrency-and-stm.md)**
  — `forkIO` and green threads, the `async` library, `MVar` patterns, STM
  (`TVar`, `retry`, `orElse`) and what may not go inside a transaction, the RTS
  flags (`-N`, `-threaded`), `par`/`Strategies`, common deadlock shapes. _Read
  before spawning a thread or sharing state._

- **[monad-transformers-and-effects.md](references/monad-transformers-and-effects.md)**
  — `transformers` vs `mtl`, the stack ordering that changes semantics,
  `lift`/`liftIO`, `MonadUnliftIO` and why `StateT` can't do it, the
  `ReaderT` pattern, and the effect-system landscape (effectful, polysemy,
  fused-effects, RIO). _Read before adding a layer to a stack._

### Data and libraries

- **[strings-and-text.md](references/strings-and-text.md)**
  — `String` vs `Text` vs `ByteString` (and their lazy/short variants),
  `OverloadedStrings`, encoding and decoding safely, `Builder`s, formatting and
  printf alternatives. _Read for any text handling — and before writing
  `String` in a hot path._

- **[containers-and-arrays.md](references/containers-and-arrays.md)**
  — the container decision table, `Data.Map` strict vs lazy, `Seq`,
  `HashMap`, `vector` (boxed/unboxed/storable/mutable), `array`, complexity
  numbers, and lists as control flow rather than storage. _Read when picking a
  data structure or when `Map.insertWith` leaked._

- **[records-and-optics.md](references/records-and-optics.md)**
  — record syntax and its historical pain, `DuplicateRecordFields`,
  `NoFieldSelectors`, `OverloadedRecordDot`, `lens` vs `optics` vs `microlens`,
  the optic hierarchy, `generic-lens`, and when a plain function is better.
  _Read when nested updates get ugly._

- **[json-and-serialization.md](references/json-and-serialization.md)**
  — `aeson` (2.x `Key`/`KeyMap`), `ToJSON`/`FromJSON` by hand and by generics,
  `Options` for field mangling, decoding errors, `binary`/`cereal`/`serialise`,
  CSV, YAML, and schema drift. _Read when crossing a wire format._

- **[parsing-and-streaming.md](references/parsing-and-streaming.md)**
  — `megaparsec` vs `attoparsec` vs `flatparse`, combinator idioms and error
  messages, lexers and `alex`/`happy`, then the streaming libraries (`conduit`,
  `streamly`, `pipes`, `streaming`) and `ResourceT`. _Read before parsing a
  format by hand or reading a file that doesn't fit in RAM._

### Practice

- **[build-and-tooling.md](references/build-and-tooling.md)**
  — `ghcup`, cabal vs stack (and how to work in both), the `.cabal` file
  anatomy, `cabal.project` and freeze files, version bounds, HLS, formatters,
  `ghcid`, warnings worth turning on, Nix. _Read when setting up or fixing a
  build._

- **[testing-and-debugging.md](references/testing-and-debugging.md)**
  — `hspec`/`tasty`, QuickCheck vs Hedgehog, property patterns (round-trip,
  invariant, model), golden tests, `doctest`, `Debug.Trace`, the GHCi debugger,
  and how to test `IO`. _Read when adding tests or chasing a bug interactively._

- **[performance.md](references/performance.md)**
  — the order of operations, cost centres and `+RTS -p`, heap profiling and
  reading a leak, RTS/GC tuning, `INLINE`/`SPECIALIZE`/rewrite rules, fusion,
  unboxing, reading Core, `tasty-bench`/criterion. _Read before optimizing
  anything, and instead of guessing._

- **[ffi-and-interop.md](references/ffi-and-interop.md)**
  — `foreign import ccall` safe vs unsafe, marshalling and `Storable`,
  `ForeignPtr` and finalizers, `hsc2hs`, calling Haskell from C (`foreign
export`, `hs_init`), cabal's C build options, and the JS/WASM backends.
  _Read before binding a C library._

- **[ecosystem-libraries.md](references/ecosystem-libraries.md)**
  — the "which library" map: web servers and clients, databases, logging, CLI
  parsing, time, random, concurrency, alternative preludes, and how to judge a
  package on Hackage before depending on it. _Read for any "what do people use
  for X" question._

- **[ghc-versions.md](references/ghc-versions.md)**
  — the GHC/`base` version map, what each release changed, the migrations that
  actually break code (simplified subsumption, `MonadFail`, Semigroup/Monoid,
  `head` warnings), `CPP` version guards, and choosing a baseline. _Read before
  using a feature you're not sure the project's GHC has._

## Working rules for Haskell in this shelf

1. **Check the GHC version and the extension set first.** `ghc --version`, the
   `.cabal` file's `default-language` / `default-extensions`, the module's own
   pragmas. Half of "why doesn't this compile" is an extension that isn't on.
2. **Types first, then implementation.** Write the signature, let GHC tell you
   what's missing. Typed holes (`_`) are a design tool, not just an error.
3. **A memory problem is a laziness problem until proven otherwise.** Profile
   with `-hc`/`-hT` before rewriting anything.
4. **Prefer the boring stack.** `transformers` + `ReaderT env IO` gets further
   than most effect systems, and every Haskeller can read it.
5. **Partial functions are a bug you haven't hit yet.** `head`, `fromJust`,
   `read`, `!!`, and incomplete patterns — enable `-Wall` and mean it.
6. **Don't type-level-program your way out of a data-modelling problem.** If a
   `newtype` and a smart constructor solve it, they win.

## Conventions for this skill

- Each reference cites its source URLs at the top; prefer stable Hackage
  package-root URLs (`hackage.haskell.org/package/<pkg>`) and the `latest`
  GHC User's Guide path so links don't rot.
- Keep SKILL.md lean: two-line pointers only. Detail lives on the shelf.
- To add a topic: write `references/<topic>.md` in the same format (Source block
  up top, numbered sections, Gotchas at the end), then add a pointer above.
