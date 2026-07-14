---
topic_id: "v2:EJOH"
topic_path: "prisma-orm/types-performance"
semantic_id: "-_KQAPYRG7Gb5p4YMqeT0c36l6zAEAAA"
related_ids:
  - "vuSYYOfQOrEb5t4BuqFT05nalb7KMAAB"
  - "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
---
# Prisma: Performance

Source:

- https://www.prisma.io/docs/orm/prisma-client/queries/query-optimization-performance (N+1, the findUnique dataloader, `in`, bulk methods)
- https://www.prisma.io/docs/orm/prisma-client/queries/relation-queries (`relationLoadStrategy: 'join' | 'query'`, the `relationJoins` preview feature)
- https://www.prisma.io/docs/orm/prisma-client/queries/transactions (`$transaction([])` batch, interactive tx, `maxWait`/`timeout`, P2034 retry)
- https://www.prisma.io/docs/orm/prisma-client/queries/pagination (offset vs cursor)
- https://www.prisma.io/docs/orm/prisma-client/queries/aggregation-grouping-summarizing (`groupBy`, and: "Prisma Client's `distinct` option does not use SQL `SELECT DISTINCT`", it is in-memory post-processing)
- https://www.prisma.io/docs/orm/prisma-client/queries/crud (`createMany`, `skipDuplicates`, `createManyAndReturn`)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/indexes (`@@index`, sort, length, PostgreSQL index `type`)
- https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections/connection-pool (pool size formula, `pool_timeout`, `connect_timeout`)
- https://www.prisma.io/docs/orm/prisma-client/observability-and-logging/logging (capturing SQL to EXPLAIN it)
- https://www.prisma.io/docs/accelerate/caching and https://www.prisma.io/docs/accelerate/reference/api-reference (`cacheStrategy`, `$accelerate.invalidate`)
- https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7 (v7 driver adapters own the pool; metrics removed)

**Version note:** the current line is **Prisma ORM v7** (v7.0.0 shipped 2025-11-19; `prisma@7.8.0` is `latest` on npm as of July 2026, `6.19.2` is tagged `prev`). The single biggest performance consequence: **the connection pool now belongs to the driver, not to Prisma**, so `?connection_limit=` and `?pool_timeout=` on `DATABASE_URL` are **inert** and the old `num_cpus * 2 + 1` default is gone (node-postgres defaults to `max: 10`). A driver adapter is mandatory on every client, and the `metrics` preview feature (the old way to watch the pool) was removed in 7.0.0. v6-only advice is marked `[v6]`.

## 1. The N+1 problem, and the three real answers

N+1 is looping over parents and issuing one query per parent. In Prisma it shows up in GraphQL resolvers and in hand-written `for (const u of users) await prisma.post.findMany(...)`.

**Answer 1: one nested read.** `include`/`select` on a relation is executed by Prisma as a small fixed number of queries (parent, then one query per relation level with an `IN (...)`), never one per row.

```ts
const usersWithPosts = await prisma.user.findMany({
  include: { posts: { select: { id: true, title: true } } },
});
// 2 queries regardless of how many users come back
```

**Answer 2: the findUnique dataloader.** Prisma automatically batches `findUnique()` calls made in the same event-loop tick into a single `WHERE id IN (...)`. This is what makes the fluent API safe inside a per-parent GraphQL resolver:

```ts
// resolver called once per parent, still 1 query total
posts: (parent, _args, ctx) =>
  ctx.prisma.user.findUnique({ where: { id: parent.id } }).posts(),
```

It batches **`findUnique` only**. `findMany` in a resolver is not batched and is the classic way people reintroduce N+1 while believing Prisma handles it.

**Answer 3: `relationLoadStrategy: 'join'`.** Push the join into the database: one query, `LATERAL JOIN` + JSON aggregation on PostgreSQL/CockroachDB, correlated subqueries on MySQL.

