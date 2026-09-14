---
topic_id: "v2:EBOC"
topic_path: "prisma-orm/client-setup"
semantic_id: "I-EAsl-BOeMRqsvHJbAyU43LF85oAAAG"
related_ids:
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
  - "E_GIuHaDOUEbIs4TYLHScUWZl4DIoAAA"
---
# Prisma Client: Everyday CRUD and Querying

**Status check (July 2026): the current release line is Prisma ORM v7 (`prisma@7.8.0` is `latest` on npm; `6.19.2` is tagged `prev`), and it changes how you get a client, not how you query with one.** Every query shape on this page (filters, nested writes, pagination, `groupBy`, `select`/`omit`) is unchanged in v7; what changed is the top of the file: a driver adapter is now mandatory, you import `PrismaClient` from the generator's `output` path rather than `@prisma/client`, `Prisma.validator` is gone (use `satisfies`), and `$use` middleware was removed back in 6.14.0. Sections are marked `[v6]` / `[v7]` where a reader still on 6.x needs the old shape.

Source:

- https://www.prisma.io/docs/orm/prisma-client/queries/crud (the CRUD guide: all model methods, provider notes for `skipDuplicates` / `createManyAndReturn`)
- https://www.prisma.io/docs/orm/reference/prisma-client-reference (the API reference: query options, every filter condition, atomic ops, constructor options)
- https://www.prisma.io/docs/orm/prisma-client/queries/select-fields (default return shape, `select` / `include` / `omit`)
- https://www.prisma.io/docs/orm/prisma-client/queries/relation-queries (nested reads, every nested write op, fluent API)
- https://www.prisma.io/docs/orm/prisma-client/queries/filtering-and-sorting (filters, `mode: 'insensitive'`, `orderBy`)
- https://www.prisma.io/docs/orm/prisma-client/queries/pagination (offset vs cursor, the perf tradeoff)
- https://www.prisma.io/docs/orm/prisma-client/queries/aggregation-grouping-summarizing (`count`, `aggregate`, `groupBy`, `distinct`)
- https://www.prisma.io/docs/orm/prisma-client/special-fields-and-types/null-and-undefined (null vs undefined, `strictUndefinedChecks`, `Prisma.skip`)
- https://www.prisma.io/docs/orm/prisma-client/special-fields-and-types/working-with-json-fields (JSON path filters, provider differences, `DbNull` / `JsonNull` / `AnyNull`)
- https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7 (v7 breaking changes: mandatory driver adapters, generator `output`, removal of `Prisma.validator`)
- https://www.prisma.io/docs/orm/reference/preview-features/client-preview-features (verified July 2026: `strictUndefinedChecks` is still Preview)
  Siblings: schema-and-datamodel.md, relations.md, transactions.md, raw-sql.md, client-extensions.md, performance.md, errors-and-debugging.md, setup-and-deploy.md

## 1. Instantiating PrismaClient

**[v7]** Two things are non-negotiable: a **driver adapter**, and importing from the **generated `output` path**. `new PrismaClient()` with nothing but a `DATABASE_URL` in the environment does not work in v7, and neither does `datasources: { db: { url } }`. The adapter is the connection; the client is just the query builder on top of it.

```ts
// [v7] `output` in the generator block decides this path; it is NOT '@prisma/client'
import { PrismaClient } from "./generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg"; // or adapter-mariadb, adapter-better-sqlite3, adapter-mssql, ...

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
});

export const prisma = new PrismaClient({
  adapter, // mandatory in v7, for every database
  log: ["query", "warn", "error"], // or [{ emit: 'event', level: 'query' }]
  errorFormat: "pretty", // 'pretty' | 'colorless' | 'minimal'
  omit: { user: { password: true } }, // global omit, applies to every query
  transactionOptions: { maxWait: 2000, timeout: 5000 },
});
```

```ts
// [v6] the old shape: engine-managed connection, barrel import from node_modules.
// Still what 6.x code looks like; it throws in v7.
import { PrismaClient } from "@prisma/client";
export const prisma = new PrismaClient({ log: ["query", "warn", "error"] });
```

Every other option (`log`, `errorFormat`, `omit`, `transactionOptions`) is identical across the two; only `adapter` and the import moved. Note that `.env` is no longer auto-loaded in v7, so `process.env.DATABASE_URL` is only populated if something loaded it (your runtime, your process manager, or an explicit loader); `prisma.config.ts` is where the CLI gets its adapter. See setup-and-deploy.md.

