---
topic_id: "v2:EMGL"
topic_path: "prisma-orm"
semantic_id: "M9mSK_cKHKOX6saJKoTisEWaFWCoIAAN"
related_ids:
  - "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
---
# Prisma Migrate and the Schema Workflow

Source:

- https://www.prisma.io/docs/orm/prisma-migrate (Migrate overview)
- https://www.prisma.io/docs/orm/prisma-migrate/understanding-prisma-migrate/mental-model (schema, migration history, `_prisma_migrations`, drift)
- https://www.prisma.io/docs/orm/prisma-migrate/getting-started (first migration; existing-project integration)
- https://www.prisma.io/docs/orm/prisma-migrate/workflows/development-and-production (what `migrate dev` vs `migrate deploy` actually do; advisory lock)
- https://www.prisma.io/docs/orm/prisma-migrate/understanding-prisma-migrate/shadow-database (shadow DB, `shadowDatabaseUrl`, required privileges)
- https://www.prisma.io/docs/orm/prisma-migrate/workflows/baselining (baselining an existing prod DB)
- https://www.prisma.io/docs/orm/prisma-migrate/workflows/customizing-migrations (`--create-only`, expand and contract)
- https://www.prisma.io/docs/orm/prisma-migrate/workflows/patching-and-hotfixing (failed migrations, `migrate resolve`)
- https://www.prisma.io/docs/orm/prisma-migrate/workflows/prototyping-your-schema (`db push`)
- https://www.prisma.io/docs/orm/prisma-migrate/workflows/seeding (seed config)
- https://www.prisma.io/docs/orm/prisma-schema/introspection (`db pull`, re-introspection)
- https://www.prisma.io/docs/orm/reference/prisma-cli-reference (full CLI surface and flags)
- https://www.prisma.io/docs/cli/migrate/diff (`migrate diff` flags, v7 removals)
- https://www.prisma.io/docs/orm/reference/prisma-config-reference (`prisma.config.ts`)
- https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7 (v6 to v7 breaking changes for the CLI)
- https://www.prisma.io/docs/guides/performance-and-optimization/connection-management/configure-for-external-connection-pooler (pooler vs direct connection)
- https://www.prisma.io/docs/orm/overview/databases/mongodb (no Migrate for MongoDB)

## 1. Version reality check (read this before anything else)

Prisma ORM shipped **v7** (Rust-free client, WASM query compiler) and as of mid-2026 is on the **7.x** line. Most tutorials, StackOverflow answers, and your own memory describe **v6**, and several Migrate behaviors changed. Where behavior differs, this page marks it **[v7]** / **[v6]**. Old docs are pinned at `/docs/orm/v6/...`.

The v7 changes that bite Migrate users:

- `prisma.config.ts` at the project root is the default place for CLI configuration (schema path, migrations path, seed command, datasource URL used by the CLI).
- `datasource.directUrl` and `datasource.shadowDatabaseUrl` in `schema.prisma` are deprecated; the CLI reads `datasource.url` / `datasource.shadowDatabaseUrl` from `prisma.config.ts`.
- **Automatic seeding was removed.** `migrate dev` and `migrate reset` no longer run the seed script. Run `prisma db seed` yourself.
- **`prisma generate` is no longer implicit.** `migrate dev` and `db push` do not regenerate the client for you.
- `--skip-generate` (from `migrate dev`, `db push`) and `--skip-seed` (from `migrate dev`) were removed because there is nothing left to skip.
- `generator client { output = ... }` is now mandatory; the client no longer lands in `node_modules`.
- `migrate diff` lost `--from-url`, `--to-url`, `--from-schema-datasource`, `--to-schema-datasource`, `--shadow-database-url`; use `--from-config-datasource` / `--to-config-datasource`.

See setup-and-deploy.md for driver adapters and client instantiation, schema-and-datamodel.md for the schema file itself.

## 2. The mental model

Migrate is **model-first**: the Prisma schema is the source of truth, and Migrate keeps four things in agreement.

