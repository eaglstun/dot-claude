---
semantic_id: "2vC-TVZ5bsyhB7yQCJWY0fkdVxdoMAAF"
related_ids:
  - "3PCoCXZd78wrDZg5rJFYUflZVpdJoAAM"
  - "lPD-DXbp6RT7h5y4CJExUbg6VkUpIAAH"
---
# Performance and profiling

Source:

- <https://nnethercote.github.io/perf-book/> (The Rust Performance Book)
- <https://doc.rust-lang.org/cargo/reference/profiles.html> (opt-level, lto, codegen-units)
- <https://doc.rust-lang.org/rustc/codegen-options/index.html> (target-cpu and friends)
- <https://bheisler.github.io/criterion.rs/book/> (statistically honest benchmarks)
- <https://github.com/flamegraph-rs/flamegraph> and <https://github.com/mstange/samply>

## 1. Measure first, and measure in release

A debug build is 10x to 100x slower than release and tells you nothing about where the time
goes. Every number in this page assumes `--release`. Optimising from a debug profile is the
most common wasted week in Rust.

The order of operations that actually works: pick a representative workload, get a
reproducible timing, profile it to find where the time is, fix the top item, re-measure.
Algorithmic wins dominate micro-optimisation, and a profiler will tell you which one you
have.

## 2. Profiles worth setting

```toml
[profile.release]
opt-level = 3          # default; "s"/"z" optimise for size instead
lto = "thin"           # "fat" for max cross-crate inlining, much slower to build
codegen-units = 1      # better optimisation, slower build, no parallelism
panic = "abort"        # smaller and slightly faster; kills catch_unwind and unwind tests
strip = "debuginfo"

# The profile you actually profile with: release speed, but symbols
[profile.profiling]
inherits = "release"
debug = true
strip = false
```

`lto = "thin"` plus `codegen-units = 1` is the usual 5% to 20% win on a real binary, paid
for in build time. Measure whether your crate cares before making CI 3x slower.

For dependency-heavy debug builds, the reverse trick is excellent:

```toml
[profile.dev.package."*"]
opt-level = 2          # optimise DEPENDENCIES only; your crate stays fast to compile
```

`RUSTFLAGS="-C target-cpu=native"` (or a `.cargo/config.toml` `rustflags` entry) enables
AVX2/AVX-512/NEON features the portable baseline cannot assume. It produces a binary that
crashes with SIGILL on older CPUs, so it is for your own machines and containers you
control, not for a published artifact.

## 3. Profilers

| tool                    | platform     | shows                                       |
| ----------------------- | ------------ | ------------------------------------------- |
| `cargo flamegraph`      | Linux, macOS | sampled stacks as a flame graph             |
| `samply record`         | Linux, macOS | same, opens in the Firefox Profiler UI      |
| Instruments             | macOS        | Time Profiler, Allocations, System Trace    |
| `perf` / `perf stat`    | Linux        | cycles, cache misses, branch mispredicts    |
| `dhat` (crate)          | any          | heap profile from inside the process        |
| `heaptrack`             | Linux        | allocation counts and peaks                 |
| `cargo-bloat`           | any          | which functions/crates dominate binary size |
| `cargo-llvm-lines`      | any          | which generic instantiations dominate IR    |
| `cargo build --timings` | any          | HTML report of what is slow to **compile**  |

On macOS, `samply record ./target/profiling/mytool` is the fastest path to a usable
profile, and it needs `debug = true` in the profile or you get hex addresses.

`cargo llvm-lines` is the specific tool for "my compile times exploded": it usually
fingers one over-generic function that should take `&dyn` or be split into a small generic
shell around a large non-generic body.

## 4. Benchmarking without lying to yourself

Use criterion or divan, never a hand-rolled `Instant::now()` loop:

```rust
c.bench_function("parse", |b| b.iter(|| parse(black_box(&input))));
```

`black_box` is mandatory in both directions: it stops the optimiser from constant-folding
the input and from deleting the unused result. A benchmark reporting single-digit
picoseconds has been optimised away.

Criterion reports confidence intervals and compares to the previous run, which is the only
way to distinguish a 3% improvement from machine noise. Pin the CPU governor, close the
browser, and treat anything under 5% on a laptop as unproven.

## 5. The wins, roughly in order of payoff

**Allocation.** Most Rust hot loops are allocator-bound, not compute-bound.

