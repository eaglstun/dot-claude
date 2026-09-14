---
semantic_id: "WNHvDJfXqeR7JxyxqAEzE7q6URC5MAAG"
related_ids:
  - "lPD-DXbp6RT7h5y4CJExUbg6VkUpIAAH"
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
---
# Pattern matching and enums

Source:

- <https://doc.rust-lang.org/book/ch06-00-enums.html> (enums, Option, match)
- <https://doc.rust-lang.org/book/ch18-00-patterns.html> (all pattern forms)
- <https://doc.rust-lang.org/reference/patterns.html> (the normative grammar)
- <https://doc.rust-lang.org/reference/items/enumerations.html> (discriminants, repr)
- <https://doc.rust-lang.org/std/macro.matches.html> (matches!)
- <https://doc.rust-lang.org/edition-guide/rust-2024/match-ergonomics.html> (2024 binding-mode rules)

## 1. Enums are sum types, not C constants

A Rust enum variant can carry data, and each variant carries a different shape:

```rust
enum Shape {
    Unit,                              // no data
    Circle(f64),                       // tuple variant
    Rect { w: f64, h: f64 },           // struct variant
}
```

The value is exactly one variant at a time, and the only way to read the payload is to
match. That is the whole design: illegal states are unrepresentable, and the compiler
forces you to handle every case you claimed could exist.

A field-less enum is still C-like and can be cast: `Color::Red as u8`. Assign explicit
discriminants (`Red = 1`) when the numbers cross an FFI boundary, and add `#[repr(u8)]`
so the layout is guaranteed rather than whatever rustc picked. Casting the other way
(`u8 as Color`) does not exist; write a `TryFrom` or use `num_enum`.

Rust exploits unused bit patterns ("niches"), so `Option<Box<T>>`, `Option<&T>`, and
`Option<NonZeroU32>` are the same size as the inner type. `Option<u32>` is not: 8 bytes,
because every `u32` bit pattern is valid.

## 2. The pattern catalogue

```rust
match value {
    0 => ...,                          // literal
    1..=9 => ...,                      // inclusive range (exclusive `..` also allowed)
    n @ 10..=99 => ...,                // binding plus subpattern: n is bound AND range-checked
    Shape::Circle(r) if r > 0.0 => ..., // guard
    Shape::Rect { w, .. } => ...,      // struct destructure, `..` ignores the rest
    Shape::Unit | Shape::Circle(_) => ..., // or-pattern
    _ => ...,                          // catch-all
}
```

Slices and arrays have their own forms, which are underused:

```rust
match args.as_slice() {
    [] => usage(),
    [one] => run(one),
    [first, .., last] => span(first, last),
    [head, tail @ ..] => recurse(head, tail),   // tail: &[T]
}
```

`matches!(expr, PAT)` and `matches!(expr, PAT if cond)` collapse a match to a bool. It
does not bind anything usable outside the macro; it is a test, not an extractor.

## 3. Match ergonomics and the 2024 edition rules

Matching a reference against a non-reference pattern auto-dereferences and flips the
default binding mode to `ref`, so this works and `name` is a `&String`:

```rust
let opt: &Option<String> = &Some("x".into());
if let Some(name) = opt { /* name: &String */ }
```

Before this feature you wrote `Some(ref name)`. `ref` and `ref mut` still exist and are
still occasionally needed (binding by reference out of a value you own, without moving
it), but in new code they are rare.

The 2024 edition tightened the rules: you can no longer mix an explicit `&` pattern with
an already-flipped binding mode, and `mut` on a binding resets the mode instead of
silently inheriting it. Code that compiled in 2021 and now errors under 2024 usually
just needs the redundant `&` or `ref` deleted.

## 4. if let, while let, let-else, and let-chains

- `if let PAT = expr { }` when one arm matters and nothing needs to early-return.
- `while let Some(x) = stack.pop() { }` loops until the pattern stops matching.
- `let PAT = expr else { diverge };` binds into the enclosing scope or bails. The else
  block must diverge (`return`, `break`, `continue`, `panic!`) or it is E0308.
