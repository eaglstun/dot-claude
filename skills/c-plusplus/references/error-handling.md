---
semantic_id: "paaJ0arbyxp7KsZDqnGfc_ivhVTQcAAF"
related_ids:
  - "oYIZQevJizy_KooSq2GfY_wvmRnQIAAK"
  - "pQIIQOvLiA73ysaCqnDfMPUvlVgIcAAB"
---
# Error handling: exceptions, `expected`, and the guarantees

Source:

- https://en.cppreference.com/w/cpp/language/exceptions
- https://en.cppreference.com/w/cpp/error/exception
- https://en.cppreference.com/w/cpp/utility/expected (C++23)
- https://en.cppreference.com/w/cpp/error/error_code
- https://en.cppreference.com/w/cpp/language/noexcept_spec
- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-errors

## 1. Choosing a mechanism

| Kind of failure                                     | Mechanism                                           |
| --------------------------------------------------- | --------------------------------------------------- |
| Programming bug (precondition violated)             | `assert` / contract / terminate. Do **not** throw.  |
| Expected, recoverable, part of the API's contract   | `std::expected<T, E>` (C++23) or `std::optional<T>` |
| Rare, exceptional, must not be ignorable            | exception                                           |
| Crossing a C ABI or a `noexcept` boundary           | error code, `std::error_code`, or `expected`        |
| Unrecoverable (OOM in a fixed-size embedded system) | terminate/abort                                     |

The community split is real: exceptions are the language default and the only
mechanism that works through constructors and operators; `expected`/error codes
dominate in game engines, embedded, and codebases built with `-fno-exceptions`.
**Follow the surrounding codebase**, and do not mix arbitrarily within one API.

## 2. Exceptions

```cpp
struct ParseError : std::runtime_error {
    std::size_t line;
    ParseError(std::size_t l, const std::string& what)
        : std::runtime_error(what), line(l) {}
};

try {
    parse(input);
} catch (const ParseError& e) {          // catch by const reference, always
    log("line {}: {}", e.line, e.what());
} catch (const std::exception& e) {
    log("unexpected: {}", e.what());
    throw;                               // rethrow preserves the original object & type
}
```

Rules that matter:

- **Throw by value, catch by `const&`.** Catching by value slices.
- Derive from `std::exception` (usually `std::runtime_error` or
  `std::logic_error`) so a generic handler can report something.
- Order handlers most-derived first; `catch (...)` last, and only to log-and-
  rethrow or to guard a thread/`main` boundary.
- `throw;` rethrows the current exception; `throw e;` copies (and may slice).
- Cleanup happens via destructors during stack unwinding — this is RAII's whole
  purpose. Never write cleanup code in a `catch` block that a destructor could do.

**Never throw from a destructor.** During unwinding, a second exception calls
`std::terminate`. Destructors are implicitly `noexcept` since C++11, so a throw
there terminates even outside unwinding.

Cost model: **zero cost on the non-throwing path** (table-driven unwinding), but
throwing is expensive — microseconds, a global lock in some runtimes, and the
unwind tables inflate the binary. Exceptions are for the exceptional; do not use
them for control flow in a hot loop.

## 3. `noexcept`

```cpp
void swap(Widget& a, Widget& b) noexcept;
Widget(Widget&&) noexcept;                     // enables vector's move-on-realloc
constexpr bool ok = noexcept(a.swap(b));       // the operator: query, don't declare
template <class T> void f(T t) noexcept(std::is_nothrow_copy_constructible_v<T>);
```

Mark `noexcept`: move constructors and move assignment (or `std::vector` copies
instead of moving on reallocation), `swap`, destructors (implicit), and simple
leaf functions. Do **not** spray it everywhere — a `noexcept` function that
throws calls `std::terminate` with no unwinding, and removing it later is an ABI
and contract break.

`noexcept` is _not_ part of the function type for overloading, but it _is_ part
of the type for function pointers since C++17.

## 4. `std::expected` (C++23) and `std::optional`

```cpp
std::expected<Config, ParseError> load(std::string_view path);

auto cfg = load("app.toml");
if (!cfg) return std::unexpected(cfg.error());
use(*cfg);                     // or cfg.value() — throws bad_expected_access if empty
int port = cfg->port;
```

