---
semantic_id: "IQATQK5ri3y3vtZWqidZc_Dx85RIMAAB"
related_ids:
  - "4YIJRq9ryfq3OsxCricZQ_QrtRhKAAAK"
  - "IQ45VK5BgTq3ssTGrmMbZ_wloZxQQAAI"
---
# Templates, concepts, and generic programming

Source:

- https://en.cppreference.com/w/cpp/language/templates
- https://en.cppreference.com/w/cpp/language/template_argument_deduction
- https://en.cppreference.com/w/cpp/language/class_template_argument_deduction (CTAD)
- https://en.cppreference.com/w/cpp/language/constraints (concepts / requires)
- https://en.cppreference.com/w/cpp/concepts (the standard concept library)
- https://en.cppreference.com/w/cpp/language/parameter_pack
- https://en.cppreference.com/w/cpp/language/sfinae

## 1. Function and class templates

```cpp
template <class T>
T max_of(T a, T b) { return a < b ? b : a; }

template <class T, std::size_t N>
struct Array { T data[N]; constexpr std::size_t size() const { return N; } };
```

Templates are **instantiated on use**, per distinct argument set. They are
compiled twice — once at definition (syntax, non-dependent names) and once at
instantiation (everything dependent) — which is why a template with a typo in an
untaken branch can compile for years.

Definitions must be visible at the point of instantiation → templates live in
headers, or you explicitly instantiate in one TU:

```cpp
// widget.cpp
template class Widget<int>;                       // explicit instantiation definition
// widget.hpp
extern template class Widget<int>;                // suppress implicit instantiation elsewhere
```

That pattern cuts compile times when a heavy template is used with a small,
known set of arguments.

## 2. Deduction, CTAD, and `auto`

Template argument deduction strips top-level `const` and references from
by-value parameters, decays arrays and functions to pointers, and does _not_
deduce through implicit conversions.

**CTAD** (C++17) lets you omit class template arguments:

```cpp
std::vector v{1, 2, 3};             // vector<int>
std::pair p{1, 2.0};                // pair<int, double>
std::lock_guard lock{mtx};          // lock_guard<std::mutex>
```

Write a **deduction guide** when the implicit ones are wrong:

```cpp
template <class It>
Range(It, It) -> Range<typename std::iterator_traits<It>::value_type>;
```

`auto` uses the same rules as template deduction; `decltype(auto)` uses
`decltype` rules and therefore _preserves_ references and cv-qualifiers — that is
the tool for perfectly forwarding a return value.

```cpp
template <class F, class... A>
decltype(auto) invoke_log(F&& f, A&&... a) {
    return std::forward<F>(f)(std::forward<A>(a)...);   // keeps T& / T&& returns intact
}
```

## 3. Concepts (C++20) — use these instead of SFINAE

```cpp
template <class T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template <class T>
concept Container = requires(T c) {
    typename T::value_type;
    { c.size() } -> std::convertible_to<std::size_t>;
    { c.begin() } -> std::input_or_output_iterator;
};
```

Four ways to apply one, all equivalent:

```cpp
template <Numeric T> T twice(T x);                  // constrained parameter
template <class T> requires Numeric<T> T twice(T);  // requires clause
template <class T> T twice(T x) requires Numeric<T>;// trailing requires
auto twice(Numeric auto x);                          // abbreviated (each `auto` is its own param!)
```

`requires` _expressions_ (`requires(T c){...}`) are the predicate;
`requires` _clauses_ (`requires Numeric<T>`) apply it. The doubled form
`requires requires (...)` is legal and means "constrain by this ad-hoc
expression" — it works, but naming the concept reads better.

Useful standard concepts: `std::same_as`, `std::derived_from`,
`std::convertible_to`, `std::integral`, `std::floating_point`,
`std::equality_comparable`, `std::totally_ordered`, `std::invocable`,
`std::regular`, `std::movable`, `std::copyable`, plus the iterator and range
concepts (`std::input_iterator`, `std::ranges::range`, `std::ranges::sized_range`).

**Subsumption**: a more-constrained overload wins over a less-constrained one,
which gives you clean overload sets without tag dispatch — but only when the
constraints are literally composed from the same atomic constraints. Two
independently-written `requires` clauses that mean the same thing do _not_
subsume each other, so name your concepts and build from them.

## 4. Variadic templates and fold expressions

