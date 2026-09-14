---
semantic_id: "n7I9WRbq68T5NzSnqLVyUpgbMU0oMAAC"
related_ids:
  - "HbA7Gddd68D7J5T4OpWSU2nbdVVpcAAO"
  - "ncB9CVZ-7c35N3b8MJTyUftLYzF5YAAL"
---
# Closures and the Fn traits

Source:

- <https://doc.rust-lang.org/book/ch13-01-closures.html> (capture, move, the three traits)
- <https://doc.rust-lang.org/reference/types/closure.html> (closure types, capture modes)
- <https://doc.rust-lang.org/std/ops/trait.FnMut.html> (and `Fn`, `FnOnce`)
- <https://doc.rust-lang.org/edition-guide/rust-2021/disjoint-capture-in-closures.html>
- <https://blog.rust-lang.org/2025/02/20/Rust-1.85.0.html> (async closures)

## 1. The three traits are a hierarchy

| trait    | receiver    | can be called             | captured by                  |
| -------- | ----------- | ------------------------- | ---------------------------- |
| `FnOnce` | `self`      | exactly once              | at least one capture by move |
| `FnMut`  | `&mut self` | many times, mutates state | at least one `&mut` capture  |
| `Fn`     | `&self`     | many times, concurrently  | all captures by `&`          |

Every `Fn` is an `FnMut`, and every `FnMut` is an `FnOnce`. So take the **weakest** bound
your code needs: a function that calls the closure once should ask for `FnOnce`, and it
will then accept all three.

The compiler picks the strictest category the body allows, automatically. You never write
`impl Fn for` anything; you write a closure and get whichever traits it qualifies for.

```rust
let s = String::from("hi");
let print = || println!("{s}");        // Fn:      borrows s
let mut n = 0;
let mut bump = || n += 1;              // FnMut:   &mut n
let consume = move || drop(s);         // FnOnce:  moves s, drops it
```

## 2. `move`, and what it actually does

`move` forces every capture to be **by value**. It does not decide whether the closure is
`FnOnce`; a `move` closure that only reads its `Copy` captures is still `Fn`.

You need `move` whenever the closure outlives the scope that created it: `thread::spawn`,
`tokio::spawn`, storing a callback in a struct, returning a closure. Those all require
`'static`, and a closure borrowing a local is not `'static`.

The idiomatic dance when you need a shared value in several `move` closures is to clone
the handle first:

```rust
let cfg = Arc::new(load_config()?);
for i in 0..4 {
    let cfg = Arc::clone(&cfg);        // shadow with a per-closure clone
    thread::spawn(move || work(i, &cfg));
}
```

Since the 2021 edition, closures capture **disjoint fields** rather than the whole struct:
`move || println!("{}", s.name)` captures `s.name` alone, leaving the rest of `s` usable.
This mostly removes the old `let name = &s.name;` preamble, and it changed drop timing (see
gotchas).

## 3. Taking a closure as a parameter

```rust
fn retry<T, E, F: FnMut() -> Result<T, E>>(mut f: F, times: u32) -> Result<T, E> { ... }
fn apply(f: impl Fn(u32) -> u32) -> u32 { f(1) }              // APIT: same thing
fn on_event(&mut self, cb: Box<dyn Fn(&Event) + Send + 'static>) { ... }
```

Generic (`F: Fn...` or `impl Fn...`) is monomorphised: no allocation, no indirection,
inlinable, but it is a distinct instantiation per call site and cannot be stored
heterogeneously. `Box<dyn Fn...>` is one allocation and a virtual call, and it is the only
option when you need a `Vec` of callbacks or a field of unknown closure type.

For a struct field, `Box<dyn Fn(&Event) + Send + Sync + 'static>` is the workhorse. Add
only the auto traits you actually need; each one narrows what callers can pass.

## 4. Returning a closure

```rust
fn adder(n: i32) -> impl Fn(i32) -> i32 { move |x| x + n }        // preferred
fn boxed(n: i32) -> Box<dyn Fn(i32) -> i32> { Box::new(move |x| x + n) }
```

