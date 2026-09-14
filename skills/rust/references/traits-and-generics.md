---
topic_id: "v2:OJKI"
topic_path: "rust-arkit/rust-fundamentals"
semantic_id: "HbA7Gddd68D7J5T4OpWSU2nbdVVpcAAO"
related_ids:
  - "GbgrDXdh6ZT7FrawCIEyUfh7dFB4YAAO"
  - "KSDvGfd468R7VzWBMJEQWErLcXV4QAAD"
---
# Traits and generics

Source:

- https://doc.rust-lang.org/book/ch10-02-traits.html (traits, bounds, default methods, blanket impls)
- https://doc.rust-lang.org/book/ch18-02-trait-objects.html (dyn Trait)
- https://doc.rust-lang.org/reference/items/traits.html (dyn compatibility rules)
- https://doc.rust-lang.org/std/convert/index.html (From/Into/TryFrom/AsRef)
- https://doc.rust-lang.org/book/ch15-02-deref.html (Deref, deref coercion)
- https://doc.rust-lang.org/reference/items/implementations.html (coherence / orphan rule)

## 1. Bounds and where clauses

```rust
fn notify<T: Summary + Display>(item: &T) { ... }          // inline bound
fn notify2<T>(item: &T) where T: Summary + Display { ... } // same, tidier when many
```

`where` clauses can express things inline bounds cannot, like bounds on non-parameter types (`where Option<T>: Debug`). Bounds also gate methods conditionally:

```rust
impl<T: Display + PartialOrd> Pair<T> { fn cmp_display(&self) { ... } }
```

## 2. impl Trait vs dyn Trait

- **Argument position** `fn f(x: impl Summary)` is sugar for a generic `fn f<T: Summary>(x: T)`. Monomorphized, static dispatch, zero cost. Difference: you can't turbofish an APIT parameter.
- **Return position** `fn f() -> impl Iterator<Item = u32>` returns one concrete, hidden type. All return paths must be the **same** type; returning either of two branches' different iterator types fails (E0308). It is the only way to return closures/iterators by value without boxing.
- **`dyn Trait`** (`Box<dyn Summary>`, `&dyn Summary`) is a fat pointer (data ptr + vtable ptr): dynamic dispatch, one code copy, heterogenous collections (`Vec<Box<dyn Draw>>`). Costs a vtable indirection and blocks inlining. Since Rust 2021, bare `dyn` is required (`Box<Trait>` no longer compiles the old way).

**Dyn compatibility** (formerly "object safety"): a trait can be a trait object only if, roughly:

- no `Self: Sized` requirement on the trait itself,
- no associated constants and no associated functions without a method receiver,
- every method is dispatchable: no generic type parameters, doesn't use `Self` except through the receiver, receiver is `&self`/`&mut self`/`Box<Self>`/`Rc<Self>`/`Arc<Self>`/`Pin` of those,
- or the offending method is opted out with `where Self: Sized`.

`Clone` is not dyn compatible (returns `Self`); neither is anything with a generic method. The compile error is E0038.

## 3. Associated types vs generic params

```rust
trait Iterator { type Item; fn next(&mut self) -> Option<Self::Item>; }   // one Item per impl
trait Convert<T> { fn convert(&self) -> T; }                              // many impls per type
```

Use an **associated type** when each implementing type has exactly one sensible choice (an iterator has one `Item`). Use a **generic parameter** when one type should implement the trait multiple ways (`From<u8>` and `From<u16>` both for `u32`). Associated types also read better in bounds: `I: Iterator<Item = u32>`.

## 4. The conversion traits

- **`From`/`Into`**: implement `From<A> for B`; you get `Into<B> for A` free via the blanket impl. Always implement `From`, never `Into` directly. Infallible.
- **`TryFrom`/`TryInto`**: fallible versions returning `Result<Self, Self::Error>` (e.g. `i32::try_from(some_u64)`). Same blanket relationship.
- **`AsRef<T>`**: cheap reference-to-reference conversion, the idiomatic flexible parameter: `fn open(p: impl AsRef<Path>)` accepts `&str`, `String`, `PathBuf`, `&Path`.
- **`Borrow<T>`**: like `AsRef` plus a contract that `Eq`/`Ord`/`Hash` agree between owned and borrowed forms. This is why `HashMap<String, V>::get` takes `&Q where String: Borrow<Q>`, letting you look up with `&str`. Prefer `AsRef` unless you need that hashing contract.