- `Vec::with_capacity(n)` and `String::with_capacity(n)` when the size is known.
- Reuse one buffer across iterations (`buf.clear()`) instead of allocating per item.
- `SmallVec`/`ArrayVec` for collections that are almost always tiny.
- Avoid `to_string()`/`clone()` in hot paths: take `&str`, return `Cow<'_, str>` when a
  function usually returns its input unchanged.
- `format!` allocates; `write!` into an existing `String` does not.

**Hashing.** The default `HashMap` hasher is SipHash 1-3, chosen for HashDoS resistance,
and it is slow for small keys. Swap in `rustc-hash` (`FxHashMap`) or `ahash` for internal
maps whose keys are not attacker-controlled. For integer keys the difference is often 2x.
Do **not** swap it for a map keyed by untrusted user input.

**Bounds checks.** Prefer iterators over indexed loops: `for x in &v` has no bounds check,
`for i in 0..v.len() { v[i] }` may. When you must index, hoist a slice and assert its
length first (`let s = &v[..n];`), which lets LLVM prove the rest.

**Vectorisation.** `chunks_exact(4)` autovectorises where `chunks(4)` cannot, because the
remainder is handled separately. `iter().sum()` on floats does **not** vectorise (float
addition is not associative and rustc will not reorder it); use explicit chunking or the
`wide` crate. `std::simd` is still nightly.

**Parallelism.** `rayon` turns `iter()` into `par_iter()` for CPU-bound data parallelism and
is usually a one-line change. It is the wrong tool for I/O concurrency (that is async).

**Dispatch.** `dyn Trait` costs an indirect call and blocks inlining. Generics cost compile
time and binary size. In a hot loop, generics; at a plugin boundary called once per request,
`dyn` and stop thinking about it.

**`#[inline]`.** Only matters **across crate boundaries** (within a crate LLVM decides for
itself, and generic functions are already available to the caller). Put `#[inline]` on small
public functions in a library. `#[inline(always)]` is a hammer that regularly makes things
slower by blowing the instruction cache.

**Allocators.** On Linux, `mimalloc` or `jemallocator` as the global allocator is often a
free 10% on allocation-heavy multithreaded workloads. macOS and Windows have their own
system allocators; measure before assuming.

## 6. Compile time, which is also performance

- `cargo check` for the edit loop; only `cargo build` when you need to run it.
- Trim features (`default-features = false`), especially on `syn`, `tokio`, and `reqwest`.
- `sccache` for shared caching, `cargo build --timings` to find the pole in the tent.
- The Cranelift backend (`-Zcodegen-backend=cranelift`) speeds up debug builds substantially
  on nightly.
- Fewer, larger crates compile faster in a clean build; more, smaller crates parallelise and
  cache better on rebuild. The workspace shape is a compile-time decision too.

## Gotchas

- **Benchmarking a debug build.** Everything else on this page is downstream of this one.
- `black_box` omitted means you benchmarked nothing. Suspiciously fast is a bug report about
  your benchmark, not a result.
- Integer overflow checks are **on in debug, off in release**, so debug timings for numeric
  code are doubly misleading, and a release build silently wraps where debug panicked.
- `-C target-cpu=native` does not apply to the precompiled standard library, so std stays at
  the baseline unless you rebuild it with `-Z build-std`. The measured win is therefore
  smaller than expected, and portability is already gone.
- `lto = true` in Cargo.toml means **fat** LTO, not thin. On a large workspace that can turn
  a 40 second build into 6 minutes for a couple of percent.
- `panic = "abort"` breaks `#[should_panic]` tests and `catch_unwind`, and it applies to the
  whole dependency graph. It is fine for a leaf binary, wrong for a library's own profile.
- Profiling on macOS without `debug = true` gives you a flame graph of hexadecimal, and
  `strip` in the release profile silently removes what you need.
- Replacing the default hasher removes HashDoS protection. If any key comes from the
  network, keep SipHash.
- `Instant::now()` around a small operation measures the timer. Anything under a microsecond
  needs a real benchmark harness.
- `String::push_str` in a loop without `with_capacity` reallocates and memcpys repeatedly;
  the growth is amortised O(1) but the constant is not free at scale.
- A `#[derive(Clone)]` on a large struct in a hot path is invisible in the source and
  expensive in the profile. Clones do not look like allocations at the call site.
- Micro-optimising a function that is 2% of the profile caps your win at 2%. Read the flame
  graph before touching anything.
