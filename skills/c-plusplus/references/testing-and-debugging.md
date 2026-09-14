---
semantic_id: "qaIJTP5piji3jtgRrGFZ4fUXnJ_IgAAG"
related_ids:
  - "oSo7SEpriq43qtQQqGXbIPU_tdjJIAAB"
  - "KYoBAO7rixqWMsoCrGGfYbAvrZxIMAAP"
---
# Testing, debugging, and benchmarking

Source:

- https://google.github.io/googletest/
- https://github.com/catchorg/Catch2/blob/devel/docs/Readme.md
- https://github.com/google/benchmark/blob/main/docs/user_guide.md
- https://cmake.org/cmake/help/latest/manual/ctest.1.html
- https://lldb.llvm.org/use/map.html (lldb ↔ gdb command map)

## 1. Frameworks

| Framework      | Why                                                                                                            |
| -------------- | -------------------------------------------------------------------------------------------------------------- |
| **GoogleTest** | the de facto standard; fixtures, parameterized tests, death tests, and **GMock** for mocking                   |
| **Catch2 v3**  | header-friendly, expressive `REQUIRE(a == b)` with expression decomposition, BDD sections, built-in generators |
| **doctest**    | Catch-like API, ~10× faster to compile; can live in the same TU as the code                                    |
| **Boost.Test** | if you're already deep in Boost                                                                                |

GoogleTest if you need mocks; doctest if compile time matters; Catch2 if you
like the syntax. All integrate with CTest.

```cpp
// GoogleTest
TEST(ParserTest, RejectsTrailingComma) {
    EXPECT_THAT(parse("[1,2,]"), IsError(ErrorCode::TrailingComma));
}

class DbTest : public ::testing::Test {
protected:
    void SetUp() override { db_.open(":memory:"); }
    Db db_;
};
TEST_F(DbTest, InsertThenRead) { ... }

INSTANTIATE_TEST_SUITE_P(Sizes, ResizeTest, ::testing::Values(0, 1, 1024));
```

```cpp
// Catch2
TEST_CASE("vector grows", "[vector]") {
    std::vector<int> v;
    REQUIRE(v.empty());
    SECTION("push_back") { v.push_back(1); REQUIRE(v.size() == 1); }  // section reruns the setup
    SECTION("reserve")   { v.reserve(10);  REQUIRE(v.capacity() >= 10); }
}
```

Assertion style: `ASSERT_*` aborts the test, `EXPECT_*` continues — prefer
`EXPECT` unless continuing would crash. `EXPECT_THAT(value, matcher)` with GMock
matchers (`ElementsAre`, `UnorderedElementsAre`, `Optional`, `Pointee`,
`StartsWith`, `Near`) gives far better failure messages than `EXPECT_TRUE`.

Wire it up:

```cmake
include(FetchContent)
FetchContent_Declare(googletest GIT_REPOSITORY https://github.com/google/googletest
                                GIT_TAG v1.15.2)
FetchContent_MakeAvailable(googletest)
enable_testing()
add_executable(tests test/parser_test.cpp)
target_link_libraries(tests PRIVATE core GTest::gtest_main GTest::gmock)
include(GoogleTest)
gtest_discover_tests(tests)          # one CTest entry per test, not one per binary
```

## 2. Beyond example-based tests

- **Property-based**: RapidCheck (GTest/Catch integration) — generate inputs,
  assert invariants, get automatic shrinking of the failing case. Ideal for
  parsers, serializers, and containers.
- **Fuzzing**: libFuzzer (`-fsanitize=fuzzer,address`) or AFL++. Any function
  taking `(const uint8_t*, size_t)` gets a harness in five lines, and it _will_
  find your crashes. OSS-Fuzz for open source.

```cpp
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    parse(std::string_view{reinterpret_cast<const char*>(data), size});
    return 0;
}
```

- **Approval/snapshot tests** for complex output (a rendered frame, a formatted
  report) — cheap to add, catches unintended diffs.