```prisma
generator client {
  provider        = "prisma-client"            // v7 default generator
  output          = "../src/generated/prisma"  // required on this generator
  previewFeatures = ["relationJoins"]
}
```

```ts
const users = await prisma.user.findMany({
  relationLoadStrategy: "join", // or "query"
  include: { posts: true },
});
```

- `join`: 1 round trip, no redundant parent rows on the wire (JSON is built server-side), DB does the work. Best when latency to the DB is high or the relation is small-to-medium.
- `query`: N separate queries (one per table) stitched in the client. Best when the DB is the bottleneck, or when the joined payload would fan out badly.

**Status: still Preview, on v7 as on v6.** `relationLoadStrategy` is gated behind the `relationJoins` preview flag and is **not** the default load strategy; the default remains `'query'` (Prisma issues a query per relation level). It is available on PostgreSQL, CockroachDB and MySQL only: **not SQLite, not SQL Server, not MongoDB**. Do not build a design around it as if it were GA.

## 2. `select` what you need; `include` on a fat model is a tax

`include: { author: true }` returns **every scalar column** of `author`, including that `bio` TEXT column and the `embedding` blob. There is no lazy field loading. On a wide table this is bytes over the wire plus JS object allocation on every row.

```ts
// good: explicit projection at every level
const rows = await prisma.post.findMany({
  select: {
    id: true,
    title: true,
    author: { select: { id: true, name: true } },
  },
});
```

`select` and `include` are mutually exclusive at the same level; to project a relation while keeping all parent scalars you use `include: { author: { select: {...} } }`. A projected `select` is also what makes a covering index actually cover the query.

## 3. Indexes

Prisma does not create indexes for you beyond `@id` and `@unique`. You declare them:

```prisma
model Post {
  id         Int      @id @default(autoincrement())
  authorId   Int
  published  Boolean
  createdAt  DateTime @default(now())
  author     User     @relation(fields: [authorId], references: [id])

  @@index([authorId, published, createdAt(sort: Desc)])
  @@index([title], map: "post_title_gin", type: Gin)   // PostgreSQL index types: Hash, Gin, Gist, SpGist, Brin
}
```

**Composite column order is the whole game.** A composite index serves any query that constrains a **left-hand prefix** of its columns. `@@index([authorId, published, createdAt])` serves `where: { authorId }`, `where: { authorId, published }`, and `where: { authorId, published }, orderBy: { createdAt: 'desc' }`. It does **not** serve `where: { published }` alone. Order: equality columns first, then the range/sort column last.

**Covering index:** if every column the query touches (filter + sort + selected scalars) is in the index, the DB answers from the index alone. This is why a tight `select` and an index that includes the returned columns pay off together. PostgreSQL's `INCLUDE` clause has no Prisma attribute, so reach for a raw migration if you want a true covering index.

**Prisma does not auto-index foreign keys, and neither does every database.** MySQL/MariaDB (InnoDB) automatically create an index on the FK column. **PostgreSQL, SQL Server, SQLite and CockroachDB do not.** So on Postgres, a `@relation(fields: [authorId], ...)` gives you a constraint and no index, and `prisma.user.findUnique({ include: { posts: true } })` (or any `ON DELETE` cascade) does a sequential scan of `Post`. Add `@@index([authorId])` yourself. This is the single most common Prisma performance bug.

## 4. EXPLAIN-ing a Prisma query

There is no `.explain()`. Capture the SQL from the query log, then run it yourself.

```ts
import { PrismaClient } from "./generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({
  adapter,
  log: [{ emit: "event", level: "query" }],
});
prisma.$on("query", (e) => {
  if (e.duration > 50)
    console.log({ sql: e.query, params: e.params, ms: e.duration });
});
```

