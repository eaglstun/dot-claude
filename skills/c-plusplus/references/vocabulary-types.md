---
semantic_id: "IYQXQPP5izhTIsSDqgHHU7wrjRxIYAAK"
related_ids:
  - "JYITQf9rzy2z6tyVq2Fbc_w_hR4AIAAF"
  - "KYoBAO7rixqWMsoCrGGfYbAvrZxIMAAP"
---
# Vocabulary types: optional, variant, tuple, chrono, filesystem

Source:

- https://en.cppreference.com/w/cpp/utility/optional
- https://en.cppreference.com/w/cpp/utility/variant
- https://en.cppreference.com/w/cpp/utility/tuple
- https://en.cppreference.com/w/cpp/chrono
- https://en.cppreference.com/w/cpp/filesystem
- https://en.cppreference.com/w/cpp/numeric/bit (C++20 `<bit>`)

These are the types that show up in _interfaces_ — using the standard ones means
two libraries that never met can talk.

## 1. `std::optional<T>`

```cpp
std::optional<Config> find_config(std::string_view name);

if (auto c = find_config("app")) use(*c);
int port = cfg.value_or(8080);
cfg.reset();  cfg.emplace(args...);
auto n = cfg.and_then(&Config::port_opt).transform(to_string).value_or("none");  // C++23
```

- `operator*` / `operator->` are **unchecked** (UB when empty); `.value()`
  throws `bad_optional_access`.
- `std::nullopt` is the empty state. `optional<bool>` and `optional<T*>` are
  legal but confusing — `if (opt)` tests presence, not the value.
- No `optional<T&>` until C++26; use a pointer or `reference_wrapper`.
- It costs `sizeof(T)` + one bool + padding. For a pointer-like `T`, a plain
  nullable pointer is smaller.

## 2. `std::variant<Ts...>` — the type-safe union

```cpp
using Value = std::variant<std::monostate, int, double, std::string>;

Value v = 42;
std::visit(overloaded{
    [](std::monostate) { std::print("empty\n"); },
    [](int i)          { std::print("int {}\n", i); },
    [](auto&& x)       { std::print("other\n"); },
}, v);

if (auto* p = std::get_if<int>(&v)) use(*p);       // no exception path
int i = std::get<int>(v);                           // throws bad_variant_access
v.index();  std::holds_alternative<double>(v);
```

- `std::monostate` gives a "no value yet" alternative when the first type isn't
  default-constructible.
- Duplicate types make `get<T>` ambiguous — index by position, or wrap in
  strong typedefs.
- `std::visit` over N variants is an N-dimensional dispatch; single-variant visit
  compiles to a jump table and is fast, multi-variant visit gets expensive.
- The "valueless by exception" state happens when an assignment's move throws —
  rare, but `valueless_by_exception()` exists for it.

Variant vs inheritance: variant is a **closed** set with value semantics, no
allocation, and exhaustiveness that the compiler can check (via a visitor with
no `auto` fallback). Virtual bases are the **open** set. Pick by whether new
alternatives come from outside your code.

## 3. `std::tuple`, `std::pair`, structured bindings

```cpp
auto [it, inserted] = m.insert({k, v});
auto [x, y, z] = point;                              // works on aggregates and arrays too
for (const auto& [key, value] : map) { }

auto t = std::make_tuple(1, "two", 3.0);
auto& [a, b, c] = t;
std::apply([](auto&&... xs){ (std::print("{} ", xs), ...); }, t);
std::tie(x, y) = std::make_pair(1, 2);               // assign into existing vars
auto ignored = std::ignore;
```

Structured bindings work on: arrays, tuple-like types (`tuple_size` +
`tuple_element` + `get`), and aggregates with all-public members. They can't be
`constexpr`-decomposed before C++26 and can't have attributes per-name.

**Prefer a named struct** for return values with more than two fields — you get
member names at the call site _and_ in the debugger. Structured bindings on your
own struct read exactly the same as on a tuple.

## 4. `<chrono>`

```cpp
using namespace std::chrono_literals;

auto start = std::chrono::steady_clock::now();
work();
auto elapsed = std::chrono::steady_clock::now() - start;
std::print("{} ms\n", std::chrono::duration_cast<std::chrono::milliseconds>(elapsed).count());
std::print("{}\n", elapsed);                       // C++20: prints with units, e.g. "42ms"

std::this_thread::sleep_for(250ms);
constexpr auto timeout = 1min + 30s;
```

