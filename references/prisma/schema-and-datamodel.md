---
topic_id: "v2:ECAG"
topic_path: "prisma-orm"
semantic_id: "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
related_ids:
  - "E_GIuHaDOUEbIs4TYLHScUWZl4DIoAAA"
  - "I-EAsl-BOeMRqsvHJbAyU43LF85oAAAG"
---
# Prisma Schema and Data Model

**Version note (verified July 2026): the current major is Prisma ORM v7, not v6.** v7.0.0 shipped 2025-11-19; v7.7.0 (2026-04-07) is the latest stable at time of writing, with releases roughly every two weeks. v7 is Rust-free (TypeScript query compiler, no query-engine binary), ESM-first, `prisma-client` generator by default, driver adapters required, and it introduces `prisma.config.ts`. Anything written for "Prisma 6" that you carry forward will be wrong on at least the generator and the datasource URL.

Source:

- https://www.prisma.io/docs/orm/reference/prisma-schema-reference (attribute/function/native-type reference, index arguments)
- https://www.prisma.io/docs/orm/prisma-schema/overview (schema anatomy: datasource, generator, data model)
- https://www.prisma.io/docs/orm/prisma-schema/overview/generators (`prisma-client` vs `prisma-client-js`, runtime/moduleFormat fields)
- https://www.prisma.io/docs/orm/prisma-schema/overview/location (schema location, multi-file schema folder)
- https://www.prisma.io/docs/orm/prisma-schema/overview/data-sources (datasource block, single-datasource rule)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/models (fields, modifiers, attributes, IDs, Unsupported, composite types)
- https://www.prisma.io/docs/orm/reference/prisma-config-reference (`prisma.config.ts`: schema, datasource, migrations, views, typedSql)
- https://www.prisma.io/docs/guides/upgrade-prisma-orm/v7 (v7 breaking changes)
- https://www.prisma.io/docs/orm/reference/preview-features/client-preview-features (active preview features + GA versions)
- https://www.prisma.io/blog/announcing-prisma-orm-7-0-0 (v7 release: Rust-free, generated code out of node_modules)

## 1. Anatomy of `schema.prisma`

Three block kinds: `datasource` (exactly one per schema), one or more `generator`, and the data model (`model`, `enum`, `type`).

```prisma
datasource db {
  provider = "postgresql"
}

generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  role      Role     @default(USER)
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("users")
}

enum Role {
  USER
  ADMIN
}
```

Default lookup: `./prisma/schema.prisma`, then `./schema.prisma`. Override with `--schema` or, preferably, the `schema` property of `prisma.config.ts`. Relations (`@relation`, referential actions, implicit m-n) are covered in relations.md.

## 2. `prisma-client` vs `prisma-client-js` (the trap)

`prisma-client-js` is deprecated. `prisma-client` is the v7 default and generates plain TypeScript that your bundler compiles like the rest of your app, instead of writing into `node_modules/@prisma/client`.

```prisma
generator client {
  provider     = "prisma-client"   // not "prisma-client-js"
  output       = "../src/generated/prisma"  // REQUIRED, no default
  runtime      = "nodejs"          // nodejs | deno | bun | workerd (cloudflare) | vercel-edge (edge-light) | react-native
  moduleFormat = "esm"             // esm | cjs, inferred from the environment if omitted
  // generatedFileExtension = "ts" // ts | mts | cts
  // importFileExtension    = "js" // ts|mts|cts|js|mjs|cjs, or omit for bare imports
}
```

What actually changes:

- `output` is mandatory. Omit it and generation errors out. There is no "magic" import from `@prisma/client`.
- Imports become path imports into your own source tree, split across files:
  ```ts
  import { PrismaClient } from "./generated/prisma/client"; // server, has PrismaClient
  import type { User } from "./generated/prisma/models"; // model types
  import { Role } from "./generated/prisma/enums"; // enums
  // ./generated/prisma/browser.ts exposes types only, no client
  ```
- `moduleFormat` decides whether generated code uses `import.meta.url` or `__dirname`.
- `Prisma.validator` is gone. Use the TypeScript `satisfies` operator.
- `.env` is no longer auto-loaded at runtime. Import `dotenv/config` yourself (Bun loads `.env` on its own).
- `binaryTargets`/`engineType = "binary"` are a `prisma-client-js` concern; the Rust-free client has no engine binary to ship. See setup-and-deploy.md.