`impl Fn` is zero-cost but pins you to exactly one concrete closure: two branches returning
two different closures is E0308, and the fix is boxing (or an enum of the two).

If the closure borrows from an argument, say so:

```rust
fn matcher<'a>(pat: &'a str) -> impl Fn(&str) -> bool + 'a {
    move |s| s.contains(pat)
}
```

Without the `+ 'a` you get E0700, "hidden type captures lifetime". Note that in the **2024
edition** RPIT captures all in-scope lifetimes by default, so this often now just works;
in earlier editions the explicit bound is required. `use<>` syntax exists to opt back out.

## 5. Closures versus function pointers

A closure that captures **nothing** coerces to a plain `fn` pointer:

```rust
let f: fn(u32) -> u32 = |x| x * 2;          // fine
let n = 3;
let g: fn(u32) -> u32 = |x| x * n;          // E0308: this one captures
```

`fn` is `Copy`, `Send`, `Sync`, and FFI-compatible (`extern "C" fn` for callbacks handed to
C). Prefer `fn` in a struct field or a `const` table when no capture is needed; it is a
single word instead of a trait object.

Any `fn` also implements all three `Fn` traits, so `iter.map(str::trim)` works: a path to a
function is a value of a zero-sized fn-item type.

## 6. Async closures

Stable since Rust 1.85. `async || { ... }` implements `AsyncFn` / `AsyncFnMut` /
`AsyncFnOnce`, which is genuinely different from a closure returning a future:

```rust
async fn retry<F>(mut f: F) where F: AsyncFnMut() -> Result<(), Error> {
    for _ in 0..3 { if f().await.is_ok() { return; } }
}
```

The pre-1.85 workaround, `F: FnMut() -> Fut, Fut: Future`, cannot express a future that
borrows from the closure's captured state, which is exactly the case that kept forcing
`Arc<Mutex<_>>` into callback APIs. Use `AsyncFn*` in new code; keep the old form if you
support older toolchains.

An `async` block (`async { ... }`) is a future, not a closure: it is created once and
awaited once. An `async move` block captures by value the same way `move` does.

## Gotchas

- **Every closure has its own unique anonymous type.** Two closures with byte-identical
  bodies are different types, so they cannot go in the same `Vec`, cannot be two arms of an
  `if`, and cannot both be returned from one `impl Fn` function. Box them or wrap in an enum.
- `move` moves **everything** captured, including things you only read. If that steals a
  value the surrounding code still needs, clone deliberately before the closure rather than
  dropping `move`.
- A closure passed to `thread::spawn` or `tokio::spawn` must be `'static` **and** the
  future/closure must be `Send`. A non-`Send` capture (`Rc`, `RefCell` guard, a raw
  pointer) produces a very long error whose real content is one line near the end.
- Holding a `MutexGuard` across an `.await` inside an async block makes the future
  non-`Send` and breaks `tokio::spawn`. Drop the guard in an inner scope first.
- `FnMut` closures cannot be called re-entrantly. `v.retain(|x| v.contains(x))` is E0502:
  the closure holds `&mut v` implicitly while `retain` also holds it.
- A `Box<dyn FnOnce()>` is callable (since 1.35) because `Box` can move out of itself, but
  `&dyn FnOnce()` is not: calling requires `self` by value.
- 2021-edition disjoint capture changed **drop order and drop timing**: a closure that used
  to capture and hold a whole struct now may drop the unused parts earlier. Types whose
  `Drop` matters (locks, spans, files) can behave differently. Force the old behaviour with
  `let _ = &whole_struct;` inside the closure.
- `iter.map(|x| x)` on a `&Vec<T>` gives `&T`, and adding `move` there does nothing useful;
  `move` on an iterator adaptor closure is almost always a symptom of confusion about which
  scope owns what.
- Recursive closures do not work directly (the type is being defined by the expression that
  names it). Use a named `fn`, or a `fn` taking itself as an argument.
- A closure capturing `self` inside a method borrows all of `self` in older editions and
  the specific fields in 2021+; a method call inside the closure (`self.helper()`) still
  captures all of `self`, which is a frequent borrow-check surprise. Destructure the fields
  you need before the closure.
