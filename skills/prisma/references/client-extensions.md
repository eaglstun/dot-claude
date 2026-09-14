---
topic_id: "v2:EHJB"
topic_path: "prisma-orm/relations-extensions"
semantic_id: "8fMDMd0Tu2uK8k4Ap73C7guaJdlyIAAJ"
related_ids:
  - "-9ERoN5SeTubskotpqdi0w2IqYpjgAAH"
  - "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
---
# Prisma Client Extensions

`$extends` and its four components, immutability and precedence, `Prisma.defineExtension`, plus lifecycle/logging. Note `$use` middleware was REMOVED in v6.14.0.

Source:

- https://www.prisma.io/docs/orm/prisma-client/client-extensions (`$extends`, four components, immutability, `Prisma.defineExtension`, precedence)
- https://www.prisma.io/docs/orm/prisma-client/client-extensions/model (custom model methods, `$allModels`, `Prisma.getExtensionContext`)
- https://www.prisma.io/docs/orm/prisma-client/client-extensions/result (`needs` / `compute`, computed-on-access, limits)
- https://www.prisma.io/docs/orm/prisma-client/client-extensions/query (`$allModels`, `$allOperations`, raw hooks, arg/result rewriting)
- https://www.prisma.io/blog/prisma-orm-v6-14-0-relationships-for-sql-views-more-robust-management-api-and-more (`$use` middleware REMOVED in v6.14.0)
- https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7 (v7: Rust-free, driver adapters mandatory, `prisma-client` generator + required `output`, `Prisma.validator` removed)

Siblings: client-crud.md, transactions.md, raw-sql.md, errors-and-debugging.md

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


## 1. Client extensions (`$extends`)

`$extends` returns a **new, extended client**. The base client is not mutated, and the extended client shares the same connection pool. Assign the result; do not expect `prisma.$extends(...)` to change `prisma` in place.

```ts
const prisma = new PrismaClient({ adapter }).$extends(ext); // reassign or name it; the base client stays plain
```

(`adapter` is the driver adapter built at the top of this page; on v7 there is no adapter-less `new PrismaClient()` to extend.)

Four components:

### `model`: custom methods on a model

```ts
const prisma = new PrismaClient({ adapter }).$extends({
  name: "userHelpers",
  model: {
    user: {
      async signUp(email: string) {
        return prisma.user.create({ data: { email } });
      },
    },
    $allModels: {
      async exists<T>(
        this: T,
        where: Prisma.Args<T, "findFirst">["where"],
      ): Promise<boolean> {
        const ctx = Prisma.getExtensionContext(this); // ctx.$name is the model name at runtime
        const found = await (ctx as any).findFirst({ where });
        return found !== null;
      },
    },
  },
});

await prisma.user.signUp("a@b.com");
await prisma.post.exists({ title: "hi" });
```

To call one custom method from another on the same model, go through `Prisma.getExtensionContext(this)`; the outer `prisma` is not yet extended while the extension object is being defined.

### `result`: computed fields

```ts
const prisma = new PrismaClient({ adapter }).$extends({
  result: {
    user: {
      fullName: {
        needs: { firstName: true, lastName: true }, // scalars only
        compute: (user) => `${user.firstName} ${user.lastName}`, // typed from `needs`
      },
    },
  },
});
```

`needs` fields are added to the underlying SELECT automatically. Computed values are produced **on access** (a getter), not on retrieval.

### `query`: hooks around every query

```ts
const softDelete = Prisma.defineExtension({
  name: "softDelete",
  query: {
    post: {
      async delete({ args, query }) {
        // rewrite delete -> update
        return prisma.post.update({ ...args, data: { deleted: true } });
      },
      async findMany({ args, query }) {
        args.where = { ...args.where, deleted: false };
        return query(args);
      },
    },
    $allModels: {
      async $allOperations({ model, operation, args, query }) {
        const start = performance.now();
        const result = await query(args);
        console.log(
          `${model}.${operation} took ${performance.now() - start}ms`,
        );
        return result;
      },
    },
  },
});
const prisma = new PrismaClient({ adapter }).$extends(softDelete);
```

