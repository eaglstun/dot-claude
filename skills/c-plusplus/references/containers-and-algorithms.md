---
semantic_id: "IQ45VK5BgTq3ssTGrmMbZ_wloZxQQAAI"
related_ids:
  - "4YIJRq9ryfq3OsxCricZQ_QrtRhKAAAK"
  - "KAoJ0b9rh763usSArGMb47E_uVxIIAAJ"
---
# Containers, iterators, and `<algorithm>`

Source:

- https://en.cppreference.com/w/cpp/container
- https://en.cppreference.com/w/cpp/algorithm
- https://en.cppreference.com/w/cpp/iterator
- https://en.cppreference.com/w/cpp/container/vector (complexity + invalidation tables)
- https://en.cppreference.com/w/cpp/container/unordered_map

## 1. Which container

| Need                                       | Container                                             | Notes                                             |
| ------------------------------------------ | ----------------------------------------------------- | ------------------------------------------------- |
| Default sequence                           | `std::vector`                                         | contiguous, cache-friendly. Start here always.    |
| Fixed size, known at compile time          | `std::array`                                          | on the stack, no allocation                       |
| Push/pop at both ends, stable refs         | `std::deque`                                          | chunked; refs stable on end-insert, iterators not |
| Splice, stable iterators, many mid-inserts | `std::list` / `forward_list`                          | almost never the right answer                     |
| Key→value, need order / range queries      | `std::map` / `set`                                    | RB-tree, node-based, `O(log n)`, stable refs      |
| Key→value, only lookup                     | `std::unordered_map` / `set`                          | `O(1)` average, poor locality                     |
| Small set of keys, tiny N                  | sorted `std::vector` + `binary_search`                | beats `map` up to surprisingly large N            |
| Stack / queue / priority queue             | `std::stack`, `queue`, `priority_queue`               | adaptors over deque/vector                        |
| Bit flags                                  | `std::bitset` (fixed) / `std::vector<bool>` (avoid)   |                                                   |
| Non-owning contiguous view                 | `std::span` (C++20)                                   |                                                   |
| Multi-dim non-owning view                  | `std::mdspan` (C++23)                                 |                                                   |
| Fixed-capacity, no heap                    | `std::inplace_vector` (C++26), `boost::static_vector` |                                                   |
| LRU/insertion-ordered map                  | not in the standard                                   | `boost::multi_index`, or vector+map               |

**Default to `std::vector`.** The constant factors of contiguity beat the
asymptotics of node-based containers for anything that fits in cache, and linear
scan of a small vector beats hashing.

`std::unordered_map` in libstdc++/libc++ is a bucket array of linked-list nodes —
one allocation and one cache miss per element. When it's hot, reach for
`absl::flat_hash_map`, `boost::unordered_flat_map`, or `ankerl::unordered_dense`;
2–5× is typical.

## 2. Invalidation rules (the ones that bite)

| Operation                                   | Invalidates                            |
| ------------------------------------------- | -------------------------------------- |
| `vector` insert/`push_back` causing realloc | **everything**                         |
| `vector` insert/erase (no realloc)          | iterators/refs at or after the point   |
| `vector::reserve`                           | everything, if capacity grows          |
| `deque` push_front/back                     | all _iterators_; references stay valid |
| `deque` insert/erase in the middle          | everything                             |
| `list`/`forward_list` insert                | nothing                                |
| `list` erase                                | only the erased element                |
| `map`/`set` insert                          | nothing                                |
| `map`/`set` erase                           | only the erased element                |
| `unordered_*` insert causing rehash         | all _iterators_; references stay valid |
| `unordered_*` erase                         | only the erased element                |

Mutating a container while iterating it is the top-3 C++ bug. The safe erase
idiom:

```cpp
for (auto it = v.begin(); it != v.end(); ) {
    if (pred(*it)) it = v.erase(it);      // erase returns the next valid iterator
    else ++it;
}
// or, better, no loop at all:
std::erase_if(v, pred);                   // C++20, works on every container
v.erase(std::remove_if(v.begin(), v.end(), pred), v.end());   // pre-C++20 erase-remove
```

## 3. `vector` mechanics

```cpp
std::vector<Widget> v;
v.reserve(n);                     // ONE allocation; do this whenever n is known
v.emplace_back(a, b);             // constructs in place; returns a reference (C++17)
v.push_back(std::move(w));        // move in
v.shrink_to_fit();                // non-binding request
std::vector<Widget>{}.swap(v);    // the pre-C++11 "actually free it" trick
```

- Growth is geometric (×2 in libstdc++/MSVC-ish, ×1.5 in MSVC) → `push_back` is
  amortized O(1), but each realloc moves everything.
- `size()` vs `capacity()`: `resize` changes size (and constructs elements),
  `reserve` changes only capacity.
- `emplace_back` avoids one move versus `push_back(T{...})`, and _nothing_
  versus `push_back(std::move(existing))`. It is not automatically faster, and it
  bypasses `explicit`, so it can construct things you didn't mean.
- Reallocation uses the move constructor only if it is `noexcept`; otherwise it
  copies to preserve the strong guarantee.

## 4. Associative containers

