---
topic_id: "v2:OJLG"
topic_path: "rust-arkit/rust-fundamentals"
semantic_id: "mNh7HTZN7Sx7lhTsrrZSUeipcjxoYAAN"
related_ids:
  - "vKDvGWJf70R7BhSoKrHZWYhJ0XTIcAAA"
  - "urRuzaZ578T7mxDgNIRyUfgpM1BJIAAE"
---
# Collections and iterators

Source:

- https://doc.rust-lang.org/std/collections/index.html (which collection when, entry API, perf table)
- https://doc.rust-lang.org/book/ch08-02-strings.html (String vs &str)
- https://doc.rust-lang.org/book/ch13-02-iterators.html (iterators, adaptors, laziness)
- https://doc.rust-lang.org/std/iter/trait.Iterator.html (adaptor reference)
- https://doc.rust-lang.org/std/primitive.slice.html (chunks/windows/sort\_\*)
- https://docs.rs/itertools/latest/itertools/ (itertools)

## 1. Which collection

- **`Vec<T>`**: the default sequence. Contiguous, cache-friendly, O(1) push/pop at the end, O(n) insert/remove in the middle. Doubles as a stack.
- **`VecDeque<T>`**: ring buffer; O(1) push/pop at **both** ends. The queue/BFS structure. Not contiguous (use `make_contiguous` if you need a slice).
- **`HashMap<K, V>`**: the default map. O(1) average ops, arbitrary iteration order (randomized per-process by SipHash, HashDoS-resistant). Keys need `Eq + Hash`.
- **`BTreeMap<K, V>`**: sorted by key, O(log n) ops, supports `range(a..b)`, min/max, ordered iteration. Keys need `Ord`. Pick it when order or range queries matter, not for speed.
- **`HashSet<T>` / `BTreeSet<T>`**: the maps with unit values; membership, dedup, set algebra (`union`, `intersection`).
- Std's own advice: **Vec and HashMap cover most use cases**; `LinkedList` is almost never the answer; `BinaryHeap` for priority queues.

## 2. String vs &str vs slices

`String` is an owned, growable, heap UTF-8 buffer (a `Vec<u8>` with invariants). `&str` is a borrowed view of UTF-8 bytes: string literals, slices of a String, both. Same relationship as `Vec<T>` to `&[T]`. API rule: **take `&str` (or `impl AsRef<str>`) as parameters, store/return `String`**; `&String` as a parameter is a smell (deref coercion makes `&str` strictly more general).

- No integer indexing: `s[0]` doesn't compile because UTF-8 is variable-width. `s.chars()` for chars, `s.bytes()` for bytes, `&s[a..b]` slices by **byte** offsets and panics mid-codepoint.
- Concatenation: `format!("{a}{b}")` clones both; `a + &b` moves `a`; `push_str` appends in place.

## 3. The entry API

One lookup instead of contains-then-insert:

```rust
let mut counts: HashMap<String, u32> = HashMap::new();
for w in text.split_whitespace() {
    *counts.entry(w.to_string()).or_insert(0) += 1;
}
// also: .or_default(), .or_insert_with(Vec::new), .and_modify(|v| *v += 1)
```

`or_insert` returns `&mut V`. For "insert if absent, else update" always reach for `entry`; the naive `if !m.contains_key(k) { m.insert(...) }` hashes twice and fights the borrow checker.

## 4. Iterator adaptors

All adaptors are **lazy**: nothing runs until a consumer (`collect`, `sum`, `for`, `fold`, `count`, `for_each`) pulls. `iter.map(f);` alone does nothing (the compiler warns: "iterators are lazy and do nothing unless consumed").

- `map(f)` transform; `filter(p)` keep matching; `filter_map(f)` filter+map in one via `Option` (great with `.parse().ok()`); `flat_map(f)` map then flatten one level.
- `fold(init, f)` general reduction; `sum`/`product`/`max_by_key` are special cases.
- `zip(other)` pairs until the **shorter** ends (silently truncates); `enumerate()` gives `(usize, item)`; `rev()` needs `DoubleEndedIterator`; `chain(other)` concatenates.
- `take(n)`, `skip(n)`, `take_while`, `skip_while`, `step_by(n)`, `peekable()` round out the usual set.

## 5. collect and the turbofish

`collect` is generic over `FromIterator`; the target must be stated by annotation or turbofish:

```rust
let v: Vec<i32> = (1..=3).map(|x| x * 2).collect();
let v = (1..=3).map(|x| x * 2).collect::<Vec<_>>();     // turbofish
let m: HashMap<_, _> = pairs.into_iter().collect();      // from (K, V) tuples
let s: String = chars.into_iter().collect();
```

