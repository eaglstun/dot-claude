---
topic_id: "v2:ACOB"
semantic_id: "-9ERoN5SeTubskotpqdi0w2IqYpjgAAH"
related_ids:
  - "8fMDMd0Tu2uK8k4Ap73C7guaJdlyIAAJ"
  - "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
---
# Prisma Transactions

Nested writes, the `$transaction` array and interactive forms, isolation levels, optimistic concurrency, and P2028/P2034.

Source:

- https://www.prisma.io/docs/orm/prisma-client/queries/transactions (nested writes, `$transaction` array + interactive forms, isolation levels, optimistic concurrency, P2034)
- https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7 (v7: Rust-free, driver adapters mandatory, `prisma-client` generator + required `output`, `Prisma.validator` removed)

Siblings: client-crud.md, raw-sql.md, client-extensions.md, performance.md

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


## 1. Transactions

Four tools, in increasing order of cost:

| Need                                          | Tool                                                        |
| --------------------------------------------- | ----------------------------------------------------------- |
| Dependent writes (parent + children)          | nested write                                                |
| Same-model batch                              | `createMany` / `updateMany` / `deleteMany` (already atomic) |
| Independent writes, no data flow between them | `$transaction([...])`                                       |
| Read-modify-write, branching logic            | `$transaction(async (tx) => ...)`                           |

### Nested writes = implicit transaction

A single `create`/`update` with nested relation writes is one transaction. It is also the only way to use a database-generated id in a dependent write, since you cannot pass a generated id between elements of a `$transaction([...])` array.

```ts
const user = await prisma.user.create({
  data: {
    email: "alice@prisma.io",
    posts: { create: [{ title: "Post 1" }, { title: "Post 2" }] },
  },
});
```

Workaround for the array form: pre-compute ids client side (`crypto.randomUUID()`), which makes the writes independent.

### Sequential array form

Queries run in array order, in one transaction, and roll back together. Everything in the array must be a `PrismaPromise` (Prisma query builders or `$queryRaw`), not an arbitrary promise.

```ts
const [posts, count] = await prisma.$transaction([
  prisma.post.findMany({ where: { title: { contains: "prisma" } } }),
  prisma.post.count(),
]);

await prisma.$transaction(
  [
    prisma.resource.deleteMany({ where: { userId } }),
    prisma.resource.createMany({ data }),
  ],
  { isolationLevel: Prisma.TransactionIsolationLevel.Serializable },
);
```

### Interactive form

```ts
import { Prisma } from "./generated/prisma/client";

const result = await prisma.$transaction(
  async (tx) => {
    const sender = await tx.account.update({
      where: { email: "alice@prisma.io" },
      data: { balance: { decrement: 100 } },
    });
    if (sender.balance < 0) throw new Error("Insufficient funds"); // throw = rollback
    return tx.account.update({
      where: { email: "bob@prisma.io" },
      data: { balance: { increment: 100 } },
    });
  },
  {
    maxWait: 5000, // how long to wait to ACQUIRE a connection/tx slot. default 2000ms
    timeout: 10000, // how long the tx body may RUN before rollback. default 5000ms
    isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
  },
);
```