- **let-chains**: `if let Some(a) = x && a.is_valid() && let Some(b) = a.next() { }`.
  Stable since Rust 1.88, **2024 edition only**. In 2021 and earlier this is a syntax
  error, which is the most common "why does this not compile on my machine" for let
  chains: check the `edition` in Cargo.toml before anything else.

`let-else` is the right tool for guard clauses because the happy path stays unindented.

## 5. Exhaustiveness, `_`, and `#[non_exhaustive]`

The compiler proves every possible value is covered, and the proof ignores guards: a
`match` whose only arms are `Some(x) if x > 0` and `None` is non-exhaustive (E0004),
because the checker cannot evaluate `x > 0`.

Prefer listing variants over a trailing `_ =>` in code you own. When a new variant is
added later, an explicit list gives you a compile error at every place that needs
updating, which is the main practical benefit of enums; a `_` arm silently absorbs it.

`#[non_exhaustive]` on a public enum forces _downstream_ crates to include a `_` arm, so
you can add variants without a semver break. Inside the defining crate it has no effect.
The same attribute on a struct blocks literal construction and exhaustive destructuring
outside the crate.

## 6. Option and Result without matching

Most matches on `Option`/`Result` are better as combinators:

| want                   | Option                         | Result                            |
| ---------------------- | ------------------------------ | --------------------------------- |
| transform the value    | `map`                          | `map`                             |
| transform the failure  | (n/a)                          | `map_err`                         |
| chain a fallible step  | `and_then`                     | `and_then`                        |
| default value          | `unwrap_or`/`_else`/`_default` | `unwrap_or`/`_else`               |
| keep only if predicate | `filter`                       | (n/a)                             |
| convert between them   | `ok_or`/`ok_or_else`           | `ok`/`err`                        |
| iterate 0-or-1 items   | `into_iter`/`iter`             | `into_iter`                       |
| collect many into one  | `Option<Vec<_>>` via `collect` | `Result<Vec<_>, E>` via `collect` |

That last row is the trick worth memorising: `iter.map(fallible).collect::<Result<Vec<_>, _>>()`
short-circuits on the first error and gives you a `Result` around the whole batch.
`?` handles the rest. Reach for `match` when several variants need genuinely different
code, not to unwrap one value.

## Gotchas

- **A lowercase identifier in a pattern always binds, never compares.** `match x { limit => ... }`
  with a `const limit` in scope shadows it and matches everything. Constants used in
  patterns must be `SCREAMING_CASE`, and this is exactly why that convention is enforced
  by a lint rather than being cosmetic.
- Matching by value moves non-`Copy` payloads out of the scrutinee, so the original is
  gone afterwards (E0382). Match on `&value`, or use `ref`, or call `.as_ref()` first.
- A guard cannot move out of the bound value, because the guard runs before the arm is
  committed to and might fall through to the next arm.
- `..=` is the inclusive range in patterns; `...` is removed. An exclusive `..` range
  pattern is allowed but only stabilised relatively recently, so old code uses `..=` plus
  arithmetic.
- Float patterns are deprecated and lint-warned: `f64::NAN` matches nothing, including
  itself, so exhaustiveness on floats is a lie.
- Or-patterns must bind **exactly the same names with the same types** in every alternative;
  `Some(x) | None` is E0408.
- `_` discards without binding and therefore does not drop the value at the match; `let _ = guard;`
  drops the guard immediately, while `let _guard = guard;` holds it to end of scope. This
  silently breaks `MutexGuard` and RAII types.
- `..` in a struct pattern means "the remaining fields"; `..` in a slice pattern means "any
  number of elements". Same token, different rules, and only one of them can appear once
  per slice pattern.
- Adding `#[non_exhaustive]` to an enum after publishing is itself a breaking change for
  anyone who wrote an exhaustive match. Add it in the first release or never.
- `matches!` swallows type errors in the pattern position in confusing ways because the
  macro expands to a `match`; if the message points at the macro, expand it by hand first.