One instance per process. Each client owns a connection pool (in v7 the pool lives in the adapter), so constructing one per request will exhaust the database. In dev, hot reload re-executes module scope, so stash the instance on `globalThis`:

```ts
import { PrismaClient } from "./generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const makeClient = () =>
  new PrismaClient({
    adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }),
  });

const globalForPrisma = globalThis as unknown as {
  prisma?: ReturnType<typeof makeClient>;
};
export const prisma = globalForPrisma.prisma ?? makeClient();
if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
```

Caching the client on `globalThis` matters more in v7, not less: the adapter holds the real pool, so a hot-reload leak leaks `pg` pools, not just client objects.

Connection is lazy (first query connects). `$connect()` / `$disconnect()`, the per-database adapter packages, serverless, and edge runtimes: see setup-and-deploy.md. Pool sizing and `connection_limit`: see performance.md.

**Typing query arguments.** `Prisma.validator` was **removed in v7**. Use `satisfies` against the generated arg types, which gives you the same "check this object literal without widening it" behaviour with no Prisma-specific API:

```ts
// [v7]
import { Prisma } from "./generated/prisma/client";

const userSelect = {
  email: true,
  posts: { select: { title: true } },
} satisfies Prisma.UserSelect;

// [v6] the removed API, for reference when reading old code
const userSelect = Prisma.validator<Prisma.UserSelect>()({
  email: true,
  posts: { select: { title: true } },
});
```

The `Prisma` namespace itself (`Prisma.DbNull`, `Prisma.JsonNull`, `Prisma.skip`, the generated `Prisma.*Select` / `*WhereInput` types used throughout this page) still exists in v7; it just comes from the generated client, not from `@prisma/client`.

## 2. The model methods

| Method                | Returns                              | Notes                                                              |
| --------------------- | ------------------------------------ | ------------------------------------------------------------------ |
| `findUnique`          | record or `null`                     | `where` must target a unique: `@id`, `@unique`, `@@id`, `@@unique` |
| `findUniqueOrThrow`   | record                               | throws `PrismaClientKnownRequestError` (P2025) if absent           |
| `findFirst`           | record or `null`                     | any `where`; pair with `orderBy` or it is nondeterministic         |
| `findFirstOrThrow`    | record                               | throws on no match                                                 |
| `findMany`            | array (`[]` if none)                 | never null                                                         |
| `create`              | created record                       | supports nested writes                                             |
| `createMany`          | `{ count }`                          | no nested writes, no relation returns                              |
| `createManyAndReturn` | array of created records             | PostgreSQL, CockroachDB, SQLite only                               |
| `update`              | updated record                       | `where` is unique; throws P2025 if not found                       |
| `updateMany`          | `{ count }`                          | non-unique `where`; no throw on zero rows                          |
| `updateManyAndReturn` | array of updated records             | PostgreSQL, CockroachDB, SQLite only                               |
| `upsert`              | record                               | `{ where, create, update }`                                        |
| `delete`              | deleted record                       | unique `where`; throws P2025 if not found                          |
| `deleteMany`          | `{ count }`                          | `deleteMany({})` truncates logically                               |
| `count`               | number, or object with `select`      | `select: { _all: true, name: true }` counts non-null per field     |
| `aggregate`           | `{ _count, _avg, _sum, _min, _max }` | numeric fields for `_avg` / `_sum`                                 |
| `groupBy`             | array of groups                      | `by`, `having`, aggregate keys                                     |

```ts
const user = await prisma.user.findUnique({
  where: { email: "elsa@prisma.io" },
});
const users = await prisma.user.findMany({
  where: { email: { endsWith: "prisma.io" } },
});
const { count } = await prisma.user.createMany({
  data: [{ email: "bob@prisma.io" }, { email: "yewande@prisma.io" }],
  skipDuplicates: true, // not supported on MongoDB, SQL Server, or SQLite
});
const created = await prisma.user.createManyAndReturn({
  data: [{ email: "a@x.io" }],
});
const viola = await prisma.user.upsert({
  where: { email: "viola@prisma.io" },
  update: { name: "Viola the Magnificent" },
  create: { email: "viola@prisma.io", name: "Viola" },
});
```

`upsert` with an empty `update: {}` is the idiomatic `findOrCreate`.

## 3. select vs include vs omit

Default: all scalar fields of the model, and no relations.

- `select`: allowlist. Only what you name comes back (scalars and relations).
- `include`: adds relations on top of the default scalars.
- `omit`: denylist. Everything except what you name.

`select` and `include` cannot appear at the same level of the same query. `select` and `omit` cannot be combined either (they are opposites). Nesting resets the level, so `select: { posts: { include: { categories: true } } }` is fine.