Generated code should be gitignored or committed deliberately, and it must be regenerated after every schema change (`prisma generate`).

## 3. `prisma.config.ts` and where the connection URL lives

In v7 the datasource block keeps only `provider` (plus `relationMode`, `schemas`, `extensions`). `url`, `directUrl`, and `shadowDatabaseUrl` are deprecated in the schema and configured in `prisma.config.ts`:

```ts
import "dotenv/config";
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma", // or a folder path
  datasource: {
    url: env("DATABASE_URL"),
    shadowDatabaseUrl: env("SHADOW_DATABASE_URL"),
  },
  migrations: {
    path: "prisma/migrations",
    seed: "tsx prisma/seed.ts",
  },
  views: { path: "prisma/views" },
  typedSql: { path: "prisma/sql" },
});
```

Notes: the `directUrl` config property was removed in v7 (if you were using `directUrl` for migrations against a pooled connection, put that direct connection string in `datasource.url` in the config, since the config drives the CLI, while the runtime connection comes from the driver adapter you pass to `PrismaClient`). `seed` moved out of `package.json`'s `prisma` key into `migrations.seed`. See migrations.md and setup-and-deploy.md.

`env("VAR")` in the schema is still the mechanism for schema-level env interpolation (legacy `url`, `binaryTargets`), but it reads from the process environment; it does not load `.env` for you in v7.

## 4. Multi-file schema (schema folder)

`prismaSchemaFolder` went GA in 6.7.0, so no preview flag is needed. Point `schema` at a directory; every `.prisma` file inside is concatenated.

```
prisma/
├── migrations/
├── schema.prisma      // datasource + generator live here
└── models/
    ├── user.prisma
    └── post.prisma
```

Rules: the file holding the `generator` block must sit in the directory you configured as the schema location, and the `migrations` directory must sit at the same level as `schema.prisma`. Enums, models, and types are global across files, so names must be unique across the whole folder.

## 5. Scalar types and default DB mappings

| Prisma     | PostgreSQL         | MySQL            | SQLite    | SQL Server       | MongoDB       |
| ---------- | ------------------ | ---------------- | --------- | ---------------- | ------------- |
| `String`   | `text`             | `varchar(191)`   | `TEXT`    | `nvarchar(1000)` | `String`      |
| `Boolean`  | `boolean`          | `TINYINT(1)`     | `INTEGER` | `bit`            | `Bool`        |
| `Int`      | `integer`          | `INT`            | `INTEGER` | `int`            | `Int`         |
| `BigInt`   | `bigint`           | `BIGINT`         | `INTEGER` | `bigint`         | `Long`        |
| `Float`    | `double precision` | `DOUBLE`         | `REAL`    | `float(53)`      | `Double`      |
| `Decimal`  | `decimal(65,30)`   | `DECIMAL(65,30)` | `DECIMAL` | `decimal(32,16)` | not supported |
| `DateTime` | `timestamp(3)`     | `DATETIME(3)`    | `NUMERIC` | `datetime2`      | `Timestamp`   |
| `Json`     | `jsonb`            | `JSON`           | `JSONB`   | not supported    | BSON object   |
| `Bytes`    | `bytea`            | `LONGBLOB`       | `BLOB`    | `varbinary`      | `BinData`     |

`Decimal` maps to a Decimal.js-style value in the client, `BigInt` to JS `bigint`, `Bytes` to `Uint8Array`. See client-crud.md for the runtime shapes.

## 6. Field modifiers

- `?` optional/nullable: `name String?`
- `[]` list: `tags String[]`

You cannot combine them: `String[]?` is invalid, there are no optional lists. Scalar lists are only supported on PostgreSQL/CockroachDB (native arrays) and MongoDB; on MySQL/SQLite/SQL Server a `String[]` scalar list will not compile.

Every model must have a unique identifier: `@id`, `@@id`, `@unique`, or `@@unique`.

## 7. Attributes

