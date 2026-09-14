---
topic_id: "v2:ELDC"
topic_path: "prisma-orm/raw-sql"
semantic_id: "M4mTtXfTuam_wtajuYXz1wXEtFj6gAAJ"
related_ids:
  - "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
  - "M9mSK_cKHKOX6saJKoTisEWaFWCoIAAN"
---
# Prisma Raw SQL & TypedSQL

`$queryRaw`/`$executeRaw`, the `Prisma.sql`/`join`/`empty`/`raw` builders, type-mapping caveats, MongoDB raw, and TypedSQL (`prisma generate --sql`).

Source:

- https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/raw-queries (`$queryRaw`/`$executeRaw`, `Prisma.sql`/`join`/`empty`/`raw`, type-mapping caveats, MongoDB raw)
- https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/typedsql (`prisma generate --sql`, `sql/` dir, `$queryRawTyped`, limits)
- https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7 (v7: Rust-free, driver adapters mandatory, `prisma-client` generator + required `output`, `Prisma.validator` removed)

Siblings: client-crud.md, transactions.md, client-extensions.md, errors-and-debugging.md

**Version note:** the current line is **Prisma ORM v7** (v7.0.0 shipped 2025-11-19; `prisma@7.8.0` is `latest` on npm as of July 2026, `6.19.2` is tagged `prev`). On this page that changes three things: every `new PrismaClient()` must be given a **driver adapter** (a bare `DATABASE_URL`, or `datasources: { db: { url } }`, no longer works), imports come from your **generated output path** rather than `@prisma/client`, and `maxWait` is now time spent waiting on the **driver's** pool rather than Prisma's. Transactions, raw queries, TypedSQL, and extensions are otherwise unchanged from v6; the deltas are marked `[v6]` / `[v7]` inline.


### Constructing the client (v7)

Every snippet below assumes a client built like this. It is written out once here and abbreviated to `new PrismaClient({ adapter })` afterwards.

```ts
import { PrismaClient } from "./generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
export const prisma = new PrismaClient({ adapter });
```

`[v6]` `new PrismaClient()` read `DATABASE_URL` from the schema's `datasource` block on its own, and adapters were an opt-in preview feature. `[v7]` the adapter is mandatory for **every** database, including SQLite (`@prisma/adapter-better-sqlite3`) and MySQL (`@prisma/adapter-mariadb`). See setup-and-deploy.md for the adapter-per-provider table.


## 1. Raw queries (relational)

- `$queryRaw` returns rows. Tagged template, values are sent as bind parameters, safe.
- `$executeRaw` returns the affected-row `number`. Tagged template, safe.
- `$queryRawUnsafe` / `$executeRawUnsafe` take a plain string plus positional params. String interpolation here is a SQL-injection hole.

```ts
const email = "alice@prisma.io";
const users =
  await prisma.$queryRaw`SELECT * FROM "User" WHERE email = ${email}`;
const n =
  await prisma.$executeRaw`UPDATE "User" SET active = true WHERE "emailValidated" = true`;

// Unsafe form: the ONLY reason to use it is a dynamic identifier (table/column name).
const rows = await prisma.$queryRawUnsafe(
  `SELECT * FROM "${allowlistedTable}" WHERE email = $1`, // $1 pg, ? mysql
  email,
);
```

Template variables become parameters, so they cannot be used for identifiers, nor inside a string literal (`LIKE '%${x}%'` does not work; pass `` `LIKE ${'%' + x + '%'}` `` instead).

### Composition helpers

```ts
import { Prisma } from "./generated/prisma/client";

// Prisma.sql: build a parameterized fragment
const q = Prisma.sql`SELECT * FROM "User" WHERE email = ${email}`;
await prisma.$queryRaw(q);

// Prisma.join: expand an array into an IN list, still parameterized
const ids = [1, 3, 5];
await prisma.$queryRaw`SELECT * FROM "User" WHERE id IN (${Prisma.join(ids)})`;

// Prisma.empty: conditional clause
await prisma.$queryRaw`
  SELECT * FROM "User"
  ${name ? Prisma.sql`WHERE name = ${name}` : Prisma.empty}
`;

// Prisma.raw: injects literal SQL text, NOT a parameter. Trusted input only.
const orderBy = Prisma.raw(`"createdAt" DESC`);
await prisma.$queryRaw`SELECT * FROM "User" ORDER BY ${orderBy}`;
```

### Typing results

`$queryRaw` returns `unknown[]` unless you supply a generic. The generic is an **assertion**, not a validation; nothing checks it at runtime.

```ts
import type { User } from "./generated/prisma/client";
const users = await prisma.$queryRaw<User[]>`SELECT * FROM "User"`;

type Row = { id: number; postCount: bigint };
const rows = await prisma.$queryRaw<
  Row[]
>`SELECT id, count(*) AS "postCount" FROM ...`;
```

### Type-mapping caveats

Raw results are deserialized from the database driver, not through Prisma's schema mapping, so JS types are frequently not what the model type says:

