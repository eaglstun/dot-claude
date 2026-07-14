---
topic_id: "v2:EHBN"
topic_path: "prisma-orm/relations-extensions"
semantic_id: "iPGCYv6RWeOJes4yA7Fj84nKt0BKEAAG"
related_ids:
  - "I-EAsl-BOeMRqsvHJbAyU43LF85oAAAG"
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
---
# Prisma Relations

**Status check (July 2026): the current release line is Prisma ORM v7 (`prisma@7.8.0` is `latest` on npm; `6.19.2` is tagged `prev`), so treat any "Prisma 6" habit as suspect.** Relation _modelling_ is one of the most stable corners of Prisma and survives v7 essentially untouched: `@relation`, referential actions, implicit/explicit m-n, and `relationMode` all behave as documented here. What did change is around the edges: the datasource `url` in the schema is deprecated in favour of `prisma.config.ts`, the `prisma-client` generator (with a required `output`) is now the default, and `relationLoadStrategy` is _still_ Preview behind `relationJoins`, not GA.

Source:

- https://www.prisma.io/docs/orm/prisma-schema/data-model/relations (relations overview: relation fields vs relation scalar fields, when `@relation` is required, disambiguation)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/relations/one-to-one-relations (1-1: FK side, `@unique`, optionality rules, multi-field)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/relations/one-to-many-relations (1-n: required vs optional, multi-field)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/relations/many-to-many-relations (implicit vs explicit m-n, join-table conventions, MongoDB m-n)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/relations/self-relations (1-1, 1-n, m-n self relations, multiple self relations)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/relations/referential-actions (Cascade, Restrict, NoAction, SetNull, SetDefault; defaults; DB caveats)
- https://www.prisma.io/docs/orm/prisma-schema/data-model/relations/relation-mode (`foreignKeys` vs `prisma`, required `@@index`, emulation cost)
- https://www.prisma.io/docs/orm/prisma-client/queries/relation-queries (`relationLoadStrategy`, `relationJoins` preview, nested writes, fluent API)
- https://www.prisma.io/docs/orm/reference/prisma-schema-reference (`@relation` argument table, `map`, default constraint naming)
- https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7 (v7 breaking changes: mandatory driver adapters, `prisma-client` generator, `prisma.config.ts`)
- https://www.prisma.io/docs/orm/reference/preview-features/client-preview-features (verified July 2026: `relationJoins` is still Preview, not GA)

Siblings: schema-and-datamodel.md, client-crud.md, performance.md, migrations.md

## 1. The Two Kinds of Fields

Every relation is expressed by exactly **two relation fields**, one on each model. A relation field has a model type (`User`, `Post[]`), exists only at the Prisma level, and has **no column** in the database. A **relation scalar field** (`authorId`) is the actual foreign key column.

```prisma
model User {
  id    Int    @id @default(autoincrement())
  posts Post[]                                  // relation field, no column
}

model Post {
  id       Int  @id @default(autoincrement())
  author   User @relation(fields: [authorId], references: [id])  // relation field
  authorId Int                                  // relation scalar = FK column
}
```

`@relation` is **required** when: defining 1-1 or 1-n relations; disambiguating multiple relations between the same two models; defining self-relations; defining m-n on MongoDB. It is **optional** for implicit m-n on relational databases (unless disambiguating).

## 2. The `@relation` Attribute

| Arg          | Type             | Notes                                                                                                                                                 |
| ------------ | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`       | String           | Relation name; must match on both sides. Also the implicit m-n join-table name. Can be given positionally: `@relation("Author", fields: [...], ...)`. |
| `fields`     | FieldReference[] | The relation scalar field(s) on this model that hold the FK.                                                                                          |
| `references` | FieldReference[] | The field(s) on the other model being referenced (usually its `@id` or a `@unique`).                                                                  |
| `map`        | String           | Database name of the FK constraint. Default: `ModelName_fieldName_fkey`.                                                                              |
| `onDelete`   | enum             | Referential action, see section 7.                                                                                                                    |
| `onUpdate`   | enum             | Referential action, see section 7.                                                                                                                    |

`fields` and `references` go on **one side only**, the side that owns the FK column. The other side gets a bare `@relation` (name only) or nothing.

```prisma
author   User @relation("AuthorPosts", fields: [authorId], references: [id], onDelete: Cascade, map: "post_author_fk")
authorId Int
```

Multi-column FKs are supported by listing multiple fields; order of `fields` must line up with order of `references`.

## 3. One-to-One

Rules that trip people up:

- The FK side **must** carry `@unique` on the relation scalar field. In SQL a 1-1 is just a 1-n with a `UNIQUE` constraint on the FK; without `@unique` you silently have a 1-n.
- The side **without** the relation scalar must be **optional** (`Profile?`). Prisma cannot enforce "every User has a Profile" on the non-FK side, because nothing in the DB stops you inserting a User with no Profile row pointing at it.
- The side **with** the relation scalar may be required or optional; if optional, the scalar must be optional too (`Int?`), and both `?`s must agree.

```prisma
model User {
  id      Int      @id @default(autoincrement())
  profile Profile?                              // must be optional
}

