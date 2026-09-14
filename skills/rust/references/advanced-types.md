---
semantic_id: "PPC6CPb97kTyWzSAKoVWUfu7VlxJcAAE"
related_ids:
  - "HbA7Gddd68D7J5T4OpWSU2nbdVVpcAAO"
  - "urRuzaZ578T7mxDgNIRyUfgpM1BJIAAE"
---
# Advanced types

Source:

- <https://doc.rust-lang.org/reference/items/generics.html> (const generics, lifetime/type params)
- <https://blog.rust-lang.org/2022/10/28/gats-stabilization.html> (generic associated types)
- <https://doc.rust-lang.org/nomicon/subtyping.html> (variance, the normative table)
- <https://doc.rust-lang.org/std/marker/struct.PhantomData.html>
- <https://doc.rust-lang.org/reference/types/impl-trait.html> (RPIT, APIT, RPITIT)
- <https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility>

## 1. Const generics

A type may be generic over a value, not just a type:

```rust
struct Matrix<const R: usize, const C: usize> { data: [[f32; C]; R] }

impl<const R: usize, const C: usize> Matrix<R, C> {
    fn transpose(&self) -> Matrix<C, R> { /* ... */ }
}

fn sum<const N: usize>(xs: [u32; N]) -> u32 { xs.iter().sum() }
```

The parameter type must be an integer, `bool`, or `char`. Sizes are checked at compile
time, so `Matrix<2,3> * Matrix<3,4>` type-checks and `Matrix<2,3> * Matrix<2,3>` does not.

The stable-Rust limit: **you cannot do arithmetic on const parameters in a type position**.
`[T; N + 1]` and `Matrix<{R * 2}, C>` require the unstable `generic_const_exprs`. The
workaround is an associated const on a trait, or accepting a second parameter and asserting
the relationship at runtime.

`{ N }` braces are needed when passing a const expression as an argument.

## 2. GATs: associated types with their own parameters

Stable since 1.65. The associated type takes lifetime or type parameters:

```rust
trait LendingIterator {
    type Item<'a> where Self: 'a;
    fn next(&mut self) -> Option<Self::Item<'_>>;
}
```

This is the thing plain `Iterator` cannot express: yielding an item that borrows from the
iterator itself, so each item is invalidated by the next call. `windows_mut`, streaming
parsers, and zero-copy row readers all want it. `Iterator` cannot be retrofitted (it would
break every existing impl), which is why `LendingIterator` is a separate trait and why the
adaptors (`map`, `filter`) do not come for free.

The `where Self: 'a` bound is almost always required, and rustc will tell you to add it.

## 3. PhantomData and variance

`PhantomData<T>` is a zero-sized field that makes a type act, to the type system, as if it
contained a `T`. Three separate effects, all of which you may or may not want:

| declaration               | variance in `T` | owns a `T` for drop check | `Send`/`Sync` from `T` |
| ------------------------- | --------------- | ------------------------- | ---------------------- |
| `PhantomData<T>`          | covariant       | yes                       | yes                    |
| `PhantomData<&'a T>`      | covariant       | no                        | needs `T: Sync`        |
| `PhantomData<*const T>`   | covariant       | no                        | neither (opts out)     |
| `PhantomData<fn(T)>`      | contravariant   | no                        | yes                    |
| `PhantomData<fn(T) -> T>` | invariant       | no                        | yes                    |
| `PhantomData<Cell<T>>`    | invariant       | no                        | not `Sync`             |

Variance decides whether `Foo<&'long T>` can be used where `Foo<&'short T>` is expected.
Covariant is the usual, permissive case (`&'long` substitutes for `&'short`). Invariance is
what `&mut T`, `Cell<T>`, and `UnsafeCell<T>` impose, and it is why a `&mut Vec<&'static str>`
will not coerce to `&mut Vec<&'a str>`: writing through it could smuggle a short reference
into a long-lived slot.

Variance is **inferred** from the fields, never declared. Getting it wrong in an FFI or
raw-pointer wrapper is unsound, not just inconvenient, which is why the table matters more
than it looks.

Common uses: a marker type parameter that appears in no field (`struct Meters<Unit>(f64, PhantomData<Unit>)`),
and telling drop check that a raw-pointer container really does own its `T`.

## 4. impl Trait, in each position

- **Argument position (APIT)**: `fn f(x: impl Display)`. Sugar for a generic parameter,
  except the caller cannot turbofish it. Prefer a named generic in public APIs.
- **Return position (RPIT)**: `fn f() -> impl Iterator<Item = u32>`. One concrete opaque
  type chosen by the body, so all `return` paths must produce the _same_ type. Two
  different closures are two different types: E0308. Box them or use an enum.
- **In traits (RPITIT)**: stable since 1.75, and it is what makes `async fn` in traits work:

