---
topic_id: "v2:OONI"
topic_path: "rust-arkit/swift-expert"
semantic_id: "rayEIfrbgU1MWVgCGRvfOKFF7MwccAAF"
related_ids:
  - "veyIgWj73Y3IGMlAYDPN4p3P9g8UUAAM"
  - "OKyLAfxtjUQYX3FQSLr1gKlPSN9UQAAB"
---
# Swift API Design Guidelines — condensed

Source: https://www.swift.org/documentation/api-design-guidelines/ (Swift.org, fetched June 2026).
The canonical reference for naming and idiomatic API shape. Quote the live page for exact wording;
this is a faithful condensation for fast recall.

## Fundamentals

- **Clarity at the point of use is the goal.** APIs are declared once but _used_ many times — design
  for the reading of the call site, not the declaration.
- **Clarity is more important than brevity.** Swift's concision comes from strong typing and reduced
  boilerplate, not from terse names. Don't shorten at the cost of clarity.
- **Write a doc comment for every declaration.** If a simple description is hard to write, the API
  design itself may be wrong.

## Promote clear usage

- **Include all the words needed to avoid ambiguity.** `employees.remove(at: x)` (clear) beats
  `employees.remove(x)` (remove _by index_ or _by value_?).
- **Omit needless words.** Drop words that merely repeat type information already at the call site.
- **Name by role, not type.** `greeting` not `string`; `supplier` not `widgetFactory`.
- **Compensate for weak type information** (`Any`, `NSObject`, `Int`, `String`) by adding a noun
  describing the role: `addObserver(_:forKeyPath:)` not `add(_:for:)`.

## Strive for fluent usage

- **Method/function names should read as grammatical English phrases** at the use site:
  `x.insert(y, at: z)` reads "insert y at z".
- **Factory methods begin with `make`**: `x.makeIterator()`.
- **Initializer/factory first arguments do not form a phrase with the base name**:
  `Color(red: 32, green: 64, blue: 128)`, not `Color(havingRGBValuesRed: …)`.
- **Name by side effects:**
  - No side effects → noun phrase: `x.distance(to: y)`, `i.successor()`.
  - Side effects → imperative verb: `x.sort()`, `x.append(y)`, `print(x)`.
- **Mutating/nonmutating pairs:**
  - Verb-based: mutating is the imperative (`x.sort()`, `x.append(y)`); nonmutating adds
    `ed`/`ing` (`x.sorted()`, `x.appending(y)`).
  - Noun-based: nonmutating is the noun (`x.union(z)`); mutating prefixes `form` (`x.formUnion(z)`).
- **Booleans read as assertions:** `x.isEmpty`, `line1.intersects(line2)`.
- **Protocols:** "what it is" → noun (`Collection`); "what it can do" → `able`/`ible`/`ing`
  suffix (`Equatable`, `ProgressReporting`).

## Use terminology well

- Avoid obscure terms when a common word works; don't surprise an expert with a coined meaning.
- Avoid abbreviations that aren't trivially searchable.
- Embrace precedent: `Array` not `List`; `sin(x)` follows math convention over beginner-friendliness.

## Conventions

- **Document any computed property that isn't O(1).**
- **Prefer methods/properties to free functions**, except: no obvious `self`; an unconstrained
  generic; or established domain notation (`sin(x)`).
- **Case:** `UpperCamelCase` for types/protocols, `lowerCamelCase` for everything else. Treat
  acronyms uniformly by case: `utf8Bytes`, `isRepresentableAsASCII`.
- **Methods may share a base name** when they do essentially the same thing in different domains.
- **Never overload solely on return type.**

## Parameters & argument labels

- **Parameter names document the API** even when not visible at the call site — name them well.
- **Use default values** to cut down on overloads; put defaulted parameters toward the end.
- **Omit labels when arguments aren't usefully distinguished:** `min(x, y)`.
- **Value-preserving conversions omit the first label** (`Int64(someUInt32)`); narrowing conversions
  add a label (`init(truncating:)`, `init(saturating:)`).
- **First argument forms a prepositional phrase → label starts at the preposition:**
  `x.removeBoxes(havingLength: 12)`.
- **First argument forms part of a phrase with the base name → omit its label:** `x.addSubview(y)`;
  otherwise include it: `view.dismiss(animated: false)`. **Label all remaining arguments.**
- **For production APIs prefer `#fileID`** over `#file`/`#filePath` (smaller, privacy-preserving).