model Profile {
  id     Int  @id @default(autoincrement())
  user   User @relation(fields: [userId], references: [id])
  userId Int  @unique                           // FK + UNIQUE
}
```

Either model may hold the FK; pick the side that is optional in the domain, or the side you most often query by. Multi-field version:

```prisma
model User {
  firstName String
  lastName  String
  profile   Profile?
  @@id([firstName, lastName])
}

model Profile {
  id            Int    @id @default(autoincrement())
  user          User   @relation(fields: [userFirstName, userLastName], references: [firstName, lastName])
  userFirstName String
  userLastName  String
  @@unique([userFirstName, userLastName])       // still needs the composite unique
}
```

## 4. One-to-Many

Same shape as 1-1, minus `@unique`. The list side (`Post[]`) is never optional and never nullable: `Post[]?` is invalid, an empty list is the "none" case.

```prisma
// optional 1-n: a Post may be authorless
model Post {
  id       Int   @id @default(autoincrement())
  author   User? @relation(fields: [authorId], references: [id])
  authorId Int?
}

// mandatory 1-n: every Post must have an author
model Post {
  id       Int  @id @default(autoincrement())
  author   User @relation(fields: [authorId], references: [id])
  authorId Int
}
```

The required/optional distinction is exactly the nullability of the FK column, and it changes the **default `onDelete`** (section 7).

## 5. Many-to-Many, Implicit

Two list fields, no join model, no `fields`/`references`. Prisma creates and manages the join table.

```prisma
model Post {
  id         Int        @id @default(autoincrement())
  categories Category[]
}

model Category {
  id    Int    @id @default(autoincrement())
  posts Post[]
}
```

Conventions of the generated table (these are exactly what `prisma db pull` looks for when deciding whether an existing table is an implicit m-n):

- **Table name**: `_` + relation name. Default relation name is the two model names in **alphabetical** order joined by `To`, so `_CategoryToPost`. Setting `@relation("MyRelation")` on **both** sides renames the table to `_MyRelation`.
- **Columns**: exactly two, `A` and `B`. `A` points at the alphabetically first model, `B` at the second. Both are FKs with `ON DELETE CASCADE`.
- **Constraints/indexes**: a unique index on `(A, B)`, plus a non-unique index on `B` alone. There is no primary key and no `id` column.
- Both models must have a single-field `@id`. Composite `@@id` or a `@unique` standing in for an id disqualifies a model from implicit m-n.
- You may not pass `fields`, `references`, `onDelete`, or `onUpdate` to `@relation` here; only `name`.

Implicit m-n is queried through the relation fields only (`connect`, `disconnect`, `set`); the join table is not in Prisma Client.

## 6. Many-to-Many, Explicit

Use explicit m-n when you need **anything extra on the join**: additional columns (`assignedAt`, `assignedBy`, `role`, `order`), your own referential actions, composite ids on the participants, direct queries against the join rows, or non-cascading deletes.

```prisma
model Post {
  id         Int                 @id @default(autoincrement())
  categories CategoriesOnPosts[]
}

model Category {
  id    Int                 @id @default(autoincrement())
  posts CategoriesOnPosts[]
}

model CategoriesOnPosts {
  post       Post     @relation(fields: [postId], references: [id])
  postId     Int
  category   Category @relation(fields: [categoryId], references: [id])
  categoryId Int
  assignedAt DateTime @default(now())
  assignedBy String

  @@id([postId, categoryId])
}
```

This is just two 1-n relations. The cost is ergonomic: writes go through the join model (`post.create({ data: { categories: { create: [{ assignedBy: "x", category: { connect: { id: 1 } } } ] } } })`) and reads need a nested `include`. You can migrate implicit to explicit later, but it is a schema migration on a table Prisma previously owned.

## 7. Self-Relations

Always require a relation `name` (both sides live on the same model, so Prisma cannot pair them otherwise).

```prisma
// 1-1: neither side may be required
model User {
  id          Int   @id @default(autoincrement())
  successorId Int?  @unique
  successor   User? @relation("BlogOwnerHistory", fields: [successorId], references: [id])
  predecessor User? @relation("BlogOwnerHistory")
}

