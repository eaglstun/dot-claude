---
topic_id: "v2:EJOG"
topic_path: "prisma-orm/types-performance"
semantic_id: "vuSYYOfQOrEb5t4BuqFT05nalb7KMAAB"
related_ids:
  - "-_KQAPYRG7Gb5p4YMqeT0c36l6zAEAAA"
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
---
# Prisma: Types, Errors, and Debugging

Source:

- https://www.prisma.io/docs/orm/reference/error-reference (the canonical error-code list: P1xxx common, P2xxx query engine, P3xxx migrate, P4xxx introspect, P5xxx/P6xxx Accelerate)
- https://www.prisma.io/docs/orm/prisma-client/debugging-and-troubleshooting/handling-exceptions-and-errors (instanceof narrowing, `e.code`)
- https://www.prisma.io/docs/orm/prisma-client/debugging-and-troubleshooting/debugging (the `DEBUG` env var namespaces)
- https://www.prisma.io/docs/orm/prisma-client/observability-and-logging/logging (`log` config, stdout vs event, `$on('query')`)
- https://www.prisma.io/docs/orm/prisma-client/observability-and-logging/opentelemetry-tracing (`@prisma/instrumentation`, span names)
- https://www.prisma.io/docs/orm/prisma-client/type-safety (generated input/select types, `Exact`/`Args`/`Result`/`Payload`)
- https://www.prisma.io/docs/orm/prisma-client/type-safety/operating-against-partial-structures-of-model-types (`GetPayload` + `satisfies`)
- https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7 (v7: driver adapters required, metrics removed, generated client output path required)

**Version note:** the current line is **Prisma ORM v7** (v7.0.0 shipped 2025-11-19; `prisma@7.8.0` is `latest` on npm as of July 2026, `6.19.2` is tagged `prev`). Three things on this page turn on that: v7 is Rust-free (TypeScript query compiler, **no query engine binary**), so the whole family of "Query engine binary not found" / `binaryTargets` / alpine-musl deployment errors **cannot occur** and is a v6-and-earlier diagnosis; `Prisma.validator` was **removed** (use `satisfies`); and the `metrics` Preview feature was **removed** in 7.0.0. A driver adapter is also mandatory, so connection-level failures (P1000, P1001, P1017) now surface through the **driver's** error path. v6-only deltas are marked `[v6]`. See setup-and-deploy.md.

## 1. Where the types come from

With the `prisma-client` generator you import from your own source tree, not `@prisma/client`:

```prisma
generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}
```

```ts
import { PrismaClient, Prisma } from "../generated/prisma/client";
import type { User, Post } from "../generated/prisma/client";
```

`Prisma` is the namespace holding every generated input/output type; the model types (`User`) are the plain scalar shape only (no relations).

## 2. The generated type surface

Per model, per operation, Prisma emits:

- `Prisma.UserCreateInput` / `Prisma.UserUncheckedCreateInput` (the "checked" form takes nested relation writes like `posts: { create: ... }`; the "unchecked" form lets you set the raw FK scalar, e.g. `authorId`)
- `Prisma.UserUpdateInput`, `Prisma.UserWhereInput`, `Prisma.UserWhereUniqueInput`, `Prisma.UserOrderByWithRelationInput`
- `Prisma.UserSelect`, `Prisma.UserInclude`, `Prisma.UserDefaultArgs`
- `Prisma.UserGetPayload<T>`: turns an args object into the actual result type
- Enums as both a value object and a type; `Prisma.ModelName`, `Prisma.SortOrder`, `Prisma.TransactionIsolationLevel`

```ts
const userEmail: Prisma.UserSelect = { email: true };
```

### 2a. Deriving a result type with `satisfies` (the current idiom)

```ts
const userWithPosts = {
  include: { posts: { select: { id: true, title: true } } },
} satisfies Prisma.UserDefaultArgs;

type UserWithPosts = Prisma.UserGetPayload<typeof userWithPosts>;
// -> User & { posts: { id: number; title: string }[] }

const users: UserWithPosts[] = await prisma.user.findMany(userWithPosts);
```

