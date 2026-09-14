---
semantic_id: "L4oZQVJrxn7zOk4ErrUv6vQvi0zIYAAB"
related_ids:
  - "La4BRftpxbrzutYQqNBbYvA_yVRIUAAE"
  - "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
---
# Value categories, move semantics, and forwarding

Source:

- https://en.cppreference.com/w/cpp/language/value_category
- https://en.cppreference.com/w/cpp/language/reference (lvalue/rvalue references)
- https://en.cppreference.com/w/cpp/utility/move
- https://en.cppreference.com/w/cpp/utility/forward
- https://en.cppreference.com/w/cpp/language/copy_elision
- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c-classes-and-class-hierarchies (C.20, C.21, C.66)

## 1. The five value categories

Every expression has a **type** and a **value category**. The categories form a
lattice from two properties: _has identity_ (`i`) and _can be moved from_ (`m`).

| Category    | Identity | Movable | Examples                                                                   |
| ----------- | -------- | ------- | -------------------------------------------------------------------------- |
| **lvalue**  | yes      | no      | named variable, `*p`, `a[i]`, function call returning `T&`, string literal |
| **prvalue** | no       | yes     | `42`, `a + b`, `T{}`, function call returning `T` by value                 |
| **xvalue**  | yes      | yes     | `std::move(x)`, function call returning `T&&`, `a[i]` on an rvalue array   |
| **glvalue** | yes      | —       | lvalue ∪ xvalue                                                            |
| **rvalue**  | —        | yes     | prvalue ∪ xvalue                                                           |

The practical rule: **glvalue = "there is an object there"; rvalue = "you may
steal from it"**. Since C++17 a prvalue is not an object at all — it is an
_initializer_ for one, which is why guaranteed copy elision works (§5).

```cpp
int  x = 0;
int& r = x;
x;              // lvalue
std::move(x);   // xvalue  (type int&&, but the *expression* is an xvalue)
x + 1;          // prvalue
r;              // lvalue
```

Note the classic confusion: **a named rvalue reference is an lvalue.** Inside
`void f(T&& t)`, the expression `t` is an lvalue — you must `std::move(t)` again
to pass the moveness along.

## 2. `std::move` and `std::forward` do nothing at runtime

Both are casts. `std::move(x)` is `static_cast<remove_reference_t<T>&&>(x)`; it
produces an xvalue and _nothing else happens_. The actual stealing is done by
whatever move constructor / move assignment operator gets selected by overload
resolution afterwards.

```cpp
std::string a = "hello";
std::string b = std::move(a);   // b's move-ctor runs; a is now valid-but-unspecified
// a.size() is legal to call, its value is unspecified. a = "new" is legal.
```

**Moved-from state**: for standard library types the object is "valid but
unspecified" — you may destroy it or assign to it, and nothing else without
first querying. (`std::unique_ptr` and `std::shared_ptr` are stricter: moved-from
is guaranteed null. `std::string`/`std::vector` are _not_ guaranteed empty,
though every real implementation leaves them empty.)

## 3. Rule of zero / three / five

- **Rule of zero** (default, do this): declare _no_ destructor, copy, or move
  operations. Compose from members that manage their own resources
  (`std::vector`, `std::unique_ptr`, `std::string`). The compiler generates
  correct copy and move for you.
- **Rule of five**: if you declare _any_ of destructor, copy ctor, copy assign,
  move ctor, move assign, you almost certainly need to reason about all five.
- **Rule of three** is the pre-C++11 subset (dtor, copy ctor, copy assign).

The trap that catches everyone: **declaring a destructor suppresses the implicit
move operations.** The class silently falls back to _copying_ wherever you
expected a move — no error, just slower code.

```cpp
struct Widget {
    std::vector<int> data;
    ~Widget() { log("bye"); }        // <-- move ctor/assign are NOT generated
};
Widget w2 = std::move(w1);           // copies the vector. Silently.
```

Fix: `Widget(Widget&&) = default; Widget& operator=(Widget&&) = default;` (and
then also `= default` the copies, because declaring a move deletes the copies).

## 4. Forwarding (universal) references