// 1-n: same, without @unique
model User {
  id        Int    @id @default(autoincrement())
  teacherId Int?
  teacher   User?  @relation("TeacherStudents", fields: [teacherId], references: [id])
  students  User[] @relation("TeacherStudents")
}

// m-n implicit: two list fields, same name
model User {
  id         Int    @id @default(autoincrement())
  followedBy User[] @relation("UserFollows")
  following  User[] @relation("UserFollows")
}
```

Explicit m-n self-relation needs a **different relation name per leg** on the join model:

```prisma
model Follows {
  followedBy   User @relation("followedBy", fields: [followedById], references: [id])
  followedById Int
  following    User @relation("following", fields: [followingId], references: [id])
  followingId  Int
  @@id([followingId, followedById])
}
```

Multiple self-relations coexist on one model as long as each pair shares a distinct name.

## 8. Multiple Relations Between the Same Two Models

With two or more relations between `User` and `Post`, Prisma cannot infer which relation field pairs with which. Every relation gets a name, identical on both sides:

```prisma
model User {
  id           Int    @id @default(autoincrement())
  writtenPosts Post[] @relation("WrittenPosts")
  pinnedPost   Post?  @relation("PinnedPost")
}

model Post {
  id         Int   @id @default(autoincrement())
  author     User  @relation("WrittenPosts", fields: [authorId], references: [id])
  authorId   Int
  pinnedBy   User? @relation("PinnedPost", fields: [pinnedById], references: [id])
  pinnedById Int?  @unique                      // 1-1 leg, so unique
}
```

Omitting the names is a validation error, not a silent guess. Note the names are Prisma-level identifiers; they do not appear in the database (except as the implicit m-n table name). Renaming a relation name therefore has no migration effect for 1-1/1-n, but **renames the join table** for implicit m-n.

## 9. Referential Actions

Set on the FK side via `onDelete` / `onUpdate`.

| Action       | On delete of the parent                    | On update of the parent key |
| ------------ | ------------------------------------------ | --------------------------- |
| `Cascade`    | delete the children                        | propagate the new key value |
| `Restrict`   | reject if children exist                   | reject if children exist    |
| `NoAction`   | DB-defined; usually deferred Restrict      | same                        |
| `SetNull`    | set child FK to NULL (FK must be optional) | same                        |
| `SetDefault` | set child FK to its `@default`             | same                        |

**Defaults**, which differ by optionality:

| Relation                                    | `onDelete` default | `onUpdate` default |
| ------------------------------------------- | ------------------ | ------------------ |
| Optional (`author User?` / `authorId Int?`) | `SetNull`          | `Cascade`          |
| Required (`author User` / `authorId Int`)   | `Restrict`         | `Cascade`          |

Caveats:

- `SetNull` on a **required** relation is accepted by the schema validator but blows up at runtime with a DB constraint violation when the parent is deleted (the FK column is `NOT NULL`). Prisma warns; make the field optional or use `Cascade`/`Restrict`.
- `SetDefault` requires `@default(...)` on **every** relation scalar in the FK, and that default must correspond to a real parent row, otherwise you get a runtime FK error. MySQL/MariaDB and MongoDB do not support it.
- SQL Server does not support `Restrict`; use `NoAction`.
- On SQL Server and MongoDB, self-relations and relation **cycles** require explicitly setting `onDelete: NoAction` and `onUpdate: NoAction` (otherwise you hit "introduces a cycle" / multiple-cascade-path errors). Same fix for multiple cascade paths between two models: break one path with `NoAction`.
- Referential actions are enforced by the **database** in `foreignKeys` mode; Prisma emits them as `ON DELETE` / `ON UPDATE` clauses in the migration (see migrations.md). They do **not** run any client-side interception: no client extension `query` component fires for the child rows, and no `$use` middleware either ([v6] `$use` existed; it was removed in 6.14.0, so [v7] extensions are the only interception mechanism, and they still do not see cascades).

## 10. `relationMode`: `foreignKeys` vs `prisma`

```prisma
// [v6] the connection string lives in the datasource block
datasource db {
  provider     = "mysql"
  url          = env("DATABASE_URL")
  relationMode = "prisma"
}

