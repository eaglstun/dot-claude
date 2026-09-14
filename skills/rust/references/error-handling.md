---
topic_id: "v2:OJJN"
topic_path: "rust-arkit/rust-fundamentals"
semantic_id: "vKDvGWJf70R7BhSoKrHZWYhJ0XTIcAAA"
related_ids:
  - "_LDnGSZx7kR7lwyEKpe_U7lKEUTsUAAM"
  - "KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"
---
# Error handling

Source:

- <https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html> (Result, ?, main)
- <https://doc.rust-lang.org/book/ch09-03-to-panic-or-not-to-panic.html> (panic vs Result)
- <https://doc.rust-lang.org/std/error/trait.Error.html> (the Error trait)
- <https://docs.rs/thiserror/latest/thiserror/> (library-style errors)
- <https://docs.rs/anyhow/latest/anyhow/> (application-style errors)
- <https://doc.rust-lang.org/rust-by-example/flow_control/let_else.html> (let-else)

## 1. Result, Option, and `?`

`Result<T, E>` is for operations that can fail with a reason; `Option<T>` is for absence with no reason. The `?` operator unwraps the success value or **early-returns** the failure, converting the error via `From`:

```rust
fn read_username(path: &str) -> Result<String, io::Error> {
    let mut s = String::new();
    File::open(path)?.read_to_string(&mut s)?;
    Ok(s)
}
```

- `?` works in any function returning `Result`, `Option`, or another `FromResidual` type; the surrounding return type must match (`?` on an `Option` inside a `Result`-returning fn is E0277; bridge with `.ok_or(...)?` or `.ok()?` the other way).
- The `From` conversion is the whole trick: `?` calls `From::from(err)` to convert the concrete error into the function's error type. Any `E2: From<E1>` lets `?` cross the boundary silently. This is what error-type crates automate.

## 2. Box<dyn Error> and the two-crate rule of thumb

`Box<dyn std::error::Error>` accepts any error (everything sensible implements `Error`) and `?` boxes it automatically. Fine for examples and quick tools; loses the ability to match on variants, and add `+ Send + Sync + 'static` if it crosses threads.

The ecosystem rule of thumb:

- **Libraries: `thiserror`.** Callers need to match on what went wrong, so expose a real enum. `thiserror` derives `Display`, `Error`, and `From` without boilerplate and is zero-cost sugar (no runtime machinery):

```rust
#[derive(Debug, thiserror::Error)]
pub enum DataError {
    #[error("io failure reading {path}")]
    Io { path: String, #[source] source: std::io::Error },
    #[error("bad record at line {0}")]
    Parse(usize),
    #[error(transparent)]
    Other(#[from] anyhow::Error),
}
```

- **Applications: `anyhow`.** The binary just reports and exits, so use one universal type, `anyhow::Result<T>` (= `Result<T, anyhow::Error>`), which swallows any `Error + Send + Sync + 'static` via `?` and carries context and a backtrace:

```rust
use anyhow::{Context, Result};
fn main() -> Result<()> {
    let cfg = std::fs::read_to_string("app.toml")
        .context("failed to read app.toml")?;
    let port: u16 = cfg.trim().parse()
        .with_context(|| format!("bad port in config: {cfg:?}"))?;
    run(port)
}
```

Mixing is normal: a binary uses anyhow at the top and consumes thiserror-typed errors from its own library crates.

## 3. panic! vs Result

Panic = unrecoverable bug (violated invariant, impossible state); Result = expected, reportable failure (missing file, bad input, network). `unwrap`/`expect` are fine when:

- prototypes, examples, and tests (a panicking test is a failing test),
- you have knowledge the compiler doesn't and the invariant is locally provable: `Regex::new("^[a-z]+$").expect("hardcoded regex is valid")`,
- an invariant violation means the program is already broken and continuing would be worse.

