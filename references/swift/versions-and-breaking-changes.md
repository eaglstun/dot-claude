---
topic_id: "v2:ODLL"
topic_path: "rust-arkit/swift-concurrency"
semantic_id: "veyIgWj73Y3IGMlAYDPN4p3P9g8UUAAM"
related_ids:
  - "qa6OAejZ3Y0aXWFDAqPF4Aluh11YUAAC"
  - "6K6eidp7xYzKH1lKcrNPSoG-w1-qQAAL"
---
# Swift versions & breaking changes

Sources: Swift changelog — https://github.com/swiftlang/swift/blob/main/CHANGELOG.md ; release
blogs — https://www.swift.org/blog/ ; swift-evolution — https://github.com/swiftlang/swift-evolution
(fetched June 2026). **The changelog is the authority — fetch it for the exhaustive per-version
list and exact SE-proposal numbers; this is the orientation map, kept deliberately light on
proposal numbers to avoid drift.**

> **Current as of June 2026:** Swift **6.3** is the current stable release; Swift **6.4** has been
> announced. Anything below 6.3 here is historical context. Re-pull before quoting specifics.

## The throughline: the concurrency rollout

The single biggest multi-version story. Track _which language mode and Swift version a target uses_
before reasoning about any concurrency diagnostic.

- **5.5** — async/await, `actor`, global actors (`@MainActor`), structured concurrency,
  `@TaskLocal`. The foundation.
- **5.6** — `any` keyword introduced for existentials; `@preconcurrency`; opt-in `Sendable`
  checking begins (warnings).
- **5.7** — `some` in parameter position; primary associated types (`any Collection<String>`);
  opening existentials into generics.
- **5.10** — global/static mutable state must be isolated or immutable `Sendable`;
  `nonisolated(unsafe)` escape hatch added. Closes the remaining strict-concurrency holes.
- **6.0** — **Swift 6 language mode: complete data-race safety on by default.** Region-based
  isolation + `sending` (SE-0414/0430). Also: **typed throws** (`throws(E)`), **noncopyable types**
  (`~Copyable`, `consuming`/`borrowing`), distributed-actor improvements. Opt in per-target; 5.x
  modes still compile.
- **6.2** — **approachable concurrency**, which _changes defaults_ (see below).

## Swift 6.2 — approachable concurrency (default-behavior changes)

Source: https://www.swift.org/blog/swift-6.2-released/

- **Main-actor-by-default mode** (`-default-isolation MainActor`): run on the main actor without
  explicit `@MainActor` — for scripts, UI, executables. Removes a lot of boilerplate and boundary
  errors in app code.
- **Caller-context `async`:** async functions run in the caller's execution context instead of
  always hopping to the global pool — kills a class of forced thread-switch errors.
- **`@concurrent`:** explicitly marks a function meant to run on the thread pool (the inverse knob).
- **`InlineArray`** (fixed-size, stack-allocated; `[40 of Sprite]` shorthand) and **`Span`**
  (memory-safe pointer alternative). Embedded Swift gains full `String`, `any`-constrained protocols.
- Tooling: officially-verified VS Code extension; per-category warning control
  (`treatWarning()`/`treatAllWarnings()` in the manifest); prebuilt swift-syntax for faster macro CI.

## Swift 6.3 — current stable

Source: https://www.swift.org/blog/swift-6.3-released/

- **`@c` attribute:** export Swift functions/enums to C with generated headers (pairs with
  `@implementation`).
- **Module selectors:** `ModuleA::getValue()` disambiguates same-named APIs across modules; also
  `Swift::Task` to reach stdlib concurrency.
- **Performance control:** `@specialize`, `@inline(always)`, `@export(implementation)`.
- **Tooling:** preview of **Swift Build** integrated into SwiftPM (unified cross-platform build
  engine); prebuilt swift-syntax for shared macro libraries; `swift package show-traits`; DocC
  experimental Markdown output + code-block annotations. Official **Android** Swift SDK; Embedded
  Swift improvements.

## Recurring breaking-change shapes (watch for these on upgrade)

- **Concurrency tightening** each version: state that compiled as a warning becomes an error in a
  later mode. Migrate warnings-clean _before_ flipping the language mode.
- **Stricter existential / opaque-type checks** (5.6→5.7 era): code relying on implicit existentials
  now wants `any`.
- **Default-value / global-isolation expressions** flagged then errored across 5.6→5.10→6.0.
- General rule: **bump the language mode deliberately, per-target, and let the compiler enumerate the
  breaks** — don't assume; build it. (This is the same "compiler over memory" discipline the agent
  applies everywhere else.)