Monadic operations (also on `optional` since C++23) chain without pyramid nesting:

```cpp
auto result = load(path)
    .and_then(validate)              // expected<T,E> -> expected<U,E>
    .transform(&Config::port)        // T -> U
    .transform_error(to_message)     // E -> F
    .value_or(8080);
```

`std::optional<T>` is `expected` with no error information: use it when "absent"
needs no explanation (a lookup miss, an unset field). Note `optional` has no
`operator bool` ambiguity trap only because it is `explicit`; still,
`if (opt)` tests _presence_, not the contained value — `std::optional<bool>` is
the classic confusion.

Neither type allows references directly (`optional<T&>` lands in C++26); use
`std::optional<std::reference_wrapper<T>>` or a raw pointer until then.

## 5. `std::error_code` and `errno`-style APIs

```cpp
std::error_code ec;
auto size = std::filesystem::file_size(path, ec);   // non-throwing overload
if (ec) log("{}: {}", path, ec.message());
```

`error_code` is a lightweight (value, category) pair with no allocation — the
right vehicle for OS errors. `error_condition` is the portable abstraction over
platform-specific codes. Register your own domain by specializing
`std::is_error_code_enum` and providing a category singleton.

The standard library exposes non-throwing overloads for `<filesystem>` and
`<charconv>`; `std::from_chars` / `std::to_chars` return a struct with an
`errc`, allocate nothing, and are the fast, locale-independent replacement for
`stoi`/`sprintf`.

## 6. The exception-safety guarantees

| Guarantee   | Meaning                                                                    |
| ----------- | -------------------------------------------------------------------------- |
| **Nothrow** | Will not throw. (`swap`, destructors, `noexcept` moves.)                   |
| **Strong**  | Commit-or-rollback: on failure, state is unchanged. (`vector::push_back`.) |
| **Basic**   | No leaks, all invariants hold, but state may have changed.                 |
| **None**    | Avoid.                                                                     |

The **copy-and-swap** idiom buys the strong guarantee cheaply:

```cpp
Widget& operator=(Widget other) noexcept {   // by value: copy or move happens in the caller
    swap(*this, other);                       // nothrow
    return *this;                             // old state destroyed with `other`
}
```

Aim for basic everywhere and strong where a caller could plausibly retry.
`vector::push_back` gives strong only if `T`'s move is `noexcept` — one more
reason to mark it.

## 7. Assertions and contracts

```cpp
assert(index < size_);                                     // disabled by NDEBUG
static_assert(std::is_trivially_copyable_v<T>);            // compile time
if (!invariant) std::abort();                              // always on
[[assume(x > 0)]];                                         // C++23: tell the optimizer, check nothing
```

Preconditions violated by _your own code_ are bugs: assert and crash loudly in
debug, and decide deliberately what release does. Preconditions violated by
_untrusted input_ are not bugs: validate and return an error.

C++26 adds real contracts (`pre`, `post`, `contract_assert`) with build-time
selectable enforcement; until then, `assert` plus a project-local
`CHECK`/`ENSURE` macro that survives NDEBUG is the common pattern.

## Gotchas

- Catching by value slices the exception to its base and loses the message.
- `throw e;` inside a `catch (const Base& e)` throws a _copy of the base_. Use
  bare `throw;`.
- Destructors are `noexcept` by default; a throwing destructor terminates.
- A `noexcept` function that throws terminates _without unwinding_ — no
  destructors run, so RAII does not clean up.
- Exceptions do not cross a C ABI boundary or a thread boundary. Wrap thread
  bodies in `try/catch`, or use `std::promise::set_exception` /
  `std::current_exception` + `std::rethrow_exception` to move one across.
- An exception escaping a `std::thread`'s function calls `std::terminate` —
  `std::jthread` does not change that.
- `-fno-exceptions` makes `throw` call `abort()` and turns every standard-library
  throw into a terminate; check before assuming a library works in that mode.
- `std::expected` unchecked `operator*` on an error state is UB, same as
  `optional`. `.value()` throws instead.
- Don't return `bool` for failure and stuff the result into an out-parameter;
  `expected`/`optional` is the same cost and cannot be ignored silently
  (`[[nodiscard]]` them).