Clocks: `steady_clock` for **durations and timeouts** (monotonic, never adjusted),
`system_clock` for **wall-clock time** (can jump), `high_resolution_clock` is an
alias for one of the two — don't use it.

C++20 added the calendar and time-zone library, which is the reason to reach for
chrono over a hand-rolled date:

```cpp
auto today = std::chrono::year_month_day{std::chrono::floor<std::chrono::days>(
                 std::chrono::system_clock::now())};
auto ymd   = 2026y/std::chrono::August/11d;
auto local = std::chrono::zoned_time{"America/Boise", std::chrono::system_clock::now()};
std::print("{:%Y-%m-%d %H:%M:%S %Z}\n", local);
```

Time-zone support needs a tzdata source: fine on Linux/macOS with a recent
libstdc++/libc++, and on Windows it needs the ICU-backed MSVC STL. If
unavailable, Howard Hinnant's `date` library is the same API.

## 5. `<filesystem>`

```cpp
namespace fs = std::filesystem;

fs::path p = fs::path{root} / "data" / "input.json";   // use /, never string concat
if (fs::exists(p) && fs::is_regular_file(p)) auto n = fs::file_size(p);
fs::create_directories(p.parent_path());
for (const auto& e : fs::recursive_directory_iterator(root))
    if (e.path().extension() == ".cpp") process(e.path());

std::error_code ec;
fs::remove_all(tmp, ec);                                // non-throwing overload
```

- `path` handles separators and encoding per platform; `p.string()`,
  `p.u8string()`, `p.native()` differ meaningfully on Windows.
- Every function has a throwing and an `error_code` overload. Filesystem calls
  race by nature — `exists()` then `open()` is a TOCTOU bug; just open and
  handle failure.
- Link `-lstdc++fs` on GCC < 9, `-lc++fs` on old libc++.

## 6. Small but load-bearing

**`std::span<T>` / `std::mdspan`** — non-owning contiguous views. The right
parameter type for buffers. (See containers page.)

**`<bit>` (C++20)** — `std::bit_cast` (safe type punning), `std::popcount`,
`countl_zero`/`countr_zero`, `bit_width`, `has_single_bit`, `rotl`/`rotr`,
`std::endian`. These replace compiler intrinsics and hand-rolled loops, and
compile to single instructions.

**`std::byte`** — `enum class byte : unsigned char`. Signals "raw memory, not a
character or a number"; supports only bitwise ops and `std::to_integer<T>`.

**`<numeric>` `std::midpoint`, `std::lerp`** — overflow-correct, and `lerp` is
monotonic and exact at the endpoints, unlike `a + t*(b-a)`.

**`std::source_location` (C++20)** — replaces `__FILE__`/`__LINE__` macros in
logging:

```cpp
void log(std::string_view msg, std::source_location loc = std::source_location::current());
```

**`std::stacktrace` (C++23)** — `std::stacktrace::current()` formatted straight
into a log line, where the toolchain supports it (GCC 14+ with
`-lstdc++exp`, MSVC 19.34+).

**`std::any`** — type-erased single value with `any_cast`. Rarely the right
answer: if the set of types is known use `variant`, if there's a common
interface use type erasure with a concept.

## Gotchas

- `*optional` and `variant`'s `get_if` deref when empty/wrong are UB; `.value()`
  and `std::get` throw. Pick deliberately.
- `std::optional<T>` where `T` already has a natural empty state (e.g. an empty
  `vector`) is usually redundant nesting.
- `std::variant`'s converting constructor picks the "best" alternative by overload
  resolution: `variant<int, std::string> v = "hi";` used to select `bool` in
  C++17's original rules (fixed by P0608 in C++17 DR — but old compilers still
  bite). Be explicit with `std::in_place_type<std::string>`.
- Structured bindings introduce _names_, not references to a tuple you can
  reseat; and `auto [a, b] = t;` copies the whole tuple.
- `duration_cast` **truncates** toward zero. Use `std::chrono::round`/`ceil`/
  `floor` when that matters.
- `system_clock` can go backwards (NTP). Never measure elapsed time with it.
- `fs::path::string()` on Windows lossily converts non-ASCII; use `native()` or
  `u8string()` deliberately.
- `fs::directory_iterator` on a missing directory throws by default and returns
  `end()` in the `error_code` form — check `ec`.
