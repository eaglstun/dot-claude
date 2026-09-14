---
semantic_id: "54YZRjprxjj2Os7WrXXbJvU7lRBIMAAB"
related_ids:
  - "p4IZT-p7nzr3Ps4E6FDbYv0b5RJQIAAN"
  - "IYIbQC-jij63usyGrWlLKvU7pdhIYAAI"
---
# Memory, smart pointers, and allocation

Source:

- https://en.cppreference.com/w/cpp/memory/unique_ptr
- https://en.cppreference.com/w/cpp/memory/shared_ptr
- https://en.cppreference.com/w/cpp/memory/weak_ptr
- https://en.cppreference.com/w/cpp/memory/new/operator_new
- https://en.cppreference.com/w/cpp/memory/memory_resource (PMR)
- https://en.cppreference.com/w/cpp/language/object (object model, `start_lifetime_as`)
- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-resource

## 1. Ownership decision table

| Situation                                     | Use                                                           |
| --------------------------------------------- | ------------------------------------------------------------- |
| Value fits and lifetime is scoped             | a plain value member — no pointer at all                      |
| Single owner, heap-allocated                  | `std::unique_ptr<T>`                                          |
| Single owner, array                           | `std::vector<T>` (not `unique_ptr<T[]>`)                      |
| Shared ownership, genuinely unclear last user | `std::shared_ptr<T>`                                          |
| Observe without owning, may outlive           | `std::weak_ptr<T>`                                            |
| Observe without owning, guaranteed alive      | `T*` or `T&` (raw = non-owning, by convention)                |
| Optional non-owning reference                 | `T*` (nullable) or `std::optional<std::reference_wrapper<T>>` |
| Contiguous view                               | `std::span<T>`                                                |

**Raw pointers are fine** — as _observers_. The rule is that a raw pointer never
owns. `new` and `delete` should not appear in application code at all;
`make_unique` / `make_shared` / containers cover it.

## 2. `unique_ptr`

Zero-overhead (same size as `T*` with a stateless deleter), move-only.

```cpp
auto w = std::make_unique<Widget>(arg1, arg2);
std::unique_ptr<Widget> moved = std::move(w);      // w is now null, guaranteed
Widget* observer = moved.get();                     // non-owning peek
Widget* released = moved.release();                 // you now own it; you must delete
moved.reset(new Widget{});                          // deletes old, adopts new
```

Custom deleters, the reason it wraps every C API cleanly:

```cpp
struct FileCloser { void operator()(std::FILE* f) const noexcept { std::fclose(f); } };
using FilePtr = std::unique_ptr<std::FILE, FileCloser>;
FilePtr f{std::fopen(path, "rb")};

// stateless functor keeps sizeof == sizeof(void*); a lambda or function pointer costs extra
using Freeing = std::unique_ptr<void, decltype([](void* p){ std::free(p); })>;   // C++20
```

`unique_ptr<T[]>` exists and calls `delete[]`, but `std::vector` is almost always
better. It is the right choice only for a fixed-size buffer you never resize.

**PIMPL**: a `unique_ptr<Impl>` member requires the enclosing class's destructor
to be _declared_ in the header and _defined_ in the .cpp where `Impl` is
complete, otherwise the implicit destructor instantiates `delete` on an
incomplete type.

## 3. `shared_ptr` and `weak_ptr`

`shared_ptr` is **two pointers wide** and does atomic refcount traffic on every
copy. It is not a default; it is what you reach for when ownership is genuinely
shared.

```cpp
auto s = std::make_shared<Widget>(args);   // ONE allocation: control block + object together
std::weak_ptr<Widget> w = s;
if (auto locked = w.lock()) { locked->use(); }   // null if the object died
```

`make_shared` fuses the control block and object into one allocation (faster,
better locality) but keeps the _whole_ block alive as long as any `weak_ptr`
lives. For huge objects with long-lived weak refs, `shared_ptr<T>(new T)` is
actually preferable.

Two hazards:

**Cycles leak.** `A` holds `shared_ptr<B>`, `B` holds `shared_ptr<A>` → neither
count reaches zero. Break with `weak_ptr` on the back-edge (parent→child owns,
child→parent weak).

**Double control blocks.** Constructing two `shared_ptr`s from the same raw
pointer creates two independent counts and a double free:

```cpp
Widget* raw = new Widget;
std::shared_ptr<Widget> a{raw};
std::shared_ptr<Widget> b{raw};      // BOOM, eventually
```

