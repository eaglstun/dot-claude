---
semantic_id: "oSo7SEpriq43qtQQqGXbIPU_tdjJIAAB"
related_ids:
  - "IYIbQC-jij63usyGrWlLKvU7pdhIYAAI"
  - "pQIIQOvLiA73ysaCqnDfMPUvlVgIcAAB"
---

# Build systems, compilers, and tooling

Source:

- https://cmake.org/cmake/help/latest/
- https://cliutils.gitlab.io/modern-cmake/ (Modern CMake)
- https://gcc.gnu.org/onlinedocs/gcc/Option-Summary.html
- https://clang.llvm.org/docs/UsersManual.html
- https://learn.microsoft.com/en-us/cpp/build/reference/compiler-options
- https://clang.llvm.org/extra/clang-tidy/

## 1. Modern CMake in one page

Target-based, never directory-based. `include_directories`,
`add_definitions`, and `link_libraries` (the global forms) are legacy — use the
`target_*` versions.

```cmake
cmake_minimum_required(VERSION 3.25)
project(myproj VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)              # -std=c++20, not -std=gnu++20
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)      # compile_commands.json for clangd/tidy

add_library(core
    src/engine.cpp
    src/parser.cpp
)
target_include_directories(core
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>
    PRIVATE src
)
target_compile_features(core PUBLIC cxx_std_20)
target_link_libraries(core PUBLIC fmt::fmt PRIVATE ZLIB::ZLIB)
target_compile_options(core PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive->
)

add_executable(app src/main.cpp)
target_link_libraries(app PRIVATE core)
```

`PUBLIC` = needed to build this target _and_ to use it. `PRIVATE` = only to build
it. `INTERFACE` = only to use it (header-only libraries). Getting this right is
what makes a dependency graph propagate flags correctly instead of by accident.

**Presets** (`CMakePresets.json`) replace the shell scripts everyone used to
write:

```json
{
  "version": 6,
  "configurePresets": [
    {
      "name": "dev",
      "generator": "Ninja",
      "binaryDir": "build/dev",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "CMAKE_CXX_FLAGS": "-fsanitize=address,undefined -g"
      }
    },
    {
      "name": "rel",
      "generator": "Ninja",
      "binaryDir": "build/rel",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "RelWithDebInfo" }
    }
  ]
}
```

```bash
cmake --preset dev && cmake --build --preset dev && ctest --preset dev
```

Build types: `Debug` (`-O0 -g`), `Release` (`-O3 -DNDEBUG`), `RelWithDebInfo`
(`-O2 -g -DNDEBUG` — ship this), `MinSizeRel` (`-Os`).

Dependencies: `find_package(Foo REQUIRED)` for system/vcpkg/conan-installed,
`FetchContent_Declare` + `FetchContent_MakeAvailable` for source deps (pin a
git tag, never a branch), and `add_subdirectory` for vendored trees.

## 2. Compilers and the flags worth knowing

| Purpose                    | GCC/Clang                                      | MSVC                 |
| -------------------------- | ---------------------------------------------- | -------------------- |
| Standard                   | `-std=c++20`                                   | `/std:c++20`         |
| Warnings                   | `-Wall -Wextra -Wpedantic`                     | `/W4`                |
| Warnings as errors         | `-Werror`                                      | `/WX`                |
| Conformance                | (default)                                      | `/permissive-`       |
| Optimize                   | `-O2` / `-O3`                                  | `/O2`                |
| Debug info                 | `-g` (`-g3` for macros)                        | `/Zi`                |
| LTO                        | `-flto=thin` (clang) / `-flto`                 | `/GL` + `/LTCG`      |
| Native ISA                 | `-march=native`                                | `/arch:AVX2`         |
| Fast math (careful)        | `-ffast-math`                                  | `/fp:fast`           |
| No RTTI / exceptions       | `-fno-rtti -fno-exceptions`                    | `/GR- /EHs-c-`       |
| Frame pointers (profiling) | `-fno-omit-frame-pointer`                      | `/Oy-`               |
| Sanitizers                 | `-fsanitize=address,undefined`                 | `/fsanitize=address` |
| Hardened release           | `-D_FORTIFY_SOURCE=3 -fstack-protector-strong` | `/GS /guard:cf`      |
| Show include cost          | `-ftime-trace` (clang)                         | `/d1reportTime`      |
| Static analysis            | `-fanalyzer` (GCC)                             | `/analyze`           |

