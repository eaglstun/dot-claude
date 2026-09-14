---
semantic_id: "pQIIQOvLiA73ysaCqnDfMPUvlVgIcAAB"
related_ids:
  - "oSo7SEpriq43qtQQqGXbIPU_tdjJIAAB"
  - "paaJ0arbyxp7KsZDqnGfc_ivhVTQcAAF"
---
# Standard versions and compiler support

Source:

- https://en.cppreference.com/w/cpp/compiler_support
- https://en.cppreference.com/w/cpp/feature_test
- https://en.cppreference.com/w/cpp/11 … /w/cpp/23 (per-standard feature lists)
- https://gcc.gnu.org/projects/cxx-status.html
- https://libcxx.llvm.org/Status/Cxx23.html
- https://learn.microsoft.com/en-us/cpp/overview/visual-cpp-language-conformance

## 1. What each standard brought

**C++11** — the reboot. `auto`, range-for, lambdas, move semantics and rvalue
references, `nullptr`, `constexpr`, `enum class`, variadic templates, `= default`
/ `= delete`, `override`/`final`, uniform init, `std::unique_ptr`/`shared_ptr`,
the threading and atomics library, `std::function`, `std::tuple`,
`unordered_*`, `std::chrono`, `<type_traits>`, `<regex>`, raw string literals.

**C++14** — polish. Generic lambdas (`auto` params), init-captures, return type
deduction for normal functions, variable templates, relaxed `constexpr`,
`std::make_unique`, `std::shared_timed_mutex`, binary literals, digit separators,
`[[deprecated]]`.

**C++17** — very large, very adopted. Structured bindings, `if`/`switch` with
initializer, `if constexpr`, CTAD, fold expressions, inline variables,
guaranteed copy elision, `std::optional`/`variant`/`any`/`string_view`,
`<filesystem>`, parallel algorithms, `std::byte`, `std::invoke`/`apply`,
`<charconv>`, nested namespaces, `[[nodiscard]]`/`[[maybe_unused]]`/
`[[fallthrough]]`, aligned `new`, `std::launder`. **This is the pragmatic
baseline for most codebases today.**

**C++20** — the second reboot. Concepts, ranges, coroutines, modules,
`operator<=>`, designated initializers, `constinit`/`consteval` and much more
`constexpr` (including allocation), `std::format`, `std::span`, `std::jthread`
and `stop_token`, `std::latch`/`barrier`/`semaphore`, atomic `wait`/`notify`,
`std::bit_cast` and `<bit>`, calendars and time zones in `<chrono>`,
`std::source_location`, `[[likely]]`/`[[unlikely]]`, abbreviated function
templates, `std::erase`/`erase_if`, `starts_with`/`ends_with`.

**C++23** — quality of life. `std::print`/`println`, `std::expected`,
`std::generator`, `std::mdspan`, `std::flat_map`/`flat_set`, `ranges::to` and a
big pile of new views (`zip`, `enumerate`, `chunk`, `slide`, `stride`,
`cartesian_product`, `repeat`, `join_with`), deducing `this`, `if consteval`,
multidimensional `operator[]`, `std::move_only_function`, `std::byteswap`,
`std::unreachable`, `std::stacktrace`, `[[assume]]`, `import std;`, monadic
`optional`, `std::to_underlying`, `static operator()`.

**C++26** (finalized 2026, shipping incrementally) — `std::execution`
(senders/receivers), reflection, contracts (`pre`/`post`/`contract_assert`),
`std::hive`, `std::inplace_vector`, `std::function_ref`, pack indexing,
`std::simd`, `std::optional<T&>`, `views::concat`, erroneous-behavior rules for
uninitialized reads (a real safety change), and `#embed`.

## 2. Choosing a baseline

| Target                                            | Standard                                           |
| ------------------------------------------------- | -------------------------------------------------- |
| Broadest reach, old distros, vendor toolchains    | **C++17**                                          |
| Modern default, everything but modules works well | **C++20**                                          |
| Greenfield on current compilers                   | **C++23**                                          |
| C++11/14                                          | legacy maintenance only; migration pays for itself |

The constraint is almost never the compiler front end — it's the _standard
library_ and the platform toolchain. GCC 13+/clang 17+/MSVC 19.38+ give you
essentially all of C++20 and most of C++23.

Rough support state (as of 2026): C++20 language features are complete across
GCC 13+, clang 17+, MSVC 19.3x+ — except **modules**, which are usable on MSVC,
workable on clang 17+/GCC 14+ with CMake 3.28+/Ninja, and still rough for
`import std;`. C++23 library coverage is furthest along in MSVC and libstdc++ 14;
libc++ lags on `<print>`, `<generator>`, and several C++23 views.

## 3. Feature-test macros — check, don't guess