If an object must hand out `shared_ptr`s to itself, derive from
`std::enable_shared_from_this<Widget>` and call `shared_from_this()` (only valid
once a `shared_ptr` already owns it — C++17 made calling it before that
well-defined to throw `bad_weak_ptr`).

Thread safety: the **control block** is atomic, the **pointee is not**, and the
`shared_ptr` _object itself_ is not — two threads writing the same `shared_ptr`
variable need `std::atomic<std::shared_ptr<T>>` (C++20).

`std::shared_ptr<T[]>` (C++17) and aliasing constructors
(`shared_ptr<Member>(owner_sp, &owner_sp->member)`) exist; the aliasing form is
how you hand out a pointer to a subobject that keeps the parent alive.

## 4. `new`, `delete`, and alignment

If you must:

```cpp
T* p        = new T{args};
T* arr      = new T[n];
T* aligned  = new (std::align_val_t{64}) T{};    // C++17 over-aligned new
T* at       = new (buffer) T{};                   // placement new: construct in existing storage
at->~T();                                          // placement new needs an explicit destructor call
delete p; delete[] arr;
```

`operator new` throws `std::bad_alloc`; `new (std::nothrow) T` returns null
instead. Class-level `operator new`/`operator delete` overloads let you pool a
type; a sized `operator delete(void*, size_t)` is the modern signature.

Alignment: `alignas(64) struct Batch {...};` and `alignof(T)`. Types with
extended alignment go through the aligned `operator new` overloads
automatically since C++17 — before that, `std::vector<alignas(32) T>` silently
under-aligned and crashed AVX loads.

## 5. Polymorphic memory resources (PMR)

`<memory_resource>` gives runtime-polymorphic allocators without infecting the
container's type:

```cpp
std::byte buffer[64 * 1024];
std::pmr::monotonic_buffer_resource pool{buffer, sizeof buffer};
std::pmr::vector<std::pmr::string> v{&pool};      // all allocation lands in `buffer`
v.emplace_back("no heap traffic at all");
```

Standard resources: `monotonic_buffer_resource` (bump allocator, frees only at
destruction — ideal for per-frame/per-request arenas),
`unsynchronized_pool_resource` / `synchronized_pool_resource` (size-class pools),
`new_delete_resource()`, `null_memory_resource()` (assert on allocation).

`std::pmr::vector<T>` is a distinct type from `std::vector<T>`; the allocator is
carried as a value, so it propagates to elements that are themselves PMR types.

## 6. The object model, briefly

- Storage ≠ object. Allocating bytes does not create an object; the constructor
  (or `std::start_lifetime_as<T>` / `std::bit_cast`) does.
- **Type punning via `reinterpret_cast` is UB** (strict aliasing). Use
  `std::bit_cast<To>(from)` (C++20, requires same size + trivially copyable) or
  `std::memcpy` — both compile to zero instructions at `-O2`.
- `std::launder` exists for the rare case of reusing storage that held a
  const/reference member; if you think you need it, you probably want a plain
  `optional` or a fresh object instead.
- `char`, `unsigned char`, and `std::byte` may alias anything. Nothing else may.

## Gotchas

- `std::shared_ptr` as a default parameter type is a design smell — it usually
  means "I did not decide who owns this". Decide.
- Reference-count churn is real: pass `const shared_ptr<T>&` (or better, `T&`)
  down a call chain instead of copying the `shared_ptr` at each level.
- `make_unique`/`make_shared` cannot use brace-init for aggregates before C++20
  (`make_unique<Point>(1,2)` fails when `Point` has no constructor); C++20 fixed
  aggregate paren-init.
- A `unique_ptr` member makes the class move-only. That is usually correct, but
  it silently deletes copy — the resulting error appears at the _use_ site.
- `delete` on a pointer to a base without a virtual destructor is UB.
- Mixing `new[]`/`delete` or `new`/`delete[]` is UB with no diagnostic.
- `weak_ptr::expired()` followed by `lock()` is a race; just call `lock()` and
  test the result.
- `std::shared_ptr<void>` erases the type but still calls the correct destructor
  (the deleter was captured at construction) — a legitimate and surprising trick.
- PMR: dangling resource. The `monotonic_buffer_resource` must outlive every
  container that points at it; declaring the vector first is a classic
  destruction-order bug.