`satisfies` type-checks the literal without widening it, so `typeof` still sees the exact shape. It is the only idiom on v7.

### 2b. `Prisma.validator` is REMOVED in v7

`[v7]` `Prisma.validator` no longer exists. `[v6]` it was the older way to get the same check:

```ts
// [v6] only. On v7 this is a TypeError: Prisma.validator is not a function.
const userSelect = Prisma.validator<Prisma.UserSelect>()({
  id: true,
  email: true,
});
// client-bound form: inferred the model + operation for you
const args = Prisma.validator(
  prisma,
  "user",
  "findMany",
  "select",
)({ email: true });
```

The mechanical port is `satisfies` plus the matching generated args type:

```ts
// [v7]
const userSelect = { id: true, email: true } satisfies Prisma.UserSelect;
const args = { select: { email: true } } satisfies Prisma.UserFindManyArgs;
```

### 2c. Type utilities (the `$inferType`-shaped helpers)

Prisma does not have a `$inferType`; the equivalents are four generics in the `Prisma` namespace:

```ts
// input args of an operation
type PostCreateBody = Prisma.Args<typeof prisma.post, "create">["data"];
// result of an operation given args
type PostResult = Prisma.Result<
  typeof prisma.post,
  { include: { author: true } },
  "findFirst"
>;
// full payload (scalars vs relations, used by extensions)
type PostPayload = Prisma.Payload<typeof prisma.post, "findMany">;
// exact-shape enforcement, no excess properties
function q<T extends Prisma.Exact<T, Prisma.UserFindManyArgs>>(args: T) {
  /* ... */
}
```

### 2d. Deriving from the query itself

For a function that already does the query, skip Prisma types entirely:

```ts
async function getUsersWithPosts() {
  return prisma.user.findMany({ include: { posts: true } });
}
type UsersWithPosts = Awaited<ReturnType<typeof getUsersWithPosts>>;
```

See client-extensions.md for how `Args`/`Result`/`Payload` are used inside `$extends`.

## 3. The error classes

All exported from the generated client's `Prisma` namespace.

| Class                             | When                                                                                                                                                                              | Key props                                  |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `PrismaClientKnownRequestError`   | The engine returned a code you can branch on                                                                                                                                      | `code`, `meta`, `message`, `clientVersion` |
| `PrismaClientUnknownRequestError` | Engine failed, no code assigned                                                                                                                                                   | `message`, `clientVersion`                 |
| `PrismaClientRustPanicError`      | `[v6]` the Rust engine panicked; the process is untrusted, restart it. `[v7]` Rust-free, so this class still exists in the type surface but essentially never fires               | `message`, `clientVersion`                 |
| `PrismaClientInitializationError` | Thrown on first connect: bad URL, unreachable DB, version mismatch. `[v6]` also "missing/incompatible query engine binary"; `[v7]` also a missing or misconfigured driver adapter | `errorCode`, `message`, `clientVersion`    |
| `PrismaClientValidationError`     | Your query args are wrong (missing field, unknown field, bad type). No `code` property                                                                                            | `message`, `clientVersion`                 |

Narrowing:

```ts
import { Prisma } from "../generated/prisma/client";

try {
  await prisma.user.create({ data: { email } });
} catch (e) {
  if (e instanceof Prisma.PrismaClientKnownRequestError) {
    if (e.code === "P2002") {
      // e.meta?.target -> the failing constraint / field list
      const target = (e.meta?.target as string[] | undefined) ?? [];
      throw new ConflictError(`Already taken: ${target.join(", ")}`);
    }
    if (e.code === "P2025") throw new NotFoundError();
  }
  if (e instanceof Prisma.PrismaClientValidationError) {
    // programmer error, not user error: 500, not 400
  }
  throw e;
}
```

`PrismaClientValidationError` has **no** `code`, so `e.code === '...'` silently never matches for it. Branch on the class first, always.

## 4. Error codes you actually hit

Verified against the error reference.

