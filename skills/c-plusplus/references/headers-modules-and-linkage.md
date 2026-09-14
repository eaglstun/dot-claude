---
semantic_id: "IYIbQC-jij63usyGrWlLKvU7pdhIYAAI"
related_ids:
  - "oSo7SEpriq43qtQQqGXbIPU_tdjJIAAB"
  - "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
---
# Headers, modules, ODR, and linkage

Source:

- https://en.cppreference.com/w/cpp/language/modules
- https://en.cppreference.com/w/cpp/language/definition (the ODR)
- https://en.cppreference.com/w/cpp/language/storage_duration (linkage)
- https://en.cppreference.com/w/cpp/language/inline
- https://en.cppreference.com/w/cpp/language/namespace
- https://en.cppreference.com/w/cpp/language/adl

## 1. The classic model

A **translation unit** is one `.cpp` after preprocessing — headers are literally
pasted in. Every TU is compiled independently; the linker then merges symbols.

Header hygiene:

```cpp
#pragma once                 // universally supported; simpler than include guards
                             // (guards are still safer for weird build setups with symlinks)
#include <vector>            // what THIS header needs, nothing more
#include "project/thing.hpp"

namespace proj {
class Widget;                // forward declare when a pointer/reference suffices
void use(const Widget&);
}
```

- **Include what you use.** Relying on a transitive include breaks the day
  someone tidies that header. `include-what-you-use` automates the check.
- Forward declare instead of including when only pointers/references/return
  types are involved — this is the main compile-time lever in a header-heavy
  codebase.
