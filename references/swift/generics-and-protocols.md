---
topic_id: "v2:OPPA"
topic_path: "rust-arkit"
semantic_id: "SKwWgOlR5YVaNQBMLpFHEilw61UkcAAA"
related_ids:
  - "6K6eidp7xYzKH1lKcrNPSoG-w1-qQAAL"
  - "qa6OAejZ3Y0aXWFDAqPF4Aluh11YUAAC"
---
# Generics & protocols — `some` vs `any`, PATs, existentials

Sources: The Swift Programming Language — Generics, Opaque & Boxed Protocol Types, and Protocols
chapters (https://docs.swift.org/swift-book/, raw markdown at
https://github.com/swiftlang/swift-book/tree/main/TSPL.docc/LanguageGuide ); the `some`/`any`/
primary-associated-type story is from swift-evolution (https://github.com/swiftlang/swift-evolution).
Fetched June 2026. Decide the abstraction tool deliberately — the wrong one boxes, loses
associated types, or over-constrains.

## The three ways to abstract over a protocol

- **Generic parameter `<T: P>`** — _the caller_ picks one concrete type; monomorphized, no boxing,
  full type identity. The default for "works for any conforming type, chosen at the call site."
- **Opaque type `some P`** — _the implementation_ picks one concrete type and hides it; "the reverse
  of a generic." One underlying type, identity preserved, no box. Use for return values that should
  stay abstract without losing what the type can do.
- **Boxed / existential `any P`** — a box that can hold _different_ conforming types over time;
  identity not known until runtime. Heterogeneous storage at the cost of indirection and lost
  associated-type access.

## `some P` (opaque)

- Guarantees **one specific underlying type**, known to the compiler, hidden from the caller. All
  return paths of a `-> some P` function must return the **same** concrete type (returning `T` on
  one branch and `FlippedShape<T>` on another is an error).
- **Preserves type identity** → type-dependent operations still work (`==`, feeding the result back
  into a function that needs the concrete type, nesting `f(f(x))`).
- **The only option for returning a protocol with associated types** (you can't return `any
Collection` and keep `Element`; `some Collection<Int>` works).
- **`some P` in _parameter_ position is just sugar for a generic** — each `some P` parameter is an
  independent unnamed generic constraint. `func g(_ a: some P, _ b: some P)` lets `a` and `b` be
  _different_ types; a named `<T: P>(_ a: T, _ b: T)` forces them equal. Pick accordingly.

## `any P` (existential / boxed)

- Stores **any** conforming type; the value's concrete type "isn't known until runtime and can
  change." The only way to hold a **heterogeneous** collection: `var shapes: [any Shape]`.
- **Costs a box** — a level of indirection with a real (if usually small) performance cost.
- **Limitations:** can't access anything beyond the protocol's own requirements; type-dependent ops
  fail (no `==`); **"a value of `any P` does not itself conform to `P`,"** so you can't pass an
  `any P` where a `some P`/generic is expected, and nesting breaks; can't be the return type for a
  protocol with associated types.
- Reach for `any` **only when you genuinely need runtime heterogeneity**; otherwise a generic or
  `some` is cheaper and keeps more capability.

## Protocols with associated types (PATs) & primary associated types

- A protocol with an `associatedtype` (or `Self` requirements) constrains where it can be used as a
  type. Modern Swift lets you write `any P` for these, but with the box limitations above.
- **Primary associated types** let you constrain the associated type at the use site:
  `any Collection<String>`, `some Sequence<Int>` — far more useful than a bare `any Collection`,
  and the idiomatic way to expose a constrained existential/opaque.
- Use `where` clauses / conditional conformance (`extension Array: P where Element: P`) to add
  capability precisely instead of widening a protocol.

## Choosing — quick table

| Situation                                                    | Use                            |
| ------------------------------------------------------------ | ------------------------------ |
| Caller chooses the type; hot path, no boxing                 | generic `<T: P>`               |
| Return a value abstractly but keep identity/associated types | `some P`                       |
| One associated type, want it constrained at use site         | `some/any P<Element == …>`     |
| Store mixed conforming types together                        | `any P`                        |
| Need `==`, nesting, or "conforms to P"                       | `some P` / generic (not `any`) |

**Rule of thumb:** start with a generic; reach for `some` to _hide_ a return type without losing it;
reach for `any` only for true heterogeneity, knowing it boxes and drops associated-type access.
