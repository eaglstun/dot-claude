---
topic_id: "v2:ODFB"
topic_path: "rust-arkit/swift-concurrency"
semantic_id: "iY2O46Lr0UJQXUhjSjv30pjNAk6VUAAP"
related_ids:
  - "veyIgWj73Y3IGMlAYDPN4p3P9g8UUAAM"
  - "qa6OAejZ3Y0aXWFDAqPF4Aluh11YUAAC"
---
# Swift 6 strict concurrency — error catalogue & fixes

Sources: Swift 6 migration guide — https://www.swift.org/migration/ and
https://github.com/apple/swift-migration-guide (Guide.docc/CommonProblems.md), fetched June 2026.
Swift 6 language mode enforces **complete data-race safety at compile time** (region-based isolation,
SE-0414). This is the catalogue of the errors that produces and the _correct_ fix for each — reach
for isolation or real `Sendable`, treat `@unchecked`/`nonisolated(unsafe)` as a last resort that
moves the proof burden onto you.

> Migrate incrementally: enable warnings in Swift 5 mode with
> `-strict-concurrency=complete` (or `swiftLanguageModes`/`StrictConcurrency` in the manifest),
> clear them, then flip to the Swift 6 language mode per-target. `@preconcurrency import` downgrades
> diagnostics from modules not yet audited.

## 1. Unsafe global / static mutable state

`error: global variable 'x' is not concurrency-safe because it is non-isolated global shared mutable state`

- Make it a `let` (immutable shared state is `Sendable`-safe).
- Isolate it to a global actor: `@MainActor static var …`.
- `nonisolated(unsafe)` **only** when you protect it yourself (lock/serial queue) — you're now
  asserting safety the compiler can't check.

## 2. Non-Sendable value crossing an isolation boundary

`error: sending 'x' risks causing data races`

- Remove the boundary: if the caller can be `@MainActor`, the value never crosses.
- Pass a `@Sendable` closure that _computes_ the value in the destination instead of shipping the
  instance.
- Mark the parameter `sending` to let a provably-disconnected value cross (region-based isolation).
- Or make the type `Sendable` (below).

## 3. Making a type `Sendable` (in order of preference)

- **Value type, all-Sendable stored properties:** add explicit `: Sendable` (public types don't get
  it inferred). `public struct ColorComponents: Sendable { … }`.
- **Global-actor isolation:** `@MainActor struct/class …` — isolated, therefore safe to share.
- **Actor:** wrap mutable state in an `actor`.
- **Checked class conformance:** `final class Style: Sendable` with no non-Sendable mutable stored
  properties and no non-NSObject superclass.
- **`@unchecked Sendable`:** class with manual synchronization (a private queue/lock). You own the
  proof. Use sparingly and comment the synchronization invariant.
- **External type you don't own:** `extension Foo: @retroactive @unchecked Sendable {}` — extreme
  caution; only if the type's real semantics match `Sendable`.

## 4. Protocol conformance isolation mismatch

`error: main actor-isolated instance method 'm()' cannot be used to satisfy nonisolated protocol requirement`

- Isolate the protocol (or the specific requirement) to `@MainActor`.
- Make the requirement `async`, letting conformers choose their isolation.
- Implement the method `nonisolated` if it touches no isolated state.
- `@preconcurrency` on the conformance for staged adoption (adds runtime checks).

## 5. Isolated default value / initializer in a nonisolated context

`error: main actor-isolated default value in a nonisolated context`

- Mark `init` (or the default expression) `nonisolated` if it touches no isolated state.
- Initialize the isolated property lazily or inside the isolated context.

## 6. `deinit` (always nonisolated) calling isolated members

`error: call to actor-isolated instance method in a synchronous nonisolated context`

- Hop off in an unstructured `Task`, **capturing the stored value, not `self`** (never extend
  `self`'s lifetime from `deinit`):
  ```swift
  deinit { Task { [store] in await store.stopNotifications() } }
  ```

## Swift 6.2 — "approachable concurrency" (changes the defaults)

Source: https://www.swift.org/blog/swift-6.2-released/ . Much of the friction above is softened in
6.2; check which mode a target is in before reasoning:

- **Main-actor-by-default mode** (`-default-isolation MainActor`): code runs on the main actor
  without explicit `@MainActor` — aimed at scripts, UI, and executable targets. Far fewer boundary
  errors in app/UI code.
- **Caller-context async:** `async` functions run in the caller's execution context rather than
  always hopping to the global pool, removing a class of forced thread-switch data-race errors.
- **`@concurrent`:** explicitly opts a function into running on the thread pool rather than the
  caller's actor — the inverse knob, used to _say_ "this is meant to be concurrent."
