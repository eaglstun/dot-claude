---
semantic_id: "oYaLQeirGTq3-sKTriN7F_A_hdHIIAAH"
related_ids:
  - "IYIbQC-jij63usyGrWlLKvU7pdhIYAAI"
  - "oYIZQevJizy_KooSq2GfY_wvmRnQIAAK"
---
# constexpr, consteval, and compile-time programming

Source:

- https://en.cppreference.com/w/cpp/language/constexpr
- https://en.cppreference.com/w/cpp/language/consteval
- https://en.cppreference.com/w/cpp/language/constinit
- https://en.cppreference.com/w/cpp/language/constant_expression
- https://en.cppreference.com/w/cpp/language/template_parameters (NTTPs)
- https://en.cppreference.com/w/cpp/types (type traits)

## 1. The four keywords

| Keyword     | Meaning                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------- |
| `const`     | "I will not modify this through this name." Says nothing about compile time.                |
| `constexpr` | _may_ be evaluated at compile time; on a variable, _must_ be.                               |
| `consteval` | **must** be evaluated at compile time (immediate function); calling at runtime is an error. |
| `constinit` | initialized at compile time, but mutable afterwards. Kills the static-init-order fiasco.    |

```cpp
constexpr int square(int n) { return n * n; }
constexpr int a = square(5);        // compile time, guaranteed
int n = read_input();
int b = square(n);                  // runtime call — perfectly legal for constexpr functions

consteval int must(int n) { return n * n; }
int c = must(n);                    // ERROR: argument is not a constant expression

constinit std::atomic<int> counter{0};   // no dynamic init, but writable at runtime
```

A `constexpr` _variable_ is implicitly `const`. A `constexpr` _member function_
is **not** implicitly `const` since C++14.

## 2. What is allowed in a constant expression

Modern `constexpr` is nearly the whole language. As of C++20 you can use loops,
`if`/`switch`, local variables, mutation, `try`/`catch` (C++20, though throwing
still ends constant evaluation), virtual calls (C++20), and — crucially —
**allocation**, as long as everything allocated during constant evaluation is
also freed during it (_transient_ allocation).

```cpp
constexpr int count_set_bits(std::uint64_t x) {
    int n = 0;
    while (x) { n += int(x & 1); x >>= 1; }
    return n;
}
static_assert(count_set_bits(0b1011) == 3);

constexpr std::size_t sum_sizes() {
    std::vector<int> v{1, 2, 3};       // C++20: OK, freed before we return
    return v.size();                    // returning the vector itself would NOT be OK
}
```

Still banned in constant evaluation: `reinterpret_cast`, `goto` (until C++23),
reading uninitialized memory, UB of any kind (this is a _feature_ — UB makes the
program ill-formed at compile time rather than silently miscompiling),
`static` local variables with non-constant init, and anything touching the
runtime environment.

C++23 adds `constexpr` to `std::unique_ptr`, most of `<cmath>`, and allows
non-literal variables, `static`/`thread_local` declarations, and `goto` in
`constexpr` functions that just aren't used in constant evaluation.

`if consteval` (C++23) / `std::is_constant_evaluated()` (C++20) branch on which
context you're in:

```cpp
constexpr double fast_pow(double b, int e) {
    if consteval { return slow_but_exact(b, e); }
    else         { return std::pow(b, e); }
}
```

Never write `if constexpr (std::is_constant_evaluated())` — the condition is
always true in that context. It is one of the sharper foot-guns in the language,
which is why `if consteval` exists.

## 3. `static_assert` and type traits

```cpp
static_assert(sizeof(void*) == 8, "64-bit only");
static_assert(std::is_trivially_copyable_v<Vertex>);
static_assert(alignof(Batch) % 64 == 0, "must be cache-line aligned");
```

C++26 allows a computed message; C++17 allows omitting the message entirely.

Trait families worth memorizing (all in `<type_traits>`, all with `_v`/`_t`
shorthands):