```cpp
template <class... Ts>
void print_all(const Ts&... xs) {
    ((std::cout << xs << ' '), ...);            // comma fold
    std::cout << '\n';
}

template <class... Ts> constexpr auto sum(Ts... xs) { return (xs + ... + 0); }  // binary right fold
template <class... Ts> constexpr bool all_of(Ts... bs) { return (bs && ...); }  // unary right fold
constexpr std::size_t n = sizeof...(Ts);
```

Fold forms: `(pack op ...)` unary right, `(... op pack)` unary left,
`(pack op ... op init)` binary right, `(init op ... op pack)` binary left.
Empty packs are only allowed for `&&` (true), `||` (false), and `,` (void).

Pack expansion happens wherever a comma-separated list is legal:
`f(g(xs)...)`, `Base<Ts>...`, `std::tuple<Ts...>`, `[xs...]` in a lambda capture.

C++26 adds pack indexing (`Ts...[0]`); until then use
`std::tuple_element_t<0, std::tuple<Ts...>>`.

## 5. `if constexpr` and tag dispatch

```cpp
template <class T>
std::string to_string(const T& x) {
    if constexpr (std::is_arithmetic_v<T>) return std::to_string(x);
    else if constexpr (requires { x.to_string(); }) return x.to_string();
    else return std::string{x};
}
```

The discarded branch is **not instantiated** (though it must still parse), which
replaces the vast majority of pre-C++17 SFINAE overload pairs. Note it only
discards when the condition is _dependent_ on a template parameter.

## 6. SFINAE, for reading old code

Substitution failure in the _immediate context_ of a signature removes the
candidate rather than erroring. Pre-C++20 you saw:

```cpp
template <class T, class = std::enable_if_t<std::is_integral_v<T>>>
void f(T);

template <class T>
auto g(T x) -> decltype(x.size(), void()) { }      // "expression SFINAE"
```

Replace with concepts in new code. `void_t`, `enable_if_t` and detection idioms
are legacy; `requires` says the same thing legibly and gives a diagnosable error
instead of "no matching function".

## 7. Specialization

```cpp
template <class T> struct Serializer { static std::string run(const T&); };
template <>        struct Serializer<bool> { static std::string run(bool b) { return b ? "true" : "false"; } };
template <class T> struct Serializer<std::vector<T>> { /* partial */ };
```

**Function templates cannot be partially specialized** — overload instead.
Full specialization of a function template is legal but interacts badly with
overload resolution (the "why is my specialization never called" FAQ); prefer
plain overloads or a class-template helper.

Specializing a standard-library template for _your own_ type is the sanctioned
customization point (`std::hash`, `std::formatter`, `std::tuple_size`):

```cpp
template <> struct std::hash<Point> {
    std::size_t operator()(const Point& p) const noexcept {
        return std::hash<int>{}(p.x) ^ (std::hash<int>{}(p.y) << 1);
    }
};
```

## 8. Dependent names

Inside a template, a name that depends on a template parameter needs help:

```cpp
template <class T>
void f() {
    typename T::value_type v;          // `typename`: it's a type
    T::template rebind<int> r;         // `template`: it's a template
    this->base_member = 1;             // needed in a class template deriving from a dependent base
}
```

C++20 relaxed many `typename` requirements; C++23 more. Older compilers still
demand it, and MSVC's permissive mode historically didn't — code that builds on
MSVC and fails on GCC is usually a missing `typename` or a missing `this->`.

## Gotchas

- Template code compiles only when instantiated. A `constexpr if` branch that is
  never taken still must **parse**, and a member function of a class template
  that is never called is never checked. Cover generic code with tests that
  actually instantiate every path.
- Error messages: constrain early with concepts, or `static_assert` at the top of
  the function body. A 400-line error from deep inside `std::sort` almost always
  means an unmet comparator requirement.
- `auto f(Numeric auto a, Numeric auto b)` declares **two independent** template
  parameters — `f(1, 2.0)` compiles. Use `template <Numeric T> f(T, T)` when you
  need them to match.
- Two-phase lookup means non-dependent names bind at definition; a helper
  declared _after_ the template but found at instantiation only works via ADL.
- Forwarding-reference constructors (`template<class T> Widget(T&&)`) beat the
  copy constructor for non-const lvalues and hijack everything. Constrain with
  `requires (!std::same_as<std::remove_cvref_t<T>, Widget>)`.
- Heavy template use is the #1 cause of slow builds and huge binaries: measure
  with `-ftime-trace` (clang) and consider type-erasing the hot generic boundary.
- `std::vector<bool>` is a specialization that is not a container of `bool`;
  `auto& b = v[i]` gives you a proxy reference. Use `std::vector<char>` or
  `std::bitset` when that matters.