```ts
await prisma.user.findFirst({
  select: {
    email: true,
    posts: { select: { title: true, published: true } },
    _count: { select: { posts: { where: { published: true } } } },
  },
});
await prisma.user.findMany({
  omit: { password: true },
  include: { posts: true },
});
```

Global `omit` in the constructor (see section 1) applies everywhere; override per query with `omit: { password: false }`.

## 4. Nested reads and nested writes

Nested reads are just `include` / `select` on relation fields, to any depth. The fluent API traverses relations with chained calls and issues a separate query:

```ts
const posts = await prisma.user
  .findUnique({ where: { email: "a@x.io" } })
  .posts();
```

The chain only works off a call that yields a single object (`findUnique`, `findFirst`, to-one relations), never off `findMany`.

Nested writes run in a single implicit transaction. Operators, and where each is legal:

| Op                | to-one                   | to-many                                            |
| ----------------- | ------------------------ | -------------------------------------------------- |
| `create`          | yes                      | yes (single or array)                              |
| `createMany`      | no                       | yes (cannot nest further creates inside it)        |
| `connect`         | yes                      | yes                                                |
| `connectOrCreate` | yes                      | yes                                                |
| `disconnect`      | yes (`disconnect: true`) | yes (array of unique wheres)                       |
| `set`             | no                       | yes (replaces the whole list; `set: []` clears it) |
| `update`          | yes                      | yes (`{ where, data }`)                            |
| `updateMany`      | no                       | yes                                                |
| `upsert`          | yes                      | yes                                                |
| `delete`          | yes (`delete: true`)     | yes                                                |
| `deleteMany`      | no                       | yes                                                |

```ts
await prisma.user.create({
  data: {
    email: "yvette@prisma.io",
    posts: {
      create: [
        { title: "Omelette", categories: { create: { name: "Cooking" } } },
      ],
      connect: [{ id: 8 }, { id: 9 }],
      connectOrCreate: {
        where: { slug: "intro" },
        create: { title: "Intro", slug: "intro" },
      },
    },
  },
});

await prisma.user.update({
  where: { id: 6 },
  data: {
    posts: {
      update: { where: { id: 9 }, data: { title: "Updated" } },
      updateMany: { where: { published: true }, data: { published: false } },
      deleteMany: { published: false },
      set: [{ id: 12 }], // authoritative list replacement
    },
  },
});
```

`disconnect` / `set` on a required relation fails: there is nowhere to put the null FK. Referential actions and required-relation rules live in relations.md.

## 5. Filter conditions

```ts
await prisma.user.findMany({
  where: {
    role: "ADMIN", // shorthand for { equals: 'ADMIN' }
    name: { not: null },
    id: { in: [1, 2, 3], notIn: [9] },
    profileViews: { gte: 100, lt: 1000 }, // lt, lte, gt, gte
    email: { contains: "prisma", mode: "insensitive" }, // also startsWith, endsWith
    AND: [{ published: true }, { views: { gt: 0 } }],
    OR: [{ name: { startsWith: "E" } }, { role: "ADMIN" }],
    NOT: { email: { endsWith: "admin.example.com" } },
  },
});
```

`mode: 'insensitive'` is PostgreSQL and MongoDB only. On MySQL, SQLite, and SQL Server, case sensitivity is a property of the column collation, not the query. `search` (full-text) is a separate feature with its own provider gates; see schema-and-datamodel.md.

Relation filters:

```ts
where: {
  posts: { some: { published: true } },   // at least one
  comments: { every: { flagged: false } }, // all (TRUE for zero related records)
  drafts: { none: {} },                    // zero related records
  author: { is: { name: 'Alice' } },       // to-one matches
  profile: { isNot: null },                // to-one does not match / is null
}
```

Scalar list filters (arrays, PostgreSQL and CockroachDB and MongoDB):

```ts
where: {
  tags: { has: 'databases' },
  tags: { hasEvery: ['databases', 'typescript'] },
  tags: { hasSome: ['databases', 'orm'] },
  tags: { isEmpty: true },
  tags: { equals: ['a', 'b'] }, // exact array, order matters
}
```

## 6. JSON filtering

```ts
// PostgreSQL: path is an array of keys
await prisma.user.findMany({
  where: {
    meta: {
      path: ["pet", "name"],
      string_contains: "Fido",
      mode: "insensitive",
    },
  },
});
// MySQL: path is a JSONPath string
await prisma.user.findMany({
  where: { meta: { path: "$.pet.name", string_contains: "Fido" } },
});
```

