---
topic_id: "v2:OCHN"
topic_path: "rust-arkit/cargo-toolchain"
semantic_id: "OAr6HAfO4Ib79pSpuJHyWXtZM1ppIAAC"
related_ids:
  - "HbA7Gddd68D7J5T4OpWSU2nbdVVpcAAO"
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
---
# Cargo and the Rust toolchain

Source:

- https://doc.rust-lang.org/cargo/ (The Cargo Book: guide, reference, commands)
- https://doc.rust-lang.org/edition-guide/ (editions and migration)
- https://rust-lang.github.io/rustup/ (toolchain management)

## 1. The everyday commands

```bash
cargo new my-crate            # new binary crate (--lib for a library)
cargo build                   # compile (debug profile, target/debug/)
cargo run -- --some-arg       # build + run; args after -- go to your binary
cargo check                   # type-check without codegen; much faster feedback loop
cargo test                    # run unit tests, integration tests, AND doc tests
cargo bench                   # run benchmarks (see Gotchas: use criterion/divan on stable)
cargo add serde --features derive   # edit Cargo.toml for you (built in since 1.62)
cargo remove serde
```

`cargo check` is the inner-loop command; `cargo build` only when you need the artifact.

## 2. clippy + fmt: the non-negotiable pair

Every serious Rust project runs both, usually in CI:

```bash
cargo fmt                      # rustfmt the whole workspace
cargo fmt --check              # CI mode: fail if anything would change
cargo clippy --all-targets --all-features -- -D warnings   # lints as errors
```

Clippy catches real bugs (needless clones, suspicious arithmetic, `unwrap` on `Option` chains) and teaches idiomatic Rust. `#[allow(clippy::lint_name)]` opts out locally; prefer that over globally silencing.

## 3. Workspaces

A workspace shares one `Cargo.lock` and one `target/` across crates. A **virtual manifest** is a root `Cargo.toml` with no `[package]`:

```toml
[workspace]
resolver = "3"                # "3" is the edition-2024 resolver
members = ["crates/*"]

[workspace.dependencies]      # single source of truth for versions
serde = { version = "1", features = ["derive"] }
```

Members inherit with `serde.workspace = true` in their own `[dependencies]`. Members depend on each other by path: `my-core = { path = "../my-core" }` (add a `version` too if you publish).

## 4. Feature flags

Features are **additive**: enabling one must never break code that did not ask for it, because Cargo unifies features across the whole build graph.

```toml
[features]
default = ["std"]             # what you get with no flags
std = []
tls = ["dep:rustls"]          # feature gates an optional dependency

[dependencies]
rustls = { version = "0.23", optional = true }
```

```rust
#[cfg(feature = "tls")]
pub mod tls;
```

```bash
cargo build --no-default-features --features tls
```

## 5. Profiles

```toml
[profile.release]
opt-level = 3        # default for release; "s"/"z" optimize for size
lto = "thin"         # link-time optimization; "fat"/true is slower to build, smaller/faster
codegen-units = 1    # best optimization, worst parallelism
panic = "abort"      # smaller binaries, no unwinding

[profile.dev.package."*"]
opt-level = 2        # optimize dependencies even in dev builds (huge for game/ML deps)
```

Profiles are only read from the **workspace root** manifest; profile sections in member crates are ignored.

## 6. Editions and the 2024 migration

Editions (2015, 2018, 2021, 2024) are opt-in, per-crate language snapshots; all editions interoperate in one build. Edition 2024 shipped in Rust 1.85. Headline changes: `unsafe extern` blocks required, unsafe attributes spelled `#[unsafe(no_mangle)]`, changed lifetime-capture rules for `impl Trait` (the `use<...>` syntax), `static mut` references disallowed.

```bash
cargo fix --edition        # apply machine-fixable migrations (run BEFORE bumping edition)
# then set edition = "2024" in Cargo.toml, build, fix the rest by hand
```

## 7. rustup: toolchains, components, targets

```bash
rustup update                          # update installed toolchains
rustup toolchain install nightly       # side-by-side toolchains
cargo +nightly miri test               # one-off run on another toolchain
rustup component add clippy rustfmt rust-analyzer
rustup target add wasm32-unknown-unknown
```

Pin a project with a `rust-toolchain.toml` (`[toolchain] channel = "1.88"`); rustup auto-switches when you cd in.

## 8. Doc comments and doc tests

`///` documents the following item, `//!` documents the enclosing module/crate. Code blocks in docs are **compiled and run** by `cargo test`:

````rust
/// Adds one.
///
/// ```
/// assert_eq!(my_crate::add_one(1), 2);
/// ```
pub fn add_one(x: i32) -> i32 { x + 1 }
````

`cargo doc --open` builds and opens the rendered docs. Doc tests are the cheapest regression tests you will ever write; keep examples honest.

## 9. Publishing basics

```bash
cargo login                 # once, with a crates.io token
cargo publish --dry-run     # verify the package builds from the .crate tarball
cargo publish
```

`Cargo.toml` needs `description` and `license` (or `license-file`). Versions follow semver and **cannot be overwritten or deleted**, only yanked (`cargo yank --version 0.1.1`), which hides them from new dependents without breaking existing lockfiles.

## 10. Cross-compilation quickstart

```bash
rustup target add x86_64-unknown-linux-musl
cargo build --release --target x86_64-unknown-linux-musl
```

Pure-Rust crates often just work; anything with C dependencies needs a cross linker, configured in `.cargo/config.toml`:

```toml
[target.aarch64-unknown-linux-gnu]
linker = "aarch64-linux-gnu-gcc"
```

When that gets painful, reach for `cargo zigbuild` (Zig as the C toolchain) or the `cross` tool (Docker images per target).

## Gotchas

- `cargo bench` uses the unstable libtest bench harness: `#[bench]` needs nightly. On stable, everyone uses **criterion** or **divan** as a `[[bench]]` target with `harness = false`.
- **Feature unification** bites: if any crate in the graph enables a feature of `dep`, every crate sees `dep` with that feature in the same build. `default-features = false` in your manifest does not win if a sibling dependency turns defaults back on.
- `cargo check` skips codegen, so link errors, some monomorphization errors, and `const` evaluation in dead code can pass `check` and fail `build`.
- `cargo fix --edition` must run while `Cargo.toml` still declares the **old** edition; bump the field afterward, not before.
- Tests run in parallel by default; tests that share files, ports, or env vars need `cargo test -- --test-threads=1` or per-test isolation.
- Doc tests only run for **library** targets. A binary-only crate's doc examples are never executed.
- `dev-dependencies` are not transitive: your crate's dev-deps are invisible to dependents, and you cannot use them outside tests/benches/examples.
- `cargo install` builds with the release profile of the **installed crate**, ignores your workspace, and does not use your lockfile unless you pass `--locked` (you almost always want `--locked` for reproducibility).
