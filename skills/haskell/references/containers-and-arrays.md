---
semantic_id: "aX5GkKZR4zmy-4iW7pEJ3W9-rV72wAAK"
related_ids:
  - "LZ5GmZAZayGY-8yG6oEfVcp-7V6WwAAO"
  - "KfsGhKYZ7-3585ySy4ELUe1urU9yAAAC"
---
# Containers, vectors, and arrays

Source:

- https://hackage.haskell.org/package/containers
- https://hackage.haskell.org/package/unordered-containers
- https://hackage.haskell.org/package/vector
- https://hackage.haskell.org/package/array
- https://hackage.haskell.org/package/massiv

## 1. The decision table

| Need                                | Use                                    |
| ----------------------------------- | -------------------------------------- |
| Ordered key→value, range queries    | `Data.Map.Strict` (size-balanced tree) |
| Key→value, keys hashable, no order  | `Data.HashMap.Strict` (HAMT)           |
| Set of ordered things               | `Data.Set`                             |
| Set of hashable things              | `Data.HashSet`                         |
| `Int` keys, dense-ish               | `Data.IntMap.Strict` / `Data.IntSet`   |
| Deque / random access / concat      | `Data.Sequence` (finger tree)          |
| Dense numeric array, immutable      | `Data.Vector.Unboxed`                  |
| Dense array of boxed values         | `Data.Vector`                          |
| Array shared with C                 | `Data.Vector.Storable`                 |
| In-place algorithm                  | `Data.Vector.Mutable` in `ST` or `IO`  |
| Multi-dimensional, parallel         | `massiv`, or `repa`                    |
| Stack, or a stream you consume once | `[]`                                   |
| Non-empty by construction           | `Data.List.NonEmpty`                   |
| Priority queue                      | `pqueue`, or `Set` of `(prio, k)`      |

## 2. Complexity cheat sheet

| Operation   | `[]` | `Seq`         | `Map`           | `HashMap` | `IntMap`    | `Vector` |
| ----------- | ---- | ------------- | --------------- | --------- | ----------- | -------- |
| index `i`   | O(i) | O(log n)      | —               | —         | —           | **O(1)** |
| cons        | O(1) | O(1)          | —               | —         | —           | O(n)     |
| snoc/append | O(n) | O(1)/O(log n) | —               | —         | —           | O(n)     |
| lookup key  | O(n) | —             | O(log n)        | ~O(1)     | O(min(n,W)) | —        |
| insert      | —    | —             | O(log n)        | ~O(1)     | O(min(n,W)) | O(n)     |
| union       | —    | —             | O(m log(n/m+1)) | O(m)      | O(m+n)      | —        |
| size        | O(n) | O(1)          | O(1)            | O(n)      | O(1)        | O(1)     |
| min/max key | —    | —             | O(log n)        | —         | O(log n)    | —        |

`HashMap.size` is O(n) — a small trap when you're used to `Map.size` being free.

**`Map` vs `HashMap`**: `Map` needs `Ord`, keeps order (so `toList` is sorted,
and you get `lookupLT`, `splitLookup`, range folds), and has no hash-collision
attack surface. `HashMap` is faster for large maps with `Text` keys. Default to
`Map`; move to `HashMap` when profiling says so and ordering doesn't matter.

## 3. `Data.Map` idioms

```haskell
import qualified Data.Map.Strict as M

M.lookup k m                     -- Maybe v
M.findWithDefault v0 k m
M.insertWith (+) k 1 m           -- counter
M.alter f k m                    -- insert/update/delete in one pass
M.adjust f k m                   -- update if present
M.unionWith (+) a b
M.fromListWith (++) [(k,[v])]    -- group; NOTE the arg order of the combining fn
M.foldrWithKey / M.foldlWithKey' / M.traverseWithKey
M.toAscList, M.keys, M.elems
M.lookupMin, M.lookupLE, M.split, M.spanAntitone
M.mapMaybe, M.filterWithKey, M.partition
M.restrictKeys, M.withoutKeys
M.merge / M.mergeA               -- Data.Map.Merge.Strict: fused two-map traversal
```

**`fromListWith f` applies `f newValue oldValue`** — reversed from what most
people assume, which silently reverses accumulated lists. Verify with a
two-element test.

`Data.Map.Strict` is strict in _values on insertion_; `Data.Map` (=
`Data.Map.Lazy`) is not, which makes `insertWith (+)` a thunk factory. Keys have
always been forced (the tree must compare them).

`Data.Map.Merge.Strict.merge` is the efficient way to combine two maps with
different behaviours for left-only/right-only/both — one traversal instead of
three.

## 4. `Data.Sequence`

Finger tree: O(1) amortized cons/snoc/head/last, O(log n) index and split, O(log)
concatenation.

