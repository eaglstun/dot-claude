---
topic_id: "v2:EBKF"
topic_path: "prisma-orm/client-setup"
semantic_id: "E_GIuHaDOUEbIs4TYLHScUWZl4DIoAAA"
related_ids:
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
  - "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
---
# Prisma: Setup and Deployment

**Status check (July 2026): the current release line is Prisma ORM v7 (`prisma@7.8.0` is `latest` on npm; `6.19.2` is tagged `prev`).** v7 landed 2025-11-19 and changed the setup story substantially: the Rust query engine is gone, driver adapters are mandatory, the `prisma-client` generator is the default, and `prisma.config.ts` is the config home. Anything you remember about `prisma-client-js`, `binaryTargets`, and `engineType` describes v6 and earlier. Both stories are covered below because plenty of production code is still on 6.x.

Source:

- https://www.prisma.io/docs/orm/prisma-schema/overview/generators (generator reference: `prisma-client` vs `prisma-client-js`, `output`, `runtime`, `moduleFormat`)
- https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7 (v7 breaking changes, authoritative)
- https://www.prisma.io/blog/announcing-prisma-orm-7-0-0 (v7 announcement: Rust-free, bundle size, defaults)
- https://www.prisma.io/changelog/2025-11-19 (v7.0.0 changelog: Rust-free client becomes the default)
- https://www.prisma.io/docs/orm/reference/prisma-config-reference (`prisma.config.ts` fields, no auto `.env` loading)
- https://www.prisma.io/docs/getting-started/setup-prisma/start-from-scratch/relational-databases-typescript-postgresql (install + `prisma init` flags, generated files)
- https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/generating-prisma-client (when to re-run `prisma generate`)
- https://www.prisma.io/docs/orm/overview/databases/database-drivers (driver adapters, adapter packages)
- https://www.prisma.io/docs/orm/reference/supported-databases (provider/version matrix)
- https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections (serverless connection exhaustion, `globalThis` singleton, poolers)
- https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections/connection-pool (`connection_limit`, `pool_timeout`, adapter pool defaults)
- https://www.prisma.io/docs/orm/prisma-client/deployment/deploy-prisma (traditional vs serverless vs edge)
- https://www.prisma.io/docs/orm/prisma-client/deployment/edge/overview (edge constraints, HTTP vs TCP drivers)
- https://www.prisma.io/docs/orm/prisma-client/deployment/edge/deploy-to-cloudflare (Workers specifics)
- https://www.prisma.io/docs/orm/prisma-client/deployment/serverless/deploy-to-vercel (the dependency-cache trap)
- https://www.prisma.io/docs/guides/docker (Docker images, alpine/musl, OpenSSL)
- https://www.prisma.io/docs/orm/prisma-client/deployment/deploy-database-changes-with-prisma-migrate (`migrate deploy` in CI)
- https://www.prisma.io/docs/accelerate (managed pool + global cache)

Siblings: schema-and-datamodel.md, migrations.md, performance.md, errors-and-debugging.md

## 1. Install and init

Two packages, two roles. `prisma` is the CLI (dev dependency). `@prisma/client` is the runtime library (regular dependency). On v7 you also need a **driver adapter package plus the underlying JS driver**, because the client no longer speaks to the database itself.

```bash
# v7, PostgreSQL via node-postgres
npm install prisma @types/pg --save-dev
npm install @prisma/client @prisma/adapter-pg pg dotenv

npx prisma init --datasource-provider postgresql --output ../generated/prisma
```

`prisma init` writes three files:

- `prisma/schema.prisma` (datasource + generator + models)
- `prisma.config.ts` (CLI config; new in the v6.x tail, the default in v7)
- `.env` (project root, **not** inside `prisma/`, holding `DATABASE_URL`)

The generated schema on v7 is thinner than you expect, because the connection URL moved out of it:

```prisma
generator client {
  provider = "prisma-client"
  output   = "../generated/prisma"
}

datasource db {
  provider = "postgresql"
}
```

### prisma.config.ts

