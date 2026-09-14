---
semantic_id: "bexgeVJd54k6-9CQM5KTWGNv3Nx2QAAC"
related_ids:
  - "Ya1y2QAJy4U4-9zSIIHQzGN__V5jAAAE"
  - "ae5-RBY5S8mw65iQLpOI1Wt_115nwAAC"
---
# The library ecosystem — which package for what

Source:

- https://hackage.haskell.org/
- https://www.stackage.org/lts
- https://hackage.haskell.org/package/servant
- https://hackage.haskell.org/package/optparse-applicative
- https://hackage.haskell.org/package/time

Package choices move slower in Haskell than in most ecosystems, but they do
move. Check the package's Hackage page for last-upload date and its Stackage LTS
membership before committing.

## 1. Web servers and APIs

| Package           | Shape                                                         |
| ----------------- | ------------------------------------------------------------- |
| **warp**          | the HTTP server everything else runs on (WAI backend)         |
| **wai**           | the interface: `Request -> IO Response`, plus middleware      |
| **servant**       | type-level API description; generates handlers, clients, docs |
| **scotty**        | Sinatra-style routing, minimal ceremony                       |
| **yesod**         | full framework: routing TH, templates, auth, forms            |
| **IHP**           | batteries-included, opinionated, its own tooling              |
| **okapi / twain** | small modern alternatives to scotty                           |

**servant** is the distinctive one: the API is a type, so the server handler,
the client functions, and the OpenAPI docs are all derived from one declaration
and can't drift. The cost is type-level machinery and error messages that get
long when a handler doesn't match its route. Excellent for internal services
with multiple Haskell consumers; heavier than you want for a three-endpoint
webhook (use scotty).

Middleware lives in `wai-extra` (logging, gzip, request size limits),
`wai-cors`, `wai-middleware-static`. TLS via `warp-tls`, or terminate at nginx.

**Clients**: `http-client` + `http-client-tls` (the base), `req` (nice typed
API, good errors), `wreq` (lens-y), `servant-client` (free from a servant API
type).

HTML: `lucid` (monadic, fast), `blaze-html` (older), `heist`/`mustache` for
templates. `shakespeare` if you're in Yesod-land.

## 2. Databases

| Package               | Style                                                   |
| --------------------- | ------------------------------------------------------- |
| **postgresql-simple** | raw SQL with typed params; the reliable default         |
| **hasql**             | fast, precise, statement/session-based; Postgres-only   |
| **persistent**        | TH-defined entities, migrations, backend-agnostic ORM   |
| **esqueleto**         | typed joins/SQL on top of persistent's schema           |
| **beam**              | type-safe query DSL, no TH schema, good Postgres/SQLite |
| **opaleye**           | relational-algebra combinators, strong typing           |
| **sqlite-simple**     | postgresql-simple's SQLite twin                         |
| **rel8**              | Opaleye-based, more ergonomic                           |

Pooling: `resource-pool` (used by most of the above). Migrations:
`persistent`'s, `postgresql-migration`, or plain versioned `.sql` files run by
a script — the last one being the most boring and most debuggable.

Default recommendation: **postgresql-simple** with hand-written SQL for
applications where the SQL matters, **persistent+esqueleto** when you want the
schema and migrations generated, **hasql** when throughput matters.

## 3. CLI, config, and logging

```haskell
-- optparse-applicative: the standard
data Opts = Opts { optVerbose :: Bool, optPath :: FilePath }

opts :: Parser Opts
opts = Opts
  <$> switch (long "verbose" <> short 'v' <> help "Chatty output")
  <*> strArgument (metavar "PATH")

main = execParser (info (opts <**> helper) (fullDesc <> progDesc "..."))
```

`optparse-applicative` — subcommands, completions, generated `--help`. The only
real choice for anything beyond `getArgs`. Lighter alternatives: `optparse-simple`,
`cmdargs` (older).

