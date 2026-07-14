---
topic_id: "v2:ONFI"
topic_path: "rust-arkit"
semantic_id: "6K6eidp7xYzKH1lKcrNPSoG-w1-qQAAL"
related_ids:
  - "qa6OAejZ3Y0aXWFDAqPF4Aluh11YUAAC"
  - "veyIgWj73Y3IGMlAYDPN4p3P9g8UUAAM"
---
# Value semantics & ARC — struct vs class, COW, cycles, ownership

Sources: The Swift Programming Language — Structures and Classes, Automatic Reference Counting,
and Memory Safety chapters (https://docs.swift.org/swift-book/, raw markdown at
https://github.com/swiftlang/swift-book/tree/main/TSPL.docc/LanguageGuide ); noncopyable types &
`consuming`/`borrowing` from swift-evolution
(https://github.com/swiftlang/swift-evolution). Fetched June 2026.

## Value vs reference — pick the default right

- **`struct`/`enum` are value types** — copied on assignment/passing; each holder has its own copy;
  no shared mutable state, no ARC. **Default to a struct.**
- **`class` is a reference type** — assignment shares one instance; mutation is visible through every
  reference; lifetime managed by ARC. Reach for a class only when you genuinely need **shared
  identity / shared mutable state**, reference semantics (e.g. a controller, a cache), `deinit`, or
  Obj-C interop.
- Value semantics is what makes Swift concurrency tractable: a `struct` of `Sendable` parts is
  trivially `Sendable` (see [[concurrency-data-race-safety]]); a shared class is where the data
  races live.

## Copy-on-write (COW) for your own value types

- Stdlib collections (`Array`, `Dictionary`, `String`) are value types backed by a reference to
  storage, copied **only on mutation** — so passing an array around is cheap; it duplicates only
  when you write to a second copy. You get value semantics at reference-copy cost.
- To give a large value type the same behavior, wrap the storage in a class and branch on
  `isKnownUniquelyReferenced(&storage)` before mutating — copy the buffer only when it's shared.
  Don't reach for this until a profiler says the copies hurt.

## ARC — applies to classes only

- ARC tracks **strong references** to each class instance; the instance lives while ≥1 strong
  reference exists and is deallocated (running `deinit`) the moment the count hits zero. Structs and
  enums are not reference-counted.

## Reference cycles — `weak` vs `unowned`

A **strong reference cycle** is two instances (or an instance and a closure) holding strong
references to each other — neither's count reaches zero, so both leak. Break it with a non-strong
reference on one side:

- **`weak`** — for a reference whose target may outlive-be-outlived independently / can become nil.
  Must be an **optional `var`**; ARC **auto-nils it on deallocation**. Use when the other instance has
  a **shorter or independent lifetime** (the classic "delegate" and parent↔child back-edges).
- **`unowned`** — for a reference whose target is assumed to **always be valid** (same-or-longer
  lifetime). **Non-optional**, no nil-ing — and **accessing it after the target deallocates is a
  runtime crash.** Use only when you can guarantee the target outlives this reference (e.g. a child
  that never outlives its parent).
- **Wrong default:** `unowned` for "I don't want the optional" is how you get use-after-free crashes.
  When unsure, `weak` is the safe choice.

## Closure capture lists

Closures are reference types and **capture `self` strongly by default** — a stored closure that
references `self` while `self` retains the closure is a cycle. Break it with a capture list:

- `[weak self]` — when the closure **may outlive** `self` (escaping, async, stored for later); `self`
  is optional inside — `guard let self else { return }`.
- `[unowned self]` — only when the closure and `self` share a lifetime and the closure **cannot**
  outlive it. Same crash risk as any `unowned`.

## Ownership: `~Copyable`, `consuming` / `borrowing` (when you need it)

- A **noncopyable type** (`struct Foo: ~Copyable`) can't be implicitly copied — it has a unique
  owner, enabling move-only resources (file handles, unique buffers) with deterministic `deinit`.
- **`consuming`** parameters take ownership (the caller's binding is invalidated after the call);
  **`borrowing`** parameters access without taking ownership. These give precise, allocation-free
  resource handling — but they're a sharp tool; reach for them for performance-critical or
  resource-handle types, not everyday code.

**Bottom line:** struct by default; class for identity/shared state; `weak` to break cycles unless
you can prove a longer lifetime; `~Copyable`/`consuming` only when ownership precision earns its
keep.
