---
topic_id: "v2:OFJC"
topic_path: "rust-arkit"
semantic_id: "qa6OAejZ3Y0aXWFDAqPF4Aluh11YUAAC"
related_ids:
  - "veyIgWj73Y3IGMlAYDPN4p3P9g8UUAAM"
  - "OKyLAfxtjUQYX3FQSLr1gKlPSN9UQAAB"
---
# Swift language references — best-practice digests

Curated, source-cited digests of authoritative Swift guidance for the **`swift-expert`** agent —
idioms, project organization, concurrency/data-race safety, and current-version breaking changes.
Unlike this repo's other reference shelves, these are **not project-bound**: they're general Swift
knowledge that holds across any codebase (apps, packages, CLIs, server-side).

Each file cites its origin (swift.org doc, swift-evolution proposal, or release notes) at the top.
**Swift moves fast and the toolchain is the final authority** — these digests are grounded as of
their fetch date, but `swift-expert` should still confirm version-specific behavior against the
live changelog and the actual compiler (its whole ethos is "compiler over memory"). Re-pull when a
new major/minor ships.

> Captured June 2026, against Swift 6.3 (current stable) / 6.4 (announced). Re-verify before
> relying on any version-specific claim.

## Index

- **api-design-guidelines.md** — the official Swift API Design Guidelines, condensed: clarity at
  the point of use, naming, fluent usage, argument labels, conventions. The canonical idioms source.
- **project-organization.md** — structuring complex Swift projects: SPM multi-module layout, the
  module-as-access-control-boundary, target/dependency graphs, layering, and when to split packages.
- **concurrency-data-race-safety.md** — the Swift 6 strict-concurrency error catalogue and the
  _correct_ fix for each (isolation, `Sendable`, `sending`, `@MainActor`) — not `@unchecked` papering.
- **versions-and-breaking-changes.md** — current releases and the source-breaking / default-behavior
  changes across the 5.5 → 6.x line (concurrency rollout, `any`/`some`, macros, typed throws,
  `~Copyable`, 6.2 approachable concurrency, 6.3 tooling). Points at the live changelog for specifics.
- **generics-and-protocols.md** — `some` vs `any` vs generic parameters, opaque types, existential
  boxing & its limits, primary associated types / PATs, and a choose-the-right-tool table.
- **value-semantics-and-arc.md** — struct vs class defaults, copy-on-write, ARC, breaking reference
  cycles (`weak` vs `unowned`, closure capture lists), and ownership (`~Copyable`/`consuming`).

## Sources these draw from (re-fetch for specifics)

- API Design Guidelines — https://www.swift.org/documentation/api-design-guidelines/
- Swift 6 migration guide — https://www.swift.org/migration/ · https://github.com/apple/swift-migration-guide
- Swift Package Manager docs — https://www.swift.org/documentation/package-manager/
- Swift changelog — https://github.com/swiftlang/swift/blob/main/CHANGELOG.md
- swift-evolution — https://github.com/swiftlang/swift-evolution
- Release blogs — https://www.swift.org/blog/
