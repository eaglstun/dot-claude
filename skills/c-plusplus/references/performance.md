---
semantic_id: "9cIxBb5Zxjq1pt5ArPedc_U_vBnIIAAF"
related_ids:
  - "JZIhRS7rzjrxCs5K7mDfcfWbiUzIIAAP"
  - "4YIJRq9ryfq3OsxCricZQ_QrtRhKAAAK"
---
# Performance: what actually pays

Source:

- https://en.cppreference.com/w/cpp/language/as_if (the as-if rule)
- https://llvm.org/docs/Benchmarking.html
- https://perf.wiki.kernel.org/index.php/Tutorial
- https://github.com/google/benchmark/blob/main/docs/user_guide.md
- Agner Fog's optimization manuals: https://www.agner.org/optimize/
- https://www.brendangregg.com/flamegraphs.html

## 1. The order of operations

1. **Measure.** A profiler, on the release build, with a realistic workload.
2. **Fix the algorithm.** O(n²)→O(n log n) beats every micro-optimization ever
   written.
3. **Fix the memory access pattern.** Layout and locality dominate on modern
   hardware; this is usually the biggest win after algorithms.
4. **Reduce allocation.** Reserve, pool, arena, reuse buffers.
5. **Then** consider SIMD, threads, and instruction-level tricks.

Rough latency budget to reason with (a modern x86/ARM core):

| Operation                          | ~cost                        |
| ---------------------------------- | ---------------------------- |
| L1 hit                             | 1 ns / ~4 cycles             |
| L2 hit                             | ~4 ns                        |
| L3 hit                             | ~15 ns                       |
| main memory                        | ~80–100 ns                   |
| branch mispredict                  | ~5–15 ns                     |
| `malloc`/`free` (small)            | ~20–100 ns                   |
| atomic RMW, uncontended            | ~5–20 ns                     |
| atomic RMW, contended across cores | 100+ ns                      |
| mutex lock/unlock, uncontended     | ~20 ns                       |
| virtual call                       | ~2–5 ns (plus lost inlining) |
| thread context switch              | ~1–5 µs                      |
| syscall                            | ~0.1–1 µs                    |
| SSD read                           | ~50–150 µs                   |

A cache miss costs what ~200 arithmetic instructions cost. That single fact
explains most of the advice below.

## 2. Profilers

| Tool                                      | Platform | For                                                       |
| ----------------------------------------- | -------- | --------------------------------------------------------- |
| `perf record/report`                      | Linux    | sampling CPU profile, the default                         |
| `perf stat -d`                            | Linux    | cache misses, branch mispredicts, IPC                     |
| Instruments (Time Profiler / Allocations) | macOS    | sampling + allocation traces                              |
| VTune                                     | x86      | microarchitectural analysis, top-down                     |
| Tracy                                     | all      | frame-level, real-time, zone instrumentation for games/UI |
| heaptrack / massif                        | Linux    | allocation counts and heap growth                         |
| `-fprofile-generate/use`                  | all      | PGO, often a free 5–15%                                   |
| Compiler Explorer                         | web      | what did the compiler actually emit                       |

Flame graphs (`perf record -g` → `flamegraph.pl`) are the fastest route from
"it's slow" to "it's slow _here_". Use `--call-graph dwarf` if frame pointers are
omitted, or build with `-fno-omit-frame-pointer`.

## 3. Memory layout — the big one

**Contiguity beats everything.** `std::vector<T>` over `std::list<T>`,
`std::vector<T>` over `std::vector<std::unique_ptr<T>>` when you can.

**AoS → SoA** when you iterate over one field:

```cpp
// array of structs: 64-byte Particle, you touch 12 bytes → 80% of every cache line wasted
struct Particle { glm::vec3 pos, vel; glm::vec4 color; float mass; /*...*/ };
std::vector<Particle> particles;

// struct of arrays: the position loop reads only positions, fully packed
struct Particles {
    std::vector<glm::vec3> pos, vel;
    std::vector<float>     mass;
};
```

Other layout levers:

- **Order members largest-to-smallest** to cut padding. Check with
  `static_assert(sizeof(T) == N)` or `-Wpadded` / `pahole`.
- **Hot/cold splitting**: move rarely-touched fields behind a pointer so the hot
  struct fits fewer cache lines.
- **Avoid pointer chasing.** Indices into a vector are smaller, relocatable, and
  prefetchable.
- **False sharing**: two threads writing adjacent data in one 64-byte line
  serializes them. Pad to `hardware_destructive_interference_size`.
- **Prefetch** only as a last resort and only with measurements
  (`__builtin_prefetch`); the hardware prefetcher handles linear scans already.

## 4. Allocation

```cpp
v.reserve(n);                                    // the single highest-value one-liner
std::pmr::monotonic_buffer_resource arena{buf, sizeof buf};
std::pmr::vector<Node> nodes{&arena};            // zero heap traffic for a whole phase
```