`T&&` where `T` is a **deduced template parameter of that same function** is a
_forwarding reference_, not an rvalue reference. Reference collapsing
(`& & → &`, `& && → &`, `&& & → &`, `&& && → &&`) makes it bind to anything.

```cpp
template <class T>
void wrapper(T&& arg) {              // forwarding reference
    inner(std::forward<T>(arg));     // preserves lvalue-ness / rvalue-ness
}
```

Not forwarding references (these are plain rvalue refs):

```cpp
template <class T> void f(std::vector<T>&& v);   // not deduced *as* T&&
template <class T> struct S { void g(T&& t); };  // T fixed by the class, not deduced
void h(auto&& x);                                 // IS a forwarding reference (C++20)
```

C++20 adds `decltype(auto)` returns and `auto&&` parameters; `auto&&` in a
range-for or a lambda parameter is also a forwarding reference.

**`std::forward` needs its template argument spelled out** — `std::forward(x)`
does not compile usefully; always `std::forward<T>(x)`. C++23 adds
`std::forward_like<T>(x)` for forwarding a _member_ with the value category of
the enclosing object (useful in deducing-`this` member functions).

## 5. Copy elision, RVO, and why `return std::move(x)` is wrong

Since **C++17**, elision of the copy from a prvalue into its destination is
_mandatory_, not an optimization:

```cpp
Widget make() { return Widget{}; }   // no copy, no move, ever. Constructed in place.
Widget w = make();                   // still zero copies
```

**NRVO** (returning a _named_ local) is still optional but universally
implemented, and even when not elided the return of a local is treated as an
rvalue automatically (implicit move on return).

So do **not** write `return std::move(local);` — it defeats NRVO and forces an
actual move where you would otherwise get zero operations. Exception: when the
local's type differs from the return type (e.g. returning `std::unique_ptr<Base>`
from a `unique_ptr<Derived>` local), the implicit move applies since C++20 but
older compilers may need the explicit `std::move`.

## 6. Passing conventions cheat sheet

| Situation                                                     | Signature                                       |
| ------------------------------------------------------------- | ----------------------------------------------- |
| Read only, cheap type (`int`, `string_view`, `span`)          | by value                                        |
| Read only, expensive type                                     | `const T&`                                      |
| Read a string, no ownership                                   | `std::string_view`                              |
| Read a contiguous sequence, no ownership                      | `std::span<const T>`                            |
| Function will store a copy                                    | by value + `std::move` into the member          |
| Function will store, both lvalue & rvalue matter and it's hot | `T&&` + `const T&` overloads, or forwarding ref |
| Out parameter                                                 | return by value (prefer), or `T&`               |
| Sink of a unique resource                                     | `std::unique_ptr<T>` by value                   |

The by-value-then-move idiom costs one extra move versus perfect forwarding and
is _much_ simpler; reach for forwarding references only in generic code.

```cpp
struct Person {
    std::string name;
    explicit Person(std::string n) : name(std::move(n)) {}   // one move from any caller
};
```

## Gotchas

- **A named `T&&` parameter is an lvalue.** Forgetting the inner `std::move` /
  `std::forward` silently copies.
- **Declaring a destructor kills implicit moves.** The single most common cause
  of "why is my class slow" in modern C++.
- **`std::move` on a `const T` does nothing.** `const T&&` binds to the _copy_
  constructor (`const T&`), so you get a silent copy. Watch for
  `const auto x = ...; use(std::move(x));`.
- **`return std::move(x)` pessimizes.** So does `return std::move(f())`.
- Moving from a member and then reading it is a bug even though it compiles;
  reassign before reuse.
- `std::move` in a loop over a container you still need afterwards leaves a
  container full of hollow objects — `std::vector<std::string>` whose elements
  are all empty. The vector's `size()` is unchanged, which is what confuses people.
- Move constructors should be `noexcept`, otherwise `std::vector` reallocation
  falls back to copying (it needs the strong exception guarantee). Mark them and
  check with `static_assert(std::is_nothrow_move_constructible_v<T>)`.
- `std::swap` of two objects is 3 moves, not a bit-blit; a class with a
  non-`noexcept` move makes every `std::sort` slower.
