---
semantic_id: "8KR5bGRcL20jn74EKARqGvKZEEVpMAAE"
related_ids:
  - "urRuzaZ578T7mxDgNIRyUfgpM1BJIAAE"
  - "2vC-TVZ5bsyhB7yQCJWY0fkdVxdoMAAF"
---
# Modules and project layout

Source:

- <https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html>
- <https://doc.rust-lang.org/reference/items/modules.html> (module items, `#[path]`)
- <https://doc.rust-lang.org/reference/visibility-and-privacy.html> (pub, pub(in ...))
- <https://doc.rust-lang.org/cargo/guide/project-layout.html> (the directories Cargo knows)
- <https://rust-lang.github.io/api-guidelines/> (public API conventions)

## 1. Package, crate, module

Three different things, routinely conflated:

- **Package**: one `Cargo.toml`. Ships zero or one library crate plus any number of binaries.
- **Crate**: one compilation unit, one root file (`src/lib.rs` or `src/main.rs`). The unit
  of linkage, of the orphan rule, and of `pub(crate)`.
- **Module**: a namespace _inside_ a crate. Modules are a tree; the root is the crate root.

`mod foo;` does not import anything. It means "the module `foo` exists here, load its
contents from a file". `use` is the import.

## 2. File layout: no mod.rs required

Since the 2018 edition:

```
src/
  lib.rs            // mod net;  mod store;
  net.rs            // the module `net`'s own code
  net/
    http.rs         // net.rs contains: mod http;
    tls.rs
  store.rs
```

The old form (`net/mod.rs`) still works and both are supported forever, but do not mix
them for the same module: `net.rs` and `net/mod.rs` existing at once is a hard error. The
flat-file form is preferred because an editor tab labelled `mod.rs` seven times over is
useless.

Inline modules (`mod tests { ... }` in the same file) are the same thing without a file,
and are the normal home for unit tests.

## 3. Visibility

| form           | visible to                                                  |
| -------------- | ----------------------------------------------------------- |
| (nothing)      | the defining module and its descendants                     |
| `pub(super)`   | the parent module                                           |
| `pub(crate)`   | anywhere in this crate                                      |
| `pub(in a::b)` | that specific ancestor module subtree                       |
| `pub`          | anywhere, **if every module on the path is also reachable** |

That last clause is the one that bites. `pub fn f()` inside a private `mod internal` is
not callable from outside the crate; `pub` only grants permission at that one hop. The
`unreachable_pub` lint finds these and is worth turning on in a library.

Struct fields are private by default even when the struct is `pub`, which is what makes
newtypes and invariants enforceable.

## 4. Re-exports and the facade pattern

`pub use` re-exports a name at the current path. This is how you keep an internal tree
that suits the implementation while presenting a flat, stable public API:

```rust
// src/lib.rs
mod client;
mod error;
mod transport;          // private: callers never name it

pub use client::{Client, ClientBuilder};
pub use error::{Error, Result};
```

Consequences worth wanting: the public API is one readable list, internal files can move
freely without a semver break, and rustdoc shows the re-export at the short path. Add
`#[doc(inline)]` if rustdoc insists on rendering a bare re-export line instead of the item.

A `pub mod prelude` containing `pub use` of the traits callers must have in scope is the
convention for trait-heavy crates. Keep it small; a prelude that imports concrete types
starts causing name collisions in user code.

## 5. The directories Cargo treats specially

```
Cargo.toml
src/lib.rs              // the library crate
src/main.rs             // a binary, named after the package
src/bin/tool.rs         // an extra binary, `cargo run --bin tool`
benches/                // cargo bench
examples/               // cargo run --example foo; compiled by `cargo test --all-targets`
tests/                  // integration tests, each FILE is a separate crate
build.rs                // build script, runs before the crate compiles
```

Key rule: everything in `src/bin/`, `examples/`, `benches/`, and `tests/` is a **separate
crate** that depends on your library through its public API. It cannot see `pub(crate)` or
private items. That is a feature: it makes integration tests exercise the real surface.

Shared helper code for integration tests goes in `tests/common/mod.rs`, not
`tests/common.rs`, because the latter would be compiled as its own test binary containing
zero tests.

## 6. Workspaces

```toml
# root Cargo.toml
[workspace]
members = ["crates/*"]
resolver = "3"

[workspace.dependencies]
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = ["rt-multi-thread", "macros"] }

[workspace.package]
edition = "2024"
license = "MIT"
```

Members then write `serde = { workspace = true }` and `edition.workspace = true`. One
`Cargo.lock`, one `target/` directory (so builds share artifacts), and `cargo test` at the
root runs everything.

Split a crate out when it has a genuinely different dependency set or compile profile
(a proc-macro crate must be separate; a `no_std` core must be separate from a tokio
server). Splitting purely for tidiness costs you `pub(crate)` and buys little, since
modules already give you namespacing.

## 7. Idioms worth copying

- One module per concept, named as a noun, `snake_case`, singular. Not `utils`.
- `mod error;` with the crate's `Error` and `type Result<T> = std::result::Result<T, Error>`.
- `#[cfg(test)] mod tests;` at the bottom of the file it tests, so unit tests can reach
  private items.
- Sealed traits to make a public trait non-implementable outside the crate:

```rust
mod sealed { pub trait Sealed {} }
pub trait Encode: sealed::Sealed { fn encode(&self) -> Vec<u8>; }
impl sealed::Sealed for u32 {}
impl Encode for u32 { /* ... */ }
```

- A thin `src/main.rs` that only parses args and calls into `src/lib.rs`, so the logic is
  testable and reusable. Binary-only crates cannot be integration-tested or doc-tested.

## Gotchas

- **A file that no `mod` declaration points at is never compiled.** No error, no warning,
  no output: the file simply does not exist as far as rustc is concerned. This is the
  single most common "my changes did nothing" in a new Rust project.
- **Doc tests only run for library targets.** A `///` example on a function in `main.rs`
  is never executed. Move the code to `lib.rs` if you want the examples verified.
- `use` inside a module is private by default; a submodule does not inherit the parent's
  imports. Every file states its own `use` lines. This is deliberate and not negotiable.
- `#[macro_export]` puts a `macro_rules!` macro at the **crate root** regardless of which
  module defines it, so its path is `mycrate::the_macro`, not `mycrate::macros::the_macro`.
- Binaries in `src/bin/` linking your library must name it by the package's lib name with
  hyphens converted to underscores (`my-tool` package, `use my_tool::...`).
- Circular module references are fine (`a` uses `b`, `b` uses `a`); circular _crate_
  dependencies are not, and the fix is usually a third crate holding the shared types.
- `pub(crate)` on an item that appears in a `pub` function's signature is E0446, "private
  type in public interface". Either the type goes public or the function does not.
- The `resolver = "3"` (2024 edition default) changes feature unification versus resolver
  1. A workspace whose root omits `resolver` while members use edition 2024 gets a warning
     and the old behaviour; set it explicitly at the root.
- `#[path = "..."]` on a `mod` overrides file lookup. Useful for platform-specific modules,
  invaluable for confusing every reader afterwards; comment it.