Field attributes (`@`):

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  uid       String   @unique @default(uuid(7))      // uuid(4) | uuid(7); also cuid(), cuid(2), ulid(), nanoid()
  slug      String   @unique @map("url_slug") @db.VarChar(120)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt                     // client-side, on every update
  score     Decimal  @default(0) @db.Decimal(9, 2)
  legacy    String?  @ignore                        // excluded from Prisma Client
  gen       String   @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  meta      Json     @default("{}")

  @@map("posts")
}
```

`@default` functions: `autoincrement()` (relational only), `sequence()` (CockroachDB), `cuid()`, `uuid()`, `ulid()`, `nanoid()`, `now()`, `auto()` (MongoDB ObjectId), `dbgenerated("...")` (raw DB-side default Prisma does not model). `@default(..., map: "...")` names the constraint on SQL Server.

Block attributes (`@@`):

```prisma
model Membership {
  userId  Int
  orgId   Int
  email   String
  title   String

  @@id([userId, orgId])                                   // composite PK, not on MongoDB
  @@unique([orgId, email], map: "org_email_uq")
  @@index([title(length: 100), userId(sort: Desc)])       // length: MySQL only; sort: Asc|Desc
  @@index([meta], type: Gin)                              // PG: BTree (default) | Hash | Gist | Gin | SpGist | Brin
  @@map("memberships")
  @@schema("app")                                         // multiSchema, GA in 6.13.0
}
```

Other index arguments: `map` (DB-level name), `name` (name surfaced in the client's `where` unique inputs), `clustered` (SQL Server), `ops` (PG operator classes), `where` (partial indexes, `partialIndexes` preview since 7.4.0). `@@ignore` excludes a whole model. `@relation` is in relations.md.

`@map`/`@@map` change only the DB identifier, never the client API name. This is how you keep `snake_case` columns and `camelCase` TypeScript.

## 8. Native type attributes

`@db.*` attributes pin the underlying column type per provider. Written PascalCase, provider-specific, validated at `prisma validate` time.

```prisma
title    String   @db.VarChar(200)
body     String   @db.Text
uuid     String   @db.Uuid                 // PostgreSQL
price    Decimal  @db.Money                // PostgreSQL
at       DateTime @db.Timestamptz(3)       // PostgreSQL, timezone-aware
day      DateTime @db.Date
flag     Boolean  @db.TinyInt(1)           // MySQL
oid      String   @db.ObjectId             // MongoDB
```

The attribute must be valid for the datasource `provider` in the same schema; switching providers is where these bite (see Gotchas).

## 9. Enums, composite types, Json, Unsupported

```prisma
enum Role {
  USER
  ADMIN     @map("admin_role")   // mapped enum values (v7)
  @@map("user_role")
}

// MongoDB embedded documents (relational DBs do not support composite types)
type Photo {
  height Int
  width  Int
  url    String
}

