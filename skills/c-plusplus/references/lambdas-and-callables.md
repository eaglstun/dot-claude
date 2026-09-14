---
semantic_id: "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
related_ids:
  - "KYoBAO7rixqWMsoCrGGfYbAvrZxIMAAP"
  - "IQ45VK5BgTq3ssTGrmMbZ_wloZxQQAAI"
---
# Lambdas, function objects, and callables

Source:

- https://en.cppreference.com/w/cpp/language/lambda
- https://en.cppreference.com/w/cpp/utility/functional/function
- https://en.cppreference.com/w/cpp/utility/functional/function_ref (C++26)
- https://en.cppreference.com/w/cpp/utility/functional/bind_front
- https://en.cppreference.com/w/cpp/utility/functional/invoke

## 1. Anatomy

```cpp
auto f = [captures] <template-params> (params) specifiers -> ReturnType { body };
//        ^          ^ C++20          ^        ^ mutable/noexcept/constexpr/static(C++23)
```

A lambda is sugar for a unique, unnamed class with an `operator()`. Each lambda
expression has its **own distinct type** — two identical-looking lambdas are
different types, which is why you store them in `auto`, not in a named type.

```cpp
auto add   = [](int a, int b) { return a + b; };
auto gen   = [n = 0]() mutable { return n++; };        // init-capture, mutable state
auto tmpl  = []<class T>(const std::vector<T>& v) { return v.size(); };   // C++20
constexpr auto sq = [](int x) constexpr { return x * x; };
```

## 2. Captures

| Form                                   | Meaning                                                   |
| -------------------------------------- | --------------------------------------------------------- |
| `[x]`                                  | copy `x`                                                  |
| `[&x]`                                 | reference `x`                                             |
| `[=]`                                  | copy everything used (and `this` **by pointer**)          |
| `[&]`                                  | reference everything used                                 |
| `[this]`                               | capture the `this` pointer (members accessed through it)  |
| `[*this]`                              | copy the whole enclosing object (C++17)                   |
| `[x = expr]`                           | init-capture: new member initialized from `expr` (C++14)  |
| `[p = std::move(p)]`                   | move a `unique_ptr` into the lambda                       |
| `[...args = std::forward<Args>(args)]` | pack init-capture (C++20)                                 |
| `[]`                                   | capture nothing → convertible to a plain function pointer |

**`[=]` does not copy `this`'s members.** It copies the `this` _pointer_, so a
lambda that outlives the object dangles even though it "captured by value". This
is the single most common lambda bug in async code; C++20 deprecates implicit
`this` capture via `[=]`. Write `[*this]` (copy) or `[self = shared_from_this()]`
(keep alive) instead.

Rules of thumb:

- **Lambda used and discarded within the expression** (algorithm predicates,
  `sort` comparators): `[&]` is fine and cheapest.
- **Lambda stored, queued, or sent to another thread**: capture explicitly, by
  value, and never `[&]`. A reference capture of a local is a dangling reference
  the moment the scope exits.

By default `operator()` is `const`, so captured-by-copy members are read-only;
`mutable` removes the `const` (it does not make copies writable "in the caller").

## 3. Storing callables

| Storage                              | Cost                                          | Use                                               |
| ------------------------------------ | --------------------------------------------- | ------------------------------------------------- |
| `auto` (the lambda itself)           | zero, inlinable                               | local use, template parameter                     |
| template parameter `F&&`             | zero, inlinable                               | generic algorithms — the default for library code |
| `std::function<R(Args...)>`          | type erasure, virtual call, may heap-allocate | stored callbacks, ABI boundaries                  |
| `std::move_only_function` (C++23)    | same, move-only, `const`-correct              | callbacks capturing `unique_ptr`                  |
| `std::function_ref` (C++26)          | non-owning, no allocation, 2 pointers         | _parameter_ type for a callback                   |
| raw function pointer `R(*)(Args...)` | zero                                          | C interop; only captureless lambdas convert       |