- `COUNT(*)`, `SUM(int)`, `bigserial`, `INT8` come back as **`BigInt`**, which `JSON.stringify` throws on. Cast in SQL (`count(*)::int`) or convert (`Number(row.postCount)`).
- `numeric`/`decimal` come back as **`Prisma.Decimal`** (decimal.js), not `number`.
- Booleans are `true`/`false` on PostgreSQL but can arrive as `1`/`0` on MySQL.
- Postgres functions that expect `INT4` may reject the `INT8` a template parameter binds as; add an explicit cast in the SQL.
- Dates/times map to JS `Date`.

### MongoDB raw

```ts
await prisma.$runCommandRaw({
  insert: "Pets",
  documents: [{ _id: 1, name: "Felinecitas" }],
});
const found = await prisma.user.findRaw({
  filter: { age: { $gt: 25 } },
  options: { projection: { _id: false } },
});
const agg = await prisma.user.aggregateRaw({
  pipeline: [
    { $match: { status: "registered" } },
    { $group: { _id: "$country", total: { $sum: 1 } } },
  ],
});
```

Do not run `find` or `aggregate` through `$runCommandRaw` (cursor/session binding); use `findRaw`/`aggregateRaw`. `ObjectId`, `Date` etc. must be written in MongoDB Extended JSON (`{ $oid: '...' }`).


## 2. TypedSQL

TypedSQL puts SQL in `.sql` files and generates a fully typed function per file, so both parameters and result rows are checked at compile time. It is the answer to "I need real SQL but I do not want `$queryRaw<Row[]>` lying to me."

```prisma
generator client {
  provider        = "prisma-client"   // v7 default. [v6] the old default was "prisma-client-js"
  output          = "../src/generated/prisma"  // REQUIRED on the prisma-client generator
  previewFeatures = ["typedSql"]
}
```

```sql
-- prisma/sql/getUsersWithPostCount.sql
-- @param {Int} $1:minPosts How many posts a user must have
SELECT u.id, u.name, COUNT(p.id)::int AS "postCount"
FROM "User" u
LEFT JOIN "Post" p ON u.id = p."authorId"
GROUP BY u.id, u.name
HAVING COUNT(p.id) >= $1
```

```bash
npx prisma generate --sql          # add --watch while developing
```

```ts
// v7 / prisma-client generator: import from the generated output path
import { getUsersWithPostCount } from "./generated/prisma/sql";
// [v6] with the old prisma-client-js generator and no custom output: '@prisma/client/sql'

const rows = await prisma.$queryRawTyped(getUsersWithPostCount(3));
//    ^ { id: number; name: string | null; postCount: number }[]
```

Details:

- File name must be a valid JS identifier (it becomes the export name); no leading `$`.
- Param annotation: `-- @param {Type} $N:alias description`, `?` suffix for nullable. Types: `Int`, `BigInt`, `Float`, `Boolean`, `String`, `DateTime`, `Json`, `Bytes`, `Decimal`, `null`. Array args are inferred, not annotatable.
- Placeholders are provider-specific: `$1` (PostgreSQL), `?` (MySQL), `$1`/`?`/`:named` (SQLite).
- Directory defaults to `prisma/sql`; configurable via `typedSql.path` in `prisma.config.ts` (6.12+).
- Result inference is automatic on PostgreSQL and MySQL 8+; SQLite and MySQL < 8 need manual annotation.

Limitations: relational only (no MongoDB); **needs a live database connection at generate time** because it introspects to infer result types (this bites in CI and Docker builds, see setup-and-deploy.md); no dynamic SQL (runtime-chosen columns or table names still require `$queryRawUnsafe`); not supported by `@prisma/adapter-better-sqlite3` (use `@prisma/adapter-libsql`).


## Gotchas

- **`$queryRaw<T[]>` does zero runtime validation.** The generic is a cast. `COUNT(*)` typed as `number` is actually a `BigInt` and will throw the moment it hits `JSON.stringify`.
- **Raw queries bypass everything Prisma does for you:** no soft-delete `query` extension, no `result` computed fields, no `@map`/`@@map` name translation (write the _database_ names, not the Prisma model/field names), no middleware, no `@default` handling.
- **`Prisma.raw` is not a parameter, it is string splicing.** `Prisma.join` and `Prisma.sql` are safe; `Prisma.raw` and the `*Unsafe` methods are the injection surface. Allowlist identifiers, never interpolate user input.
- **TypedSQL needs a reachable database at `prisma generate --sql` time.** A CI image that builds without `DATABASE_URL` will fail generation, not just skip typing.
- **`[v7]` A driver adapter is not optional.** `new PrismaClient()` with nothing but a `DATABASE_URL`, and the old `datasources: { db: { url } }` override, both fail on v7. Any snippet on this page (or on the internet) that constructs a bare client is v6-era; add `{ adapter }`.
- **`[v7]` `import { PrismaClient } from '@prisma/client'` is wrong in new code.** The `prisma-client` generator is the default and its `output` is required, so the import path is your own source tree. Copy-pasted v6 examples will fail to resolve, or worse, resolve to a stale `@prisma/client` left over from an upgrade.