Operators: `equals`, `not`, `string_contains`, `string_starts_with`, `string_ends_with`, `array_contains`, `array_starts_with`, `array_ends_with`, plus `lt` / `lte` / `gt` / `gte` on numeric JSON values.

Provider differences that bite:

- Path syntax differs (array vs `$.` JSONPath) and is not portable across providers.
- `array_contains` on PostgreSQL wants an array (`['value']`); MySQL accepts a scalar (`'value'`).
- Filtering on object keys _inside an array_ is MySQL only. PostgreSQL can match whole objects in an array, not their properties.
- JSON nulls need `Prisma.DbNull` (column is SQL NULL), `Prisma.JsonNull` (column holds the JSON literal `null`), or `Prisma.AnyNull` (filtering only, either). Plain `null` in a JSON filter is a type error.

## 7. orderBy

```ts
orderBy: [{ published: 'desc' }, { title: 'asc' }] // array preserves precedence
orderBy: { author: { name: 'asc' } }               // by a to-one relation field
orderBy: { posts: { _count: 'desc' } }             // by relation aggregate count
orderBy: { updatedAt: { sort: 'desc', nulls: 'last' } } // nulls: 'first' | 'last'
orderBy: { _relevance: { fields: ['title'], search: 'prisma', sort: 'desc' } } // full-text
```

`nulls` is only valid on an optional (nullable) field, and only on providers with NULLS FIRST/LAST (PostgreSQL, SQLite, SQL Server, MongoDB); it errors on required fields.

## 8. Pagination

```ts
// Offset
const page = await prisma.post.findMany({
  skip: 20,
  take: 10,
  orderBy: { id: "asc" },
});

// Cursor
const next = await prisma.post.findMany({
  take: 10,
  skip: 1, // step past the cursor row itself
  cursor: { id: lastPost.id },
  orderBy: { id: "asc" }, // must be stable and unique-ish
});
```

Offset pagination lets you jump to page N, but the database still walks the skipped rows, so cost grows with the offset: fine for small tables and admin UIs, bad for deep pages on big tables. Cursor pagination is O(1)-ish because the cursor becomes an index seek, but you can only move forward/backward from a known row (feeds, infinite scroll, batch jobs). The cursor field must be unique and sequential, and `orderBy` must match it or results skip and repeat. Negative `take` walks backwards from the cursor.

## 9. Atomic number operations

```ts
await prisma.post.update({
  where: { id: 1 },
  data: {
    views: { increment: 1 },
    likes: { decrement: 2 },
    score: { multiply: 2 },
    ratio: { divide: 2 },
    rank: { set: 5 }, // plain assignment, equivalent to rank: 5
  },
});
```

These compile to `SET views = views + 1` in the database, so they avoid the read-modify-write race that `views: current + 1` has. They work on `Int`, `BigInt`, `Float`, `Decimal`, and are unavailable on nullable fields whose value is currently null (the arithmetic yields null).

## 10. Aggregate, groupBy, count, distinct

```ts
const stats = await prisma.user.aggregate({
  where: { email: { contains: "prisma.io" } },
  _count: { _all: true },
  _avg: { profileViews: true },
  _sum: { profileViews: true },
  _min: { age: true },
  _max: { age: true },
});

const byCountry = await prisma.user.groupBy({
  by: ["country", "role"],
  where: { active: true }, // filters rows BEFORE grouping
  _count: { _all: true },
  _sum: { profileViews: true },
  having: { profileViews: { _avg: { gt: 100 } } }, // filters groups AFTER
  orderBy: { _sum: { profileViews: "desc" } },
  take: 10,
});

const counts = await prisma.user.count({ select: { _all: true, name: true } });
// { _all: 30, name: 10 }  <- `name` counts non-null values

const titles = await prisma.post.findMany({ distinct: ["authorId", "title"] });
```

groupBy rules: everything in `orderBy` must be in `by` or be an aggregate; `having` can only reference aggregates or fields in `by`; `skip` / `take` require an `orderBy`; there is no `select` (the `by` fields come back automatically).

Aggregates on nullable fields return `null` when there are no rows, except `_count`, which returns 0.

## Gotchas

