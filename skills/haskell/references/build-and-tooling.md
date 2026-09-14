---
semantic_id: "Ya1y2QAJy4U4-9zSIIHQzGN__V5jAAAE"
related_ids:
  - "bexgeVJd54k6-9CQM5KTWGNv3Nx2QAAC"
  - "ae5-RBY5S8mw65iQLpOI1Wt_115nwAAC"
---
# Build systems and tooling

Source:

- https://www.haskell.org/ghcup/
- https://cabal.readthedocs.io/en/stable/
- https://docs.haskellstack.org/en/stable/
- https://haskell-language-server.readthedocs.io/
- https://downloads.haskell.org/ghc/latest/docs/users_guide/using.html

## 1. Installing: `ghcup`

```bash
curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh
ghcup tui                 # interactive install/switch — the easiest interface
ghcup list
ghcup install ghc 9.6.6 && ghcup set ghc 9.6.6
ghcup install hls latest
ghc --version && cabal --version
```

`ghcup` manages GHC, cabal, HLS, and stack. It is the answer to "how do I get
Haskell" on macOS and Linux; it also handles per-project GHC switching. On
NixOS, use `haskell.nix` or `nixpkgs`' `haskellPackages` instead.

## 2. cabal vs stack

|                   | cabal                                | stack                                   |
| ----------------- | ------------------------------------ | --------------------------------------- |
| Dependency choice | solver over Hackage + version bounds | curated Stackage snapshot (LTS/nightly) |
| Reproducibility   | `cabal.project.freeze`               | snapshot pins everything by default     |
| Config            | `*.cabal` + `cabal.project`          | `package.yaml` (hpack) + `stack.yaml`   |
| GHC management    | via ghcup                            | stack installs GHC itself               |

Both are fine. cabal is the default in most modern projects and what Hackage
assumes; stack's snapshot model is nicer when you want "a set of versions known
to build together" with zero thought. A stack project can usually be built with
cabal too, since `package.yaml` generates a `.cabal` file (commit it or don't —
teams disagree; committing it makes the project cabal-buildable without hpack).

```bash
# cabal
cabal build all
cabal run myapp -- --flag
cabal test --test-show-details=direct
cabal repl lib:mylib
cabal freeze
cabal outdated
cabal haddock --haddock-all
cabal install --installdir=~/.local/bin exe:myapp

# stack
stack build --fast --file-watch
stack test
stack ghci
stack run
```

## 3. `.cabal` file anatomy

```cabal
cabal-version:   3.0
name:            myapp
version:         0.1.0.0
build-type:      Simple

common shared
  default-language: GHC2021
  default-extensions: DerivingStrategies, LambdaCase, OverloadedStrings, StrictData
  ghc-options: -Wall -Wcompat -Wincomplete-uni-patterns -Wredundant-constraints
               -Wunused-packages
  build-depends: base >=4.17 && <5

library
  import:          shared
  hs-source-dirs:  src
  exposed-modules: MyApp, MyApp.Types
  other-modules:   MyApp.Internal
  build-depends:   text, containers, aeson

executable myapp
  import:         shared
  hs-source-dirs: app
  main-is:        Main.hs
  build-depends:  myapp, optparse-applicative
  ghc-options:    -threaded -rtsopts "-with-rtsopts=-N"

test-suite spec
  import:         shared
  type:           exitcode-stdio-1.0
  hs-source-dirs: test
  main-is:        Spec.hs
  build-depends:  myapp, hspec, QuickCheck
  build-tool-depends: hspec-discover:hspec-discover
```

`common` stanzas (cabal 2.2+) with `import:` avoid repeating options across
components. Split a `library` out of your executable even for small projects —
it's the only way to test and to `repl` the code.

**`-threaded -rtsopts "-with-rtsopts=-N"`** on every executable that does
concurrency. `-rtsopts` lets users pass `+RTS` flags at runtime.

Every module must be listed in `exposed-modules` or `other-modules`, or you get
"module not found" from the _consumer_, not from the build — a classic
five-minute mystery.

## 4. `cabal.project` and freezing

```cabal
packages: . ./sub-package

package myapp
  ghc-options: -O2

source-repository-package
  type: git
  location: https://github.com/user/pkg
  tag: abc123...

allow-newer: some-pkg:base
constraints: aeson >= 2.1
```

`cabal freeze` writes `cabal.project.freeze` pinning every transitive version —
commit it for applications, **not** for libraries (a library should support a
range).

Version bounds: applications can be loose and rely on the freeze file; libraries
uploaded to Hackage need real bounds (`base >=4.17 && <5` at minimum) or they
break the solver for everyone. `cabal outdated` and `cabal gen-bounds` help.