1. `schema.prisma` (the data model you edit)
2. `prisma/migrations/*/migration.sql` (the migration history, committed to git)
3. `_prisma_migrations` (a table in the target DB recording which migrations ran, when, and their checksum/logs)
4. the actual database schema

**Drift** is any divergence between (3)+(2) and (4): someone ran DDL by hand, restored a dump, or edited an applied migration file (checksum mismatch).

The single most important split:

- `migrate dev` is a **development-only** command. It writes new migration files, it consults a shadow database, and it will **prompt to reset (drop) your database** when it detects drift or a modified/missing migration. Never point it at production.
- `migrate deploy` is the **only** command you run in CI/CD and production. It applies pending migrations and nothing else. It does not create migrations, does not detect drift, does not use a shadow DB, does not reset, and **does not generate Prisma Client**.

## 3. CLI surface

```bash
prisma init --datasource-provider postgresql   # scaffold schema + config (--db for Prisma Postgres, --prompt for AI scaffold)
prisma generate                                # generate client from schema (must be explicit in v7)
prisma validate                                # parse + typecheck the schema
prisma format                                  # canonical formatting (--check to fail in CI)
prisma debug                                   # dump resolved env/config paths for bug reports

prisma migrate dev --name add_job_title        # DEV ONLY: diff, write migration, apply, record
prisma migrate dev --create-only --name x      # write the SQL but do NOT apply it
prisma migrate deploy                          # PROD/CI: apply pending migrations, nothing else
prisma migrate status                          # read-only: what is applied / pending / failed
prisma migrate reset --force                   # DEV ONLY: drop, recreate, replay all migrations
prisma migrate resolve --applied <name>        # mark a migration as applied without running it
prisma migrate resolve --rolled-back <name>    # mark a failed migration as rolled back
prisma migrate diff --from-X --to-Y --script   # print SQL to get from state X to state Y

prisma db push                                 # prototype: sync schema to DB, no migration files
prisma db pull                                 # introspect: DB -> schema.prisma
prisma db seed                                 # run the seed command from config
prisma db execute --file ./script.sql          # run raw SQL against the datasource (--stdin also works)
prisma studio                                  # GUI at localhost:5555
```

`migrate dev` steps, in order: replay existing migration history in the shadow DB (drift check), apply any pending migrations to the dev DB, diff schema against the shadow DB state and write a new migration, apply it, update `_prisma_migrations`, and (v6 only) run generators and seed.