```cpp
auto [it, inserted] = m.try_emplace(key, expensive_args...);   // C++17: no construction if present
m.insert_or_assign(key, value);
if (auto it = m.find(key); it != m.end()) use(it->second);     // one lookup, not two
if (m.contains(key)) { }                                        // C++20
auto node = m.extract(key);  node.key() = newkey;  m.insert(std::move(node));  // rekey, no realloc
```

- `operator[]` **default-constructs on miss** and is non-const. `at()` throws.
  `find`/`contains` are the read-only ways.
- `map::emplace` constructs the pair even when the key exists; `try_emplace`
  does not. Prefer `try_emplace`.
- **Heterogeneous lookup** avoids constructing a temporary key: declare
  `std::map<std::string, V, std::less<>>` and then `m.find("literal")` does not
  allocate a `std::string`. For `unordered_map` (C++20) you need a transparent
  hash _and_ equal (`is_transparent` typedef on both).
- Custom keys: `map`/`set` need `operator<` or a comparator (strict weak
  ordering — `<=` is a bug); `unordered_*` need `std::hash` specialization plus
  `operator==`.

## 5. Iterators

Categories, weakest to strongest: input / output → forward → bidirectional →
random access → contiguous (C++20). C++20 also introduces the `std::ranges`
iterator concepts, which are stricter and better-diagnosed than the legacy tags.

```cpp
std::back_inserter(v)         // push_back on assignment
std::inserter(m, m.end())
std::istream_iterator<int>(std::cin), std::istream_iterator<int>{}
std::ostream_iterator<int>(std::cout, ", ")
std::next(it, 2), std::prev(it), std::distance(a, b), std::advance(it, n)
```

Half-open ranges `[first, last)` everywhere: `end()` is not dereferenceable, and
`last - first` is the size.

## 6. Algorithms worth knowing by name

**Search**: `find`, `find_if`, `find_first_of`, `search`, `count_if`,
`all_of`/`any_of`/`none_of`, `binary_search`, `lower_bound`/`upper_bound`/
`equal_range` (sorted input required), `min_element`/`max_element`/`minmax_element`.

**Order**: `sort`, `stable_sort`, `partial_sort`, `nth_element` (O(n) selection —
use it instead of a full sort for medians/top-k), `is_sorted`, `partition`,
`stable_partition`, `rotate`, `reverse`, `shuffle`, `next_permutation`.

**Modify**: `copy`, `copy_if`, `move`, `transform`, `fill`, `generate`,
`replace_if`, `remove_if` (does **not** erase — it shuffles and returns the new
logical end), `unique` (needs sorted input to be a true dedup), `swap_ranges`,
`sample`.

**Numeric** (`<numeric>`): `accumulate` (sequential, use the 3-arg form and mind
the init type), `reduce` (unordered, parallelizable), `transform_reduce`
(fused map-reduce, the workhorse for dot products), `inner_product`,
`partial_sum`, `inclusive_scan`/`exclusive_scan`, `iota`, `gcd`/`lcm`,
`midpoint` (C++20, overflow-safe).

**Set ops on sorted ranges**: `set_union`, `set_intersection`,
`set_difference`, `merge`, `includes`.

**Parallel** (C++17, `<execution>`): pass `std::execution::par` or `par_unseq` as
the first argument. libstdc++ needs TBB linked (`-ltbb`); libc++ support landed
only recently, and MSVC has it. Check before relying on it.

```cpp
std::sort(std::execution::par, v.begin(), v.end());
double dot = std::transform_reduce(std::execution::par_unseq,
                                   a.begin(), a.end(), b.begin(), 0.0);
```

## 7. `std::span` and `std::mdspan`

```cpp
void process(std::span<const float> data);     // takes vector, array, C array, pointer+size
process(vec);
process({ptr, n});
auto first_half = data.subspan(0, data.size() / 2);

std::mdspan m{ptr, 3, 4};                       // C++23: 2-D view, row-major by default
m[1, 2] = 0.5f;                                 // multi-arg subscript (C++23)
```

`span` is the correct parameter type for "contiguous sequence I do not own" — it
replaces the `(T* ptr, size_t n)` pair and the `const vector<T>&` that forces a
particular container. It is a view: **it never extends lifetime**.

## Gotchas

- `remove_if` doesn't remove. Without the `erase` half, the container's size is
  unchanged and the tail holds moved-from junk. `std::erase_if` (C++20) is the
  fix; it is a free function, not a member.
- `map::operator[]` inserts on read. `if (m[k] == 0)` grows the map.
- `vector<bool>` is a bitfield proxy; `auto x = v[i]` gives you a proxy, not a
  bool, and `&v[0]` doesn't compile. Use `vector<char>`/`deque<bool>`/`bitset`.
- Comparators must be **strict weak orderings**. A `<=` comparator makes
  `std::sort` read out of bounds — a real crash, not a wrong order.
- `std::sort` is unstable; equal elements are reordered. Use `stable_sort` when
  that matters (it allocates).
- Iterator invalidation during `push_back` inside a loop over the same vector.
- `std::accumulate(v.begin(), v.end(), 0)` on a vector of doubles accumulates
  into an `int`. Write `0.0`.
- Passing unsorted input to `binary_search`/`lower_bound`/`unique`/`set_*` is UB
  with no diagnostic.
- `std::string::npos` is `size_t(-1)`; comparing `find(...) >= 0` is always true.
- `unordered_map` iteration order is unspecified and differs between runs with
  some allocators — never depend on it for output determinism.