`-march=native` breaks portability of the binary — for shipped software, target
a baseline (`-march=x86-64-v2`) and use runtime dispatch (`__builtin_cpu_supports`
/ function multi-versioning) for the hot kernels.

`-Ofast` / `-ffast-math` enables reassociation and assumes no NaN/Inf; it can
change results and even break `isnan` checks. Opt in per-file, never globally,
and never in code that handles user data of unknown range.

## 3. Package management

| Tool             | Model                                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------ |
| **vcpkg**        | manifest `vcpkg.json` + toolchain file; builds from source, huge catalog, good CMake integration |
| **Conan**        | `conanfile.txt/py`, binary packages, profiles per platform/ABI                                   |
| **CPM.cmake**    | thin wrapper over `FetchContent` with caching; zero infrastructure                               |
| **FetchContent** | built into CMake, no extra tooling; rebuilds deps with your flags                                |
| system packages  | fine for Linux-only tools, hopeless for portability                                              |

There is no winner. vcpkg manifest mode is the lowest-friction default for a new
cross-platform project; CPM is the lowest-ceremony for a small one.

## 4. Cross-compiling (and why it fails)

Cross-builds fail in a handful of repeatable ways that look like port bugs and
are usually configuration. Symptoms and causes, worst-first:

**Autoconf decides you aren't cross-compiling.** `configure` treats the build as
native when the `--host` and `--build` strings are _textually_ identical, then
tries to _execute_ a test binary it just compiled:

```
checking whether we are cross compiling... configure: error: cannot run C compiled programs.
```

This bites hardest on same-arch cross-builds — arm64 macOS to arm64 iOS, x86_64
Linux to x86_64 musl — where the natural triple for both sides is the same
string. Force a distinct `--host`. But you cannot pick freely: packages
pattern-match the host string to select a platform backend. ICU matches the
substring `-apple-darwin` to choose both `U_DARWIN` and its `mh-darwin` config
fragment. So the value must differ from `--build` **and** still contain whatever
the package greps for. For Apple targets that makes `arm-apple-darwin` the
durable choice, not the more accurate-looking `aarch64-apple-ios` — which
canonicalizes fine in `config.sub` and then falls off the end of every darwin
case. Verify before guessing: `sh config.sub <triple>` prints the canonical form,
and grepping the package's `configure.ac` shows what it actually tests for.

**CMake turns every executable into an app bundle.** With
`CMAKE_SYSTEM_NAME=iOS`, `MACOSX_BUNDLE` defaults ON, so any package installing a
CLI helper dies at configure time:

```
install TARGETS given no BUNDLE DESTINATION for MACOSX_BUNDLE executable target "..."
```

Fix once, globally, with `-DCMAKE_MACOSX_BUNDLE=OFF` — never per-package, since it
recurs in every package that builds a tool.

**Silent platform fallback.** Packages that pick a backend from a flavor string
often `else()` into a default rather than erroring. A port whose dispatch reads
`if(WINDOWS) elseif(OSX) elseif(LINUX) else() → Linux` will build your iOS target
as the _Linux_ port, and you learn this from a downstream `#error Unsupported
OpenGL platform` rather than from anything naming the real problem. When a
cross-build fails deep inside a dependency, check the platform dispatch _first_.

**vcpkg specifics:**

| Thing                               | Behavior                                                                                                    |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `ios` vs `osx` platform expressions | **disjoint** — `"platform": "osx"` silently drops the dependency on iOS instead of erroring                 |
| `VCPKG_CMAKE_CONFIGURE_OPTIONS`     | triplet-level; injected into every `vcpkg_cmake_configure`. Fix whole classes of port bugs without patching |
| `VCPKG_MAKE_BUILD_TRIPLET`          | triplet-level; overrides the derived `--host`/`--build` for autotools ports                                 |
| `--dry-run --allow-unsupported`     | enumerates the entire resolved graph _and_ every `supports` warning in one shot — always run this first     |
| `supports` gates                    | frequently conservative, not factual. Check whether _your_ code needs the feature before fighting the gate  |

