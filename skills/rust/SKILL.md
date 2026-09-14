---
name: rust
description: Rust language reference — ownership/borrowing/lifetimes, traits and generics, pattern matching, closures and Fn traits, advanced types (const generics, GATs, variance), macros, error handling, collections and iterators, modules and project layout, cargo, testing and benchmarking, performance profiling, async/tokio, unsafe and FFI, serde, Python interop via PyO3, and the crate ecosystem including GUI/fullstack frameworks (Dioxus, Tauri, egui). Use when writing, reviewing, or debugging Rust in any repo, or when a borrow-checker error, trait bound, or "which crate" question comes up.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: KSDvGfd468R7VzWBMJEQWErLcXV4QAAD
  related_ids: '["aVl1Ldfhjxkb3j_DMYco2ggaiZ1sYAAG","bW5GcJLN76ZQ20SHI9ECwE_L5X6XQAAH"]'
  topic_id: v2:OMHF
  topic_path: rust-arkit/rust-async
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

### Language

- **[ownership-borrowing-lifetimes.md](../../references/rust/ownership-borrowing-lifetimes.md)**
  - moves vs Copy, the borrow rules, lifetimes and elision, interior-mutability
    decision table, Cow. _Read on any borrowck error (E0502/E0597/E0499) or
    Rc/RefCell/Arc/Mutex choice._

- **[traits-and-generics.md](../../references/rust/traits-and-generics.md)**
  - bounds, impl Trait vs dyn Trait and dyn compatibility, associated types,
    From/Into/AsRef, Deref, the orphan rule and newtypes. _Read when designing an
    API surface or fighting a trait-bound error._

- **[pattern-matching-and-enums.md](../../references/rust/pattern-matching-and-enums.md)**
  - enums as sum types, the full pattern catalogue, match ergonomics and the 2024
    binding-mode rules, let-else and let-chains, exhaustiveness and
    `#[non_exhaustive]`, Option/Result combinator table. _Read when a match will
    not compile or a `_` arm is about to hide a variant.\_

- **[closures-and-fn-traits.md](../../references/rust/closures-and-fn-traits.md)**
  - Fn/FnMut/FnOnce, `move` and disjoint capture, taking and returning closures,
    fn pointers vs closures, async closures (`AsyncFn`). _Read when a closure
    will not satisfy a bound, is not `'static`/`Send`, or two closures will not
    share a type._

- **[advanced-types.md](../../references/rust/advanced-types.md)**
  - const generics, GATs, PhantomData and the variance table, impl Trait in every
    position (RPIT/RPITIT and the missing Send bound), dyn compatibility,
    typestate, `!` and `?Sized`. _Read when the type system is the obstacle._

- **[macros.md](../../references/rust/macros.md)**
  - macro*rules fragments, repetition, hygiene, `$crate`; proc macros with
    syn/quote, the three kinds, spanned errors. \_Read before writing a macro, or
    when one expands to something baffling.*

- **[error-handling.md](../../references/rust/error-handling.md)**
  - Result/Option, `?` and From conversions, thiserror (libraries) vs anyhow
    (applications), panic policy. _Read before adding error types or plumbing
    errors through a call stack._

- **[collections-and-iterators.md](../../references/rust/collections-and-iterators.md)**
  - which collection when, String vs &str, entry API, iterator adaptors,
    collect and the turbofish, perf notes. _Read when transforming data or
    choosing a container._

- **[async-and-concurrency.md](../../references/rust/async-and-concurrency.md)**
  - lazy futures, tokio runtime and spawn bounds, channels, select!,
    spawn*blocking, Send/Sync, rayon vs async. \_Read before writing async code
    or when a future "does nothing" / a Send bound explodes.*

- **[unsafe-and-ffi.md](../../references/rust/unsafe-and-ffi.md)**
  - what unsafe permits, SAFETY comments, extern "C" both directions, repr(C),
    bindgen/cbindgen, CString/CStr, Miri. _Read before any unsafe block or
    C-boundary work._

### Project and practice

- **[modules-and-project-layout.md](../../references/rust/modules-and-project-layout.md)**
  - package vs crate vs module, file layout without mod.rs, visibility and
    `pub(crate)`, re-export facades, the directories Cargo treats specially,
    workspaces, sealed traits. _Read when structuring a crate, or when a file
    you added is not being compiled._

- **[cargo-and-tooling.md](../../references/rust/cargo-and-tooling.md)**
  - cargo commands, clippy + fmt, workspaces, feature flags, profiles,
    editions, rustup, doc tests, cross-compilation. _Read when setting up,
    structuring, or shipping a crate._

- **[testing.md](../../references/rust/testing.md)**
  - the built-in harness, unit vs integration vs doc tests, the crate shortlist
    (nextest, proptest, insta, rstest, wiremock, miri), criterion benchmarks,
    making tests deterministic. _Read when adding tests or when a test only
    fails in parallel._

- **[performance-and-profiling.md](../../references/rust/performance-and-profiling.md)**
  - release profiles and LTO, profilers (flamegraph, samply, Instruments, dhat),
    honest benchmarking with `black_box`, the wins in payoff order, compile-time
    tuning. _Read before optimising anything, and instead of guessing._

### Ecosystem

- **[ecosystem-and-frameworks.md](../../references/rust/ecosystem-and-frameworks.md)**
  - the blessed-crates map (serde, clap, reqwest, axum, sqlx, tracing) and the
    GUI/app landscape: egui, Tauri, Dioxus, Leptos/Yew, wasm. _Read for any
    "which crate do I reach for" question._

- **[serde.md](../../references/rust/serde.md)**
  - the attributes that matter, the four enum representations, `with`/`try_from`
    escape hatches and serde*with, zero-copy borrowing, the format-crate table.
    \_Read for any derive that will not do what the wire format needs, or when
    `flatten` starts misbehaving.*

- **[dioxus.md](../../references/rust/dioxus.md)**
  - Dioxus 0.7 in depth: rsx!, components, signals/hooks, the dx CLI and hot
    reload, web/desktop/mobile/fullstack targets, server functions, how it
    differs from Tauri and Leptos. _Read before building or advising on a Dioxus
    app._

- **[tauri.md](../../references/rust/tauri.md)**
  - Tauri 2 in depth: project layout and CLI, commands and typed state, events vs
    channels, the capabilities/permissions security model, plugins, mobile
    targets, vs Dioxus and Electron. _Read before building or advising on a
    Tauri app, or when a v1 snippet does not compile._

- **[pyo3-and-python-interop.md](../../references/rust/pyo3-and-python-interop.md)**
  - PyO3 and maturin: project shape and abi3 wheels, `#[pyfunction]`/`#[pyclass]`,
    the `Bound<'py, T>` API, releasing the GIL with `allow_threads`, numpy
    zero-copy, batching across the boundary. _Read when putting a Rust hot loop
    under Python._

## Conventions for this skill

- Each reference cites its source URLs at the top; prefer un-versioned
  doc.rust-lang.org URLs so links do not rot with releases.
- Keep SKILL.md lean: two-line pointers only. Detail lives on the shelf.
- To add a topic: write `../../references/rust/<topic>.md` in the same format
  (Source block up top, Gotchas at the end), then add a two-line pointer above.
  See the shelf README for the format spec.
