---
name: c-plusplus
description: C++ language and tooling reference. Use when writing, reviewing, debugging, testing, or optimizing C++; resolving lifetime, template, concurrency, undefined-behavior, CMake, or interop issues; or choosing standard-library and ecosystem tools.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: LQYZQepqn26yXlUAKHNbYtUrjX_YYAAB
  related_ids: '["p4IZT-p7nzr3Ps4E6FDbYv0b5RJQIAAN","JYITQf9rzy2z6tyVq2Fbc_w_hR4AIAAF"]'
---

# C++ reference

Condensed, source-cited notes grounded in the primary sources (cppreference, the
C++ Core Guidelines, the ISO papers, and the compiler/library vendors' own docs).
Each page cites its source URLs at the top and ends with a Gotchas section of
the sharp edges that memory gets wrong.

This is a standalone language shelf, not tied to one repo. Repo conventions (a
project CLAUDE.md, an existing style guide, the surrounding file) override
anything here — including which C++ standard is in play. **Check the build's
`-std=` before recommending a feature.**

Assumed baseline is C++17; features from C++20/23/26 are labeled inline.

## References — load on demand

Detail lives in `references/`. One pointer per page:

### Core language

- **[value-categories-and-move.md](references/value-categories-and-move.md)**
  — lvalue/prvalue/xvalue, `std::move`/`forward`, rule of zero/three/five,
  forwarding references, guaranteed copy elision, the parameter-passing table.
  _Read on any "why is this copying" question, or before writing a move
  constructor._

- **[initialization-and-lifetime.md](references/initialization-and-lifetime.md)**
  — the init zoo and when braces bite, most vexing parse, aggregates and
  designated initializers, storage duration, the static-init-order fiasco,
  temporary lifetime extension. _Read when an object holds garbage, or a
  `string_view` dangles._

- **[classes-and-polymorphism.md](references/classes-and-polymorphism.md)**
  — the six special members and what suppresses them, RAII, virtual dispatch,
  CRTP vs deducing-`this` vs type erasure, slicing, `<=>`, PIMPL. _Read when
  designing a class or when a destructor silently killed your moves._

- **[templates-and-concepts.md](references/templates-and-concepts.md)**
  — deduction and CTAD, concepts and `requires`, variadics and folds,
  `if constexpr`, specialization, dependent names. _Read when writing generic
  code or decoding a 400-line template error._

- **[constexpr-and-compile-time.md](references/constexpr-and-compile-time.md)**
  — `constexpr`/`consteval`/`constinit`, what's legal in constant evaluation,
  `static_assert` and the type traits, NTTPs, compile-time tables. _Read when
  moving work to build time or when `constexpr` "isn't running at compile time"._

- **[memory-and-smart-pointers.md](references/memory-and-smart-pointers.md)**
  — the ownership decision table, `unique_ptr` with custom deleters,
  `shared_ptr`/`weak_ptr` cycles and double control blocks, placement `new` and
  alignment, PMR arenas, the object model and `bit_cast`. _Read on any "who owns
  this" question, or before writing `new`._

- **[lambdas-and-callables.md](references/lambdas-and-callables.md)**
  — captures (and why `[=]` captures `this`), storing callables,
  `std::function` vs `function_ref` vs a template parameter, `bind_front`, the
  `overloaded` visitor. _Read before storing or threading a lambda._

- **[undefined-behavior.md](references/undefined-behavior.md)**
  — the UB catalogue, evaluation order, ASan/UBSan/TSan flags and cost, the
  warning set worth enabling. _Read when a bug only reproduces at `-O2`, in
  release, or on one compiler._

### Library

- **[containers-and-algorithms.md](references/containers-and-algorithms.md)**
  — which container when, the invalidation table, `vector` mechanics,
  `try_emplace` and heterogeneous lookup, the algorithm vocabulary, `span`.
  _Read when choosing a container or when an iterator went stale._

- **[ranges-and-views.md](references/ranges-and-views.md)**
  — range algorithms and projections, the full view catalogue, `ranges::to`,
  range concepts, when a pipeline is the wrong call. _Read before writing a
  `|` pipeline, and definitely before storing one._

- **[strings-and-formatting.md](references/strings-and-formatting.md)**
  — `string` vs `string_view` vs `const char*`, `std::format`/`print` spec,
  `<charconv>`, encoding reality, regex alternatives. _Read for any text
  handling, parsing, or output formatting._

- **[vocabulary-types.md](references/vocabulary-types.md)**
  — `optional`, `variant` + `visit`, tuple and structured bindings, `<chrono>`
  clocks and calendars, `<filesystem>`, `<bit>`, `source_location`. _Read when
  picking the type that shows up in an interface._

- **[error-handling.md](references/error-handling.md)**
  — exceptions vs `expected` vs error codes, `noexcept`, the four
  exception-safety guarantees, copy-and-swap, assertions and contracts. _Read
  when designing how a function reports failure._

### Systems

- **[concurrency-and-atomics.md](references/concurrency-and-atomics.md)**
  — `jthread`, locks and `scoped_lock`, condition variables, futures, memory
  order, false sharing, parallel algorithms, TSan. _Read before any shared
  state, and whenever "it works most of the time"._

- **[coroutines.md](references/coroutines.md)**
  — what C++20 actually shipped, `std::generator`, the `promise_type`
  protocol, awaiters and symmetric transfer, frame allocation, which library to
  use. _Read before writing `co_await`, and before writing your own task type._

- **[headers-modules-and-linkage.md](references/headers-modules-and-linkage.md)**
  — header hygiene, the ODR and how flag mismatches violate it, linkage
  keywords, namespaces and ADL, C++20 modules and their build-system reality,
  compile-time physical design. _Read on a duplicate-symbol error, an
  inexplicable crash across TUs, or a slow build._

- **[interop-and-ffi.md](references/interop-and-ffi.md)**
  — `extern "C"` boundaries, ABI instability and symbol visibility, nanobind/
  pybind11 and the GIL, Objective-C++, Rust via cxx, wasm. _Read before
  exposing C++ to anything that isn't C++._

### Practice

- **[build-and-tooling.md](references/build-and-tooling.md)**
  — modern target-based CMake and presets, the compiler flag table, package
  managers, cross-compiling failure modes (autoconf cross-detection, vcpkg
  triplets, silent platform fallback), clangd/clang-format/clang-tidy, standard
  libraries and the libstdc++ dual ABI, a CI matrix. _Read when setting up or
  fixing a build, or when a cross-build fails inside a dependency._

- **[testing-and-debugging.md](references/testing-and-debugging.md)**
  — GoogleTest/Catch2/doctest, property testing and fuzzing, the gdb↔lldb
  command map, rr, Google Benchmark and how to get numbers that mean something.
  _Read when adding tests or chasing a bug interactively._

- **[performance.md](references/performance.md)**
  — the order of operations, the latency table, profilers, AoS→SoA and cache
  layout, allocation strategy, branches and inlining, LTO/PGO, SIMD. _Read
  before optimizing anything, and instead of guessing._

- **[idioms-and-api-design.md](references/idioms-and-api-design.md)**
  — the Core Guidelines that earn their keep, const-correctness, strong types
  and `enum class`, `[[nodiscard]]`, the cast table, named idioms, and what to
  avoid. _Read when designing an interface others will call._

- **[standard-versions.md](references/standard-versions.md)**
  — what each of C++11→26 added, choosing a baseline, feature-test macros,
  removals and migration breakage, compiler-specific portability. _Read before
  using a feature you're not sure has landed in the project's toolchain._

- **[ecosystem-libraries.md](references/ecosystem-libraries.md)**
  — the "which library" map: Abseil/Boost, JSON and serialization, Asio and
  HTTP, logging and CLI, graphics/audio/math/ML/database picks, and how to
  choose. _Read for any "what do people use for X" question._

## Working rules for C++ in this shelf

1. **Check the standard first.** `-std=` in the build, or `__cplusplus` /
   `<version>` macros. Recommending `std::expected` into a C++17 build wastes
   everyone's time.
2. **Match the surrounding code.** Exceptions vs error codes, naming, header
   layout, and pointer style are codebase decisions, not universal ones.
3. **A crash that only reproduces optimized is UB until proven otherwise.**
   Reach for ASan+UBSan before reading the code twice.
4. **Never recommend a performance change without a measurement**, and never
   benchmark a debug build.
5. **RAII is the answer** to most resource questions. If a fix involves manual
   cleanup on multiple return paths, the design is wrong.

## Conventions for this skill

- Each reference cites its source URLs at the top; prefer un-versioned
  `en.cppreference.com/w/cpp/...` URLs so links don't rot.
- Keep SKILL.md lean: two-line pointers only. Detail lives on the shelf.
- To add a topic: write `references/<topic>.md` in the same format (Source block
  up top, numbered sections, Gotchas at the end), then add a pointer above.
