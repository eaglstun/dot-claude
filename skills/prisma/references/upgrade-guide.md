---
semantic_id: "k-EKMv4yFSNBqs8kQHSS2M_blSpEEAAE"
related_ids:
  - "I-EAsl-BOeMRqsvHJbAyU43LF85oAAAG"
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
---
# Prisma: Upgrading across major versions (v5 to v6 to v7)

How to move an existing project up the Prisma major versions without breaking it. The
target is v7, but you do not jump there directly from v5: you upgrade one major at a time,
v5 to v6, land it, then v6 to v7. Each hop has its own breaking changes and its own
migration, and doing them together means debugging two migrations' worth of breakage at
once with no way to tell which version caused what.

**Version note: written 2026-07, target release line Prisma ORM v7** (`prisma@7.8.0` is
`latest`; `6.19.2` is `prev`; v7.0.0 shipped 2025-11-19). v7 is a rewrite, not a bump: the
Rust query engine is gone, driver adapters are mandatory, the `prisma-client` generator is
the default, and `prisma.config.ts` owns config. The v5 to v6 hop is comparatively mild;
the v6 to v7 hop is where the real work is. Sections mark which hop each change belongs to.

Source:

- https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-6 (v5 to v6 breaking changes, authoritative)
- https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7 (v6 to v7 breaking changes, authoritative)
- https://www.prisma.io/blog/announcing-prisma-orm-7-0-0 (v7 announcement: Rust-free, defaults)
- https://www.prisma.io/changelog/2025-11-19 (v7.0.0 changelog)
- https://www.prisma.io/docs/orm/reference/prisma-config-reference (`prisma.config.ts` fields, no auto `.env` loading)
- https://www.prisma.io/docs/orm/prisma-schema/overview/generators (`prisma-client` generator, `output`, `moduleFormat`)
- https://www.prisma.io/docs/orm/overview/databases/database-drivers (driver adapter packages per provider)

Siblings: setup-and-deploy.md, migrations.md, schema-and-datamodel.md, errors-and-debugging.md

## 1. The rule: one major at a time

Do not run `5.x` straight to `7.x`. The supported path is:

1. Upgrade to the latest `6.x` first (`prisma@6`, `@prisma/client@6`).
2. Get it green: `prisma generate`, typecheck, run the suite, smoke the app.
3. Commit that as its own migration step.
4. Then upgrade to `7.x`.

Reason: v6 and v7 each change behaviour, and the v7 hop is large enough on its own. Landing
v6 first means that when something breaks after the v7 bump, it is a v7 change, not a
five-versions-ago change you skipped past. Branch every hop and keep a DB backup or run
against a copy, because migrations run here.

## 2. Preflight (both hops)

- **Runtimes.** v6 needs Node 18.18.0+/20.9.0+/22.11.0+ and TypeScript 5.1+. v7 raises the
  floor to Node 20.19.0+ (22.x recommended) and TypeScript 5.4+ (5.9.x recommended). Check
  the deploy host, not just your laptop.
- **Pin, do not caret-drift.** Bump `prisma` and `@prisma/client` together and to the same
  version. Mismatched CLI and client versions are a class of confusing errors.
- **Regenerate after every schema or version change**, or the client types lag the schema.

## 3. v5 to v6 breaking changes

The mild hop. Most projects need only a version bump and a fresh migration.

1. **Minimum versions** move to the v6 floor above.
2. **Implicit m-n relations [Postgres, CockroachDB].** The relation table's unique index
   becomes a primary key constraint. The generated migration carries `ALTER TABLE` swapping
   `UNIQUE INDEX` for `PRIMARY KEY`. Only affects implicit m-n (`@relation` with no explicit
   join model). An explicit join table (your own pivot model) is untouched. Other
   datasources (SQLite, MySQL) are not called out for this change.
3. **Full-text search flags.** MySQL: `fullTextSearch` is now GA, remove it from
   `previewFeatures`. PostgreSQL: rename the flag `fullTextSearch` to
   `fullTextSearchPostgres`. `fullTextIndex` is also GA, remove it from `previewFeatures`.