```cpp
template <class F> void for_each_row(F&& f);        // fast path: no erasure
void set_callback(std::function<void(Event)> cb);   // stored: erasure is the point
void visit_rows(std::function_ref<void(Row)> f);    // C++26: parameter, no allocation
```

Do not use `std::function` as a _parameter_ type when the callable is only used
during the call — it forces an allocation and an indirect call for nothing. That
is what `function_ref` (or a template parameter) is for.

`std::function` requires the callable to be **copyable**, so a lambda capturing a
`unique_ptr` will not fit. Hence `std::move_only_function`.

## 4. `std::invoke`, `bind_front`, and friends

`std::invoke(f, args...)` handles every callable uniformly, including
pointer-to-member syntax:

```cpp
std::invoke(&Widget::area, w);          // w.area()
std::invoke(&Widget::area, ptr);        // ptr->area()
std::invoke(&Widget::name, w) = "x";    // member data pointer
std::invoke(lambda, 1, 2);
```

Use `std::bind_front` / `bind_back` (C++20/23), never `std::bind`:

```cpp
auto bound = std::bind_front(&Server::handle, this);   // this->handle(rest...)
auto to10  = std::bind_back(std::clamp<int>, 0, 10);
```

`std::bind` has surprising placeholder semantics, breaks with overloads, and is
strictly worse than a lambda. `std::mem_fn` is still occasionally handy, but a
projection (`&Person::age`) usually beats it in ranges code.

## 5. Overload sets and the visitor idiom

A lambda cannot capture an overload set; wrap it:

```cpp
#define LIFT(f) [](auto&&... a) -> decltype(auto) { return f(decltype(a)(a)...); }
std::ranges::transform(v, out, LIFT(std::abs));
```

The `overloaded` helper for `std::visit` (C++17, needs no macro):

```cpp
template <class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template <class... Ts> overloaded(Ts...) -> overloaded<Ts...>;   // CTAD guide (not needed in C++20)

std::visit(overloaded{
    [](int i)                { std::print("int {}\n", i); },
    [](const std::string& s) { std::print("str {}\n", s); },
    [](auto&&)               { std::print("other\n"); },        // fallback
}, var);
```

## 6. Recursion, `static`, and other corners

A lambda cannot name itself. Options: `std::function` (slow), a `Y`-combinator
helper, or C++23 deducing `this`:

```cpp
auto fib = [](this auto&& self, int n) -> int {     // C++23
    return n < 2 ? n : self(n - 1) + self(n - 2);
};
```

`static operator()` (C++23) removes the unused `this` from captureless lambdas —
a real win in hot comparator loops:

```cpp
auto cmp = [](const A& a, const A& b) static { return a.k < b.k; };
```

Immediately-invoked lambdas initialize `const` values that need logic:

```cpp
const auto config = [] {
    Config c;
    c.load(default_path);
    return c;
}();                                     // note the ()
```

## Gotchas

- `[=]` captures `this` by pointer, not the object. Async callbacks on a
  destroyed object are the result. Deprecated in C++20; prefer `[*this]` or an
  explicit list.
- `[&]` in anything stored, deferred, or threaded is a dangling reference
  waiting to happen. Capture explicitly at the point of storage.
- Each lambda has a unique type: `std::vector<decltype(lambda)>` works,
  `std::vector` of _two different_ lambdas does not. Erase with `std::function`
  or a common base.
- A `mutable` lambda's `operator()` is non-`const`, so it cannot be called
  through a `const std::function` — `move_only_function` fixed this asymmetry.
- Default arguments are not allowed in lambda parameters before C++14 and are
  fine after; but a lambda's parameter pack does not deduce like a function
  template's unless you use `auto...`.
- Capturing a structured binding was ill-formed in C++17 and allowed in C++20 —
  a portability trap on older toolchains.
- `std::function` may heap-allocate; small-object optimization covers roughly
  2–3 pointers of captures on most implementations, and the threshold is not
  standardized.
- A captureless lambda converts to a function pointer implicitly — handy for C
  callbacks that take no user-data pointer, and impossible the moment you
  capture anything.
