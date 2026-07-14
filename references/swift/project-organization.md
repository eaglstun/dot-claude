---
topic_id: "v2:OODG"
topic_path: "rust-arkit/swift-expert"
semantic_id: "Oa2KCqjN5P1pEuIQBzXJCqBn0Ea2EAAH"
related_ids:
  - "veyIgWj73Y3IGMlAYDPN4p3P9g8UUAAM"
  - "OKyLAfxtjUQYX3FQSLr1gKlPSN9UQAAB"
---
# Organizing complex Swift projects

Sources: Swift Package Manager docs — https://www.swift.org/documentation/package-manager/ ;
access control — https://docs.swift.org/swift-book/documentation/the-swift-programming-language/accesscontrol/
(fetched June 2026). SPM mechanics and the module access-control model are factual; the layering
guidance below is established community practice, flagged as such.

## The unit of organization is the module

- **A module is the access-control and namespacing boundary.** `internal` (the default) is visible
  within a module; `public` exposes across modules; `package` (Swift 5.9+) exposes within the same
  _package_ but not to clients; `private`/`fileprivate` scope below the module. Splitting code into
  modules is how you enforce architecture — the compiler stops layer violations that a folder
  convention only suggests.
- **In SPM, one target == one module.** Structure lives in `Package.swift`: `targets` (each a
  module), `products` (libraries/executables you vend), and `dependencies` (other packages). Test
  targets depend on the targets they exercise.
- **Smaller modules = faster incremental builds and parallelism**, plus they force you to declare
  the seams. The cost is `public` boilerplate at boundaries — don't over-split a small app into
  twenty micro-modules.

## A typical multi-module shape

```
MyApp/
  Package.swift
  Sources/
    AppCore/        # domain models + business logic — no UIKit/SwiftUI
    Networking/     # API client; depends on nothing app-specific
    Persistence/    # storage; depends on AppCore
    Features/
      FeatureA/     # one feature module; depends on AppCore + the services it needs
      FeatureB/
    AppUI/          # shared design-system / components
  Tests/
    AppCoreTests/ …
```

- **Dependencies point inward / downward.** Feature modules depend on core + services; core depends
  on nothing app-specific. Keep the graph acyclic — SPM forbids cycles between targets anyway.
- **Keep frameworks out of the core.** Domain logic that imports no UI framework is testable,
  portable (server-side, CLI), and cheap to compile.
- **A feature module per feature** scales teams: clear ownership, isolated build, and the public
  surface of a feature is an explicit, reviewable thing.

## When to split a _package_ (not just a target)

- The code is reused across **multiple apps/repos** (extract to its own versioned package).
- It has a **genuinely independent release cadence** or external consumers.
- Otherwise prefer **multiple targets in one package** — far less version-pinning overhead, and you
  still get module boundaries. Don't reach for a separate repo to get a module.

## Conventions that age well

- **`package` access** for cross-module-but-internal API instead of `public` — keeps it out of the
  client-facing surface.
- **`@testable import`** to reach `internal` symbols from tests without widening them to `public`.
- **Resources** belong to the target that owns them (`.target(resources:)` + `Bundle.module`).
- **Plugins** (build-tool / command, Swift 5.6+) for codegen and lint steps, wired in the manifest.
- **Traits** (Swift 6.1+) for compile-time feature flags / optional dependencies across a package's
  consumers — `swift package show-traits` lists them (6.3+).
- Let the **toolchain be the arbiter:** if a dependency edge surprises you, `swift package
show-dependencies` and the build graph are ground truth, not the folder names.