Both `migrate dev` and `migrate deploy` take an **advisory lock** with a 10 second timeout so two concurrent deploys cannot interleave. Since 5.3.0 this can be disabled with the `PRISMA_SCHEMA_DISABLE_ADVISORY_LOCK` env var (useful when your platform's connection proxy breaks advisory locks; see errors-and-debugging.md).

## 4. The shadow database

A **second, temporary database that Migrate creates and drops automatically** during `migrate dev` (and `migrate reset`). It exists to do two things safely:

- replay the whole migration history from scratch and compare the result to your dev DB, which is how drift and edited migrations are detected;
- generate the new migration against a known-clean state and decide whether it is destructive.

It is used **only** by `migrate dev` / `migrate reset`. `migrate deploy`, `migrate resolve`, and `db push` never touch it, so production needs no shadow DB and no extra privileges.

You must supply your own shadow DB when the CLI cannot `CREATE DATABASE`, which is the normal case on hosted Postgres/MySQL (Heroku, DigitalOcean, many managed Postgres offerings, most "one database per project" plans):

```ts
// prisma.config.ts  [v7]
import "dotenv/config";
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "tsx prisma/seed.ts",
    // SQL run against the shadow DB before migrations replay (extensions, roles, external tables)
    initShadowDb: `CREATE EXTENSION IF NOT EXISTS citext;`,
  },
  datasource: {
    url: env("DATABASE_URL"),
    shadowDatabaseUrl: env("SHADOW_DATABASE_URL"),
  },
});
```

```prisma
// schema.prisma  [v6]
datasource db {
  provider          = "postgresql"
  url               = env("DATABASE_URL")
  shadowDatabaseUrl = env("SHADOW_DATABASE_URL")
}
```

Privileges the migrate user needs when Prisma creates the shadow DB itself: PostgreSQL `SUPERUSER` or `CREATEDB`; MySQL/MariaDB `CREATE, ALTER, DROP, REFERENCES ON *.*`; SQL Server sysadmin or the `SERVER` securable; SQLite none. The shadow DB **must be a separate, disposable database**: Migrate wipes it.

## 5. `db push` (prototyping) vs `migrate`

`db push` uses the same engine as Migrate but computes a direct schema-to-database sync. It does **not** write a migration file and does **not** create or update `_prisma_migrations`.

```bash
prisma db push
prisma db push --accept-data-loss   # required when the sync would drop columns/tables
prisma db push --force-reset        # drop everything first, then push
```

Right for: local prototyping, throwaway branches, ephemeral test databases, and **MongoDB (which has no Migrate at all)**.
Wrong for: anything whose schema changes must be reviewed, replayed, or rolled forward on another environment.

The intended flow is: iterate with `db push` until the model feels right, then run `prisma migrate dev --name whatever` once to capture the whole thing as a single migration. Because `db push` leaves no trace in `_prisma_migrations`, the subsequent `migrate dev` sees the pushed changes as **drift** and will offer to reset the dev DB. That is expected and fine locally. In v7, `db push` does not run `prisma generate`, so run it yourself.

## 6. Introspection (`db pull`) for an existing database

```bash
prisma db pull            # DB -> schema.prisma (re-introspection preserves your edits)
prisma db pull --print    # dump to stdout, do not write
prisma db pull --force    # discard ALL manual schema edits and regenerate from the DB
```

Re-introspection on relational DBs is non-destructive: it keeps `@map`/`@@map`, custom `@relation` names, comments, and Prisma-level defaults such as `@default(uuid())`. Field order inside a model and enum values are re-derived from the database, so expect churn there. Unrepresentable features (partitioned tables, RLS, check constraints, and similar) produce warnings and are simply absent from the schema, which means Migrate will not manage them.

MongoDB is different: introspection **samples documents** to derive models, and it is a one-shot operation. Re-running it will clobber your manual changes.

## 7. Baselining an existing production database

Use when the DB already exists and you want future changes managed by Migrate without Migrate trying to recreate the world.

```bash
mkdir -p prisma/migrations/0_init

# 1. Make the schema match the DB
npx prisma db pull

# 2. Generate the "create everything" SQL as migration 0_init
npx prisma migrate diff \
  --from-empty \
  --to-schema prisma/schema.prisma \
  --script > prisma/migrations/0_init/migration.sql

# 3. Tell Migrate this migration is ALREADY applied (it does not run the SQL)
npx prisma migrate resolve --applied 0_init
```

[v6] step 2 is spelled `--to-schema-datamodel prisma/schema.prisma`. The `-datamodel` / `-datasource` suffixed forms were folded into `--to-schema` / `--to-config-datasource` in v7. If a command errors with an unknown flag, that is the version skew talking.

`migrate resolve --applied` inserts the row into `_prisma_migrations` with a matching checksum. Afterwards `migrate deploy` skips `0_init` and applies only migrations that come after it. Commit `0_init` and run the same `resolve` once per pre-existing environment (staging, prod), or bake it into the deploy script guarded by `migrate status`.

## 8. Editing a migration before it runs (`--create-only`)

```bash
npx prisma migrate dev --create-only --name rename_bio
# edit prisma/migrations/<ts>_rename_bio/migration.sql by hand
npx prisma migrate dev            # applies the pending, hand-edited migration
```

Canonical case: Prisma cannot know a rename is a rename, so a renamed field produces a drop plus an add, which loses data. Fix the generated SQL:

```sql
-- generated (destructive)
ALTER TABLE "Profile" DROP COLUMN "biograpy",
ADD COLUMN "biography" TEXT NOT NULL;

-- what you actually want
ALTER TABLE "Profile" RENAME COLUMN "biograpy" TO "biography";
```

Other `--create-only` uses: adding a `NOT NULL` column to a populated table (add nullable, backfill, then set not null), creating indexes `CONCURRENTLY`, adding extensions, or inserting a data-migration `UPDATE`. Once applied, **never edit a migration file**: the checksum in `_prisma_migrations` changes and `migrate dev` will demand a reset while `migrate deploy` warns.

## 9. Expand and contract (zero-downtime breaking change)

For a rename in production, a single `RENAME COLUMN` still breaks the currently-running old code between migration and deploy. Split it across releases:

1. **Expand**: add `biography` alongside `bio` in the schema; migrate. Both columns exist and are nullable.
2. **Backfill + dual write**: ship code that writes both fields and reads `bio`. Add a data migration:
   ```bash
   npx prisma migrate dev --name copy_biography --create-only
   ```
   ```sql
   UPDATE "Profile" SET "biography" = "bio" WHERE "biography" IS NULL;
   ```
3. **Switch reads** to `biography`; verify.
4. **Contract**: remove `bio` from the schema and `npx prisma migrate dev --name drop_bio`.

Same shape applies to type changes, splitting a table, and making a column required.

## 10. Failed migrations in production

A migration is "failed" when its `_prisma_migrations` row has `started_at` but no `finished_at` (bad SQL, a `NOT NULL` add against existing rows, the DB or pod dying mid-run). The error text is in the row's `logs` column. **While a failed migration sits there, every subsequent `prisma migrate deploy` refuses to run.** Two ways out:

```bash
# A. You reverted (or the DB rolled back) the partial changes; you want to retry
npx prisma migrate resolve --rolled-back 20260712120000_add_index
# fix the SQL (or make it idempotent with IF NOT EXISTS), redeploy
npx prisma migrate deploy

# B. You finished the migration by hand in psql; just record it as done
npx prisma migrate resolve --applied 20260712120000_add_index
```

Postgres and SQL Server run each migration in a transaction, so a failure there usually leaves nothing behind and `--rolled-back` is honest. **MySQL and MariaDB do not do transactional DDL**, so a failed migration is typically half-applied and you must manually revert the completed statements (or make the migration re-runnable) before `--rolled-back`. Diagnose first with `prisma migrate status`.

## 11. Seeding

```ts
// prisma.config.ts  [v7]
export default defineConfig({
  migrations: { seed: "tsx prisma/seed.ts" },
});
```

```json
// package.json  [v6]
{
  "prisma": { "seed": "tsx prisma/seed.ts" }
}
```

```bash
npx prisma db seed
npx prisma db seed -- --environment development   # args after -- reach your script
```

[v6] seeding ran automatically after `migrate dev` (on a fresh DB) and after `migrate reset`. **[v7] it does not run automatically at all**; only `prisma db seed` triggers it. If your CI "reset then seed" step silently stopped seeding after an upgrade, that is why. `ts-node` works in place of `tsx` but needs ESM/CJS flags (`ts-node --compiler-options '{"module":"CommonJS"}' prisma/seed.ts`) often enough that `tsx` is the recommended runner.

## 12. Pooler vs direct connection (`directUrl`)

Migrate issues DDL, uses session-level state, and takes advisory locks. Transaction-mode poolers (PgBouncer, Supabase's `:6543` pooler, RDS Proxy, and similar) break all three. So the CLI needs a **direct** connection even when the app runs through the pooler.

```bash
DATABASE_URL="postgres://user:pw@pooler.host:6543/db?pgbouncer=true"
DIRECT_URL="postgres://user:pw@db.host:5432/db"
```

```prisma
// schema.prisma  [v6]
datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")   // Prisma Client, through the pooler
  directUrl = env("DIRECT_URL")     // migrate dev / deploy / db push / db pull
}
```

```ts
// prisma.config.ts  [v7] -- directUrl is GONE; the CLI's datasource.url IS the direct URL
export default defineConfig({
  datasource: { url: env("DIRECT_URL") },
});
```

That is the v7 inversion worth internalizing: in v6, `url` is the pooled runtime URL and `directUrl` is the CLI escape hatch. In v7 the CLI has its own config file, so `datasource.url` there means "the connection the CLI uses" (point it at the direct URL), while the runtime pooled connection is configured on the driver adapter you pass to `PrismaClient`.

## 13. CI/CD shape

```bash
# build
npx prisma generate          # explicit in v7

# release step, before the new app version takes traffic
npx prisma migrate deploy
```

Do not run `migrate dev`, `db push`, or `migrate reset` in CI against a shared database. Run them against ephemeral databases only. `prisma migrate status` is safe read-only and exits non-zero when migrations are pending, which makes it a decent drift/pending gate. `migrate deploy` will not detect drift, so a hand-edited production schema stays invisible until a later migration collides with it; a scheduled `migrate diff --from-config-datasource --to-migrations ./prisma/migrations --exit-code` job is the cheap drift alarm (`--exit-code` returns 2 when the diff is non-empty).

## Gotchas

- **`migrate dev` can drop your database.** It does not silently reset, but on drift or a modified migration it prompts, and in a non-interactive shell (CI, a script, an agent) that prompt turns into a hard failure or an unattended reset. It is a dev-only command; treat it as destructive.
- **`migrate deploy` does not run `prisma generate`.** Ever, in any version. A deploy pipeline that only runs `migrate deploy` ships a stale client. Generate at build time.
- **[v7] `migrate dev` and `db push` also stopped generating.** In v6 they did. Upgrades break in a confusing way: types compile against yesterday's schema.
- **[v7] `migrate dev` / `migrate reset` no longer seed.** `--skip-seed` and `--skip-generate` were removed as flags, which is the tell.
- **The shadow database is dev-only.** People add `shadowDatabaseUrl` to production env vars "for safety" and then panic about the extra database. Production never needs one. Conversely, if `migrate dev` fails with P3014 (cannot create shadow database), the fix is to provision one and set `shadowDatabaseUrl`, not to grant `SUPERUSER` in prod.
- **A shadow DB must be empty and disposable.** Pointing `shadowDatabaseUrl` at staging wipes staging.
- **`db push` leaves no migration history**, so the next `migrate dev` sees drift and wants to reset. That is by design; do not "fix" it by hand-inserting `_prisma_migrations` rows.
- **Never edit an applied migration.** The checksum is stored; editing it turns into drift on every future `migrate dev` and a warning on `migrate deploy`.
- **Renames always come out as DROP + ADD.** Prisma diffs states, not intents. Any rename without `--create-only` is data loss.
- **Failed migration = deploy is bricked** until `migrate resolve` clears it. And on MySQL/MariaDB (no transactional DDL) `--rolled-back` is a lie unless you manually undid the partially applied statements.
- **`migrate resolve --applied` does not execute SQL.** It only writes the bookkeeping row. Using it to "fix" a migration you never ran leaves the DB missing the change, silently, forever.
- **Flag names moved between v6 and v7**: `--to-schema-datamodel` -> `--to-schema`, `--from-schema-datasource`/`--from-url` -> `--from-config-datasource`. Baselining snippets copied from blog posts will error on v7.
- **MongoDB has no Prisma Migrate at all**, and there are no plans for it: `db push` only, no migration files, no `_prisma_migrations`, and `db pull` samples documents (so re-running it destroys manual schema edits).
- **`prisma migrate diff` writes nothing.** It prints. Pair it with `prisma db execute --file` to actually apply the SQL (the standard drift-repair and down-migration recipe).
- Advisory locks (10s timeout) mean two pods racing `migrate deploy` at boot is survivable but slow; on platforms whose proxies break advisory locks, set `PRISMA_SCHEMA_DISABLE_ADVISORY_LOCK=1` and serialize the migration into a single release step instead. See errors-and-debugging.md for the P3xxx migration error codes.
