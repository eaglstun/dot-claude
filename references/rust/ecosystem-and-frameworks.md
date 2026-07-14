---
topic_id: "v2:OCAL"
topic_path: "rust-arkit/cargo-toolchain"
semantic_id: "Tah5fXbBrYdyVpahHZC6-Nh3qUTo4AAF"
related_ids:
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
  - "W68X52QNrzB1NCaxzZG6I0l2CcCCQAAH"
---
# Ecosystem: the blessed-crates map

Source:

- https://serde.rs/ (serde derive, attributes)
- https://docs.rs/clap/ and https://docs.rs/reqwest/ and https://docs.rs/axum/
- https://docs.rs/tracing/ and https://rustsec.org/ (advisory DB behind cargo audit)
- GUI/app: https://www.egui.rs/, https://tauri.app/, https://dioxuslabs.com/, https://leptos.dev/, https://yew.rs/

## 1. Serialization: serde + serde_json

The de facto standard. One derive, many formats (JSON, TOML, YAML, bincode, ...):

```toml
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

```rust
#[derive(serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "camelCase")]          // userId <-> user_id
struct User {
    user_id: u64,
    #[serde(default)]                        // missing field -> Default
    nickname: String,
}

let u: User = serde_json::from_str(&body)?;
let s = serde_json::to_string_pretty(&u)?;
```

Enum representations matter: the default is externally tagged (`{"Variant": {...}}`); `#[serde(tag = "type")]` gives internally tagged; `#[serde(untagged)]` tries each variant in order until one parses (order-sensitive, and error messages get vague). `serde_json::Value` is the escape hatch for free-form JSON.

## 2. CLI: clap (derive API)

```rust
#[derive(clap::Parser)]
#[command(version, about)]
struct Cli {
    /// Input file (doc comment becomes --help text)
    input: std::path::PathBuf,
    #[arg(short, long, default_value_t = 1)]
    jobs: usize,
    #[command(subcommand)]
    cmd: Option<Commands>,
}

let cli = Cli::parse();   // parse errors and --help/--version handled for you
```

Subcommands are an enum with `#[derive(Subcommand)]`. For tiny tools where clap's compile time stings, `pico-args` or `lexopt` exist, but clap is the default answer.

## 3. HTTP client: reqwest (and the async pull)

```rust
let resp: serde_json::Value = reqwest::get(url).await?.json().await?;
```

Ergonomic, but note what it drags in: reqwest is async-first, so adding it effectively adds **tokio** to your dependency graph and pushes `main` toward `#[tokio::main]`. For scripts and sync tools, either use `reqwest::blocking` (feature `blocking`; it spins up an internal runtime) or reach for `ureq`, a genuinely synchronous, small client. Build a `Client` once and reuse it: it holds the connection pool.

## 4. Services: axum

The default web framework, from the tokio team. Handlers are plain async fns; parameters are **extractors** (path, query, JSON body, state), return types implement `IntoResponse`; middleware is tower layers shared with the rest of the ecosystem:

```rust
let app = axum::Router::new()
    .route("/users/{id}", axum::routing::get(get_user))
    .with_state(pool);

async fn get_user(
    axum::extract::Path(id): axum::extract::Path<u64>,
    axum::extract::State(pool): axum::extract::State<PgPool>,
) -> Result<axum::Json<User>, StatusCode> { /* ... */ }
```

Alternatives: actix-web (mature, fast, its own actor-ish world), rocket (batteries included). New services default to axum.

## 5. Databases: sqlx vs diesel, in one line each

**sqlx**: async, no ORM, you write real SQL, and the `query!` macros check it against a live database **at compile time**. **diesel**: sync-first ORM with a type-safe query DSL generated from your schema, strongest when you want the query builder to prevent malformed SQL by construction. Rough guide: async service with hand-written SQL, sqlx; schema-heavy CRUD with migrations as a first-class citizen, diesel (or SeaORM for an async ORM).

## 6. Observability: tracing over log

`log` gives you `info!("msg")` lines. `tracing` gives you that **plus spans**: structured key-value fields and enter/exit context that follows async tasks across `.await` points, which flat log lines cannot do. It is what tokio, axum, and friends are instrumented with.

