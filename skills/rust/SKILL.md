---
name: rust
version: 1.0.0
public: true
description: >-
  Rust language reference — ownership/borrowing/lifetimes, traits and generics, error
  handling, collections and iterators, cargo and tooling, async/tokio, unsafe and FFI, and
  the crate ecosystem including GUI/fullstack frameworks (Dioxus, Tauri, egui). Use when
  writing, reviewing, or debugging Rust in any repo, or when a borrow-checker error, trait
  bound, or "which crate" question comes up.
semantic_id: "KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"
related_ids:
  - "CaB-BXHI76x7FTaEJoQaegtPd3F4MAAC"
  - "HbA7Gddd68D7J5T4OpWSU2nbdVVpcAAO"
topic_id: "v2:OMHF"
topic_path: "rust-arkit/rust-async"
---

# Rust reference

Condensed, source-cited notes grounded in the primary sources (The Book, the
Reference, std docs, the Cargo Book, the Nomicon, tokio.rs, dioxuslabs.com).
Each page cites its source URLs at the top and ends with a Gotchas section of
the sharp edges that memory gets wrong.

This is a standalone language shelf, not tied to one repo. Repo conventions
(a project CLAUDE.md, an existing workspace layout) override anything here.

## References - load on demand

Detail lives in `../../references/rust/`. One pointer per page:

- **[ownership-borrowing-lifetimes.md](../../references/rust/ownership-borrowing-lifetimes.md)**
  - moves vs Copy, the borrow rules, lifetimes and elision, interior-mutability
    decision table, Cow. _Read on any borrowck error (E0502/E0597/E0499) or
    Rc/RefCell/Arc/Mutex choice._

- **[traits-and-generics.md](../../references/rust/traits-and-generics.md)**
  - bounds, impl Trait vs dyn Trait and dyn compatibility, associated types,
    From/Into/AsRef, Deref, the orphan rule and newtypes. _Read when designing an
    API surface or fighting a trait-bound error._

- **[error-handling.md](../../references/rust/error-handling.md)**
  - Result/Option, `?` and From conversions, thiserror (libraries) vs anyhow
    (applications), panic policy. _Read before adding error types or plumbing
    errors through a call stack._

- **[collections-and-iterators.md](../../references/rust/collections-and-iterators.md)**
  - which collection when, String vs &str, entry API, iterator adaptors,
    collect and the turbofish, perf notes. _Read when transforming data or
    choosing a container._

- **[cargo-and-tooling.md](../../references/rust/cargo-and-tooling.md)**
  - cargo commands, clippy + fmt, workspaces, feature flags, profiles,
    editions, rustup, doc tests, cross-compilation. _Read when setting up,
    structuring, or shipping a crate._

- **[async-and-concurrency.md](../../references/rust/async-and-concurrency.md)**
  - lazy futures, tokio runtime and spawn bounds, channels, select!,
    spawn*blocking, Send/Sync, rayon vs async. \_Read before writing async code
    or when a future "does nothing" / a Send bound explodes.*

- **[unsafe-and-ffi.md](../../references/rust/unsafe-and-ffi.md)**
  - what unsafe permits, SAFETY comments, extern "C" both directions, repr(C),
    bindgen/cbindgen, CString/CStr, Miri. _Read before any unsafe block or
    C-boundary work._

- **[ecosystem-and-frameworks.md](../../references/rust/ecosystem-and-frameworks.md)**
  - the blessed-crates map (serde, clap, reqwest, axum, sqlx, tracing) and the
    GUI/app landscape: egui, Tauri, Dioxus, Leptos/Yew, wasm. _Read for any
    "which crate do I reach for" question._

- **[dioxus.md](../../references/rust/dioxus.md)**
  - Dioxus 0.7 in depth: rsx!, components, signals/hooks, the dx CLI and hot
    reload, web/desktop/mobile/fullstack targets, server functions, how it
    differs from Tauri and Leptos. _Read before building or advising on a Dioxus
    app._

## Conventions for this skill

- Each reference cites its source URLs at the top; prefer un-versioned
  doc.rust-lang.org URLs so links do not rot with releases.
- Keep SKILL.md lean: two-line pointers only. Detail lives on the shelf.
- To add a topic: write `../../references/rust/<topic>.md` in the same format
  (Source block up top, Gotchas at the end), then add a two-line pointer above.
  See the shelf README for the format spec.