```rust
trait Fetch {
    async fn get(&self, url: &str) -> Result<Vec<u8>, Error>;
    // desugars to: fn get(...) -> impl Future<Output = ...> + '_
}
```

The catch is that the returned future has **no `Send` bound**, so a generic caller cannot
`tokio::spawn` it. Options: use `trait_variant::make` to generate a `Send` variant of the
trait, return `Pin<Box<dyn Future + Send>>` by hand (what `async_trait` does), or keep the
trait non-generic and take a concrete type.

- **Type alias impl Trait (TAIT)** is still unstable; `type Fut = impl Future;` does not
  compile on stable.

`impl Trait` in return position leaks auto traits: callers _can_ rely on the returned type
being `Send` if the concrete type happens to be, so making it non-`Send` later is a
breaking change even though nothing in the signature says `Send`.

## 5. dyn compatibility (formerly object safety)

A trait can become `dyn Trait` only if the vtable can be built. The rules that bite:

- No generic methods (`fn f<T>(&self)`), because there is no single vtable entry.
- No methods returning `Self` (except in a `where Self: Sized` method).
- No associated constants, no GATs.
- `Self: Sized` on a method exempts that method: it is excluded from the vtable and simply
  unavailable through `dyn`. That is the standard escape hatch (`Iterator::map` works this
  way, which is why `dyn Iterator` exists at all but has no adaptors).
- Since 1.86, `dyn Trait` upcasting to a supertrait object works, so `&dyn Sub` coerces to
  `&dyn Super`.

Write `dyn Trait` explicitly. Bare `Trait` in type position is a hard error in the 2021
edition and later.

## 6. Type-level techniques

**Newtype** for invariants and for the orphan rule: `struct Sanitized(String)` with a
private field and a validating constructor makes "this string is safe" a compile-time fact.

**Sealed trait** to make a public trait usable but not implementable (see
`modules-and-project-layout.md`).

**Typestate**: encode the state machine in the type so illegal transitions do not compile.

```rust
struct Conn<S> { sock: TcpStream, _s: PhantomData<S> }
struct Open; struct Closed;

impl Conn<Closed> { fn open(self) -> Conn<Open> { /* ... */ } }
impl Conn<Open>   { fn send(&mut self, b: &[u8]) { /* ... */ }
                    fn close(self) -> Conn<Closed> { /* ... */ } }
```

`send` on a closed connection is not a runtime error, it is a missing method.

**The never type `!`** is the type of an expression that does not return (`panic!`,
`return`, `continue`, `loop {}`). It coerces to every type, which is why `let x: u32 = if c { 1 } else { panic!() };`
compiles. `!` in return position is stable (`fn exit() -> !`); `!` as a general type
parameter is not. Absent that, use `std::convert::Infallible`.

**DSTs and `?Sized`**: `str`, `[T]`, and `dyn Trait` have no compile-time size and can only
live behind a pointer. Generic parameters are implicitly `Sized`; write `T: ?Sized` to opt
out, which is what lets `Box<dyn Error>` and `&str` satisfy generic bounds.

## Gotchas

- **`T: 'static` does not mean the value lives forever.** It means the type contains no
  references shorter than `'static`, which every owned type satisfies. `String: 'static` is
  true. The bound is about what a type _can_ borrow, not about lifetime of the value.
- Variance mistakes are silent. A `struct Wrapper<T>(*mut T)` with no `PhantomData` is
  covariant in `T` by inference, which is unsound for a mutable container. Add
  `PhantomData<fn(T) -> T>` to force invariance.
- A GAT method used generically often needs a higher-ranked bound
  (`where for<'a> Self::Item<'a>: Debug`), and the error message for the missing bound is
  famously unhelpful.
- `impl Trait` in return position cannot return two different concrete types from two
  branches, no matter how similar they look. Two closures with identical bodies are still
  two types.
- `async fn` in a trait is not `dyn`-compatible, so `Box<dyn MyAsyncTrait>` does not work
  without `async_trait` or manual `Pin<Box<dyn Future>>` returns.
- Const generic parameters cannot be inferred from a value's runtime length: a `Vec` does
  not convert to `[T; N]` without `try_into()` and a fallible check.
- A type alias creates no new type and enforces nothing: `type UserId = u64;` still accepts
  any `u64`. Use a newtype when you want the compiler's help.
- Adding a lifetime or const parameter to a public type is a breaking change; adding a
  _defaulted_ type parameter usually is not, unless someone wrote the full parameter list.
- Zero-sized types are real and have addresses; `Vec<()>` with a million elements allocates
  nothing but does count, and pointer arithmetic on ZSTs is a classic `unsafe` trap.
- `#[non_exhaustive]` and sealed traits solve different problems: one stops downstream
  _matching_, the other stops downstream _implementing_.