```haskell
import Data.Sequence (Seq, (|>), (<|), (><), ViewL(..), viewl)
import qualified Data.Sequence as Seq

q  = Seq.fromList [1,2,3]
q' = q |> 4                     -- append right
Seq.index q 1
case Seq.viewl q of x :< rest -> ...
-- or pattern synonyms:  case q of x Seq.:<| rest -> ...
```

The right choice for a queue, a builder you also need to read from, or an
undo/redo list. Overkill for a list you only fold once.

## 5. `vector`

```haskell
import qualified Data.Vector as V
import qualified Data.Vector.Unboxed as U
import qualified Data.Vector.Unboxed.Mutable as UM

v  = U.fromList [1..10 :: Int]
U.sum (U.map (*2) v)             -- fused: no intermediate vector allocated
v U.! 3                          -- unchecked-ish: throws on out of range
v U.!? 3                         -- Maybe
U.slice 2 5 v                    -- O(1), shares memory
U.generate n f
U.foldl' , U.zipWith, U.enumFromN
```

- **Unboxed** (`Data.Vector.Unboxed`) — contiguous raw values, no pointers.
  Requires an `Unbox` instance (`Int`, `Double`, `Bool`, tuples of those;
  `vector-th-unbox`/`Generic` deriving for your own). Fastest for numerics.
- **Storable** — same, but `Storable`-based and pinned, so the buffer can be
  handed to C (`unsafeWith`).
- **Boxed** — holds pointers to thunks; can contain any type, including lazy
  values and functions.

**Stream fusion** eliminates intermediates in `map`/`filter`/`fold` pipelines —
but it breaks when a vector is used twice, stored in a data structure, or passed
across a non-inlined function boundary. Check with `-ddump-simpl` if it matters.

In-place work goes through the mutable API in `ST` or `IO`:

```haskell
sortInPlace :: U.Vector Int -> U.Vector Int
sortInPlace v = runST $ do
  mv <- U.thaw v
  VAI.sort mv                        -- vector-algorithms
  U.unsafeFreeze mv
```

`freeze`/`thaw` copy; `unsafeFreeze`/`unsafeThaw` don't — safe only when you
provably never touch the other view again.

## 6. `array` and `massiv`

`Data.Array` is the Haskell 2010 array: `Ix`-indexed, immutable, and mostly
superseded by `vector` for 1-D work. It still shines for **multi-dimensional
indexing** and for lazy-array dynamic programming, where an element's definition
refers to other elements of the same array:

```haskell
fibs = listArray (0, n) [f i | i <- [0..n]]
  where f 0 = 0; f 1 = 1; f i = fibs!(i-1) + fibs!(i-2)   -- knot-tying memoization
```

`STUArray`/`IOUArray` are the unboxed mutable versions. For serious
multi-dimensional numeric work with parallelism, use **`massiv`** (delayed and
manifest representations, stencils, parallel folds); `repa` is its older,
less-maintained ancestor.

## 7. Lists are control flow, not storage

A list is a lazy stream. Used as such — generate, transform, consume once — it
fuses and costs almost nothing. Used as storage (repeated `!!`, `length`, `nub`,
`++` in a loop) it's the wrong data structure.

Quadratic list patterns to recognize:

```haskell
foldl (++) []  xs        -- O(n²)   → concat, or a Builder/DList
xs ++ [x]                -- O(n) per append, O(n²) in a loop  → Seq, or reverse-accumulate
nub xs                   -- O(n²)   → Set-based nubOrd (containers ≥ 0.6.7 / extra)
xs !! i    in a loop     -- O(n·i)  → Vector or Map
length xs > 0            -- forces the spine → null xs
```

`Data.List.NonEmpty` removes the `head`/`maximum` partiality when a list truly
can't be empty. `dlist` gives O(1) append for building.

## Gotchas

- **`Data.Map` unqualified is the LAZY map.** Import `Data.Map.Strict`.
- **`fromListWith`/`insertWith` pass `f new old`** — argument order reversed
  from intuition, which quietly reverses grouped lists.
- **`HashMap.size` is O(n)**, unlike `Map.size`.
- **`HashMap` iteration order is unspecified and varies with insertion order** —
  never serialize it without sorting, or your golden tests will flap.
- **`Data.Map` with an `Ord` inconsistent with `Eq` corrupts silently.**
- **`unsafeFreeze` after further mutation is undefined behaviour**, and the
  bug shows up as impossible values much later.
- **Vector fusion breaks silently.** A "fused" pipeline that got stored in a
  record allocates every intermediate.
- **`V.head`/`V.!` are partial**; `!?` isn't.
- **Boxed vectors of `Int` are ~3× the memory of unboxed** and defeat the point.
- **`Seq.length` is O(1) but `Seq.index` is O(log n)** — it's not a random-access
  array.
- **`Data.Array`'s bounds are part of the type's value, not the type** — a
  mismatch throws at runtime.