## 5. Deref and deref coercion

`Deref` makes `*x` work and powers **deref coercion**: `&String -> &str`, `&Box<T> -> &T`, `&Vec<T> -> &[T]` happen automatically at call sites, and method lookup walks the deref chain. Implement `Deref` only for smart pointers that genuinely "are" a `T` (Box, Rc, guards, newtype wrappers around one field, cautiously).

**Do not abuse Deref for inheritance.** `impl Deref for Dog { type Target = Animal }` to "inherit" methods compiles but is widely considered an anti-pattern: it confuses method resolution, doesn't implement traits for you (a `Dog` still isn't `impl Animal`-bounded anywhere), and breaks silently when names collide. Use trait default methods or composition + delegation instead.

## 6. Orphan rule and the newtype workaround

Coherence: you may `impl Trait for Type` only if the trait **or** the type is local to your crate. So no `impl Display for Vec<String>` (both foreign). Workaround is a **newtype**:

```rust
struct Wrapper(Vec<String>);
impl fmt::Display for Wrapper {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "[{}]", self.0.join(", "))
    }
}
```

Cost: the wrapper has none of `Vec`'s methods; forward what you need, or (judiciously) `impl Deref`. Newtypes are also the idiom for units (`Meters(f64)`) and for restricting APIs.

## 7. Default methods and blanket impls

Default method bodies let implementors override only what they must, and defaults may call the trait's required methods (`summarize` calling `summarize_author`). A **blanket impl** implements a trait for everything meeting a bound:

```rust
impl<T: Display> ToString for T { ... }   // std's own example
```

Blanket impls are powerful and viral: they can conflict with any other impl of that trait in your crate, and you can't specialize around them on stable.

## 8. GATs in one breath

Generic associated types (stable since 1.65) let an associated type take its own generics: `type Item<'a> where Self: 'a;`. The headline use is **lending iterators**, where `next` returns an item borrowing from the iterator itself, which plain `Iterator` cannot express. Reach for a GAT when an associated type must mention a lifetime supplied per-call.

## Gotchas

- `impl Trait` in return position is **one** hidden concrete type, not "any type implementing Trait". Two different return branches need `Box<dyn Trait>` (or an enum).
- `Box<dyn Trait>` is `Box<dyn Trait + 'static>` by default; storing borrowed data in one needs an explicit `Box<dyn Trait + 'a>`.
- E0038 messages often point at one method; the `where Self: Sized` opt-out on that method restores dyn compatibility for the rest of the trait.
- `impl<T> From<T> for T` exists (reflexive), so writing your own `From<MyType> for MyType`-shaped blanket conversions collides with std's.
- `.into()` frequently needs a type annotation or turbofish because inference can't pick the target: `let n: u64 = x.into();`.
- `Borrow` vs `AsRef` mixups bite in map keys: `HashMap<String, _>` lookup by `&str` works through `Borrow`, but a newtype key without `Borrow<str>` forces you to allocate a `String` per lookup.
- Deref coercion does not apply to generic bounds: a `fn f(x: &str)` accepts `&String`, but `fn f<T: SomeTrait>(x: T)` won't coerce a `String` argument to meet `SomeTrait for &str`.
- Method resolution prefers inherent methods over trait methods, and `&self` methods on the wrapper shadow `Deref`-reached ones; a newtype's own `len` silently wins over the inner type's.
- The orphan rule has a subtlety: `impl ForeignTrait<LocalType> for ForeignType` is allowed when the local type appears as a generic argument before any foreign type parameters (fundamental-type rules); when in doubt, newtype.
- Trait objects don't get auto traits for free: `Box<dyn Error>` is not `Send`; spell it `Box<dyn Error + Send + Sync>` when threads are involved.