Resolve the graph before you compile anything. A dry run costs seconds and tells
you whether the target is plausible; discovering an unsupported package four
hours into building ICU does not.

## 5. Clang tooling

**clangd** (LSP) is the single biggest quality-of-life win: real completion,
go-to-definition, and inline diagnostics, driven by `compile_commands.json`.
Generate it with `CMAKE_EXPORT_COMPILE_COMMANDS=ON` and symlink into the repo
root.

**clang-format** — commit a `.clang-format`, run it in CI, and stop discussing
braces:

```yaml
BasedOnStyle: Google
ColumnLimit: 100
DerivePointerAlignment: false
PointerAlignment: Left
IncludeBlocks: Regroup
```

**clang-tidy** — the linter that finds real bugs, not just style:

```yaml
# .clang-tidy
Checks: >
  bugprone-*, performance-*, modernize-*, readability-*,
  cppcoreguidelines-*, clang-analyzer-*,
  -modernize-use-trailing-return-type,
  -readability-magic-numbers
WarningsAsErrors: "bugprone-*,clang-analyzer-*"
```

Run incrementally on the diff (`clang-tidy-diff.py`) — a full run on a large
codebase takes as long as a build. `run-clang-tidy -j` for the nightly pass.

Others worth wiring up: `include-what-you-use`, `cppcheck` (catches a different
class than clang-tidy), `clang-format --dry-run -Werror` in CI, and
`ClangBuildAnalyzer` on `-ftime-trace` output when builds get slow.

## 6. Standard libraries and ABI

- **libstdc++** (GNU) — default on Linux, most complete. `_GLIBCXX_DEBUG` gives
  checked iterators (and changes the ABI, so it must be all-or-nothing).
- **libc++** (LLVM) — default on macOS; `_LIBCPP_HARDENING_MODE_FAST` /
  `_EXTENSIVE` / `_DEBUG` for checked builds.
- **MSVC STL** — open source, tracks the standard closely.

The libstdc++ **dual ABI** (`_GLIBCXX_USE_CXX11_ABI=0/1`) still bites when
linking prebuilt binaries from an older distro: the symptom is an undefined
reference mentioning `__cxx11::basic_string`. All objects in a program must
agree.

C++ has no stable ABI across compilers, and MSVC debug/release CRTs cannot be
mixed. If you ship a library for others to link, either ship a C API or ship the
source.

Check what your library supports with the feature-test macros rather than
version numbers:

```cpp
#if __cpp_lib_ranges >= 201911L
#include <version>          // all library feature-test macros live here
```

## 7. A sane default CI matrix

- gcc-latest + libstdc++, `-Wall -Wextra -Werror`, Debug + sanitizers
- clang-latest + libc++, Release, clang-tidy on the diff
- MSVC, `/W4 /permissive- /WX`, Release
- one older compiler at your declared minimum (the constraint your users live with)
- `ctest --output-on-failure` everywhere; ASan+UBSan on at least one leg

## Gotchas

- `CMAKE_CXX_STANDARD` set _after_ `add_library` doesn't apply. Set it before, or
  use `target_compile_features`.
- Mixing `PUBLIC`/`PRIVATE` inconsistently in `target_link_libraries` is an error
  ("The plain signature ... has already been used"), not a warning.
- `file(GLOB)` for sources: CMake won't notice new files without a re-configure.
  List sources explicitly, or use `CONFIGURE_DEPENDS` and accept the cost.
- `-O3` is not reliably faster than `-O2`; it inflates code size and can hurt
  I-cache. Measure both.
- Different flags per TU (especially `NDEBUG`, `_GLIBCXX_DEBUG`, `-std`) is an
  ODR violation and produces crashes with no link error.
- `-Werror` in a release tarball breaks builds on compilers newer than yours.
  Enable it in CI, not in the shipped default.
- Sanitizer builds need the _whole_ program instrumented, including the standard
  library for MSan. ASan works fine with an uninstrumented libc.
- `find_package` failing silently because `REQUIRED` was omitted is the source of
  most "why is this header not found".
- Ninja is faster than Make and gives correct dependency scanning for modules;
  there is no reason to use Make generators for new projects.