// [v7] `url` / `directUrl` / `shadowDatabaseUrl` are deprecated in the schema;
// the connection string moves to the driver adapter in prisma.config.ts.
// `provider` and `relationMode` stay here, because they are schema semantics.
datasource db {
  provider     = "mysql"
  relationMode = "prisma"
}
```

`relationMode` itself is unchanged in v7: same two values, same emulation, same `@@index` requirement.

- `foreignKeys` (default for all relational providers): real FK constraints, DB-enforced integrity and referential actions. Prefer this whenever the database supports it.
- `prisma`: **no FK constraints are created**. Prisma Client emulates integrity and referential actions in application code with extra queries per write. Required for MongoDB (its only mode) and for databases that forbid FKs: PlanetScale, some Vitess/proxy setups.

Consequences you must plan for:

- **You must add `@@index` on every relation scalar field yourself.** Without an FK, the database creates no backing index, so every emulated check and every `include` scans. Prisma raises a validation warning if you omit it.

```prisma
model Post {
  id       Int  @id @default(autoincrement())
  author   User @relation(fields: [authorId], references: [id])
  authorId Int

  @@index([authorId])                          // mandatory in prisma mode
}
```

- **Integrity is not enforced on create.** Emulation covers update and delete paths; you can insert a row whose FK points at nothing. Writes made outside Prisma Client (raw SQL, other services, a migration) are entirely unchecked.
- `SetDefault` is **not supported** in `prisma` mode. `NoAction` means "do nothing", so it provides no protection at all. `Cascade`, `Restrict`, `SetNull` are emulated; `NoAction` is only available on MySQL, SQL Server, CockroachDB, MongoDB (not PostgreSQL/SQLite emulation).
- Performance: every delete/update on a parent turns into extra SELECTs plus the child writes, inside a transaction. This is strictly slower than a DB-level cascade; see performance.md.
- Switching modes is a migration: `foreignKeys` to `prisma` drops all FKs on the next migration; `prisma` to `foreignKeys` creates them. PlanetScale users typically use `db push` rather than Prisma Migrate, and should remove a pre-existing `migrations/` directory when switching (see migrations.md).

## 11. MongoDB Relations

- `relationMode` is always `prisma`; there are no FKs and no join tables.
- FK fields are `String @db.ObjectId` (or `String[] @db.ObjectId` for m-n) referencing `@id @default(auto()) @map("_id") @db.ObjectId`.
- 1-1 does not need `@unique` on the FK (Mongo does not enforce it anyway).
- m-n is **always explicit-ish**: an ID array on **both** sides, each with its own `@relation(fields: [...], references: [id])`. There is no implicit m-n.

```prisma
model Post {
  id          String     @id @default(auto()) @map("_id") @db.ObjectId
  categoryIDs String[]   @db.ObjectId
  categories  Category[] @relation(fields: [categoryIDs], references: [id])
}

model Category {
  id      String   @id @default(auto()) @map("_id") @db.ObjectId
  name    String
  postIDs String[] @db.ObjectId
  posts   Post[]   @relation(fields: [postIDs], references: [id])
}
```

Both arrays must be kept in sync; Prisma Client does this for `connect`/`disconnect`, hand-written Mongo writes do not. Query either through the relation (`categories: { some: { name: ... } }`) or through the raw ID list (`categoryIDs: { hasSome: [...] }`).

## 12. Loading Relations (Brief)

Relations are read with `include` / `select`, written with nested writes, and traversed with the fluent API:

The `prisma` instance in these snippets is a client you built yourself. In v7 that means an explicit driver adapter and an import from your generated `output` path, never `new PrismaClient()` off a bare `DATABASE_URL` and never `import { PrismaClient } from '@prisma/client'`; see client-crud.md section 1 and setup-and-deploy.md.

```ts
await prisma.user.findMany({ include: { posts: true } });
await prisma.user.create({
  data: { email: "a@b.c", posts: { create: [{ title: "Hi" }] } },
});
await prisma.user.findUnique({ where: { email: "a@b.c" } }).posts(); // fluent
```

`relationLoadStrategy` picks how the relation is fetched: `"join"` (single query, `LATERAL JOIN` on PostgreSQL, correlated subqueries on MySQL, JSON-aggregated in the DB) or `"query"` (one query per table, merged in the client). Verified against the docs in July 2026: it is **still Preview**, still behind the `relationJoins` preview feature, and still limited to PostgreSQL, CockroachDB, and MySQL. v7 did not promote it to GA, and the default strategy remains `"query"`.

```prisma
// [v7] `prisma-client` is the default generator and `output` is required;
// it generates into your source tree, not node_modules.
generator client {
  provider        = "prisma-client"
  output          = "../src/generated/prisma"
  previewFeatures = ["relationJoins"]
}