1. **`undefined` means "ignore this key", not "match null".** `where: { id: undefined }` is not a filter, it is an absent filter. `prisma.user.deleteMany({ where: { id: maybeUndefined } })` deletes every user. Guard the input, or turn on the `strictUndefinedChecks` preview feature and use `Prisma.skip` (`email: optionalEmail ?? Prisma.skip`) so a stray `undefined` throws instead of silently widening the query.
2. **`null` in `data` writes NULL; `undefined` in `data` leaves the column alone.** This is what you want for PATCH semantics, and it is why `data: { name: req.body.name }` silently ignores a client trying to clear a field.
3. **`undefined` inside `OR` behaves differently from `AND` / `NOT`.** `OR: [{ email: { contains: undefined } }]` returns an empty list; the same inside `AND` returns everything.
4. **`findUnique` only accepts unique fields.** No `contains`, no `gt` on the identifying field. The extended-where behavior lets you add _additional_ non-unique conditions alongside the unique one, but the unique one must still be there. If you want an arbitrary filter, that is `findFirst`.
5. **`findFirst` without `orderBy` is nondeterministic.** The database has no obligation to hand you rows in insertion order.
6. **`createMany` does not do nested writes and does not return rows.** It returns `{ count }`. Need the rows back, use `createManyAndReturn` (PostgreSQL, CockroachDB, SQLite only), or loop `create` inside a transaction. `updateManyAndReturn` has the same provider restriction.
7. **`skipDuplicates` is not supported on MongoDB, SQL Server, or SQLite.** Passing it there is a validation error, not a no-op.
8. **`update` and `delete` throw P2025 on a missing row; `updateMany` and `deleteMany` return `{ count: 0 }` quietly.** Pick deliberately, and see errors-and-debugging.md for the error codes.
9. **`every: {}` is vacuously true.** A user with zero posts matches `posts: { every: { published: true } }`. Add `posts: { some: {} }` if you meant "has posts, all published".
10. **`select` plus `include` at the same level is a runtime validation error**, not a merge. Same for `select` plus `omit`.
11. **`distinct` is not SQL `SELECT DISTINCT`.** Prisma fetches rows and de-duplicates in memory, so it does not reduce the work the database does or the bytes on the wire, and it interacts badly with `take` (dedupe happens after the limit). For real distinctness at scale, use `groupBy` or raw SQL.
12. **`mode: 'insensitive'` is PostgreSQL and MongoDB only.** On MySQL the default collation is already case-insensitive, which quietly makes your "insensitive" query work in dev and behave differently on a case-sensitive Postgres in prod.
13. **JSON `null` is three things.** `Prisma.DbNull`, `Prisma.JsonNull`, `Prisma.AnyNull`. Writing `meta: null` on a `Json` field will not type-check.
14. **`findUniqueOrThrow` / `findFirstOrThrow` inside a sequential `$transaction([...])` do not roll back the earlier operations when they throw.** Use an interactive transaction (`$transaction(async tx => ...)`) if you rely on that; see transactions.md.
15. **`set: []` on a to-many relation silently detaches everything.** It is the relation equivalent of a full overwrite, and a partially-populated input object will happily wipe the list.
16. **[v7] Forgetting the driver adapter.** `new PrismaClient()` with a `DATABASE_URL` in the environment is a v6 reflex and it does not work in v7: adapters are mandatory for every database, not just serverless/edge ones. `datasources: { db: { url } }` is gone too. Build the adapter (`new PrismaPg({ connectionString })`) and pass it as `adapter`.
17. **[v7] `import { PrismaClient } from '@prisma/client'` is wrong in new code.** The default generator is now `prisma-client` (not `prisma-client-js`), `output` is required, and the client is generated **into your source tree**. Import from that path (`./generated/prisma/client`). This bites hardest when you paste a snippet from a v6-era blog post or from an LLM: the query code is fine, the import line is not. Corollary: the generated directory is real source, so decide deliberately whether it is committed or gitignored-and-generated in CI.
18. **[v7] `Prisma.validator` no longer exists.** Reach for `satisfies Prisma.UserSelect` instead. The failure mode is confusing because the `Prisma` namespace still exists (for `DbNull`, `skip`, and the generated types), so `Prisma.validator` looks like it should be there and simply is not.
19. **`$use` middleware was removed in 6.14.0.** Anything you remember about `prisma.$use(async (params, next) => ...)` for soft deletes, auditing, or tenancy is dead code on 6.14+ and on all of v7. Use a client extension with a `query` component (`$extends`); see client-extensions.md. Note extensions still do not see database-level cascades (relations.md).
20. **[v7] `.env` is not auto-loaded anymore.** A `DATABASE_URL` that is sitting in `.env` and nowhere else will be `undefined` when your adapter reads `process.env`, and the failure looks like a connection error rather than a config error. The CLI reads `prisma.config.ts`; your application code has to load its own environment.
