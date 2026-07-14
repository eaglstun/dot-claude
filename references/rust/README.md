---
topic_id: "v2:OIDL"
topic_path: "rust-arkit"
semantic_id: "CaB-BXHI76x7FTaEJoQaegtPd3F4MAAC"
related_ids:
  - "KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
---
# Rust language references

Condensed, source-cited notes on the Rust language, toolchain, and ecosystem.
This is a standalone shelf (like `xformers/`), not tied to any one repo. The
annotated index (a two-line pointer per file) lives in the skill:
`skills/rust/SKILL.md`.

## Format for every page

- H1 title, then a `Source:` block listing the primary-source URLs the page is
  grounded in. Prefer stable, un-versioned URLs: `doc.rust-lang.org/book/...`,
  `doc.rust-lang.org/reference/`, `doc.rust-lang.org/std/`,
  `doc.rust-lang.org/cargo/`, `doc.rust-lang.org/nomicon/`, `tokio.rs`,
  `dioxuslabs.com/learn/0.7/`.
- Body: accurate, current (Rust 2024 edition era), code in ```rust fences,
  compiler-error-aware (name the E-codes).
- Ends with a `## Gotchas` section: the sharp edges someone answering from
  memory gets wrong.
- No em dashes, anywhere. House rule.

## Currency notes

- Written 2026-07. Rust edition 2024 is current; Dioxus is at 0.7 (fast-moving
  0.x API, re-verify against dioxuslabs.com before leaning on specifics).
- When a page's claims feel stale, re-verify against the Source URLs and update
  the page rather than trusting it.