```rust
tracing_subscriber::fmt().with_env_filter("info,my_crate=debug").init();

#[tracing::instrument(skip(pool))]
async fn handle(user_id: u64, pool: &PgPool) { tracing::info!(user_id, "handling"); }
```

`tracing-subscriber` formats/filters; exporters exist for OpenTelemetry, Jaeger, etc. `log`-based crates still work via the `tracing-log` bridge.

## 7. Parallelism: rayon / crossbeam

`rayon` for CPU-bound data parallelism: change `iter()` to `par_iter()` and it work-steals across a global pool. `crossbeam` for the building blocks: `crossbeam::channel` (fast MPMC, `select!`), scoped threads, epoch-based lock-free structures. Neither is async; bridge from tokio with `spawn_blocking` plus a `oneshot`. See `async-and-concurrency.md`.

## 8. GUI and app frameworks, honestly

- **egui**: immediate-mode GUI (the whole UI is re-declared every frame, like Dear ImGui). Superb for tools, debug panels, and anything a game loop would host; portable (native + wasm) via `eframe`. It will not look native, and complex retained-style layouts fight the paradigm.
- **Tauri**: not a Rust GUI at all; it is a lightweight shell that puts **your JS/TS web frontend** (React, Svelte, whatever) in the OS webview with a Rust backend over an IPC bridge. Tiny binaries vs Electron, mature tooling, but your UI code is still JavaScript.
- **Dioxus**: React's mental model **in Rust**: components, signals, `rsx!`, one codebase targeting web, desktop (webview), mobile, and fullstack with server functions. The most ambitious "all-Rust app" story going. Depth in the dedicated `dioxus.md` page.
- **Leptos / Yew**: web-first Rust frameworks compiled to wasm. Leptos is the modern one (fine-grained signal reactivity, strong SSR + server-function story); Yew is the elder React-alike, still maintained but losing mindshare to Leptos and Dioxus.
- **wasm plumbing**: `wasm-bindgen` generates the JS<->Rust glue for wasm modules; `trunk` is the zero-config bundler/dev server for wasm apps (Leptos/Yew workflows lean on it; Dioxus has its own `dx`).

Native-toolkit purists: `gtk4-rs` is solid on Linux; Slint and Iced are the notable Rust-native retained-mode toolkits. There is still no "the" Rust GUI framework.

## 9. Crates.io hygiene

Before adopting a crate: recent releases and commit activity, download curve, open-issue triage, and whether big projects depend on it (reverse deps on crates.io / lib.rs). Then automate the supply chain:

```bash
cargo install cargo-audit && cargo audit    # scan Cargo.lock against the RustSec advisory DB
cargo install cargo-deny  && cargo deny check   # advisories + license policy + duplicate/banned crates
```

`cargo deny` belongs in CI; `cargo tree -d` shows duplicate dependency versions bloating your build.

## Gotchas

- serde needs the `derive` feature; the bare `serde` crate silently lacks the macros and the error ("cannot find derive macro") doesn't say why.
- `#[serde(untagged)]` matches variants **in declaration order**: put the most specific first, or an early permissive variant swallows everything (numbers parsing as the `String`-holding variant, etc.).
- clap derive: doc comments become help text, so a stray paragraph in `///` ends up user-visible. `#[arg(short)]` panics at runtime on duplicate short flags, caught only when the parser builds (test with `Cli::command().debug_assert()`).
- Constructing a new `reqwest::Client` per request leaks the connection-pool benefit and can exhaust sockets under load; clone one shared client (it is an `Arc` internally).
- sqlx compile-time checking needs `DATABASE_URL` at build time or committed `sqlx prepare` metadata (`.sqlx/`); CI fails mysteriously without one of them.
- `tracing` emits nothing until a subscriber is installed; a library that logs but no output usually means `tracing_subscriber::fmt().init()` never ran in the binary.
- axum handler type errors are notorious: a handler that doesn't satisfy the `Handler` trait produces a wall of generics. Slap `#[axum::debug_handler]` on it for a human-readable diagnosis.
- Tauri apps' UI bugs are web bugs: you are debugging a webview (platform-divergent WebKit/WebView2), not Rust. Don't pick Tauri expecting to write the frontend in Rust; that is Dioxus/Leptos territory.