Callback receives `{ model, operation, args, query }`. `model` is `undefined` for top-level raw ops, which you hook under `$allOperations` alongside `$queryRaw`, `$executeRaw`, `$queryRawUnsafe`, `$executeRawUnsafe` (or `$runCommandRaw` on MongoDB). `args` is mutable except for `include` and `select`. You may transform the awaited result, but prefer a `result` extension for that (it is lazier and cheaper).

### `client`: top-level methods

```ts
const prisma = new PrismaClient({ adapter }).$extends({
  client: {
    $log: (s: string) => console.log(s),
    async $totalUsers() {
      const ctx = Prisma.getExtensionContext(this);
      return (ctx as any).user.count();
    },
  },
});
```

### Sharing and combining

`Prisma.defineExtension` gives you a typed, reusable extension in its own file (and is how extension packages ship). Chain with `.$extends(a).$extends(b)`; on conflict the **last** extension declared wins, and chained `query` hooks run first-in-first-out.

### `$use` is gone

`prisma.$use()` middleware was deprecated in 4.16.0 and **removed entirely in v6.14.0**. Translation is mechanical:

```ts
// before (removed)
prisma.$use(async (params, next) => {
  if (params.model === "Post" && params.action === "delete") {
    params.action = "update";
    params.args.data = { deleted: true };
  }
  return next(params);
});

// after
prisma.$extends({
  query: {
    post: {
      delete: ({ args, query }) =>
        prisma.post.update({ ...args, data: { deleted: true } }),
    },
  },
});
```

`params.model` -> `model`, `params.action` -> `operation` (per-key, so you usually do not branch on it), `next(params)` -> `query(args)`.


## 2. Lifecycle and logging (brief)

```ts
const prisma = new PrismaClient({
  adapter,
  log: [{ emit: "event", level: "query" }],
});
prisma.$on("query", (e) => console.log(e.query, e.params, `${e.duration}ms`));
```

`$on('query')` requires `emit: 'event'` in `log`; details and the caveats (params redaction, no events on an extended client instance you did not attach to) are in errors-and-debugging.md.

`$connect()` is optional: the first query connects lazily. Call `$disconnect()` in short-lived processes (scripts, serverless teardown, tests) so the process can exit; do not call it after every request in a long-lived server (see performance.md and setup-and-deploy.md).


## Gotchas

- **Extensions are immutable.** `prisma.$extends(x)` returns a new client; if you ignore the return value nothing happens. Also, `$on` and `$connect` semantics attach to the instance you called them on, so extend first, then wire up.
- **`result` computed fields cannot be used in `where`, `orderBy`, or aggregations, and cannot depend on relations.** They are scalar-only, computed in JS on property access.
- **`$use` middleware no longer exists (removed in 6.14.0).** Any tutorial or library still calling `prisma.$use` is pre-6.14 and will throw at runtime.
- **`[v7]` `Prisma.validator` was removed.** Extension args and select/include literals are typed with `satisfies` now (see errors-and-debugging.md); `Prisma.Args` / `Prisma.Result` / `Prisma.Payload` / `Prisma.getExtensionContext` all survive unchanged.
- **`[v7]` Extensions are the only interception layer, and `metrics` is gone.** With `$use` removed and `$metrics` deleted in 7.0.0, a `query` extension on `$allOperations` is now the only place to hang timing, tracing, or pool instrumentation of your own.
- **`[v7]` A driver adapter is not optional.** `new PrismaClient()` with nothing but a `DATABASE_URL`, and the old `datasources: { db: { url } }` override, both fail on v7. Any snippet on this page (or on the internet) that constructs a bare client is v6-era; add `{ adapter }`.
- **`[v7]` `import { PrismaClient } from '@prisma/client'` is wrong in new code.** The `prisma-client` generator is the default and its `output` is required, so the import path is your own source tree. Copy-pasted v6 examples will fail to resolve, or worse, resolve to a stale `@prisma/client` left over from an upgrade.