4. **`Buffer` replaced with `Uint8Array`** for `Bytes` fields. Any code reading or writing a
   `Bytes` column now gets a `Uint8Array`. Update handling accordingly.
5. **`NotFoundError` removed.** `findUniqueOrThrow` / `findFirstOrThrow` now throw
   `PrismaClientKnownRequestError` with code `P2025`. Replace any `instanceof NotFoundError`
   check with a `P2025` code check.
6. **Reserved model names.** `async`, `await`, and `using` can no longer be model names.

Procedure: bump the packages, review the above against your code, then
`prisma migrate dev --name upgrade-to-v6` (dev) to capture any schema-level changes, and
`prisma migrate deploy` in prod.

## 4. v6 to v7 breaking changes

The big hop. This is a client-architecture change, not a feature bump. Expect to touch the
schema, the client instantiation, the imports, the tsconfig, and the deploy scripts.

1. **Generator provider.** `prisma-client-js` (Rust) becomes `prisma-client` (Rust-free,
   the mandatory default). Faster, smaller bundle, no engine binary.
2. **`output` is required** in the generator block, and the client generates into your
   source tree, not `node_modules`:
   ```prisma
   generator client {
     provider = "prisma-client"
     output   = "./generated/prisma"
   }
   ```
3. **Import path changes.** `import { PrismaClient } from '@prisma/client'` becomes
   `import { PrismaClient } from './generated/prisma/client'` (relative to your `output`).
   Every import site moves.
4. **ESM-only.** The client ships as an ES module. Set `"type": "module"` in
   `package.json`, and in `tsconfig.json`: `"module": "ESNext"`,
   `"moduleResolution": "bundler"`, `"target": "ES2023"` (or newer). A project already ESM
   is most of the way there.
5. **Driver adapters are mandatory, for every database including SQLite.** A bare
   `new PrismaClient()` on a `DATABASE_URL` now connects to nothing. Install the adapter for
   your provider and pass it:
   ```ts
   // Postgres
   import { PrismaPg } from '@prisma/adapter-pg'
   const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL })
   export const prisma = new PrismaClient({ adapter })

   // SQLite
   import { PrismaBetterSQLite3 } from '@prisma/adapter-better-sqlite3'
   const adapter = new PrismaBetterSQLite3({ url: process.env.DATABASE_URL })
   export const prisma = new PrismaClient({ adapter })
   ```
   The common misread is that adapters are a Postgres/serverless thing. In v7 SQLite needs
   one too (`@prisma/adapter-better-sqlite3` plus `better-sqlite3`).
6. **The driver owns the connection pool.** `connection_limit` and `pool_timeout` URL
   params are inert; pool behaviour comes from the underlying Node driver. Defaults changed
   (for example the pg pool uses a 0-second acquire timeout where v6 used 5s). Post-upgrade
   pool timeouts are almost always this. Configure the adapter to restore v6 behaviour.
7. **`prisma.config.ts` is required** at the project root. Datasource `url`, `directUrl`,
   and `shadowDatabaseUrl` are deprecated in the schema block and move here:
   ```ts
   import 'dotenv/config'
   import { defineConfig, env } from 'prisma/config'
   export default defineConfig({
     schema: 'prisma/schema.prisma',
     migrations: { path: 'prisma/migrations', seed: 'tsx prisma/seed.ts' },
     datasource: { url: env('DATABASE_URL') },
   })
   ```
8. **`.env` is no longer auto-loaded.** Load it yourself (`import 'dotenv/config'`, or a
   loader). Exception: Bun loads `.env` on its own. Deploy scripts that leaned on Prisma
   reading `.env` for them break silently.
