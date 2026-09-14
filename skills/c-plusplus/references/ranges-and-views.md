---
semantic_id: "JZIhRS7rzjrxCs5K7mDfcfWbiUzIIAAP"
related_ids:
  - "pQYhxOrrxTr8vshKrGFfcfV7tVvBYAAJ"
  - "paaJ0arbyxp7KsZDqnGfc_ivhVTQcAAF"
---
# Ranges and views (C++20 / C++23)

Source:

- https://en.cppreference.com/w/cpp/ranges
- https://en.cppreference.com/w/cpp/algorithm/ranges
- https://en.cppreference.com/w/cpp/ranges/range_adaptor_closure
- https://en.cppreference.com/w/cpp/ranges/to (C++23)
- https://github.com/ericniebler/range-v3 (the pre-C++20 library, still ahead of the standard)

## 1. Why bother

`std::ranges` algorithms take a range instead of an iterator pair, are
constrained by concepts (so errors point at your code, not at line 1800 of
`bits/stl_algo.h`), support projections, and compose with `|`.

```cpp
std::ranges::sort(v);                                  // no .begin()/.end()
std::ranges::sort(people, {}, &Person::age);           // projection: sort by member
auto it = std::ranges::find(v, 42);
bool ok = std::ranges::all_of(v, [](int x){ return x > 0; });
```

The **projection** parameter (3rd/4th argument on most range algorithms) is the
underrated feature: it replaces most one-line comparator lambdas with a
pointer-to-member.

## 2. Views

A **view** is a lazy, non-owning, O(1)-copyable range. Nothing is computed until
iterated; nothing is allocated.

```cpp
namespace rv = std::views;

auto evens_squared = v | rv::filter([](int x){ return x % 2 == 0; })
                       | rv::transform([](int x){ return x * x; })
                       | rv::take(10);

for (int x : evens_squared) { ... }        // work happens HERE, once, per element
```

The catalogue (C++20 unless noted):

| View                                          | Does                                               |
| --------------------------------------------- | -------------------------------------------------- |
| `views::all`                                  | wrap a range as a view                             |
| `views::filter`                               | keep elements matching a predicate                 |
| `views::transform`                            | map each element                                   |
| `views::take` / `take_while`                  | prefix                                             |
| `views::drop` / `drop_while`                  | suffix                                             |
| `views::reverse`                              | backwards (needs bidirectional)                    |
| `views::join`                                 | flatten a range of ranges                          |
| `views::split` / `lazy_split`                 | split on a delimiter                               |
| `views::keys` / `values`                      | `elements<0>` / `elements<1>` on a map             |
| `views::elements<N>`                          | the Nth of each tuple                              |
| `views::common`                               | make begin/end the same type for legacy algorithms |
| `views::counted(it, n)`                       | n elements from an iterator                        |
| `views::iota(0)` / `iota(0, n)`               | lazy integer sequence, infinite if unbounded       |
| `views::single` / `empty`                     | 1 or 0 elements                                    |
| `views::zip` (C++23)                          | tuple-wise pairing of N ranges                     |
| `views::zip_transform` (C++23)                | zip + apply                                        |
| `views::enumerate` (C++23)                    | `(index, value)` pairs                             |
| `views::adjacent<N>` / `pairwise` (C++23)     | sliding tuple window                               |
| `views::slide` / `chunk` / `chunk_by` (C++23) | windowing and grouping                             |
| `views::stride` (C++23)                       | every Nth                                          |
| `views::join_with` (C++23)                    | flatten with a separator                           |
| `views::cartesian_product` (C++23)            | N-ary product                                      |
| `views::repeat` (C++23)                       | value, N times or forever                          |
| `views::as_const` / `as_rvalue` (C++23)       | change element category                            |
| `views::concat` (C++26)                       | chain ranges end to end                            |

## 3. Materializing

Views are lazy; to get a container back, C++23 has `ranges::to`:

```cpp
auto names = people
    | std::views::filter(&Person::active)
    | std::views::transform(&Person::name)
    | std::ranges::to<std::vector>();                  // C++23

auto lookup = pairs | std::ranges::to<std::map<int, std::string>>();
```

Pre-C++23, the manual version:

```cpp
std::vector<std::string> names;
std::ranges::copy(view, std::back_inserter(names));
// or, when the view is sized and common:
std::vector<int> out(view.begin(), view.end());
```

## 4. Range concepts

```cpp
template <std::ranges::input_range R>
    requires std::same_as<std::ranges::range_value_t<R>, int>
void consume(R&& r);
```

Concept ladder: `range` → `input_range` → `forward_range` → `bidirectional_range`
→ `random_access_range` → `contiguous_range`. Orthogonal: `sized_range`,
`common_range` (begin and end are the same type), `borrowed_range` (iterators
outlive the range — `span`, `string_view`, lvalue containers), `viewable_range`.

Helper aliases: `range_value_t`, `range_reference_t`, `range_size_t`,
`iterator_t`, `sentinel_t`.

**Sentinels** are the deep change: `end()` need not be an iterator of the same
type, which is how `views::iota(0)` can be infinite and how a null-terminated
string can be a range without a first pass to find its length.

## 5. Writing a function that takes a range

```cpp
// takes any range, forwards correctly
void print_all(std::ranges::input_range auto&& r) {
    for (auto&& e : r) std::print("{} ", e);
}

// a custom view: inherit view_interface, hold iterators, be O(1) copyable
class Repeat : public std::ranges::view_interface<Repeat> { /* ... */ };
```

For a custom pipeable adaptor, C++23 gives
`std::ranges::range_adaptor_closure<Derived>` — before that, writing one
portably was genuinely hard and most people used range-v3.

## 6. Ranges vs plain loops

Ranges win on: composability, no intermediate containers, no index arithmetic,
projections, and the fact that `filter | transform` fuses into one pass.

Ranges lose on: compile time (measurably — heavy pipelines are template-thick),
debug-build performance (unoptimized views are _slow_, sometimes 10×; always
measure release), error message length when a constraint fails, and debugger
readability.

Practical stance: use range _algorithms_ freely (they cost nothing over the
classic ones); use view _pipelines_ where they clarify, and check the release
numbers before putting a five-stage pipeline in a hot loop.

## Gotchas

- **`filter_view` caches `begin()`.** The first `begin()` walks to the first
  matching element and memoizes it, so a filter view is not `const`-iterable and
  mutating the underlying range through the view can give stale results.
- Views do not own. `auto v = get_vector() | views::filter(...)` dangles the
  moment the temporary dies. C++20 partly guards this via `viewable_range` /
  `borrowed_range`, but a pipeline stored in a variable that outlives its source
  is a use-after-free. (C++23's `owning_view` helps for the _direct_ temporary
  case only.)
- Re-iterating a view re-runs the work. Two passes over a `transform` view call
  the function twice per element. Materialize if the function is expensive or
  has side effects.
- `views::split` in C++20 was nearly unusable (it produced a lazy range of lazy
  ranges); C++23 fixed it and added `join_with`. If a split example from a blog
  post doesn't compile, that's why.
- Range algorithms live in `std::ranges::`, not `std::`. `std::sort(v)` does not
  exist; `std::ranges::sort(v)` does.
- `std::ranges::sort` requires `random_access_range` + `sortable`; passing a
  `std::list` gives a concept error (use `list::sort`).
- Debug-mode iteration through a deep pipeline is slow enough to change
  benchmark conclusions. Compare at `-O2`.
- libstdc++/libc++/MSVC differ in which C++23 views have shipped; check
  `__cpp_lib_ranges_zip` and friends rather than assuming.