- Categories: `is_integral`, `is_floating_point`, `is_pointer`, `is_enum`,
  `is_class`, `is_same`, `is_base_of`, `is_convertible`
- Properties: `is_trivially_copyable`, `is_standard_layout`, `is_polymorphic`,
  `is_empty`, `is_aggregate`, `has_virtual_destructor`
- Operations: `is_constructible`, `is_nothrow_move_constructible`,
  `is_default_constructible`, `is_invocable_r`
- Transformations: `remove_cvref_t` (C++20 — use this, not the
  `remove_const_t<remove_reference_t<>>` dance), `decay_t`, `conditional_t`,
  `common_type_t`, `underlying_type_t`, `invoke_result_t`

In C++20 prefer the _concepts_ (`std::integral<T>`) over the traits
(`std::is_integral_v<T>`) in constraints; the traits remain the right tool inside
`if constexpr` and `static_assert`.

## 4. Non-type template parameters

```cpp
template <std::size_t N> struct FixedBuffer { char data[N]; };

template <auto V> struct Constant { static constexpr auto value = V; };  // C++17
Constant<42>   c1;
Constant<'x'>  c2;
```

C++20 allows **structural types** (literal class types with public,
non-mutable members) as NTTPs, which unlocks compile-time strings:

```cpp
template <std::size_t N>
struct FixedString {
    char value[N];
    constexpr FixedString(const char (&s)[N]) { std::copy_n(s, N, value); }
};
template <FixedString Name> struct Named { static void hello(); };
Named<"widget">::hello();
```

Floating-point NTTPs are allowed since C++20 too.

## 5. Practical uses

**Compile-time lookup tables** — replaces a generated header or a lazy-init
runtime table:

```cpp
constexpr auto make_crc_table() {
    std::array<std::uint32_t, 256> t{};
    for (std::uint32_t i = 0; i < 256; ++i) {
        std::uint32_t c = i;
        for (int k = 0; k < 8; ++k) c = (c & 1) ? (0xEDB88320u ^ (c >> 1)) : (c >> 1);
        t[i] = c;
    }
    return t;
}
inline constexpr auto crc_table = make_crc_table();
```

**Compile-time validation** — a `consteval` constructor turns a bad literal into
a build error:

```cpp
struct Percent {
    int v;
    consteval Percent(int x) : v(x) { if (x < 0 || x > 100) throw "out of range"; }
};
Percent p = 150;   // compile error; `throw` in constant evaluation is ill-formed
```

(This is exactly how `std::format`'s compile-time format-string checking works.)

**`constexpr` over macros**: `constexpr int kMax = 100;` respects scope, has a
type, and shows up in the debugger. There is no remaining reason to `#define` a
constant.

## Gotchas

- `constexpr` on a function is a _permission_, not a guarantee. The only way to
  force compile-time evaluation is `constexpr`/`constinit` on the initialized
  variable, `consteval`, or use in a template argument / `static_assert`.
- A `constexpr` function that can never be evaluated at compile time for _any_
  argument is ill-formed NDR — compilers may or may not tell you.
- `const` ≠ `constexpr`. `const int n = f();` is a runtime value; `const` on a
  pointer (`int* const` vs `const int*`) is read right to left.
- Anything allocated during constant evaluation must be freed there. A
  `constexpr std::vector` cannot escape to runtime — `constexpr std::array` can.
  (C++26's `std::constexpr_vector`-style fixes are not here yet.)
- `if constexpr (std::is_constant_evaluated())` is always true. Use
  `if (std::is_constant_evaluated())` or C++23 `if consteval`.
- Heavy compile-time computation is _slow_ compilation and can blow the
  constexpr step limit (`-fconstexpr-steps=` on clang, `-fconstexpr-ops-limit=`
  on GCC, `/constexpr:steps` on MSVC).
- `constexpr` implies `inline` for functions, so definitions belong in headers —
  but `constexpr` _variables_ at namespace scope need `inline` (C++17) to avoid
  one copy per TU.
