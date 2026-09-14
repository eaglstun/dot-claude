---
name: swift
description: Swift language and SwiftPM reference for apps, packages, CLIs, and servers. Use when writing, reviewing, refactoring, or debugging Swift, especially API design, ownership and ARC, generics and protocols, Swift 6 concurrency, package organization, and version migrations.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: qKwUAaJ7hcVaHhBKQhPDCgCPy0ewUAAI
  related_ids: '["6K6eidp7xYzKH1lKcrNPSoG-w1-qQAAL","SKwWgOlR5YVaNQBMLpFHEilw61UkcAAA"]'
---

# Swift reference

Condensed, source-cited notes grounded in the primary sources (the API Design
Guidelines, The Swift Programming Language, the Swift 6 migration guide,
swift-evolution, the changelog, and the release blogs). Each page cites its
origin URLs and fetch date at the top.

This is a standalone language shelf, not tied to one repo — it holds across
apps, packages, CLIs, and server-side Swift. Repo conventions (a project
CLAUDE.md, an existing module layout) override anything here.

**Swift moves fast and the toolchain is the final authority.** These digests are
grounded as of their fetch date; confirm any version-specific claim against the
live changelog and the actual compiler before leaning on it. Captured June 2026
against Swift 6.3 (current stable) / 6.4 (announced).

Written and consulted by the **`swift-expert`** agent.

## References - load on demand

Detail lives in `references/`. One pointer per page:

### Language

- **[api-design-guidelines.md](references/api-design-guidelines.md)**
  - the official API Design Guidelines condensed: clarity at the point of use,
    naming, fluent usage, argument labels, conventions. _Read when naming
    anything public, or when a call site reads badly._

- **[value-semantics-and-arc.md](references/value-semantics-and-arc.md)**
  - struct vs class defaults, copy-on-write for your own types, ARC, breaking
    cycles (`weak` vs `unowned`, capture lists), ownership (`~Copyable`,
    `consuming`/`borrowing`). _Read on a leak, a retain cycle, or a "should this
    be a class" question._

- **[generics-and-protocols.md](references/generics-and-protocols.md)**
  - `some` vs `any` vs a generic parameter, opaque types, existential boxing and
    its limits, PATs and primary associated types, a choose-the-right-tool table.
    _Read when the abstraction won't type-check or an existential is losing its
    associated types._

- **[concurrency-data-race-safety.md](references/concurrency-data-race-safety.md)**
  - the Swift 6 strict-concurrency error catalogue and the _correct_ fix for each
    (isolation, real `Sendable`, `sending`, `@MainActor`) — not `@unchecked`
    papering — plus the 6.2 approachable-concurrency default changes. _Read on any
    Sendable / isolation / actor-boundary diagnostic._

### Project and practice

- **[project-organization.md](references/project-organization.md)**
  - SPM multi-module layout, the module as access-control boundary (`internal`,
    `package`, `public`), target/dependency graphs, layering, when to split a
    package. _Read when structuring a project or deciding where a type belongs._

- **[versions-and-breaking-changes.md](references/versions-and-breaking-changes.md)**
  - the 5.5 → 6.x line: the concurrency rollout, `any`/`some`, macros, typed
    throws, `~Copyable`, 6.2 approachable concurrency, 6.3 tooling, and the
    recurring breaking-change shapes. _Read before an upgrade, or when a snippet
    from the web won't compile._

## Sources these draw from (re-fetch for specifics)

Each page cites its own subset at the top. The full set:

- API Design Guidelines — https://www.swift.org/documentation/api-design-guidelines/
- The Swift Programming Language — https://docs.swift.org/swift-book/
  (raw markdown: https://github.com/swiftlang/swift-book/tree/main/TSPL.docc/LanguageGuide)
- Swift 6 migration guide — https://www.swift.org/migration/ ·
  https://github.com/apple/swift-migration-guide
- Swift Package Manager docs — https://www.swift.org/documentation/package-manager/
- Swift changelog — https://github.com/swiftlang/swift/blob/main/CHANGELOG.md
- swift-evolution — https://github.com/swiftlang/swift-evolution
- Release blogs — https://www.swift.org/blog/

## Conventions for this shelf

- Each page starts with its source URL(s) and fetch date, and stays light on
  SE-proposal numbers where the changelog is the better authority — drift is the
  enemy here.
- Keep SKILL.md lean: two-line pointers only. Detail lives on the shelf.
- To add a topic: write `references/<topic>.md` in the same format (Sources block
  up top), then add a two-line pointer above. This file is the only index — there
  is deliberately no second one to keep in sync.
- Re-pull when a new major/minor ships; prefer un-versioned swift.org URLs so
  links survive releases.
