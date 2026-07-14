---
topic_id: "v2:EINK"
topic_path: "prisma-orm"
semantic_id: "g-iSIH2UH6nbAdaJIqACewG7l2FaIAAH"
related_ids:
  - "q_kSIV-COfmfw96LI7ES10WalSjYIAAB"
  - "E-GAuNeSGWETws6DYrBSO0Hal4zoEAAN"
---
# Prisma ORM references

Condensed, source-cited notes on Prisma ORM: the schema language, Prisma Client,
Migrate, and the deployment story. This is a standalone shelf (like `rust/`), not
tied to any one repo. The annotated index (a two-line pointer per file) lives in
the skill: `skills/prisma/SKILL.md`.

## Format for every page

- H1 title, then a bolded **version note** (what release line the page is written
  against, and what changes on this page between v6 and v7), then a `Source:`
  block listing the primary-source URLs the page is grounded in. Prefer stable
  un-versioned URLs: `prisma.io/docs/orm/...`. The v6 docs are pinned under
  `prisma.io/docs/orm/v6/...` if you need them.
- Body: numbered `## N. Section` headings, dense and practical, code in
  `prisma / `ts / ```bash fences.
- Where v6 and v7 genuinely differ and a reader on 6.x still needs the old
  answer, mark it inline with `[v6]` / `[v7]` rather than deleting it. Plenty of
  production code is still on 6.
- Ends with a `## Gotchas` section: the sharp edges someone answering from
  memory gets wrong. This is the highest-value part of every page.
- No em dashes, anywhere. House rule.

## Currency notes

- Written 2026-07, against **Prisma ORM v7** (`prisma@7.8.0` is `latest` on npm;
  `6.19.2` is tagged `prev`). v7.0.0 shipped 2025-11-19.
- v7 is not a routine bump. The things that break every v6-era memory and most
  blog posts, and that this shelf exists to keep straight:
  - Rust-free. TypeScript query compiler, no query-engine binary, so no
    `binaryTargets`, no `engineType`, and the classic "Query engine binary not
    found" alpine/musl error cannot happen.
  - **Driver adapters are mandatory** for every database. A bare
    `new PrismaClient()` on a `DATABASE_URL` connects to nothing.
  - The **`prisma-client` generator is the default**, `output` is required, and
    it generates into your source tree. `import { PrismaClient } from
'@prisma/client'` is wrong in new code.
  - **`prisma.config.ts`** is the config home; datasource `url` / `directUrl` /
    `shadowDatabaseUrl` are deprecated in the schema block, and `.env` is no
    longer auto-loaded.
  - The connection pool belongs to the driver now, so `connection_limit` and
    `pool_timeout` URL params are inert.
  - `Prisma.validator` is gone (use `satisfies`); `$use` middleware was removed
    back in 6.14.0 (use `$extends` query components).
- Still Preview as of 2026-07 (verify before leaning on them): `relationJoins` /
  `relationLoadStrategy`, `typedSql`, `strictUndefinedChecks`.
- When a page's claims feel stale, re-verify against the Source URLs and update
  the page rather than trusting it.