| Code  | Meaning                                                                                                                                             | Usual fix                                                                                                                            |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| P1000 | Authentication failed against database server (bad user/password)                                                                                   | Fix credentials; URL-encode special chars in the password                                                                            |
| P1001 | Can't reach database server at host:port                                                                                                            | DB down, wrong host/port, SG/firewall, missing `sslmode`                                                                             |
| P1002 | Database server timed out (reachable, did not answer in time)                                                                                       | Network/latency; raise `connect_timeout`; check DB load                                                                              |
| P1008 | Operations timed out after `{time}`                                                                                                                 | Slow query, or pool starvation. Fix the query, or raise the timeout (`[v7]` on the driver, not `?pool_timeout=`; see performance.md) |
| P1012 | Schema validation error (thrown by `prisma validate`/`generate`/`migrate`, not at runtime)                                                          | Fix schema.prisma: missing relation scalar, bad attribute, reserved name                                                             |
| P1017 | Server has closed the connection                                                                                                                    | Idle timeout, PgBouncer/proxy killing the conn, DB restart. Reconnect/retry; check pooler idle settings                              |
| P2002 | Unique constraint failed on `{constraint}`                                                                                                          | Upsert, or catch and return 409. `e.meta.target` names the field(s)                                                                  |
| P2003 | Foreign key constraint failed on field `{field_name}`                                                                                               | Parent row missing or a delete violates the FK. Check ordering, or set `onDelete` (relations.md)                                     |
| P2005 | Invalid value stored in database for field (DB value cannot be coerced to the schema type)                                                          | Schema drift: column type diverged from schema, or a NULL/garbage row. Introspect and reconcile                                      |
| P2011 | Null constraint violation on `{constraint}`                                                                                                         | You wrote `null`/omitted a required column. Make the field optional or supply a value/default                                        |
| P2014 | The change would violate the required relation between models                                                                                       | You tried to disconnect/delete a parent that a required child points at. Delete children, make the relation optional, or cascade     |
| P2015 | A related record could not be found                                                                                                                 | A nested `connect`/`update` targeted a row that does not exist                                                                       |
| P2018 | The required connected records were not found                                                                                                       | Nested write's `connect` filter matched nothing                                                                                      |
| P2021 | The table does not exist in the current database                                                                                                    | Migrations not applied, wrong schema/search_path, wrong DB                                                                           |
| P2022 | The column does not exist in the current database                                                                                                   | Schema drift: you generated a client ahead of the applied migration                                                                  |
| P2024 | Timed out fetching a new connection from the connection pool                                                                                        | Pool starvation. `[v6]` raise `connection_limit`/`pool_timeout` on the URL; `[v7]` raise the driver adapter's `max` (performance.md) |
| P2025 | An operation failed because it depends on one or more records that were required but not found                                                      | `update`/`delete`/`findUniqueOrThrow` on a missing row. Use `upsert` or catch it as a 404                                            |
| P2028 | Transaction API error `{error}` (most often "Transaction already closed": the tx exceeded `timeout`, or `maxWait` expired waiting for a connection) | Shorten the transaction body, move network IO out of it, or raise `timeout`/`maxWait`. Check pool size (transactions.md)          |
| P2029 | Query parameter limit exceeded                                                                                                                      | A `createMany`/`IN (...)` payload blew the driver's bind-parameter cap. Chunk the batch                                              |
| P2031 | MongoDB needs to be run as a replica set to use transactions                                                                                        | Standalone `mongod` cannot do transactions. Use a replica set or Atlas                                                               |
| P2034 | Transaction failed due to a write conflict or a deadlock                                                                                            | Retry the transaction with backoff (transactions.md)                                                                   |
| P2037 | Too many database connections opened                                                                                                                | The database, not Prisma, refused. Shrink pools, count instances, or put a pooler in front (performance.md)                          |
| P3005 | The database schema is not empty                                                                                                                    | Baseline: `prisma migrate resolve --applied <migration>` (migrations.md)                                                             |
| P3006 | Migration failed to apply cleanly to the shadow database                                                                                            | The migration is not replayable from scratch, or shadow DB perms are missing                                                         |
| P3009 | Failed migrations found in the target database; new migrations will not be applied                                                                  | `prisma migrate resolve --rolled-back <name>` (or `--applied`), then fix and redeploy                                                |
| P3018 | A migration failed to apply; new migrations cannot be applied                                                                                       | Same family as P3009: repair the failed migration state, do not just re-run `deploy`                                                 |