`[v6]` `maxWait` was time spent waiting on **Prisma's own** Rust-engine pool. `[v7]` it is time spent waiting on the **driver's** pool (`pg`'s `Pool`, etc.), whose size you set on the adapter, not in the connection string. The knob is in a different place; the failure mode (P2028 on a busy pool) is the same. See performance.md.

Defaults can be set client-wide (Prisma 5.10+):

```ts
const prisma = new PrismaClient({
  adapter, // v7: still required alongside any other options
  transactionOptions: {
    maxWait: 5000,
    timeout: 10000,
    isolationLevel: "ReadCommitted",
  },
});
```

**The rule:** an interactive transaction holds a pooled connection open and a database row lock for its whole body. Never do slow IO inside it (no `fetch`, no Stripe call, no S3 upload, no `await sleep`). Do the network call before or after; keep the transaction to database work only. Long transactions cause pool exhaustion (see performance.md) and deadlocks.

### Isolation levels per provider

| Provider    | ReadUncommitted | ReadCommitted | RepeatableRead | Snapshot | Serializable | Default        |
| ----------- | --------------- | ------------- | -------------- | -------- | ------------ | -------------- |
| PostgreSQL  | yes             | yes           | yes            | no       | yes          | ReadCommitted  |
| MySQL       | yes             | yes           | yes            | no       | yes          | RepeatableRead |
| SQL Server  | yes             | yes           | yes            | yes      | yes          | ReadCommitted  |
| CockroachDB | no              | no            | no             | no       | yes          | Serializable   |
| SQLite      | no              | no            | no             | no       | yes          | Serializable   |

MongoDB: isolation levels do not apply.

### Optimistic concurrency control (version field)

Interactive transactions do not protect a read-then-write across separate requests. For that, carry a `version` column and make the update conditional on it. `updateMany` is used because `where` on a non-unique field is allowed there, and it returns a `count` you can test.

```ts
const seat = await prisma.seat.findFirst({
  where: { movieId, claimedBy: null },
});

const { count } = await prisma.seat.updateMany({
  where: { id: seat.id, version: seat.version }, // loses the race if version moved
  data: { claimedBy: userEmail, version: { increment: 1 } },
});
if (count === 0)
  throw new Error("That seat is already booked, please try again.");
```

### Write conflicts and retries

Under `Serializable` (and on CockroachDB generally) concurrent transactions can abort with **P2034** ("Transaction failed due to a write conflict or a deadlock"). This is expected, not a bug. Retry it:

```ts
for (let attempt = 0; attempt < 5; attempt++) {
  try {
    return await prisma.$transaction(fn, { isolationLevel: "Serializable" });
  } catch (e) {
    if (e instanceof Prisma.PrismaClientKnownRequestError && e.code === "P2034")
      continue;
    throw e;
  }
}
```

Error codes: see errors-and-debugging.md (P2028 = transaction API error / timeout, P2034 = write conflict).


## Gotchas

- **`maxWait` and `timeout` are different clocks.** `maxWait` (default 2s) is time spent waiting to _get_ a transaction; `timeout` (default 5s) is time the body may _run_. A busy pool blows the first, a slow body blows the second, and both surface as P2028.
- **Slow IO inside an interactive transaction is the single most common Prisma production incident.** An `await fetch(...)` between two writes holds a pooled connection and row locks for the duration of somebody else's network. Move it outside.
- **`Promise.all` around `$transaction` calls does not parallelize them.** One connection handles one query at a time, so they serialize, and you can deadlock yourself against your own pool.
- **`$transaction([...])` only accepts `PrismaPromise`.** A `fetch()`, an `await`ed value, or a wrapped `Promise.resolve` will not compose; the array form is not "run these promises in a transaction".
- **Interactive transactions do not stop lost updates across requests.** Read-then-write in two separate HTTP calls still needs a version field or a `SELECT ... FOR UPDATE`. Serializable helps only within one transaction, and then it hands you P2034 to retry.
- **P2034 is normal under Serializable / CockroachDB.** Code without a retry loop will look flaky under load.
- **`[v7]` `maxWait` now waits on the driver's pool, not Prisma's.** `?connection_limit=` and `?pool_timeout=` in the URL are inert; if interactive transactions start throwing P2028 right after a v7 upgrade, the cause is almost always the driver's default pool size (node-postgres `max: 10`) being smaller than what Prisma used to allocate. Fix it on the adapter (`new PrismaPg({ connectionString, max: 20 })`), not in the URL.
- **`[v7]` A driver adapter is not optional.** `new PrismaClient()` with nothing but a `DATABASE_URL`, and the old `datasources: { db: { url } }` override, both fail on v7. Any snippet on this page (or on the internet) that constructs a bare client is v6-era; add `{ adapter }`.
- **`[v7]` `import { PrismaClient } from '@prisma/client'` is wrong in new code.** The `prisma-client` generator is the default and its `output` is required, so the import path is your own source tree. Copy-pasted v6 examples will fail to resolve, or worse, resolve to a stale `@prisma/client` left over from an upgrade.