Real, current, and the recommended home for CLI configuration. It replaces the `url` / `directUrl` / `shadowDatabaseUrl` fields in the `datasource` block and the `prisma.seed` key in `package.json`.

```ts
import "dotenv/config";
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "tsx prisma/seed.ts",
  },
  datasource: {
    url: env("DATABASE_URL"),
    // shadowDatabaseUrl: env("SHADOW_DATABASE_URL"),
  },
});
```

Critical behavior change: **once `prisma.config.ts` exists, the CLI stops auto-loading `.env`.** That `import "dotenv/config"` line is not decorative; drop it and `env("DATABASE_URL")` resolves to undefined. (Bun loads `.env` natively, so it is the one runtime that gets away without it.) Your application code also has to load `.env` itself; `@prisma/client` never did that, the CLI did.

Fields that exist: `schema`, `migrations`, `datasource`, `views`, `typedSql`, `experimental`. Fields **removed in v7**: `adapter`, `engine`, `studio`, `directUrl`. The adapter now lives only in your app code (see section 5).

## 2. Generators: `prisma-client` vs `prisma-client-js`

This is the part most people get wrong from memory.

### `prisma-client` (default and recommended, GA since 6.16.0)

```prisma
generator client {
  provider               = "prisma-client"
  output                 = "../src/generated/prisma"  // REQUIRED
  runtime                = "nodejs"   // nodejs | deno | bun | workerd | vercel-edge | react-native
  moduleFormat           = "esm"      // esm | cjs
  generatedFileExtension = "ts"
  importFileExtension    = "ts"
}
```