model Product {
  id     String @id @default(auto()) @map("_id") @db.ObjectId
  photos Photo[]
  specs  Json
  region Unsupported("POLYGON")?
}
```

- Enums are unsupported on SQLite and SQL Server (Prisma emulates neither; the schema will not validate).
- Composite types support `@default`, `@map`, and native types; they do NOT support `@unique`, `@id`, `@relation`, or `@ignore`.
- `Json` is opaque to Prisma's type system: it types as `Prisma.JsonValue`, filtering uses path-based JSON filters, and `null` has two meanings (`Prisma.DbNull` vs `Prisma.JsonNull`). See client-crud.md.
- `Unsupported("...")` holds a column Prisma cannot model. Fields of this type are excluded from the client API (reach them with raw queries), and a required `Unsupported` field makes `create` impossible unless the DB supplies a default.

## 10. Preview features

Enable in the generator block, then re-run `prisma generate` (and restart the TS server in VS Code):

```prisma
generator client {
  provider        = "prisma-client"
  output          = "../src/generated/prisma"
  previewFeatures = ["relationJoins", "typedSql"]
}
```

Active as of mid-2026: `views` (4.9.0), `relationJoins` (5.7.0), `nativeDistinct` (5.7.0), `typedSql` (5.19.0), `strictUndefinedChecks` (5.20.0), `fullTextSearchPostgres` (6.0.0), `shardKeys` (6.10.0), `partialIndexes` (7.4.0).

Promoted to GA (drop the flag, it will warn or error): `tracing` (6.1.0), `prismaSchemaFolder` (6.7.0), `multiSchema` (6.13.0), `driverAdapters` (6.16.0). `metrics` was removed in v7.

## Gotchas

- **"Prisma 6" is stale.** v7 (Nov 2025) is current. Answering from memory gives you `prisma-client-js`, a `url` in the datasource block, and a Rust query engine, all three of which are wrong for a fresh v7 project.
- **`output` is required on `prisma-client`.** There is no default, and the generated client no longer lands in `node_modules/@prisma/client`. Importing `from '@prisma/client'` in a v7 project silently gives you the wrong package (types only / nothing) instead of your client.
- **`url` in the datasource block is deprecated.** It lives in `prisma.config.ts` under `datasource.url`. `directUrl` as a config property was removed entirely; the CLI uses `datasource.url`, the runtime uses the driver adapter you construct.
- **`.env` is not loaded for you anymore.** Both the CLI (via `prisma.config.ts`) and the runtime need explicit `import 'dotenv/config'`. A missing `DATABASE_URL` at generate time is the classic v6→v7 first failure.
- **`Cannot find module './internal/class.js'` under `tsx`/ts-node.** Set `importFileExtension = "ts"` in the generator block. This is the single most common v7 ESM footgun.
- **`String[]?` does not exist.** Optional lists are invalid. An empty list is the "absent" state; there is no nullable array.
- **Scalar lists are PostgreSQL/CockroachDB/MongoDB only.** People move a schema to MySQL and are surprised the `String[]` field will not validate.
- **`@updatedAt` is set by Prisma Client, not by the database.** Raw SQL, other services, and `$executeRaw` writes will not touch it. If you need DB-enforced behavior, use a trigger and `@default(dbgenerated(...))`/`@ignore`.
- **`@default(uuid())` and `cuid()` are generated in the client, not the DB.** The column has no DB-level default, so inserts from outside Prisma get NULL/error. Use `@default(dbgenerated("gen_random_uuid()")) @db.Uuid` when other writers exist. Note `uuid()` now takes a version argument: `uuid(7)` for time-sortable IDs.
- **`@map` vs `@@map` vs the `name`/`map` args on `@@unique`/`@@index`.** `name:` renames the field-combination in the Prisma Client API surface; `map:` renames the constraint/index in the database. Swapping them produces a migration that renames the wrong thing.
- **`@@index([field(length: 100)])` is MySQL only**, and `sort:` on `@id` is SQL Server only. A prefix length on Postgres will not validate.
- **Native types are provider-locked.** `@db.Timestamptz`, `@db.Uuid`, and `@db.Money` are PostgreSQL; `@db.TinyInt` is MySQL. You cannot keep them while flipping `provider`, which is why "just switch SQLite to Postgres" is rarely a one-line change.
- **MongoDB IDs must be `@id @default(auto()) @map("_id") @db.ObjectId`,** and `@@id` (composite) does not exist there.
- **`Json` `null` is ambiguous.** `Prisma.DbNull` (SQL NULL) and `Prisma.JsonNull` (JSON `null`) are different values; a plain `null` in a filter is a type error under `strictUndefinedChecks`.
- **Enums are not available on SQLite or SQL Server**, so a schema that validates on Postgres will fail on SQLite in your test setup.
- **Multi-file schema:** the file with the `generator` block must be in the configured schema directory, and `migrations/` must sit beside `schema.prisma`, otherwise the CLI cannot find either. Names are global across all `.prisma` files.
- **Preview flags that reached GA are not inert.** Leaving `previewFeatures = ["driverAdapters"]` or `["prismaSchemaFolder"]` in place after upgrading produces warnings, and `metrics` was removed in v7 outright.
- **`prisma generate` is not optional.** Adding a field and not regenerating produces type errors that look like schema bugs. See errors-and-debugging.md.
- **`@@index` on a relation scalar is still your job.** Prisma does not automatically index foreign-key columns on every provider; a missing index here is the most common cause of "Prisma is slow" reports. See performance.md and relations.md.