- **Coverage**: `--coverage` (gcov/lcov) or clang's `-fprofile-instr-generate
-fcoverage-mapping` + `llvm-cov show`. Branch coverage on parsing and error
  paths is where the value is; chasing 100% line coverage is not.
- Always run at least one CI leg under **ASan+UBSan** and one under **TSan** if
  threaded. Sanitizers find bugs that all the assertions in the world miss.

## 3. Debugging

```bash
lldb ./app -- --arg      # macOS/clang default
gdb --args ./app --arg   # Linux/GCC default
```

| Task                  | gdb                          | lldb                      |
| --------------------- | ---------------------------- | ------------------------- |
| break at function     | `b func`                     | `b func` / `br s -n func` |
| break at file:line    | `b file.cpp:42`              | `b file.cpp:42`           |
| conditional break     | `b f if x==3`                | `br s -n f -c 'x==3'`     |
| run / continue        | `r` / `c`                    | `r` / `c`                 |
| step over/in/out      | `n` / `s` / `fin`            | `n` / `s` / `finish`      |
| backtrace             | `bt`                         | `bt`                      |
| all thread backtraces | `thread apply all bt`        | `bt all`                  |
| print                 | `p expr`                     | `p expr` / `expr --`      |
| pretty containers     | built-in (libstdc++ pythons) | `type summary` / built-in |
| watchpoint            | `watch var`                  | `w s v var`               |
| examine memory        | `x/16xb ptr`                 | `me read -c16 -fx ptr`    |
| core dump             | `gdb ./app core`             | `lldb ./app -c core`      |

Practical notes:

- Debug the `RelWithDebInfo` build when the bug only reproduces optimized;
  variables will show `<optimized out>` — that's the trade.
- `ulimit -c unlimited` plus a `core_pattern` gets you postmortem cores;
  `coredumpctl` on systemd distros.
- **rr** (Linux, x86) is transformative for heisenbugs: record once, replay
  deterministically, and _step backwards_. `rr record ./app && rr replay`.
- Pretty-printers for libstdc++ ship with GCC; if `p vec` shows raw pointers,
  your gdb isn't loading them (`python import ...` in `.gdbinit`).
- `std::print`-debugging is not shameful — but prefer a real logger with
  levels and `std::source_location` so the statements survive.
- For crash triage in production: build with `-g` and _ship_ the split debug info
  (`objcopy --only-keep-debug`, `-gsplit-dwarf`), keep a symbol server, and
  symbolize with `llvm-symbolizer` / `addr2line`.

## 4. Benchmarking

**Google Benchmark** is the standard tool. It handles warmup, iteration count,
and statistical repetition — all things hand-rolled timing loops get wrong.

```cpp
#include <benchmark/benchmark.h>

static void BM_Sort(benchmark::State& state) {
    std::vector<int> data = make_random(state.range(0));
    for (auto _ : state) {
        state.PauseTiming();
        auto copy = data;                      // setup outside the measured region
        state.ResumeTiming();
        std::sort(copy.begin(), copy.end());
        benchmark::DoNotOptimize(copy.data()); // stop DCE from deleting the work
        benchmark::ClobberMemory();
    }
    state.SetComplexityN(state.range(0));
    state.SetBytesProcessed(int64_t(state.iterations()) * state.range(0) * sizeof(int));
}
BENCHMARK(BM_Sort)->RangeMultiplier(8)->Range(1 << 10, 1 << 20)->Complexity();
BENCHMARK_MAIN();
```

Rules for numbers you can trust:

- `DoNotOptimize` / `ClobberMemory` on anything whose result is unused, or the
  optimizer deletes the code you're measuring and you "achieve" 0.3 ns.
- Benchmark the **release** build. Debug-build numbers are meaningless,
  especially for anything template-heavy (ranges, `std::function`).
- Pin the CPU governor to performance, disable turbo variance if you can, close
  everything else, and use `--benchmark_repetitions=10 --benchmark_report_aggregates_only=true`
  to see the median and stddev — a single run is noise.
- Compare against a baseline with `compare.py` from the benchmark repo; a change
  under ~3% is usually not a change.
- Microbenchmarks lie about cache behavior. Confirm with an end-to-end
  measurement before believing a 10× microbenchmark win.

## Gotchas

- `ASSERT_*` inside a helper function that returns non-void doesn't compile;
  it can only `return;`. Use `EXPECT_*` or a `void` helper with `SCOPED_TRACE`.
- GTest death tests (`EXPECT_DEATH`) fork and don't play well with threads or
  sanitizers; expect flakiness in a threaded suite.
- Tests that share global/static state pass alone and fail under
  `--gtest_shuffle` or parallel `ctest -j`. Run both in CI.
- `gtest_discover_tests` runs the binary at build time; a test binary that
  crashes on startup produces a confusing CMake error.
- Sanitizer + benchmark = meaningless timings. Separate the CI legs.
- Floating-point comparisons: `EXPECT_DOUBLE_EQ` (ULP-based) or
  `EXPECT_NEAR(a, b, tol)`, never `==`.
- A test that mocks everything tests the mocks. Integration tests over real
  components find the bugs that ship.
- `benchmark::State`'s loop must be the only timed region — allocation in the
  loop body measures the allocator, not your algorithm.