Other codes worth knowing: **P2000** (value too long for the column type), **P2001** (record searched for in the `where` condition does not exist: rarer than people think, see Gotchas), **P2010** (raw query failed, carries the driver's own message), **P1003** (database file/schema does not exist), **P1010** (user denied access), **P1011** (TLS error), **P1013** (invalid connection string), **P1014** (the underlying table/view for a model does not exist), **P1015** (DB version does not support a schema feature), **P1016** (raw query given the wrong number of parameters).

Every code above is in the published error reference; if a code is not on that page, it is not a Prisma code. There are no engine-binary error codes on v7, because there is no engine binary (see Gotchas).

## 5. Logging

```ts
import { PrismaClient } from "../generated/prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });

const prisma = new PrismaClient({
  adapter, // v7: mandatory, on every client you construct
  log: ["query", "info", "warn", "error"], // shorthand: all to stdout
});
```

Levels: `query`, `info`, `warn`, `error`. Expanded form picks the sink per level:

```ts
const prisma = new PrismaClient({
  adapter,
  log: [
    { emit: "event", level: "query" },
    { emit: "stdout", level: "warn" },
    { emit: "stdout", level: "error" },
  ],
});

prisma.$on("query", (e) => {
  console.log(e.query); // the SQL, with $1, $2 placeholders
  console.log(e.params); // the bound params, as a JSON string
  console.log(e.duration); // ms
});
```

That `e.query` + `e.params` pair is how you get real SQL to paste into `EXPLAIN ANALYZE` (see performance.md).

Typing note: with an inline `log` array TypeScript infers which events `$on` accepts. If you build the options object separately, type it `Prisma.PrismaClientOptions` or use `as const`, or `$on('query')` will not typecheck.

## 6. DEBUG and `prisma debug`

```bash
export DEBUG="prisma:client"            # client runtime
export DEBUG="prisma:engine"            # [v6] the Rust engine layer; on v7 there is no engine process to trace
export DEBUG="prisma:client,prisma:engine"
export DEBUG="prisma*"                  # everything prisma
export DEBUG="*"                        # everything, very loud
```

`[v7]` the query compiler runs in-process, so `prisma:client` (plus your driver's own debug output, e.g. `DEBUG=pg`) is where the useful signal is; `prisma:engine` no longer has a separate binary behind it.

`npx prisma debug` prints a diagnostic dump (Prisma versions, resolved schema path, env vars it sees such as `DATABASE_URL`/`PRISMA_*`, platform info). It is the first thing to run when "it works locally but not in CI/Docker".

## 7. Tracing and metrics

Tracing is **stable since 6.1.0** (before that it needed `previewFeatures = ["tracing"]`). No schema flag now; just register the instrumentation:

```ts
import {
  PrismaInstrumentation,
  registerInstrumentations,
} from "@prisma/instrumentation";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";

const provider = new NodeTracerProvider({
  spanProcessors: [
    /* ... */
  ],
});
registerInstrumentations({
  tracerProvider: provider,
  instrumentations: [new PrismaInstrumentation()],
});
provider.register();
```

Spans emitted: `prisma:client:operation` (parent) wrapping `prisma:client:serialize` and `prisma:engine:query`, which wraps `prisma:engine:connection`, `prisma:engine:db_query` (the actual SQL, as a span attribute), and `prisma:engine:serialize`.

Metrics: the `metrics` Preview feature (`prisma.$metrics.json()` / `$metrics.prometheus()`, pool gauges and query counters) was **deprecated in 6.14.0 and removed in 7.0.0**. On v7 get pool stats from the driver adapter's underlying pool (for example `pg`'s `pool.totalCount`/`idleCount`) or from a client extension.

## Gotchas

- `PrismaClientValidationError` has no `.code`. Code that only does `if (e.code === 'P2002')` will treat a malformed query as an unknown error and often as a 500-with-no-detail. Narrow by class first.
- **P2025 vs P2001.** `update`/`delete` on a missing row throws **P2025**, not P2001. P2001 ("record searched for in the where condition does not exist") is far rarer than memory suggests.
- `e.meta` is typed `unknown`-ish (`Record<string, unknown> | undefined`). `e.meta.target` is a `string[]` on PostgreSQL but the **constraint name as a string** on MongoDB and on some MySQL cases. Cast defensively; do not build user-facing copy off it without a fallback.
- P2002 is not only about your `@unique` fields: it also fires on unique indexes Prisma does not know about, and on the primary key. The remedy for a "check then insert" race is `upsert` or a caught P2002, never a pre-flight `findUnique`.
- **P2024 (pool timeout) is not a database problem.** It means requests are queueing on the client-side pool: `[v6]` Prisma's own Rust-engine pool, `[v7]` the driver adapter's pool. It shows up in serverless because every warm lambda holds its own pool, and it shows up right after a v7 upgrade because node-postgres defaults to `max: 10` where Prisma used to compute `num_cpus * 2 + 1`. See performance.md.
- P1017 ("server has closed the connection") is usually a pooler (PgBouncer/RDS Proxy) or an idle timeout, not a crash. Prisma does not transparently retry it, so a long-idle client's first query after a lull can fail once.
- `$on('query')` prints the SQL with `$1`-style placeholders and the params as a **separate JSON string**, not interpolated. Do not paste `e.query` straight into psql expecting it to run.
- **`[v7]` "Query engine binary not found" is not a v7 error. It cannot happen.** The whole classic deployment saga (`binaryTargets`, `linux-musl-openssl-3.0.x` on Alpine, `PRISMA_QUERY_ENGINE_LIBRARY`, `PRISMA_CLI_QUERY_ENGINE_TYPE`, engine downloads blocked by a corporate proxy, a `.prisma/client` copied into a Lambda bundle without its `.node` file) belongs to **v6 and earlier**. v7 is Rust-free: the query compiler is TypeScript, there is no binary to target, download, or fail to find. If you are hitting one of these, you are on 6.x, and the fix is the v6 fix (`binaryTargets = ["native", "linux-musl-openssl-3.0.x"]`) or an upgrade. `PrismaClientRustPanicError` likewise survives in the type surface but essentially never fires.
- **`[v7]` a missing driver adapter is the new version of that error.** `new PrismaClient()` with only a `DATABASE_URL`, or a `datasources: { db: { url } }` override, throws `PrismaClientInitializationError` on v7. The class is the same one that used to mean "missing engine", so a stale StackOverflow answer will send you looking for a binary that does not exist. Build the adapter (`new PrismaPg({ connectionString })`) and pass it.
- **`[v7]` `Prisma.validator` is removed.** It is a runtime `TypeError`, not a type error, so a `Prisma.validator<...>()` call copied out of a v6 tutorial compiles and then dies at import time. Port it to `satisfies` (section 2b).
- **`[v7]` `$metrics` is removed.** `prisma.$metrics.json()` / `.prometheus()` and the `metrics` preview flag were deprecated in 6.14.0 and deleted in 7.0.0. A schema still carrying `previewFeatures = ["metrics"]` will fail validation. Pool observability comes from the driver's pool now.
- **`[v7]` connection-level errors originate in the driver.** P1000/P1001/P1017 still surface as Prisma codes, but the underlying `pg`/`mariadb` error is what actually fired, and driver-specific settings (TLS, `keepAlive`, `statement_timeout`) live on the adapter, not in the Prisma connection string.
- The migrate codes are not runtime codes. P1012 (schema validation), P3005/P3006/P3009/P3018 come from the CLI and schema engine; you will never catch them in application `try/catch`.
- Logging `query` on stdout in production is a data-leak vector: params include PII. Use `emit: 'event'` and redact, or log only `duration` above a threshold.
