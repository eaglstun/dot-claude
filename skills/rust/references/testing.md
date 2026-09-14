---
semantic_id: "3PCoCXZd78wrDZg5rJFYUflZVpdJoAAM"
related_ids:
  - "2vC-TVZ5bsyhB7yQCJWY0fkdVxdoMAAF"
  - "lPD-DXbp6RT7h5y4CJExUbg6VkUpIAAH"
---
# Testing and benchmarking

Source:

- <https://doc.rust-lang.org/book/ch11-00-testing.html> (writing and organising tests)
- <https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html> (doc tests)
- <https://doc.rust-lang.org/cargo/commands/cargo-test.html> (the CLI)
- <https://nexte.st/> (cargo-nextest)
- <https://bheisler.github.io/criterion.rs/book/> (criterion benchmarks)
- <https://docs.rs/proptest/latest/proptest/> and <https://insta.rs/> (property and snapshot testing)

## 1. The built-in harness

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_a_port() {
        assert_eq!(parse_port("8080").unwrap(), 8080);
    }

    #[test]
    fn rejects_garbage() -> Result<(), Box<dyn std::error::Error>> {
        assert!(parse_port("nope").is_err());
        Ok(())          // a test may return Result; Err fails the test
    }

    #[test]
    #[should_panic(expected = "index out of bounds")]
    fn panics_on_overrun() { let v: Vec<u8> = vec![]; let _ = v[3]; }

    #[test]
    #[ignore = "hits the network"]
    fn live_api() { /* cargo test -- --ignored */ }
}
```

`#[cfg(test)] mod tests` inside the file under test is the unit-test convention: it can
reach private items, and it is compiled out of normal builds entirely.

Assertions: `assert!`, `assert_eq!`, `assert_ne!`, all of which take a trailing format
string (`assert!(ok, "expected {x} to be valid")`). `assert_eq!` requires `Debug` and
`PartialEq`. `debug_assert!` compiles away in release.

## 2. cargo test in practice

```bash
cargo test                        # unit + integration + doc tests
cargo test parses                 # substring filter on test names
cargo test -- --exact a::b::c     # one test, precisely
cargo test -- --ignored           # only the #[ignore]d ones
cargo test -- --include-ignored   # everything
cargo test -- --show-output       # print stdout from PASSING tests too
cargo test -- --test-threads=1    # serialise (see gotchas)
cargo test --lib                  # unit tests only, skip doc tests: fastest loop
cargo test --doc                  # doc tests only
cargo test --all-features --workspace
```

Tests run in **parallel threads within one process** by default, and output from passing
tests is captured and discarded.

## 3. Test kinds and where they live

- **Unit**: `#[cfg(test)] mod tests` in the source file. Sees private items. Fast.
- **Integration**: `tests/foo.rs`. A separate crate; sees only the public API. Shared
  helpers go in `tests/common/mod.rs` (a plain `tests/common.rs` becomes its own empty
  test binary).
- **Doc tests**: fenced code in `///` comments, compiled and run as standalone programs.
  They are documentation first and regression tests second, which is the right priority.

````rust
/// Adds two ports.
///
/// ```
/// # use mycrate::add;                 // `#` hides the line from rendered docs
/// assert_eq!(add(2, 3), 5);
/// ```
///
/// ```should_panic
/// mycrate::add(u16::MAX, 1);
/// ```
///
/// ```no_run
/// mycrate::connect("prod")?;          // compiled, never executed
/// # Ok::<(), mycrate::Error>(())
/// ```
````

Other fence attributes: `ignore` (not even compiled, use sparingly), `compile_fail` (must
fail to compile, good for proving a sealed trait or lifetime is enforced), `text` (not
Rust at all).

## 4. The crates worth reaching for