## 5. HLS and editor setup

```bash
ghcup install hls latest
```

`haskell-language-server` gives type-on-hover, go-to-definition, inline errors,
code actions (add import, fill hole, add type signature), formatting, and
`hlint` diagnostics. It needs to be able to _build_ your project — if HLS shows
"no cradle" or nothing works, you need an `hie.yaml`:

```yaml
cradle:
  cabal:
    - path: "./src"
      component: "lib:myapp"
    - path: "./app"
      component: "exe:myapp"
```

`gen-hie > hie.yaml` (from `implicit-hie`) generates it. HLS must be built
against the _same GHC version_ as your project — version mismatch is the number
one HLS problem, and `ghcup` tracks that for you.

## 6. Fast feedback

```bash
ghcid -c "cabal repl lib:myapp"          # re-typechecks on save, ~instant
ghcid -c "cabal repl test:spec" -T :main # ...and runs tests
cabal build --ghc-options=-fno-code      # typecheck only, much faster
stack build --fast --file-watch          # -O0
```

`-fno-code` (or `-fwrite-interface -fno-code`) typechecks without generating
code — the fastest possible "does it compile" loop for a big project.

## 7. Formatters and linters

| Tool              | Style                                    |
| ----------------- | ---------------------------------------- |
| `ormolu`          | opinionated, zero config, deterministic  |
| `fourmolu`        | ormolu fork with configuration           |
| `stylish-haskell` | light touch: imports, pragmas, alignment |
| `brittany`        | older, less maintained                   |
| `hlint`           | linter with auto-applicable suggestions  |

Pick one formatter and enforce it in CI (`ormolu --mode check`). `hlint`'s
suggestions are mostly good; silence the ones you disagree with in
`.hlint.yaml` rather than ignoring the tool.

## 8. Warnings and flags worth setting

```
-Wall -Wcompat -Widentities -Wincomplete-record-updates
-Wincomplete-uni-patterns -Wmissing-export-lists -Wpartial-fields
-Wredundant-constraints -Wunused-packages -Wmissing-deriving-strategies
-Werror                    # in CI only
-O2                        # release builds; -O0 for dev iteration
-fdefer-type-errors        # never commit this
```

`-Wunused-packages` catches `build-depends` you no longer use.
`-Wmissing-export-lists` forces explicit module APIs, which prevents accidental
exposure and speeds up recompilation checking.

## 9. Docker, CI, and deployment

- **Static linking**: `-optl-static` with a musl toolchain, or use the
  `haskell:x.y.z` image plus a distroless runtime stage. GHC binaries are large
  (tens of MB) but self-contained apart from libc/libgmp.
- **CI caching**: cache `~/.cabal/store` (or `~/.stack`) keyed on the
  `.cabal`/`freeze`/`stack.yaml` hash. Without it, every CI run rebuilds the
  world and takes 20 minutes.
- `haskell-actions/setup` is the maintained GitHub Action.
- Build once with `-O2` in a builder stage, copy the binary out. Don't ship the
  compiler.

## 10. Nix, briefly

`nixpkgs`' `haskellPackages` gives a pinned, cached set built against one GHC;
`haskell.nix` (IOG) builds from Hackage/Stackage with per-package granularity
and better cross-compilation. Both give exact reproducibility and cost you a
learning curve plus a lot of rebuilds when you step off the cache. If the
project isn't already on Nix, `ghcup` + `cabal freeze` gets you most of the
reproducibility for a fraction of the effort.

## Gotchas

- **A module not listed in `exposed-modules`/`other-modules` fails at _use_
  time**, often only for a downstream consumer.
- **HLS built against a different GHC than the project does nothing useful.**
  Check `ghcup list`.
- **`cabal build` doesn't rebuild when only `cabal.project` local flags change**
  in some versions — `cabal build --ghc-options=...` forces it.
- **Missing `-threaded` means `-N` is silently ignored** and a blocking FFI call
  freezes everything.
- **Committing `cabal.project.freeze` in a library** makes it un-solvable for
  users; it belongs in applications only.
- **hpack regenerates the `.cabal` file** — editing the `.cabal` in an hpack
  project silently loses your changes on the next build.
- **`-Werror` in local dev wastes your time**; put it in CI.
- **Stackage snapshot ≠ latest Hackage.** A package's newest features may not be
  in your LTS; check the snapshot before reading the docs.
- **`cabal install` for libraries is not a thing anymore** (v2-build is
  project-local). `cabal install exe:foo` for binaries only.