- `output` is **mandatory**. There is no default. Omitting it is a hard error.
- Emits plain TypeScript into your source tree, split across multiple files (tree-shakeable, greppable, debuggable, and visible to your editor's go-to-definition).
- `runtime` targets the JS host, which is how edge support works now.
- Nothing is written to `node_modules/.prisma`.

Import from the output path, not from the package:

```ts
import { PrismaClient } from "../generated/prisma/client";
```

### `prisma-client-js` (legacy, deprecated)

```prisma
generator client {
  provider      = "prisma-client-js"
  binaryTargets = ["native", "debian-openssl-3.0.x"]
  previewFeatures = ["driverAdapters"]
}
```

Generates into `node_modules/.prisma/client` and re-exports through `@prisma/client`, which is why `import { PrismaClient } from "@prisma/client"` used to work with zero configuration. It carries the Rust query engine binary, which is the entire source of the `binaryTargets` and "engine not found" class of deployment pain. Deprecated in v7.

### Migrating between them

1. Change `provider` to `"prisma-client"` and add an `output` path.
2. Rewrite every `from "@prisma/client"` import to the output path. Enums, `Prisma` namespace types, and `PrismaClient` all move.
3. Add the generated directory to `.gitignore` (or commit it deliberately; see section 4).
4. Drop `binaryTargets`, `engineType`, and the `driverAdapters` / `queryCompiler` preview flags. They are no longer flags.
5. Add a driver adapter (section 5). Passing `datasources: { db: { url } }` to `new PrismaClient()` no longer connects to anything.
6. If your project is CJS, set `moduleFormat = "cjs"`. v7 is ESM-first; the generator will happily emit ESM into a CJS project and you get a `require() of ES Module` explosion at runtime.

**For a new project in 2026: `prisma-client`, unconditionally.** `prisma-client-js` is deprecated and exists for migration only.

## 3. `prisma generate`

Regenerate the client whenever the shape of the client could change:

- after editing `schema.prisma` (models, enums, `@@map`, anything)
- after editing generator config
- after `prisma migrate dev` / `db pull` (these run generate for you)
- after pulling a branch where someone else touched the schema
- after `npm install`, if the generated output is not committed

The last one is the CI killer. Generated output that lives in `node_modules` (v6) or in a gitignored `src/generated` (v7) does not exist in a fresh checkout.

```json
{
  "scripts": {
    "postinstall": "prisma generate",
    "vercel-build": "prisma generate && prisma migrate deploy && next build"
  }
}
```

**The Vercel dependency-cache trap:** Vercel caches `node_modules` between builds. If your only trigger for `prisma generate` is `npm install`, and the install is served entirely from cache, `postinstall` never fires and you ship an **outdated client that does not match your schema**. You get type errors at build time in the good case and `Unknown field` / `Unknown argument` runtime errors in the bad one. Fix by putting `prisma generate` in an explicit build step (`vercel-build` above), not only in `postinstall`. With the v7 generator the risk is smaller because the output is inside your repo rather than in the cached `node_modules`, but the failure mode remains if the generated dir is gitignored.

Related trap: `prisma` is a devDependency, and some platforms prune devDependencies before the build or the release step. If you see `prisma: command not found` during a Vercel/Heroku build, or `migrate deploy` cannot run at release, move `prisma` into `dependencies`.

## 4. Databases, providers, and driver adapters

Datasource `provider` values: `postgresql`, `mysql`, `sqlite`, `sqlserver`, `mongodb`, `cockroachdb`. Version floors worth knowing: PostgreSQL 9.6 to 18, MySQL 5.6/5.7/8.0/8.4, MariaDB 10+, SQL Server 2017/2019/2022, MongoDB 4.2+, CockroachDB 21.2.4+.

A **driver adapter** is a thin translation layer between Prisma Client and an ordinary JavaScript database driver. Historically Prisma opened its own TCP connections from a Rust binary and the JS driver ecosystem was bypassed entirely. Now Prisma compiles your query to SQL in TypeScript/WASM (the **query compiler**) and hands it to a driver you chose and configured. That is what makes edge runtimes, HTTP-based serverless drivers, and per-driver pool tuning possible.

```ts
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
export const prisma = new PrismaClient({ adapter });
```

| Adapter package                  | Driver / target                                        |
| -------------------------------- | ------------------------------------------------------ |
| `@prisma/adapter-pg`             | `pg` (node-postgres), any Postgres, TCP                |
| `@prisma/adapter-neon`           | Neon serverless driver (HTTP/WS), also Vercel Postgres |
| `@prisma/adapter-planetscale`    | PlanetScale serverless driver (HTTP)                   |
| `@prisma/adapter-libsql`         | libSQL / Turso (HTTP or local file)                    |
| `@prisma/adapter-d1`             | Cloudflare D1                                          |
| `@prisma/adapter-better-sqlite3` | local SQLite via `better-sqlite3`                      |
| `@prisma/adapter-mariadb`        | MySQL and MariaDB via `mariadb`                        |
| `@prisma/adapter-mssql`          | SQL Server via `node-mssql`                            |
| `@prisma/adapter-ppg`            | Prisma Postgres                                        |

Community adapters exist for TiDB Cloud and PGlite. **MongoDB is the exception**: it keeps its own driver and its own internal pool, configured through connection-string parameters.

### queryCompiler / "Rust-free" status

**GA and no longer preview.** The Rust-free client shipped GA in 6.16.0 and became the **default** in 7.0.0. If you still carry `previewFeatures = ["queryCompiler", "driverAdapters"]` in a schema, delete both; on v7 they are meaningless. The payoff: no engine binary in the bundle (roughly 14 MB down to 1.6 MB), no cross-language serialization hop, and materially faster queries. The cost: driver adapters are now required rather than optional, and pool defaults changed underneath you (section 5).

## 5. Connection management

### The pool

On v6 the Rust engine owned the pool and you tuned it through URL parameters: `connection_limit` (default `num_cpus * 2 + 1`) and `pool_timeout` (default 10s).

```
postgresql://user:pw@host:5432/db?connection_limit=5&pool_timeout=20
```

On v7 **the driver owns the pool**, so those URL parameters are inert and you configure the driver instead. Defaults are lower and no longer scale with CPU count:

```ts
const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
  max: 10, // pg default 10 (v6 would have computed ~17 on an 8-core box)
  idleTimeoutMillis: 10_000,
  connectionTimeoutMillis: 0, // pg default: wait forever
});
```

`mariadb` uses `connectionLimit` (10) / `acquireTimeout` (10s); `mssql` uses `pool.max` (10) / `connectionTimeout` (15s). A v6 app that quietly relied on a 17-connection pool will start throwing pool timeouts after the upgrade with no code change. See errors-and-debugging.md for what those look like.

### The serverless problem

Every warm function instance holds its own client and therefore its own pool. Twenty concurrent Lambdas at `max: 10` is 200 connections against a Postgres box that allows 100. The mitigations, in order of preference:

1. Instantiate the client **outside** the handler so warm invocations reuse it.
2. Shrink the per-instance pool hard (`max: 1` to `3`).
3. Put an external pooler in front of the database.

### The `globalThis` singleton (Next.js dev)

Hot reload re-evaluates modules and leaks a new client per reload until the database refuses connections. Cache on `globalThis`, which survives HMR:

```ts
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../generated/prisma/client";

const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }),
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
```

Guard the assignment on non-production so serverless production instances do not pin a stale client.

### External poolers (PgBouncer, Supabase)

Point the app at the pooler and the CLI at the database. Migrations and introspection need session-level features (advisory locks, prepared statements, DDL) that a transaction-mode pooler will not give you.

```
DATABASE_URL="postgresql://user:pw@pooler:6543/db?pgbouncer=true&connection_limit=1"
DIRECT_URL="postgresql://user:pw@db:5432/db"
```

`pgbouncer=true` tells Prisma to stop using named prepared statements. Wire `DIRECT_URL` into `prisma.config.ts` (v7) or the `directUrl` datasource field (v6) so `migrate` bypasses the pooler. Details in migrations.md.

### Prisma Accelerate

A managed global connection pool plus a query cache, reached over HTTP with a `prisma://` connection string and the `@prisma/extension-accelerate` client extension. It solves connection exhaustion by holding the pool outside your function, and adds per-query caching via `cacheStrategy: { ttl: 60, swr: 10 }`. Because it is HTTP, it also works from edge runtimes that cannot open TCP sockets. Included with Prisma Postgres, available as an add-on for any other database.

### Prisma Postgres

Prisma's own managed Postgres, built for serverless: connection pooling and caching are built in, and as of the v7 era it speaks the standard Postgres wire protocol, so ordinary tools (psql, TablePlus, Cloudflare Hyperdrive) connect to it directly. Use `@prisma/adapter-ppg`. It is the path of least resistance for edge deployments because it needs no specialized edge driver.

## 6. Deployment targets

### Long-running Node servers

The easy case. One module-scope client, reused for the process lifetime. Do not call `$disconnect()` per request; connection setup is expensive and the pool exists precisely to amortize it. Size the pool to what the database can actually take, divided by the number of app instances.

### Serverless (Vercel functions, AWS Lambda)

Client outside the handler, small pool, pooler or Accelerate in front of the database. Run `prisma migrate deploy` as a separate release/CI step, never inside a request handler (concurrent cold starts will race the migration lock). Watch the dependency-cache trap from section 3.

### Edge (Cloudflare Workers, Vercel Edge)

Edge isolates are not Node. The binding constraint is that you generally cannot open arbitrary TCP sockets, so the driver must speak HTTP, or the platform must emulate the socket.

```prisma
generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
  runtime  = "workerd"       // or "vercel-edge", "deno"
}
```

- HTTP-based and portable across edge platforms: Prisma Postgres / Accelerate, Neon serverless, PlanetScale serverless, libSQL (Turso).
- TCP-based, Cloudflare only: `pg` (needs `nodejs_compat` / `node_compat` in `wrangler.toml`), plus D1 which is Cloudflare-native.
- Read env from the Worker `env` argument, not `process.env`. That means the client has to be constructed **inside** `fetch`, so pair it with `ctx.waitUntil(prisma.$disconnect())`.

```ts
export default {
  async fetch(request, env, ctx) {
    const adapter = new PrismaPg({ connectionString: env.DATABASE_URL });
    const prisma = new PrismaClient({ adapter });
    const users = await prisma.user.findMany();
    ctx.waitUntil(prisma.$disconnect());
    return Response.json(users);
  },
};
```

### Docker

On **v7 there are no query engine binaries to ship**, which deletes an entire genre of Docker bug. Ship the generated client directory and the `prisma/migrations` folder, and run `prisma generate` in the image build (or at startup) so the client matches the schema baked into that image.

```dockerfile
FROM node:lts-alpine
WORKDIR /usr/src/app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx prisma generate
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/main.js"]
```

On **v6 (`prisma-client-js`)** the engine binary is real and platform-specific, and it is the source of the classic failure:

```
Error: Query engine binary for current platform "linux-musl-openssl-3.0.x" could not be found.
```

That means you generated on macOS (or on Debian) and ran on Alpine. Fix it by declaring the runtime platform explicitly:

```prisma
generator client {
  provider      = "prisma-client-js"
  binaryTargets = ["native", "linux-musl-openssl-3.0.x"]
}
```

`native` covers your laptop; the second entry covers the image. Common runtime targets: `linux-musl-openssl-3.0.x` (Alpine 3.17+), `linux-musl-arm64-openssl-3.0.x` (Alpine on arm64), `debian-openssl-3.0.x` (`node:slim`, modern), `debian-openssl-1.1.x` (older Debian/Ubuntu), `rhel-openssl-3.0.x` (Lambda AL2023). If you are on Alpine, do **not** install glibc to "fix" it; Prisma downloads musl-linked engines on purpose. On `node:slim` you may need `apt-get install -y openssl` because some tags ship without libssl.

Even on v7 the **CLI** still carries a schema engine binary for `migrate` and `db pull`. That affects your builder image and any container that runs migrations, not your application runtime.

## Gotchas

- **"Prisma v6" is not current.** v7 shipped 2025-11-19; `latest` is 7.8.0. Any answer built on `prisma-client-js`, `binaryTargets`, `engineType`, or `previewFeatures = ["driverAdapters"]` is describing the previous major.
- **`output` is required** with the `prisma-client` generator. There is no fallback to `node_modules/.prisma`. And therefore `import { PrismaClient } from "@prisma/client"` is wrong on a new v7 project; import from your output path.
- **A driver adapter is mandatory on v7.** `new PrismaClient({ datasources: { db: { url } } })` does not connect. The `datasources` override and the `url` field in the `datasource` block are both deprecated; the URL belongs in `prisma.config.ts` for the CLI and in the adapter for the runtime.
- **`.env` is no longer auto-loaded** once `prisma.config.ts` exists. Missing `import "dotenv/config"` produces an "environment variable not found" error that looks exactly like a missing secret.
- **Pool defaults shrank in v7.** `connection_limit` in the URL is dead; the driver's own option (`max`, `connectionLimit`, `pool.max`) rules, and it defaults to 10 rather than `num_cpus * 2 + 1`. Post-upgrade pool timeouts under load are usually this.
- **Vercel's dependency cache can skip `postinstall`**, shipping a client that does not match your schema. Put `prisma generate` in the build command, not only in `postinstall`.
- **`prisma` is a devDependency** and gets pruned on some platforms. `prisma: command not found` at build or release time means move it to `dependencies`.
- **v7 is ESM-first.** Setting `moduleFormat = "esm"` in a package without `"type": "module"` (or vice versa) gives you `ERR_REQUIRE_ESM` at runtime, not at generate time.
- **Middleware (`$use`) was removed in v7.** Client extensions are the replacement. The `metrics` preview feature is gone too.
- **Migrations no longer auto-seed** in v7, and `--skip-generate` / `--skip-seed` were removed from `migrate dev`. Call `prisma db seed` explicitly.
- **`pgbouncer=true` is not optional cosmetics.** Without it, transaction-mode PgBouncer plus Prisma's prepared statements yields intermittent `prepared statement "s0" already exists`. And a pooler URL cannot run migrations; that is what `DIRECT_URL` is for.
- **On edge, `process.env` is empty.** Cloudflare hands you `env` inside `fetch`, which forces per-request client construction. Pair it with `ctx.waitUntil(prisma.$disconnect())`.
- **The alpine/musl engine error only exists on v6.** If someone reports "Query engine binary not found" on a v7 project, something else is wrong (usually a stale generated directory, or `generate` never ran).
