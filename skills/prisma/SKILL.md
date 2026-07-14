---
name: prisma
version: 1.0.0
public: true
description: >-
  Prisma ORM reference — the schema language and data model, relations, Prisma Client
  querying (CRUD, filters, nested writes), transactions, raw SQL and TypedSQL, client
  extensions, Prisma Migrate, driver adapters, connection pooling, deployment, error
  codes, and query performance. Use when writing, reviewing, or debugging any
  schema.prisma or Prisma Client code in any repo, when a migration or P-code error comes
  up, or on any "how do I query X with Prisma" question.
semantic_id: "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
related_ids:
  - "g-iSIH2UH6nbAdaJIqACewG7l2FaIAAH"
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
topic_id: "v2:ELNK"
topic_path: "prisma-orm/raw-sql"
---

# Prisma ORM reference

Condensed, source-cited notes grounded in the primary sources (prisma.io/docs,
the Prisma schema reference, the Client API reference, the CLI reference, the
error reference). Each page cites its source URLs at the top and ends with a
Gotchas section of the sharp edges that memory gets wrong.

This is a standalone ORM shelf, not tied to one repo. Repo conventions (a project
CLAUDE.md, an existing schema layout) override anything here.

**Read this first: the shelf is written against Prisma ORM v7** (v7.0.0 shipped
2025-11-19; `prisma@7.8.0` is `latest`, `6.19.2` is `prev`). v7 is a rewrite, not
a bump, and almost every Prisma answer from memory or a blog post is v6-shaped
and will simply error. The four that bite immediately:

- **Driver adapters are mandatory.** `new PrismaClient()` on a bare
  `DATABASE_URL` connects to nothing. Build an adapter, pass `{ adapter }`.
- **The `prisma-client` generator is the default**, `output` is required, and it
  generates into your source tree, so `import { PrismaClient } from
'@prisma/client'` is wrong in new code.
- **`prisma.config.ts` owns config.** Datasource `url` / `directUrl` /
  `shadowDatabaseUrl` are deprecated in the schema block, and `.env` is no
  longer auto-loaded.
- **The driver owns the connection pool**, so `connection_limit` and
  `pool_timeout` are inert. Post-upgrade pool timeouts are almost always this.

Check which major the target repo is actually on before answering. Pages mark
divergences inline with `[v6]` / `[v7]`.

## References - load on demand

Detail lives in `../../references/prisma/`. One pointer per page:

- **[schema-and-datamodel.md](../../references/prisma/schema-and-datamodel.md)**
  - schema.prisma anatomy, the `prisma-client` vs `prisma-client-js` generators,
    multi-file schema, scalar types and native types, attributes (@id, @default,
    @unique, @map, @@index), enums, Json, Unsupported, preview features. _Read
    before writing or changing any schema.prisma._

- **[relations.md](../../references/prisma/relations.md)**
  - @relation, one-to-one / one-to-many / implicit vs explicit many-to-many,
    self-relations and relation names, referential actions and their
    optionality-dependent defaults, relationMode foreignKeys vs prisma. _Read
    before modelling any relation or debugging a cascade._

- **[client-crud.md](../../references/prisma/client-crud.md)**
  - the query methods, select vs include vs omit, nested reads and writes,
    filters (scalar, relation, list, JSON), orderBy, offset vs cursor
    pagination, atomic updates, groupBy, and the null-vs-undefined footgun.
    _Read for any everyday "how do I query this" question._

- **[transactions.md](../../references/prisma/transactions.md)**
  - $transaction (array and interactive), maxWait vs timeout, isolation levels,
    optimistic concurrency, P2028/P2034 and the retry loop. _Read before writing
    a transaction — especially if there is any IO inside it._

- **[raw-sql.md](../../references/prisma/raw-sql.md)**
  - $queryRaw vs $queryRawUnsafe, Prisma.sql/join/raw, the type-mapping and
    BigInt traps, MongoDB raw, and TypedSQL (prisma generate --sql). _Read before
    dropping to SQL._

- **[client-extensions.md](../../references/prisma/client-extensions.md)**
  - $extends (model/client/query/result), immutability and precedence,
    Prisma.defineExtension, lifecycle/logging, and how to port dead $use
    middleware. _Read before a soft-delete, audit, or tenancy hook._

- **[migrations.md](../../references/prisma/migrations.md)**
  - the CLI surface, migrate dev (dev only, destructive) vs migrate deploy (the
    only prod command), the shadow database, db push vs migrate, introspection,
    baselining an existing DB, expand-and-contract, recovering a failed prod
    migration, seeding. _Read before running any migrate command against
    anything you care about._

- **[setup-and-deploy.md](../../references/prisma/setup-and-deploy.md)**
  - init and generate, the generator choice, driver adapters per provider,
    prisma.config.ts, connection pooling and the serverless client-per-invocation
    problem, the globalThis singleton, PgBouncer and directUrl, Accelerate and
    Prisma Postgres, edge and Docker targets. _Read when standing a project up or
    when it breaks only in deployment._

- **[errors-and-debugging.md](../../references/prisma/errors-and-debugging.md)**
  - the generated type surface (and `satisfies` now that Prisma.validator is
    gone), the error classes, a verified table of the P-codes you actually hit
    (P2002, P2003, P2025, P2024, P2028, P2034, P1001, P1012, P3xxx) with fixes,
    query logging to see real SQL, DEBUG and tracing. _Read when something throws
    a P-code or you need to see the SQL._

- **[performance.md](../../references/prisma/performance.md)**
  - N+1 and how Prisma batches, relationLoadStrategy join vs query (still
    Preview), select discipline, indexes and composite column order, EXPLAIN via
    the query log, cursor pagination, createMany, driver-owned pool sizing.
    _Read when a query is slow or the pool is timing out._

## Conventions for this skill

- Each reference carries a version note and a Source block up top; verify claims
  against those URLs rather than trusting a stale page.
- Keep SKILL.md lean: two-line pointers only. Detail lives on the shelf.
- To add a topic: write `../../references/prisma/<topic>.md` in the same format
  (version note, Source block, numbered sections, Gotchas at the end, no em
  dashes), then add a two-line pointer above. See the shelf README for the
  format spec.