- Reuse buffers across iterations instead of reallocating (`buf.clear()` keeps
  capacity).
- Small-string and small-vector optimization: `std::string` is already inline for
  short values; for vectors use `boost::container::small_vector` /
  `absl::InlinedVector` / `llvm::SmallVector`.
- A per-frame / per-request **arena** (`monotonic_buffer_resource`) turns
  thousands of `malloc`s into a pointer bump and one bulk free.
- Swap in a better global allocator when malloc shows up in the profile:
  **mimalloc**, **tcmalloc**, or **jemalloc** — often 10–30% on allocation-heavy
  multithreaded servers, for one link flag.

## 5. Branches, calls, and the optimizer

- Branch mispredicts hurt on _unpredictable_ branches only. Predictable ones are
  free. Branchless tricks (`std::min`, arithmetic selects, `cmov`) pay off only
  when the branch is genuinely random.
- `[[likely]]` / `[[unlikely]]` (C++20) help the layout, occasionally; PGO does
  it better and automatically.
- Devirtualize by making the class or method `final`, or by replacing the
  hierarchy with `std::variant` + `std::visit` for a closed set.
- Inlining is the enabling optimization for everything else. Keep hot small
  functions in headers (or use LTO), and check `-Rpass-missed=inline`.
- **LTO** (`-flto=thin`) is typically 5–10%, sometimes much more for
  header-light code. **PGO** on top is another 5–15% on branchy code.
- Do not fight the optimizer with tricks it already does: `++i` vs `i++` on
  ints, manual loop unrolling, `register`, `inline` for speed, or replacing
  `x/2` with `x>>1`. Verify on Compiler Explorer before "optimizing" by hand.

## 6. Copies and moves

- Pass `string_view`/`span` instead of `const std::string&`/`const vector&` when
  you only read — no conversion, no allocation.
- Mark move constructors `noexcept` or `std::vector` copies on growth.
- Watch for accidental copies: a `const auto&` loop variable that binds to a
  temporary because the range yields prvalues; a lambda capturing by value in a
  loop; a `std::function` parameter allocating per call; returning by `const T`
  (blocks moves).
- `-Wreturn-std-move`, clang-tidy's `performance-unnecessary-copy-initialization`
  and `performance-move-const-arg` catch a surprising number.

## 7. SIMD and parallelism

- Auto-vectorization works when loops are countable, contiguous, alias-free, and
  branch-light. `-Rpass=loop-vectorize -Rpass-missed=loop-vectorize` (clang) tells
  you why it failed; `__restrict` on pointers is often the fix.
- Portable SIMD: `std::simd` (C++26), `xsimd`, `highway`, `Eigen` for linear
  algebra. Intrinsics when you must, behind a runtime-dispatch layer.
- Threads: `std::execution::par` on standard algorithms costs one line, but
  needs real work per element. A bounded thread pool (or TBB / Taskflow) beats
  ad-hoc `std::async` for anything sustained.
- Amdahl is unforgiving: profile the serial fraction before parallelizing.

## 8. Compile-time performance

Slow builds cost more engineer-hours than most runtime wins save. See
`headers-modules-and-linkage.md`; the short list is: `-ftime-trace` +
ClangBuildAnalyzer to find the cost, forward declarations and PIMPL to cut the
graph, `extern template` to stop redundant instantiation, precompiled headers,
ccache, and Ninja.

## Gotchas

- Optimizing without a profile is a coin flip. The bottleneck is very rarely
  where it feels like it is.
- Debug-build benchmarks are worthless — ranges, `std::function`, and small
  wrappers cost 10× at `-O0` and 0× at `-O2`.
- `-O3` over `-O2` is not automatically faster; bigger code can thrash I-cache.
- `-ffast-math` changes results, breaks NaN handling, and is contagious across
  inlining boundaries. Never enable it globally.
- Microbenchmarks measure an empty cache-warm loop; the same code in a real
  program may be memory-bound and behave nothing like it.
- `std::endl` flushes on every line. Use `'\n'`. In a hot logging path this
  alone can be the bottleneck.
- `std::cout` with `sync_with_stdio(true)` (the default) is slow;
  `std::ios::sync_with_stdio(false)` roughly doubles throughput but forbids
  mixing with `printf`.
- Shared-pointer copies in a hot call chain do atomic refcount traffic for
  nothing. Pass `const&` or a raw reference downward.
- `std::unordered_map` is a linked-list-per-bucket design in every standard
  implementation; when hashing shows up in a profile, swapping to an open-
  addressing map is usually a bigger win than anything else you'll do that day.
- Measuring on a laptop with thermal throttling and turbo produces a 20% spread.
  Repetitions and medians, or a quiet machine.