- Never `using namespace` at file scope in a header. Never.
- Order includes: own header first (proves it's self-contained), then project,
  then third-party, then standard. clang-format's `SortIncludes` + include
  categories enforce it.

## 2. The One Definition Rule

- Every entity may be _declared_ many times, _defined_ once per TU.
- Non-inline functions and variables with external linkage: exactly **one**
  definition in the whole program.
- Classes, templates, `inline` functions/variables: may be defined in multiple
  TUs, but **every definition must be token-for-token identical** with the same
  meaning for every name.

ODR violations are **ill-formed, no diagnostic required** — the linker picks one
definition arbitrarily and you get impossible behavior. The usual causes:

- The same class defined differently in two TUs because of a `#define` /
  compiler flag mismatch (`-DDEBUG` changing a member, `-D_GLIBCXX_DEBUG` in one
  TU only, different `-std=`, different NDEBUG). **This is the classic
  mixed-build crash**, and it is why every TU must share the same flags.
- Two anonymous structs with the same name in different headers.
- An `inline` function whose body differs between builds.

ASan detects some ODR violations (`detect_odr_violation=1`, on by default) —
heed those reports, they are never false alarms worth ignoring.

## 3. Linkage keywords

| Form                                    | Effect                                                       |
| --------------------------------------- | ------------------------------------------------------------ |
| `static` at namespace scope             | internal linkage — one per TU, invisible to the linker       |
| anonymous namespace                     | internal linkage, works for types too — **prefer this**      |
| `inline` function/variable              | external linkage, definition allowed in every TU, one wins   |
| `extern`                                | declaration only, definition elsewhere                       |
| `extern "C"`                            | C name mangling and calling convention                       |
| `constexpr` variable at namespace scope | implicitly `const` → internal linkage; add `inline` to share |

```cpp
namespace { struct Helper { }; void detail_fn(); }     // TU-local
inline constexpr int kMaxRetries = 3;                   // C++17: header-safe constant
inline std::string& registry() { static std::string s; return s; }   // header-safe global
```

`inline` is about **linkage**, not inlining. The optimizer decides inlining;
`inline` just tells the linker "duplicates are expected, pick one".

## 4. Namespaces and ADL

```cpp
namespace proj::net {           // C++17 nested namespace definition
    namespace detail { }        // convention: implementation, not API
    inline namespace v2 { }     // versioning: proj::net::v2::X is found as proj::net::X
}
namespace pn = proj::net;       // alias, fine in a .cpp
```

**Argument-dependent lookup** finds free functions in the namespaces of the
argument types. It is why `swap(a, b)` beats `std::swap(a, b)`:

```cpp
using std::swap;      // fallback
swap(a, b);           // ADL finds a better overload if the type provides one
```

The same two-step is correct for `begin`/`end`/`size` in generic code; C++20's
`std::ranges::swap`/`begin` are _customization point objects_ that do the dance
for you.

Define operators and ADL-found free functions as **hidden friends** inside the
class — they're only findable via ADL, which keeps overload sets tiny and error
messages readable.

## 5. Modules (C++20)

```cpp
// math.cppm  (module interface unit)
export module proj.math;

import std;                     // C++23; or #include <cmath> in the global module fragment
export int add(int a, int b);   // exported
int helper();                   // internal to the module, not visible to importers

// math.cpp  (implementation unit)
module proj.math;
int add(int a, int b) { return a + b; }
```

```cpp
// consumer.cpp
import proj.math;
int main() { return add(1, 2); }
```

Structure:

- **Interface unit**: `export module X;` — one per module.
- **Implementation unit**: `module X;` — many.
- **Partitions**: `export module X:part;` then `export import :part;`.
- **Global module fragment**: `module;` then `#include`s, then `export module X;`
  — the only legal place for includes before the module declaration.
- **Header units**: `import <vector>;` — an intermediate step, poorly supported.

What you get: no textual inclusion (so no macro leakage, no include-order
dependence), a real interface/implementation split, and **big compile-time
wins** on large codebases — the interface is compiled once into a BMI rather than
re-parsed per TU.

What it costs: the build system must compile modules in dependency order, which
means scanning sources for imports before building. Support as of 2026:
CMake 3.28+ with Ninja 1.11+ handles C++20 modules for clang 16+/GCC 14+/MSVC;
`import std;` requires CMake 3.30+ plus a compiler-provided std module and is
still the flakiest part. MSVC is furthest along.

Practical stance: **modules are viable for new projects on a modern toolchain,
and painful to retrofit.** A pragmatic middle ground is to keep headers but
adopt precompiled headers and unity builds for the compile-time win.

## 6. Physical design for build speed

- Prefer PIMPL or an abstract interface at the heaviest boundaries — it cuts the
  header dependency graph, which is what actually rebuilds.
- Explicit template instantiation (`extern template` in the header, `template
class X<int>;` in one .cpp) stops every TU re-instantiating the same thing.
- Precompiled headers (`target_precompile_headers` in CMake) for the stable
  third-party + standard headers.
- Unity/jumbo builds cut redundant parsing dramatically but hide missing includes
  and ODR problems — keep a non-unity CI job.
- `ccache`/`sccache` in front of everything.
- Measure before guessing: `clang -ftime-trace` + ClangBuildAnalyzer names the
  expensive headers and template instantiations exactly.

## Gotchas

- Different preprocessor flags across TUs → ODR violation → inexplicable
  crashes. Same `-std`, same `NDEBUG`, same `_GLIBCXX_DEBUG`, everywhere.
- `static` on a class member means something entirely different from `static` at
  namespace scope. In headers, use an anonymous namespace or `inline`.
- A non-`inline` function defined in a header is a multiple-definition link error
  the second time the header is included in a different TU.
- `constexpr`/`const` globals in a header are internal-linkage, so each TU gets
  its own copy and their addresses differ. Add `inline` (C++17).
- `#pragma once` fails to dedupe when the same file is reachable via two
  different paths (symlinks, bind mounts, copied trees) — rare but real.
- ADL will find functions you never intended, especially with `std::` types in
  the arguments. Qualify calls that must not be hijacked (`::f(x)` or `ns::f(x)`).
- `using namespace std;` at namespace scope in a header poisons every consumer;
  in a `.cpp` it is merely risky (`std::size`, `std::data`, `std::byte` collide
  with common names).
- Modules do not export macros. A header-to-module port of a macro-based API
  needs a redesign.
- Mixing `#include` of a header and `import` of a module that includes the same
  header can produce duplicate-declaration errors on some toolchains. Pick one
  per dependency.
