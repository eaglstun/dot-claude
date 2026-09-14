---
semantic_id: "oYIZQevJizy_KooSq2GfY_wvmRnQIAAK"
related_ids:
  - "paaJ0arbyxp7KsZDqnGfc_ivhVTQcAAF"
  - "KYoBAO7rixqWMsoCrGGfYbAvrZxIMAAP"
---
# Strings, text, and formatting

Source:

- https://en.cppreference.com/w/cpp/string/basic_string
- https://en.cppreference.com/w/cpp/string/basic_string_view
- https://en.cppreference.com/w/cpp/utility/format
- https://en.cppreference.com/w/cpp/io/print (C++23)
- https://en.cppreference.com/w/cpp/utility/from_chars
- https://fmt.dev/latest/index.html (the library `std::format` came from)

## 1. `string` vs `string_view` vs `const char*`

| Type               | Owns | Null-terminated    | Use for                              |
| ------------------ | ---- | ------------------ | ------------------------------------ |
| `std::string`      | yes  | yes                | storage, building, anything you keep |
| `std::string_view` | no   | **not guaranteed** | read-only parameters                 |
| `const char*`      | no   | yes                | C APIs only                          |
| `std::span<char>`  | no   | no                 | mutable byte buffers                 |

**Parameter rule**: take `std::string_view` for read-only strings. It binds to
`std::string`, string literals, `char*`+len, and substrings without allocating.
Take `std::string` **by value** when you will store a copy (then `std::move` it in).

```cpp
void log(std::string_view msg);              // no allocation for any caller
struct User { std::string name;
              explicit User(std::string n) : name(std::move(n)) {} };
```

`string_view`'s two hazards:

```cpp
std::string_view sv = get_string();          // DANGLES if get_string() returns by value
std::printf("%s", sv.data());                // WRONG: not null-terminated; prints past the end
```

Use `std::string(sv)` when a C API needs a `const char*`. And never store a
`string_view` in a struct that outlives the call unless the lifetime is
documented and obvious.

Small-string optimization: libstdc++ and libc++ store ~15 chars inline before
allocating, so short `std::string`s are already free. Do not micro-optimize
around this without measuring.

## 2. `std::format` (C++20) and `std::print` (C++23)

```cpp
std::string s = std::format("{} scored {:.2f}%", name, pct);
std::print("{:>8} | {:<12} | {:#06x}\n", id, name, flags);     // C++23, writes to stdout
std::println("done");                                           // adds the newline
std::format_to(std::back_inserter(buf), "{}", x);               // append, no temp string
```

Format spec: `{[index][:[[fill]align][sign][#][0][width][.precision][L][type]]}`

| Piece        | Values                                                               |
| ------------ | -------------------------------------------------------------------- |
| align        | `<` left, `>` right, `^` center                                      |
| sign         | `+`, `-`, ` `                                                        |
| `#`          | alt form: `0x`, `0b`, trailing `.` for floats                        |
| type (int)   | `b` `B` `o` `x` `X` `d` `c`                                          |
| type (float) | `a` `e` `E` `f` `F` `g` `G`                                          |
| type (other) | `s` for strings/bool, `p` for pointers, `?` for debug-quoted (C++23) |
| `L`          | locale-aware                                                         |

Dynamic width/precision: `{:{}.{}f}` with the width and precision as arguments.
Escape literal braces as `{{` and `}}`.

The format string is **checked at compile time** — a type mismatch is a build
error, not a runtime crash like `printf`. For a runtime-chosen format use
`std::vformat(fmt, std::make_format_args(args...))`.

Custom types: specialize `std::formatter`.

```cpp
template <> struct std::formatter<Point> : std::formatter<std::string> {
    auto format(const Point& p, auto& ctx) const {
        return std::format_to(ctx.out(), "({}, {})", p.x, p.y);
    }
};
```

C++23 adds formatters for ranges, tuples/pairs, and `std::thread::id`, so
`std::print("{}", vector_of_pairs)` just works.

If your toolchain lacks `<format>`/`<print>` (libstdc++ < 13, libc++ < 17 for
format; `<print>` is newer still), use **{fmt}** — same API, header-only,
`fmt::format`/`fmt::print`. Note libc++'s `<print>` may need
`-fexperimental-library` on some versions.

## 3. Parsing and conversion — `<charconv>`

`std::from_chars` / `std::to_chars` are locale-independent, non-allocating,
non-throwing, and the fastest conversions in the standard library.