// [v6] the old default; `prisma-client-js` is deprecated in v7
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["relationJoins"]
}
```

```ts
const users = await prisma.user.findMany({
  relationLoadStrategy: "join",
  include: { posts: true },
});
```

Which strategy is faster depends on cardinality and index shape; see performance.md. CRUD mechanics live in client-crud.md.

## Gotchas

- **`@unique` is the only thing that makes a 1-1 a 1-1.** Drop it and you have a 1-n with a singular-looking field name and a Prisma Client type that lies to you. Prisma will actually reject the 1-1 shape without it, but people "fix" the error by changing `Profile?` to `Profile[]` and quietly ship the wrong cardinality.
- **The default `onDelete` depends on optionality, and people memorize the wrong one.** Optional relation: `SetNull`. Required relation: `Restrict`. Neither default is `Cascade`. Making a field optional silently changes deletes from "blocked" to "orphaned with NULL".
- **`onDelete`/`onUpdate` belong on the side with `fields`/`references`**, i.e. the child. Putting `onDelete: Cascade` on the parent's list field is a validation error, and the intuition "cascade from the parent" is backwards from where the attribute lives.
- **`SetNull` on a required relation compiles and then fails in production.** The schema accepts it (with a warning); the `NOT NULL` FK column rejects it at delete time.
- **Implicit m-n column names are `A` and `B`, assigned alphabetically by model name.** If you rename a model such that the alphabetical order flips (`Post`/`Category` to `Post`/`Zategory`), the meaning of `A` and `B` flips too. Anything raw-SQL that hardcoded `_CategoryToPost.A` breaks. There is no `id` and no primary key on that table, only a unique index on `(A, B)` plus a lone index on `B`.
- **Renaming a `@relation("Name")` on an implicit m-n renames the physical join table** (`_Name`), which is a destructive migration. On 1-1/1-n a relation name is Prisma-only and renaming it is a no-op in the DB.
- **You cannot add a column to an implicit m-n join table.** The moment you need `createdAt` or `role` on the association, you must convert to an explicit join model, and that means rewriting every `connect`/`set` call.
- **Implicit m-n silently cascades.** Both FKs on the generated join table are `ON DELETE CASCADE` and you cannot change that (no `onDelete` allowed in `@relation` there). If you need `Restrict` on an association, go explicit.
- **`relationMode = "prisma"` does not validate on create.** It is not "foreign keys in the app layer"; it is "referential _actions_ in the app layer, plus best-effort checks on update/delete". You can and will create dangling FKs.
- **Forgetting `@@index` under `relationMode = "prisma"`** is the classic PlanetScale performance cliff: no FK means no implicit index, and emulated cascades then do full scans on every parent delete.
- **`NoAction` in `prisma` mode means literally nothing happens.** It is not a deferred `Restrict`; there is no database to defer to.
- **Cycles and SQL Server / MongoDB**: a self-relation or any relation cycle needs explicit `onDelete: NoAction, onUpdate: NoAction`, otherwise migration fails with a multiple-cascade-path error. This is a schema-level fix, not a query-level one.
- **Referential actions bypass Prisma Client entirely** in `foreignKeys` mode: a `Cascade` delete does not fire extensions (or, on 6.x, middleware), does not appear in query logs as child deletes, and will not be seen by any application-level audit hook. Note there is nothing to fall back on in v7: `$use` middleware was removed in 6.14.0, so an audit trail for cascaded child rows has to come from database triggers or from doing the deletes yourself.
- **`relationLoadStrategy` is still preview, in v7 too.** `relationJoins` must be in `previewFeatures`, and it does not exist for SQLite, SQL Server, or MongoDB. v7 being Rust-free did not GA it; do not assume `"join"` is on by default in a project that has not enabled the flag. The default is still `"query"`.
- **[v7] Do not copy a `url = env("DATABASE_URL")` line out of an old `relationMode` snippet.** In v7 the datasource block keeps `provider` and `relationMode` but the connection string is deprecated there; the URL belongs to the driver adapter configured in `prisma.config.ts`. Half-migrated schemas that keep both are the most common v7 upgrade mess.
- **[v7] Relation-heavy example code from v6 blogs will not even construct a client.** The relation modelling in those posts is still correct, but their `new PrismaClient()` and `import { PrismaClient } from '@prisma/client'` lines are not: v7 requires a driver adapter and an import from the generator's `output` path. Copy the schema, not the bootstrap.