Prefer `expect("why this cannot fail")` over bare `unwrap`: the message becomes the panic string. Never `unwrap` on data from outside the program (user input, files, the network). Indexing (`v[i]`), integer division, and `RefCell::borrow_mut` are implicit panic sites; use `get`, `checked_div`, `try_borrow_mut` where failure is real.

## 4. Returning Result from main

`main` may return any `Result<(), E> where E: Debug` (via the `Termination` trait). On `Err`, the process prints the `Debug` form and exits with a nonzero code, and `?` becomes usable in `main`:

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let contents = std::fs::read_to_string("input.txt")?;
    println!("{contents}");
    Ok(())
}
```

With anyhow, `fn main() -> anyhow::Result<()>` prints the full context chain, which is usually the nicest zero-effort CLI error output.

## 5. Context patterns

- **`.context("...")` / `.with_context(|| ...)`** (anyhow, on both Result and Option): wraps the error with a human breadcrumb; chains print as `error: X / Caused by: Y`. Use `with_context` when the message allocates, so it's lazy.
- **`.map_err(|e| ...)`** (std): transform the error type by hand when there's no `From` impl or you need data from the call site:

```rust
let n: u32 = s.parse().map_err(|e| ConfigError::BadPort { raw: s.into(), source: e })?;
```

- **`.ok_or(err)` / `.ok_or_else(|| err)`**: Option -> Result so `?` can take over.
- In thiserror types, `#[from]` generates the `From` impl so plain `?` converts; `#[source]` preserves the cause chain without a `From` (use it when two variants wrap the same source type, since `#[from]` twice on one source type conflicts).

## 6. matching vs let-else

`match` when every variant gets real handling. `if let` when only one arm matters and there's no early return. **`let-else`** (stable since 1.65) when you want to destructure or bail, keeping the happy path unindented:

```rust
let Some(user) = find_user(id) else {
    return Err(AppError::UnknownUser(id));
};
// `user` is bound here, no nesting
```

The else block must diverge (`return`, `break`, `continue`, `panic!`); that requirement is E0308 if you forget.

## Gotchas

- `?` on `Option` inside a `Result`-returning function does not compile (E0277); it needs `.ok_or(...)?`. The error message ("`?` couldn't convert...") confuses people into blaming the Ok type.
- `anyhow::Error` does **not** implement `std::error::Error` itself (deliberate, to avoid a blanket-impl conflict), so a thiserror variant wrapping it needs `#[error(transparent)] Other(#[from] anyhow::Error)` rather than `#[source]` tricks, and a library returning anyhow leaks that decision to every caller: don't do it in libraries.
- Two thiserror variants with `#[from]` on the same source type (e.g. two `std::io::Error` wrappers) is a compile error: `From` impls would overlap. Use `#[source]` plus `map_err` for the second.
- `Box<dyn Error>` is not `Send`, so it fails the moment it crosses `tokio::spawn` or a thread boundary; the working general type is `Box<dyn Error + Send + Sync + 'static>` (which is exactly what anyhow wraps).
- `.context()` on a `Result<T, E>` requires `E: Error + Send + Sync + 'static`; a `Box<dyn Error>` error (not Send) won't take context. Convert earlier.
- `unwrap_or(expensive())` evaluates the fallback eagerly even on the Ok path; use `unwrap_or_else(|| expensive())`, same for `ok_or` vs `ok_or_else`, `map_or` vs lazy forms.
- Returning `Result` from `main` prints the **Debug** representation, not Display: a custom error without a useful `Debug` prints poorly; anyhow's Debug is specifically formatted to look like Display plus the cause chain, which is why it looks good there.
- Panics unwind by default but abort under `panic = "abort"` profiles; library code must not rely on `catch_unwind` for control flow, and `catch_unwind` doesn't catch aborts.
- `expect` messages should state the invariant ("config validated at startup"), not restate the failure ("failed to parse"), because the runtime already prints the underlying error after your message.