```cpp
int value{};
auto [ptr, ec] = std::from_chars(sv.data(), sv.data() + sv.size(), value);
if (ec == std::errc{}) use(value);
else if (ec == std::errc::result_out_of_range) ...

char buf[32];
auto [end, ec2] = std::to_chars(buf, buf + sizeof buf, 3.14159, std::chars_format::fixed, 2);
std::string_view out{buf, end};
```

Avoid `std::stoi` (throws, allocates, locale-sensitive), `atoi` (no error
reporting at all), and `sscanf`/`sprintf` (unchecked, slow, UB-prone).
`std::ostringstream` works but is heavy — it touches a locale and usually a mutex.

## 4. Common operations

```cpp
s.starts_with("pre");  s.ends_with(".txt");        // C++20
s.contains("mid");                                  // C++23
s.substr(pos, n);                                   // allocates; sv.substr does not
std::string joined = a + b;                         // consider s.reserve() + append in loops
s.append(n, 'x');  s.insert(0, "pre");  s.erase(0, 3);
std::erase(s, ' ');                                 // C++20 remove all spaces
auto pos = s.find(':');  if (pos != std::string::npos) ...
std::string upper = s | std::views::transform(::toupper) | std::ranges::to<std::string>();
```

Splitting still has no clean standard one-liner before C++23 ranges; the
workhorse loop:

```cpp
std::vector<std::string_view> split(std::string_view s, char delim) {
    std::vector<std::string_view> out;
    for (std::size_t start = 0; start <= s.size(); ) {
        auto end = s.find(delim, start);
        if (end == std::string_view::npos) { out.push_back(s.substr(start)); break; }
        out.push_back(s.substr(start, end - start));
        start = end + 1;
    }
    return out;
}
```

## 5. Encoding and the character types

`char` is bytes with no encoding attached. In practice: **treat `std::string` as
UTF-8** on every platform, convert at the Windows API boundary
(`MultiByteToWideChar` / `std::filesystem::path`'s native handling), and never
index into a multi-byte string assuming characters.

- `char8_t`/`std::u8string` (C++20) mark UTF-8 at the type level but have almost
  no library support and force casts; most codebases stick with `char`.
- `char16_t`/`char32_t` for UTF-16/UTF-32; `wchar_t` is 16-bit on Windows and
  32-bit elsewhere — avoid in portable code.
- `std::codecvt` is deprecated and there is no standard replacement. For real
  Unicode work (normalization, case folding, grapheme clusters, collation) use
  **ICU**, `utfcpp`, or `simdutf`. C++26 adds only minimal `<text_encoding>`.
- `std::toupper`/`isalpha` take an `int` and UB on negative `char` values —
  always cast: `std::toupper(static_cast<unsigned char>(c))`.

## 6. Regex

`std::regex` works and is **extremely slow** — often 10–100× slower than PCRE2 or
RE2, with pathological compile times. For anything hot or user-supplied, use
`RE2` (linear-time, safe against catastrophic backtracking), `PCRE2`, or
`ctre` (compile-time regex, header-only, very fast).

```cpp
static const std::regex re{R"(^(\w+)=(\d+)$)"};      // hoist: construction is the expensive part
std::smatch m;
if (std::regex_match(line, m, re)) { auto key = m[1].str(); }
```

Raw string literals `R"(...)"` are mandatory for readable patterns; use
`R"delim(...)delim"` when the pattern contains `)"`.

## Gotchas

- `string_view` over a temporary dangles. `sv = std::string("x") + "y";` is a
  use-after-free that compiles cleanly.
- `string_view::data()` is not null-terminated. Passing it to a `%s`, `fopen`,
  or any C API reads past the end.
- `s.substr()` allocates; `sv.substr()` doesn't. In a parsing loop that
  difference dominates.
- `std::string::npos` is `size_t(-1)`. `if (s.find(x) > 0)` is true even on a
  miss; always compare against `npos`.
- `operator+` chains create a temporary per operation. Use `std::format`,
  `append`, or `reserve` first.
- `std::format("{}", 'a')` prints `a`, but `std::format("{}", uint8_t{97})` also
  prints... `97` (it's an integer type). Watch `char`-vs-`uint8_t` in byte code.
- `getline` leaves the `\r` on Windows-authored files read in text mode on Unix.
  Strip it explicitly.
- `std::cout` and `printf` interleave badly unless
  `std::ios::sync_with_stdio(true)` (the default, and the reason `cout` is slow —
  turning it off doubles throughput but forbids mixing).
- `std::regex` construction inside a loop is the classic "why is parsing taking
  4 seconds".