`e.query` has `$1`-style placeholders and `e.params` is a JSON array string, so substitute manually (or use `PREPARE`/`EXECUTE`):

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT "id","title" FROM "Post" WHERE "authorId" = 42 ORDER BY "createdAt" DESC LIMIT 20;
```

Alternatively `prisma.$queryRaw` the `EXPLAIN` directly, or read `prisma:engine:db_query` spans if you have OpenTelemetry wired (errors-and-debugging.md).

## 5. Pagination

**Offset (`skip`/`take`)** is straightforward and it gets more expensive as the offset grows: the database still walks and discards every skipped row, so `skip: 100000` scans 100k rows to return 20. Also unstable: inserts shift rows between pages.

```ts
const page = await prisma.post.findMany({
  skip: 20 * (n - 1),
  take: 20,
  orderBy: { id: "asc" },
});
```

**Cursor** stays flat regardless of depth, because it becomes a `WHERE id > $cursor ... LIMIT n` seek against an index:

```ts
const page = await prisma.post.findMany({
  take: 20,
  skip: 1, // skip the cursor row itself
  cursor: { id: lastSeenId },
  orderBy: { id: "asc" }, // must be stable and unique-ish
});
```

Rules: the cursor field must be unique or sequential, and the `orderBy` must match it (a non-unique sort column needs a tiebreaker, e.g. `orderBy: [{ createdAt: 'desc' }, { id: 'desc' }]`). Cursor pagination cannot jump to page 7; that is the trade.

Also: `_count` / `count()` on a large table is its own full scan. Do not ship `$transaction([findMany, count])` on a 50M-row table and call it pagination.

## 6. Bulk writes

```ts
await prisma.user.createMany({
  data: [{ email: "a@x.io" }, { email: "b@x.io" }],
  skipDuplicates: true, // NOT supported on MongoDB, SQL Server, SQLite
});
```

`createMany` sends one multi-row `INSERT` (chunked internally); a loop of `create` is one round trip per row plus one implicit transaction per row. The gap is one to two orders of magnitude on any non-local database.

`createManyAndReturn` and `updateManyAndReturn` give you the rows back but are **PostgreSQL, CockroachDB and SQLite only** (they rely on `RETURNING`), and they do not support nested relation writes.

Very large payloads hit the driver's parameter cap (P2029, "query parameter limit exceeded"); chunk to a few thousand rows. For true bulk (100k+), `COPY`/`LOAD DATA` via a raw driver beats anything the ORM will do.

## 7. Batching with `$transaction([])`

```ts
const [posts, total] = await prisma.$transaction([
  prisma.post.findMany({ where: { published: true }, take: 20 }),
  prisma.post.count({ where: { published: true } }),
]);
```

The array form ships all operations to the database in a single round trip inside one transaction, in order. It is a latency win as well as an atomicity win. You cannot feed a generated id from one operation into the next; use a nested write or an interactive transaction for that.

Interactive transactions hold a connection for their whole body:

```ts
await prisma.$transaction(
  async (tx) => {
    /* reads + writes */
  },
  {
    maxWait: 5000,
    timeout: 10000,
    isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
  },
);
```

Defaults: `maxWait` 2000ms (how long to wait for a connection from the pool), `timeout` 5000ms (how long the transaction may run). Every long interactive transaction is a connection removed from the pool, which is how you manufacture P2024 pool timeouts under load. Never `await fetch()` inside one.

Under `Serializable` (or high contention) expect **P2034** (write conflict / deadlock) and retry with backoff:

```ts
for (let i = 0; i < 5; i++) {
  try {
    await prisma.$transaction(ops, { isolationLevel: "Serializable" });
    break;
  } catch (e) {
    if (e.code === "P2034") continue;
    throw e;
  }
}
```

Wrapping `$transaction` calls in `Promise.all()` does not parallelize them: one connection executes one query at a time.

## 8. Connection pool sizing

**Who owns the pool is the whole story, and it changed in v7.**

`[v6]` the Rust query engine owned the pool and you configured it with query params on the connection string:

- default `connection_limit` = `num_physical_cpus * 2 + 1`
- default `pool_timeout` = 10s (exceeding it throws **P2024**)
- default `connect_timeout` = 5s

```bash
# [v6] only. On v7 every one of these params is silently ignored.
DATABASE_URL="postgresql://u:p@host:5432/db?connection_limit=20&pool_timeout=20&connect_timeout=10"
```

`[v7]` there is no Rust engine and no Prisma-owned pool. The **driver's** pool is the pool: `pg`'s `Pool` behind `@prisma/adapter-pg`, `mariadb`'s behind `@prisma/adapter-mariadb`, and so on. Consequences, all of which bite on the day you upgrade:

- **`connection_limit` and `pool_timeout` in `DATABASE_URL` are inert.** They do not error, they do not warn, they simply do nothing. A carefully tuned v6 URL becomes decoration.
- **The default pool size is the driver's, not Prisma's.** node-postgres defaults to `max: 10`, flat, regardless of CPU count. On a 16-core box where v6 gave you 33 connections you now get 10. **Post-upgrade P2024 pool timeouts and P2028 transaction timeouts are, in the overwhelming majority of cases, exactly this and nothing else.** Do not go hunting for a slow query first; check the adapter's `max`.
- **Timeout defaults change too.** `pg` has **no connect timeout by default (`connectionTimeoutMillis: 0`, wait forever)** where v6 gave you 5s, and its `idleTimeoutMillis` defaults to 10s.

Configure it on the adapter. Every `pg.Pool` option is accepted here:

```ts
import { PrismaClient } from "./generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
  max: 20, // <- this is your connection_limit now
  connectionTimeoutMillis: 5_000, // <- pg's default is 0 = wait forever
  idleTimeoutMillis: 30_000,
});
const prisma = new PrismaClient({ adapter });
```

You can also hand the adapter a `Pool` you built yourself (`new PrismaPg(new pg.Pool({ ... }))`), which is how you share one pool with non-Prisma code, or read `pool.totalCount` / `pool.idleCount` for the pool observability that `$metrics` used to give you.

Sizing math is unchanged: every pool must satisfy `instances * pool_size <= db_max_connections - reserved`. Postgres `max_connections` is often 100 on managed small tiers, minus superuser reservations. Serverless is still the trap: each warm lambda holds its own pool, so 50 concurrent lambdas at `max: 5` want 250 connections. The answer is an external pooler (PgBouncer in transaction mode, RDS Proxy, Prisma Accelerate) plus a pool of **1** per function (`[v7]` `max: 1` on the adapter; `[v6]` `connection_limit=1` on the URL). With PgBouncer in transaction mode, prepared statements must be off: `[v6]` `pgbouncer=true` in the URL; `[v7]` that URL flag is a driver concern, so disable them on the driver instead (for `pg`, avoid named prepared statements; several adapters expose an explicit option). Verify against your adapter's README, since this is the one place the v6 muscle memory silently misfires.

## 9. Caching

Prisma has no built-in result cache. Options:

- **Accelerate** (managed pooler + global edge cache). Extend the client and add `cacheStrategy` per query:

```ts
const posts = await prisma.post.findMany({
  where: { published: true },
  cacheStrategy: { ttl: 60, swr: 300, tags: ["published_posts"] },
});
await prisma.$accelerate.invalidate({ tags: ["published_posts"] }); // up to 5 tags per call, paid plans
```

`ttl` = seconds the cached response is fresh; `swr` = seconds a stale response may be served while it revalidates in the background. Default is no caching.

- **Your own layer:** a client extension on `$allOperations` (or a `query` extension per model) wrapping Redis is a 30-line alternative with none of the vendor coupling. See client-extensions.md.

## 10. MongoDB notes

- `relationLoadStrategy` does not exist on MongoDB; relations are always resolved with additional queries, so an `include` on a MongoDB relation is genuinely more round trips than a Postgres join.
- `skipDuplicates` on `createMany` is unsupported; `createManyAndReturn` is unsupported.
- Transactions require a **replica set** (a standalone mongod throws **P2031**).
- `@@index` maps to real Mongo indexes and is applied by `prisma db push` (there are no migration files on MongoDB); `@@fulltext` is supported.
- The `in` operator, `select` projection, and cursor pagination all behave as expected, and cursor pagination on `_id` is the natural fit.

## Gotchas

- **The findUnique dataloader batches `findUnique` only.** Swapping a resolver to `findMany({ where: { id: parent.id } })` looks equivalent and silently restores N+1.
- **Postgres does not index foreign keys.** Prisma's `@relation` creates the constraint, not the index. Every "why is this join slow" and every slow cascade delete on Postgres starts here. MySQL people never learn this because InnoDB does it for them.
- `relationLoadStrategy: 'join'` is not always faster. With a one-to-many fan-out of thousands of children per parent, the JSON aggregation and the single fat result set can lose to two clean indexed queries. Measure; `'query'` exists for a reason.
- Nested `include` is not free: each relation level adds a query (or a lateral join). `include` three levels deep on a list endpoint is a fan-out you did not intend.
- `skip`/`take` looks like `LIMIT/OFFSET` because it is. Deep offsets do not get faster because you added an index.
- `$transaction([...])` is a **batch**, not a parallel executor; and `Promise.all([tx1, tx2])` serializes rather than parallelizes.
- Interactive transactions default to a **5s** timeout and a **2s** maxWait. A slow body does not just fail, it also strands a pooled connection for the whole window.
- **`[v7]` `?connection_limit=` and `?pool_timeout=` in `DATABASE_URL` are no-ops.** They are not warnings, they are silence. The driver adapter's pool config is the only thing that counts, and its defaults differ (node-postgres `max: 10` flat, no connect timeout at all). A v6 app that ran fine on a 16-core box loses two thirds of its pool the moment it is upgraded, and reports it as "Prisma got slow".
- **`[v7]` "pool timeouts started right after the upgrade" is a pool-size bug, not a query bug.** P2024 and P2028 immediately post-upgrade are almost always the driver's default `max`, not a regression in the query compiler. Set `max` on the adapter before you profile anything.
- **`[v7]` there is no adapter-less client.** `new PrismaClient()` on a bare `DATABASE_URL`, and `datasources: { db: { url } }`, both fail. Every benchmark snippet on this page assumes an adapter was built.
- The `metrics` Preview feature (`$metrics.json` / `.prometheus()`) is **gone in v7** (deprecated 6.14.0, removed 7.0.0). Pool observability now comes from the driver's own pool object (`pool.totalCount`, `pool.idleCount`, `pool.waitingCount`) or a client extension.
- **`relationLoadStrategy` is still Preview on v7.** It is not the default and it is not GA; without `previewFeatures = ["relationJoins"]` the option does not exist, and on SQLite / SQL Server / MongoDB it never will. Anything that presents `'join'` as Prisma's normal behaviour is wrong.
- **`distinct` is not `SELECT DISTINCT`.** Prisma Client's `distinct` is **in-memory post-processing**: the database returns every matching row and the client throws duplicates away. It therefore does not reduce what crosses the wire, it interacts badly with `take` (the limit is applied before deduplication, so you can ask for 20 and get 3), and on a large table it is a full fetch dressed up as a cheap query. For real deduplication at scale use `groupBy`, or `$queryRaw` with `SELECT DISTINCT` / `DISTINCT ON`.
- `count()` and `_count` are full aggregate queries. Pairing one with every paginated `findMany` is a quiet way to make a fast page slow.
- Sibling pages: schema-and-datamodel.md (attributes), relations.md (`onDelete`, relation scalars), client-crud.md, client-extensions.md, raw-sql.md, transactions.md, migrations.md, setup-and-deploy.md (adapters, serverless), errors-and-debugging.md (P2024, P2034, query log).
