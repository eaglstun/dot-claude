---
topic_id: "v2:OJLK"
topic_path: "rust-arkit/rust-fundamentals"
semantic_id: "ncB9CVZ-7c35N3b8MJTyUftLYzF5YAAL"
related_ids:
  - "HbA7Gddd68D7J5T4OpWSU2nbdVVpcAAO"
  - "mNh7HTZN7Sx7lhTsrrZSUeipcjxoYAAN"
---
# Ownership, borrowing, and lifetimes

Source:

- https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html (ownership + moves)
- https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html (borrow rules)
- https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html (lifetime annotations, elision)
- https://doc.rust-lang.org/book/ch15-05-interior-mutability.html (RefCell, interior mutability)
- https://doc.rust-lang.org/std/borrow/enum.Cow.html (Cow)
- https://doc.rust-lang.org/error_codes/E0502.html (and E0597, E0499 siblings)

## 1. Moves vs Copy

Assignment, passing by value, and returning by value all **move** ownership. After a move the source binding is dead; using it is E0382 ("use of moved value"). Types that are `Copy` (all-scalar types: integers, floats, `bool`, `char`, shared references `&T`, tuples/arrays of Copy types) are bit-copied instead, and the source stays valid.

```rust
let s1 = String::from("hi");
let s2 = s1;            // move: String is not Copy (owns heap data)
// println!("{s1}");    // E0382
let n1 = 5; let n2 = n1; // Copy: both fine
```

- `Copy` requires `Clone` and is incompatible with `Drop`. A struct is only `Copy` if you derive it AND every field is `Copy`.
- `Clone` is the explicit, possibly-expensive deep copy. `Copy` is implicit and always a cheap memcpy.
- Moves happen in more places than people expect: into closures with `move`, into `for` loops (`for x in vec` moves the Vec), and per-field via partial moves out of structs.

## 2. The borrow rules

At any given point, for a given value, you may have **either any number of shared references (`&T`) or exactly one mutable reference (`&mut T`), never both**. References must never outlive the value they point to. The compiler enforces this with **non-lexical lifetimes (NLL)**: a borrow ends at its **last use**, not at the end of its lexical scope, so this compiles:

```rust
let mut v = vec![1, 2, 3];
let first = &v[0];
println!("{first}");   // last use of the shared borrow
v.push(4);             // fine: borrow already ended (NLL)
```

## 3. Common borrowck errors and idiomatic fixes

- **E0502** (cannot borrow as mutable because also borrowed as immutable): usually a read borrow held across a mutation. Fix by finishing the read first (copy the value out: `let len = v.len();` before `v.push(len)`), or restructure with `split_at_mut`, indices, or the entry API.
- **E0499** (cannot borrow as mutable more than once): two `&mut` alive at once, classically two `&mut v[i]` from the same slice. Fix with `slice::split_at_mut`, `std::mem::swap`/`take`/`replace`, or iterate with `iter_mut()` instead of indexing twice.
- **E0597** (borrowed value does not live long enough): a reference escapes the scope of its owner, e.g. returning `&local` or storing a ref to a temporary. Fix by returning the owned value, extending the owner's scope (`let` the temporary into a binding), or storing owned data (`String` not `&str`) in the struct.

## 4. Lifetime annotations and elision

Lifetimes never change how long anything lives; they only **describe** relationships so the compiler can check them. You write them when the compiler cannot infer which input a returned reference borrows from:

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

The **elision rules** (why most signatures need no `'a`):

1. Each elided input reference gets its own fresh lifetime parameter.
2. If there is exactly one input lifetime, it is assigned to all elided output lifetimes.
3. If one of the inputs is `&self` or `&mut self`, `self`'s lifetime is assigned to elided outputs.

If none of the three rules produces an output lifetime, you must annotate. `'static` means "lives for the whole program" (string literals, leaked boxes); reaching for `'static` to silence an error is almost always wrong: fix ownership instead.

## 5. Interior mutability decision table

Mutating through a shared handle requires an interior-mutability wrapper. Pick by thread model and access pattern:

| Need                                  | Single-thread                                            | Multi-thread                                                              |
| ------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------- |
| Shared ownership (refcount)           | `Rc<T>`                                                  | `Arc<T>`                                                                  |
| Mutate a `Copy` value in place        | `Cell<T>` (get/set, no borrow)                           | `AtomicUsize` etc.                                                        |
| Mutate non-Copy data, runtime-checked | `RefCell<T>` (borrow/borrow_mut, **panics** on conflict) | `Mutex<T>` / `RwLock<T>` (blocks; `RwLock` = many readers XOR one writer) |
| Shared AND mutable                    | `Rc<RefCell<T>>`                                         | `Arc<Mutex<T>>`                                                           |

The split is enforced by the type system: `Rc` and `RefCell` are not `Send`/`Sync`, so the compiler stops you from using the single-thread column across threads. `Rc<RefCell<T>>` misuse is a **runtime panic** (BorrowMutError); `Arc<Mutex<T>>` misuse is a **deadlock**. Reference cycles through `Rc<RefCell<T>>` leak: break them with `Weak<T>`.

## 6. Cow, and when to just clone

`std::borrow::Cow<'a, B>` (clone-on-write) holds either `Borrowed(&'a B)` or `Owned(B::Owned)`. Use it when a function usually returns its input untouched but sometimes must allocate a modified copy:

```rust
use std::borrow::Cow;
fn strip_dashes(s: &str) -> Cow<'_, str> {
    if s.contains('-') { Cow::Owned(s.replace('-', "")) } else { Cow::Borrowed(s) }
}
```

**When to clone and stop fighting:** if satisfying the borrow checker requires threading lifetimes through three structs, or a self-referential struct, or an `Rc` web you don't want, a `.clone()` of a small `String`/`Vec` is fine. Clone first, profile later; the borrow checker rewards owned data at API boundaries (`String` in struct fields, `&str` in function parameters).

## Gotchas

- `&mut` requires the binding itself to be `mut`: `let x = ...; &mut x` fails with E0596. `let mut x` first.
- Indexing `v[0]` on a `Vec<String>` tries to **move** the element out and fails (E0507); use `&v[0]`, `v[0].clone()`, or `v.remove(0)`.
- NLL is per-use, but a borrow stored in a variable that is used later stays live that whole span, and any borrow held by a value with a `Drop` impl lasts until the drop point.
- Method calls auto-reborrow, so `v.push(x)` inside a loop over `&v` still errors: the loop's shared borrow spans the body (E0502). Collect indices or use `retain`/`drain`.
- `Copy` types inside a struct don't make the struct `Copy`; you must derive it, and you can't if any field (like `String`) isn't `Copy`.
- Elision rule 3 means `fn get(&self) -> &str` borrows from `self`, even if you meant it to borrow from a field's `'static` data. Annotate explicitly if the output should outlive `self`.
- `RefCell::borrow_mut()` while any `borrow()` guard is alive panics at runtime; the classic bug is holding a guard across a call that re-borrows. Keep guards in tight scopes (`{ let b = cell.borrow(); ... }`).
- `Mutex` in std has no poisoning escape hatch you can ignore: `.lock().unwrap()` panics if a previous holder panicked. Handle or accept the propagation deliberately.
- A `match` or `if let` on `&option` gives you references to the innards (`Some(x)` binds `x: &T`); people then fight E0507 trying to move `x`. Use `as_ref()`, `cloned()`, or `take()` intentionally.
- Returning `&str` from a function that builds a `String` locally is E0597 forever; return `String` (or `Cow<str>`), not a reference to a dead local.