```cpp
#include <version>          // all *library* feature-test macros

#if __cpp_lib_format >= 201907L
    std::string s = std::format("{}", x);
#else
    std::string s = fmt::format("{}", x);
#endif

#if __cpp_concepts >= 201907L        // language macros need no header
template <std::integral T> void f(T);
#endif

#if __cpp_lib_ranges_zip >= 202110L
    for (auto [a, b] : std::views::zip(v1, v2)) { }
#endif
```

Common ones: `__cpp_lib_format`, `__cpp_lib_expected`, `__cpp_lib_print`,
`__cpp_lib_ranges`, `__cpp_lib_generator`, `__cpp_lib_mdspan`,
`__cpp_lib_jthread`, `__cpp_lib_source_location`, `__cpp_concepts`,
`__cpp_lib_three_way_comparison`, `__cpp_deducing_this`, `__cpp_modules`.

Testing `__cplusplus` alone is not enough: `-std=c++23` does not mean the library
shipped the feature. (And on MSVC, `__cplusplus` reports `199711L` unless you
pass `/Zc:__cplusplus`.)

## 4. Deprecated and removed

- **Removed in C++17**: `std::auto_ptr`, `std::random_shuffle`, `register`,
  trigraphs, dynamic exception specifications (`throw(X)`), `std::bind1st/2nd`,
  `std::unary_function`.
- **Removed in C++20**: `std::raw_storage_iterator`, `std::is_pod` (use
  `is_trivial` + `is_standard_layout`), `throw()` as a synonym for `noexcept`,
  implicit capture of `this` via `[=]` (deprecated), `u8` character literal type
  change (`char8_t` — a source-breaking change).
- **Removed in C++26**: `std::strstream`, most of `<codecvt>` (already deprecated
  since C++17 with no replacement), `std::rel_ops`.
- Deprecated but alive: `std::iterator` as a base class, `volatile` compound
  assignment, `std::aligned_storage`/`aligned_union` (use `alignas` + a byte
  array), `std::allocator<void>`.

## 5. Migration notes that actually bite

- **C++17**: guaranteed copy elision changes which constructors are required;
  a class that was copyable-only may now work where it didn't, and vice versa
  for classes relying on a copy being made. `auto x{1}` changed meaning from
  `initializer_list<int>` to `int` (C++17 DR, applied retroactively).
- **C++20**: `operator<=>` synthesis changes overload resolution for `==`/`!=` —
  code with hand-written asymmetric comparison operators can become ambiguous.
  `u8"..."` becomes `const char8_t[]`, breaking every `const char*` assignment.
  `std::pow`/comparison of unrelated pointer types tightened.
- **C++23**: mostly additive; `std::aligned_storage` deprecation and the
  narrowing of `char8_t` interfaces are the visible edges.
- The **`_GLIBCXX_USE_CXX11_ABI`** flag and MSVC's `/std:c++latest` are the two
  most common causes of "it links on my machine".

## 6. Compiler-specific portability

```cpp
#if defined(_MSC_VER)
#elif defined(__clang__)          // check clang BEFORE __GNUC__ — clang defines both
#elif defined(__GNUC__)
#endif
```

Standard attributes over vendor extensions where they exist: `[[nodiscard]]`,
`[[maybe_unused]]`, `[[fallthrough]]`, `[[deprecated("use X")]]`,
`[[no_unique_address]]` (huge for empty members — MSVC needs
`[[msvc::no_unique_address]]`), `[[likely]]`/`[[unlikely]]`, `[[assume]]`.

MSVC quirks worth knowing: `/permissive-` is required for two-phase lookup
conformance; `min`/`max` macros from `<windows.h>` need `NOMINMAX`;
`__declspec(dllexport/dllimport)` instead of visibility attributes; and
`/Zc:preprocessor` for a conforming preprocessor.

## Gotchas

- `-std=c++20` does not guarantee `<format>`, `<ranges>` completeness, or
  modules. Check `<version>` macros.
- `__cplusplus` on MSVC is `199711L` without `/Zc:__cplusplus`.
- Mixing `-std=` across translation units is an ODR violation, not a warning.
- `import std;` requires both compiler and build-system support and is the
  single flakiest modern feature; don't make a project depend on it yet.
- libc++ vs libstdc++ differ in _which_ C++23 library features exist — code that
  builds on Linux/GCC may not on macOS/clang for library reasons alone.
- `char8_t` in C++20 breaks `const char* p = u8"x";`. Cast, or avoid `u8`.
- Concepts error messages differ wildly between compilers; if one is unreadable,
  try the other before rewriting the constraint.
- Old Boost workarounds (`boost::optional`, `boost::variant`, `BOOST_FOREACH`,
  `boost::shared_ptr`) in a C++17+ codebase are pure cost — the std versions are
  better supported and interoperate. Migrating them is usually mechanical.