| need                            | crate                      | note                                              |
| ------------------------------- | -------------------------- | ------------------------------------------------- |
| faster runner, per-test process | `cargo-nextest`            | process isolation, better output, retries, JUnit  |
| readable diffs on failure       | `pretty_assertions`        | drop-in `assert_eq!` replacement                  |
| async tests                     | `#[tokio::test]`           | needs tokio `macros` + `rt` features              |
| parameterised tests/fixtures    | `rstest`                   | `#[case]` tables, fixture injection               |
| property testing                | `proptest`                 | generates inputs, shrinks failures to a minimum   |
| snapshot testing                | `insta`                    | `assert_yaml_snapshot!`, `cargo insta review`     |
| HTTP mocking                    | `wiremock`                 | real local server, better than mocking the client |
| trait mocking                   | `mockall`                  | only when the seam is genuinely a trait           |
| temp files/dirs                 | `tempfile`                 | auto-cleaned, unique per test                     |
| serialised env/CWD tests        | `serial_test`              | `#[serial]` for the tests that cannot be parallel |
| coverage                        | `cargo-llvm-cov`           | `cargo llvm-cov --html`                           |
| UB detection                    | `cargo +nightly miri test` | mandatory if the crate has `unsafe`               |

Property testing is the highest-value addition to a parser, codec, or numeric routine:

```rust
proptest! {
    #[test]
    fn roundtrips(s in ".*") {
        prop_assert_eq!(decode(&encode(&s))?, s);
    }
}
```

## 5. Benchmarking

`#[bench]` is nightly-only and effectively frozen. Use **criterion** on stable:

```toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "parse"
harness = false          # REQUIRED: criterion supplies its own main()
```

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_parse(c: &mut Criterion) {
    let input = std::fs::read_to_string("fixtures/big.json").unwrap();
    c.bench_function("parse big", |b| b.iter(|| parse(black_box(&input))));
}
criterion_group!(benches, bench_parse);
criterion_main!(benches);
```

`black_box` is not optional. Without it the optimiser observes that the result is unused
and deletes the work, and you measure an empty loop at 300 picoseconds. Criterion runs
warmups, reports confidence intervals, and compares against the previous run, which is the
only way to tell a real 3% win from noise. `divan` is a lighter modern alternative with
the same discipline.

## 6. Making tests deterministic

- Never read or write the process environment or the current directory from a parallel
  test. In the 2024 edition `std::env::set_var` is **`unsafe`** precisely because it is a
  data race against any other thread. If you must, use `#[serial]`.
- Inject the clock, the RNG seed, and the filesystem root rather than reaching for the
  ambient one. A `struct Deps { now: fn() -> Instant, root: PathBuf }` beats a mocking
  framework.
- Use `tempfile::tempdir()` instead of a fixed `/tmp/test` path shared by every test.
- Bind test servers to port 0 and read back the assigned port.

## Gotchas

- **Tests run in parallel by default**, so any shared global state (env vars, current dir,
  a fixed port, a singleton logger, a file on disk) produces failures that only appear
  under load and vanish under `--test-threads=1`. That vanishing act is the diagnosis, not
  the fix.
- **Doc tests do not run under `cargo test --all-targets`.** That flag looks like "even
  more tests" and actually excludes the doc tests entirely. Run `cargo test` plain, or add
  an explicit `cargo test --doc`.
- Doc tests do not exist for binary crates, and they do not exist for private items.
- `cargo nextest run` does not run doc tests at all (by design: each test is its own
  process). Keep a separate `cargo test --doc` step in CI.
- `#[should_panic]` **without** `expected = "..."` passes when the test panics for a
  completely unrelated reason, including a typo in the setup. Always give the expected
  substring.
- `assert!(result.is_ok())` prints `assertion failed: result.is_ok()` and throws the error
  away. Use `result.unwrap()` or `assert!(x.is_ok(), "{:?}", x.err())` so the failure is
  legible.
- Integration tests in `tests/` cannot see `pub(crate)` items, so a test that "used to
  work" after moving it out of the module is a visibility problem, not a logic one.
- `--release` disables integer-overflow checks and `debug_assert!`, so a test suite that
  is green in debug can be wrong in release and vice versa. Run CI both ways for numeric
  code.
- Criterion benches without `harness = false` fail with a confusing "no main function"
  or run libtest's harness and find zero tests.
- `cargo test` compiles `dev-dependencies` into the same feature-unified graph, so a
  dev-dependency enabling a feature of a normal dependency can mask a broken default build.
  Verify with `cargo check --no-default-features`.
- Miri does not run code that calls out to C or does real I/O. A crate with FFI needs the
  `unsafe` logic factored into a pure part that Miri can reach.