9. **CLI changes.**
   - `prisma migrate dev` no longer auto-runs the seed; run `prisma db seed` explicitly.
   - `prisma generate` no longer runs automatically in places it used to; call it
     explicitly (keep it in the `build` script).
   - Removed flags: `--skip-generate` and `--skip-seed` (from `migrate dev` / `db push`),
     `--schema` and `--url` (from `db execute`).
   - `prisma migrate diff`: `--from-url` becomes `--from-config-datasource`, `--to-url`
     becomes `--to-config-datasource`, and `--shadow-database-url` moves into the config.
10. **SSL certificate validation is now enforced** instead of ignored. A previously working
    connection to a DB with a self-signed or invalid cert now errors `P1010`. Fix the cert
    or set `ssl: { rejectUnauthorized: false }` on the adapter deliberately.
11. **Removed: Metrics API and Client Middleware.** `$use` middleware was already gone in
    6.14.0; the Metrics API is removed in 7. Port both to `$extends` (query components /
    client extensions).
12. **Removed `PRISMA_*` env vars** that selected the engine: `PRISMA_CLIENT_ENGINE_TYPE`,
    `PRISMA_QUERY_ENGINE_BINARY`, `PRISMA_QUERY_ENGINE_LIBRARY`,
    `PRISMA_GENERATE_SKIP_AUTOINSTALL`, `PRISMA_MIGRATE_SKIP_SEED`, and the rest of that
    family. They no longer do anything (there is no engine binary to select).
13. **Enum mapping reverted.** TypeScript enums use the schema names again (not the mapped
    DB values). v7 matches v6 here; only pre-6 code that relied on mapped values is affected.
14. **MongoDB is not supported in v7 yet.** A Mongo project stays on v6 until support lands.
15. **Accelerate.** Keep the Accelerate URL in `.env`, do not pass it to a driver adapter;
    use the `accelerateUrl` parameter and the `withAccelerate()` extension.

## 5. Full 5-to-7 checklist

1. Branch. Back up the DB (or run against a copy). Confirm Node and TS meet the v7 floor.
2. **Hop A, to v6:** bump `prisma`/`@prisma/client` to latest 6.x, apply the section 3
   changes, `prisma generate`, typecheck, test, `prisma migrate dev --name upgrade-to-v6`.
   Commit.
3. **Hop B, to v7:** bump to 7.x. Then, in order:
   - schema: change the generator `provider` to `prisma-client`, add `output`.
   - create `prisma.config.ts`; move `url`/`directUrl`/`shadowDatabaseUrl` out of the
     datasource block.
   - install the driver adapter (plus its underlying driver) and rewrite the single
     `PrismaClient` construction to pass `{ adapter }`.
   - update every `@prisma/client` import to the generated `output` path.
   - set `"type": "module"` and the ESM tsconfig options if not already ESM.
   - add `dotenv` (or equivalent) so env vars load.
   - update scripts: explicit `prisma generate` in build, explicit `prisma db seed`, drop
     any removed flags, and fix any `migrate diff --from-url`/`--to-url` in CI.
4. `prisma generate`, typecheck, test, smoke the app locally, then deploy.

## Gotchas

- **Never skip v6.** A 5-to-7 jump in one shot stacks two majors of breakage with no way to
  bisect which version broke what.
- **SQLite needs a driver adapter in v7 too.** The single most common wrong assumption is
  that adapters are a Postgres/serverless concern. Every provider needs one now.
- **`prisma generate` and `.env` loading stopped being automatic in v7.** A deploy script
  that ran `migrate deploy` and relied on Prisma generating the client and reading `.env`
  for it will fail silently after the upgrade. Make both explicit.
- **Post-upgrade pool timeouts are the driver-owned pool**, not your `connection_limit`
  (which is now inert). Set the pool on the adapter.
- **Forgetting to move imports to the `output` path** leaves stale `@prisma/client` imports
  that resolve to nothing useful. Change the generator and the imports together.
- **`P1010` after upgrading** is almost always the new SSL cert validation, not a
  credentials problem.
- **`Bytes` columns hand you a `Uint8Array` from v6 on**, not a `Buffer`. Code that assumed
  `Buffer` methods breaks at runtime, not at compile time.
</content>
</invoke>