Power move: `collect` through `Result` or `Option` short-circuits on the first failure:

```rust
let nums: Result<Vec<i32>, _> = ["1", "2", "x"].iter().map(|s| s.parse()).collect();
```

## 6. iter() vs into_iter() vs iter_mut()

- `iter()` -> `&T`, collection untouched.
- `iter_mut()` -> `&mut T`, mutate in place.
- `into_iter()` -> `T`, **consumes** the collection (needed to collect owned values out).

`for x in &v` desugars to `iter()`, `for x in &mut v` to `iter_mut()`, `for x in v` to `into_iter()` (moves `v`). On a `&Vec<T>`, `into_iter()` yields `&T`, which surprises people: ownership of the iterator's source decides.

## 7. chunks, windows, sorting

- `slice.chunks(n)`: non-overlapping runs (last may be short); `chunks_exact(n)` for a guaranteed size plus a `remainder()`.
- `slice.windows(n)`: **overlapping** views, length n each; classic for pairwise diffs (`w[1] - w[0]`).
- `sort()` / `sort_by(cmp)` / `sort_by_key(f)`: stable, allocates temp memory. `sort_unstable*`: usually faster, no allocation, equal elements may reorder. `sort_by_key` calls the key fn multiple times; `sort_by_cached_key` memoizes when the key is expensive.
- Floats aren't `Ord`; use `v.sort_by(|a, b| a.total_cmp(b))`.
- `select_nth_unstable` (quickselect) beats a full sort for "top k" / median.

## 8. itertools, briefly

The `itertools` crate fills std gaps: `sorted`, `group_by`/`chunk_by`, `unique`, `join`, `cartesian_product`, `multipeek`, `izip!` (3+ way zip), `tuples::<(_, _)>()`. If you're writing a gnarly manual fold, check itertools first; it's the one near-universal utility dependency.

## 9. Performance notes

- **`Vec::with_capacity(n)`** (and `HashMap::with_capacity`) when the size is known or estimable: repeated `push` reallocates and copies at each doubling. `String::with_capacity` likewise for building strings.
- **`extend(iter)` over a push loop**: `v.extend(iter)` uses `size_hint` to reserve once; `collect` into a fresh Vec does the same. A manual `for x in it { v.push(x) }` forfeits that.
- **Avoid collect-then-iterate**: `let tmp: Vec<_> = xs.iter().map(f).collect(); for t in tmp {...}` allocates a whole intermediate for nothing; keep the chain lazy and consume once. Same for `.collect::<Vec<_>>().len()` (use `count()`) and `.collect::<Vec<_>>().into_iter()` bridges.
- `retain` beats filter-collect-reassign for in-place removal; `drain(..)` moves elements out without freeing capacity.
- Iterator chains generally compile to the same code as hand loops (zero-cost); prefer clarity, then profile.

## Gotchas

- HashMap iteration order is random and changes between runs; any test or output relying on it is flaky by construction. Want determinism: BTreeMap, or collect and sort.
- Modifying a collection while iterating it is E0502 by design; use `retain`, `drain`, indices, or collect the changes and apply after.
- `zip` truncating to the shorter side silently loses data; length-check first or use `itertools::zip_eq` (panics on mismatch) when equality is an invariant.
- `&s[0..n]` on a String panics at runtime if n is not a char boundary; use `char_indices`, `get(0..n)` (returns Option), or `floor_char_boundary` (recent std).
- `sort_by_key(|x| foo(x))` can't return a key that borrows from `x` (lifetime error E0311-ish); use `sort_by` with a comparator, or `sort_by_cached_key`.
- `filter` on `iter()` gives the closure `&&T` (reference to the reference the iterator yields); pattern-match `|&&x|` for Copy types or deref, a classic confusing E0308.
- `into_iter()` on an **array** yields values since edition 2021, but older code and some docs still show the `iter().copied()` workaround; on `&Vec` it still yields references.
- `collect::<String>()` works from `char` or `&str` items but not from `u8`; bytes need `String::from_utf8(vec)?`.
- `with_capacity(n)` sets capacity, not length: `v[0]` on it still panics. `vec![0; n]` or `resize` if you need initialized length.
- `drain` without consuming the returned iterator still removes elements (it removes on drop); relying on laziness to "cancel" a drain does not work, but `leak`-ing it via `mem::forget` leaves the Vec in a valid but element-lost state.