Config: `yaml` (reuses aeson instances, line-numbered errors), `toml-reader`,
`dhall` (typed, functional config language with imports — excellent when config
is complex and shared, overkill when it's twelve keys), plus `envparse`/
`envy` for 12-factor environment variables.

Logging: `co-log` (composable, `LogAction` as a `Monoid`), `katip` (structured,
contexts, scribes), `fast-logger` (the fast backend under most of them),
`monad-logger` (the `mtl`-style one, used by persistent). For a small app, a
`Text -> IO ()` in your `Env` beats all of them.

## 4. Time, random, UUID, and other basics

- **`time`** — `UTCTime`, `Day`, `DiffTime`, `NominalDiffTime`, `ZonedTime`,
  `formatTime`/`parseTimeM` with strftime-ish specifiers. **`getCurrentTime` is
  UTC**; local time needs `getCurrentTimeZone`/`utcToLocalTime`.
  `time-1.9+` has `TimeZoneSeries` support via `timezone-olson`/`tz` for real
  IANA zones.
- **`random` (1.2+)** — a rewritten API: `StdGen`, `uniformR`,
  `randomRIO`, splittable `SplitGen`. `mwc-random` for fast, high-quality
  simulation numbers; `splitmix` underneath both.
- **`uuid`** — v4 via `nextRandom`.
- **`cryptonite`/`crypton`** — hashing, HMAC, AES, signatures. `crypton` is the
  maintained fork; `cryptonite` is the older widely-depended-on one.
  Never hand-roll crypto; also never hand-roll constant-time comparison
  (`Data.ByteArray.constEq`).
- **`text-icu`** for real Unicode collation/normalization.
- **`scientific`**, `Data.Ratio`, `Numeric.Natural` for exact numerics;
  `Data.Fixed` for money-ish decimals (or a `newtype` over `Integer` cents,
  which is the honest answer).
- **`typed-process`** — the modern subprocess API; `process` is the base
  version. `typed-process` gets streaming and exceptions right.
- **`directory`, `filepath`, `temporary`, `unix`/`Win32`** for the filesystem.
- **`async`, `stm`, `unliftio`** for concurrency (see
  `concurrency-and-stm.md`).

## 5. Alternative preludes

| Prelude            | Character                                                    |
| ------------------ | ------------------------------------------------------------ |
| **relude**         | `Text` by default, no partial functions, `NonEmpty` variants |
| **rio**            | prelude + `RIO` monad + logging + process, one dependency    |
| **classy-prelude** | mono-traversable-based, heavy                                |
| **protolude**      | minimal, safe                                                |
| **base-compat**    | not a replacement — backports newer `base` to older GHCs     |

The pitch: `String` is gone, `head`/`fromJust` are gone, `Text` and `Map` are in
scope. The cost: every reader must learn _your_ prelude, and StackOverflow
answers don't compile. Reasonable for a team's application monorepo, poor
manners in a library. If you skip it, `-Wall` plus discipline gets most of the
benefit.

## 6. Data and numerics

- **`containers`, `unordered-containers`, `vector`** — see
  `containers-and-arrays.md`.
- **`massiv`** — multi-dimensional arrays with parallel stencils; the best
  numeric-array story in Haskell today.
- **`hmatrix`** — BLAS/LAPACK bindings for linear algebra.
- **`statistics`**, `math-functions`.
- **`Chart`/`Chart-diagrams`, `diagrams`, `plotly-hs`** for plotting;
  `hvega`/`vega-lite` for declarative charts.
- **`hasktorch`, `grenade`, `massiv`** for ML — small ecosystem; honest advice
  is that ML lives in Python, and Haskell's role is the surrounding service.
- **`pandoc`** — not just a tool; an excellent library for document conversion.

## 7. Judging a package before you depend on it

Check, in order:

1. **Is it in the current Stackage LTS?** That's a strong signal of active
   maintenance and compatibility with a coherent set.
2. **Last upload date** on Hackage, and whether the version bounds admit current
   `base`. A package pinned to `base < 4.16` won't build on a modern GHC.
3. **Reverse dependencies** on Hackage — how many packages rely on it.
4. **The dependency tree it drags in.** `lens` and `aeson` are fine in an
   application; in a small library they're an imposition.
5. **Whether the maintainer is responsive** — open issues/PRs and their ages.
6. **Whether `base` already does it.** A surprising amount of what people reach
   for is `Data.List`, `Data.Function`, or `Data.Bifunctor`.

Hoogle (`hoogle.haskell.org`) searches by _type signature_, which is the fastest
way to find a function you can describe but not name — `(a -> b) -> [a] -> [b]`
finds `map`. Learn to use it; it has no equivalent in most ecosystems.

## Gotchas

- **`cryptonite` vs `crypton`**: two forks of the same API in the wild; mixing
  them gives duplicate-instance and ambiguity errors.
- **`aeson` 1.x vs 2.x** is a breaking change for anything touching `Object`.
- **`random` 1.1 vs 1.2** changed the API and the generator; old tutorials fail
  to compile.
- **`text` 2.0** changed the internal encoding (UTF-16 → UTF-8), which matters
  for FFI and for anything using internal modules.
- **An alternative prelude in a library forces nothing on users but confuses
  every contributor.**
- **`servant` error messages scale badly** with API size; keep the API type in
  named chunks.
- **`String`-based `FilePath` cannot represent all OS paths** — `OsPath` is the
  fix (see `strings-and-text.md`).
- **A package that isn't in Stackage LTS is not necessarily bad**, but you now
  own its bounds in your freeze file.
- **`getCurrentTime` is UTC.** Every "off by N hours" bug is a missing
  `utcToLocalTime`.
