---
semantic_id: "Tq17nc3n_9kI1eGSKGfEKSNndGROMAAN"
related_ids:
  - "TqVrn8zj_9lY3WGCOCfELQNnEWDGsAAO"
  - "bu9tAf1kt5uOXYOSEJ_GIAofVAb8UAAG"
---

# Foundation Models — guided generation and tool calling

Session, model, availability, context window, errors, and safety live in
`foundation-models.md`. This file is `@Generable` / `@Guide` / `Tool`.

Source (API reference + articles, fetched via Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation>
- <https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling>
- <https://developer.apple.com/documentation/foundationmodels/generable>
- <https://developer.apple.com/documentation/foundationmodels/generable(description:)>
- <https://developer.apple.com/documentation/foundationmodels/guide(description:)> and `guide(description:_:)`
- <https://developer.apple.com/documentation/foundationmodels/generationguide>
- <https://developer.apple.com/documentation/foundationmodels/generationschema>
- <https://developer.apple.com/documentation/foundationmodels/dynamicgenerationschema>
- <https://developer.apple.com/documentation/foundationmodels/generatedcontent>
- <https://developer.apple.com/documentation/foundationmodels/tool>
- <https://developer.apple.com/documentation/foundationmodels/languagemodelsession/responsestream>
- <https://developer.apple.com/documentation/foundationmodels/managing-the-context-window>

Signatures and the conformance list were verified against the **shipping SDK interface**, not
only the doc site:

```
Xcode 26.6 (17F113) · MacOSX.sdk/System/Library/Frameworks/FoundationModels.framework/
  Modules/FoundationModels.swiftmodule/arm64e-apple-macos.swiftinterface
```

Claims marked **compile-verified** were typechecked with
`xcrun swiftc -typecheck -target arm64-apple-macos26.0 -swift-version 6`.

WWDC guidance: sessions [286](https://developer.apple.com/videos/play/wwdc2025/286/),
[301](https://developer.apple.com/videos/play/wwdc2025/301/),
[259](https://developer.apple.com/videos/play/wwdc2025/259/).

Fetched: 2026-08-19

---

## 0. Two API generations, and three doc bugs

**developer.apple.com documents the 27.0 beta surface; the shipping SDK is 26.x.** Divergences
are flagged inline throughout. The short version of what exists only in the docs:
`Generable(name:…)`, `ToolCallingMode`, `DynamicProfile`, `transcriptErrorHandlingPolicy`,
`Transcript.Reasoning`, `Snapshot.transcriptEntries`/`.usage`.

**Apple's own documentation contains three examples that do not compile.** All three were
verified against the 26.x SDK:

| Where                                       | Apple says                                                                   | Reality                                                                                           |
| ------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Guided-generation article                   | _"Use `Generable(description:)` on structures, actors, and enumerations."_   | **Actors and classes are rejected.** `error: '@Generable' can only be used on structs and enums.` |
| `Generable` protocol page, flagship example | `var id: GenerationID` inside a `@Generable` struct                          | **Does not compile** — `GenerationID` isn't `Generable`. Four errors. And it's unnecessary (§4).  |
| Tool-calling article, `WeatherTool`         | `func call(...) async throws -> Forecast` where `struct Forecast: Encodable` | **Does not conform.** `Encodable` ≠ `PromptRepresentable`.                                        |

Copying Apple's sample code here will not work. Details in place below.

---

## 1. `@Generable`

```swift
// iOS 26.0+ (watchOS 27.0 beta)
macro Generable(description: String? = nil)

// 26.4+
macro Generable(description: String? = nil, representNilExplicitlyInGeneratedContent: Bool)

// 27.0 BETA only
macro Generable(name: String, description: String? = nil,
                representNilExplicitlyInGeneratedContent: Bool = false)
```

**Applies to `struct` and `enum` only.** Not actors, not classes, regardless of what the article
says.

### What it generates

For a decorated type, the macro emits three things:

1. **`static var generationSchema`**, built from **declaration order** (§5).
2. **A nested `PartiallyGenerated` struct** — `Identifiable`, every property optional.
3. **A `Generable` conformance extension** with `init(_ content: GeneratedContent) throws`.

```swift
@Generable(description: "A cat")
struct CatProfile {
    var name: String
    @Guide(description: "The age of the cat", .range(0...20)) var age: Int
    var tags: [String]
    var nickname: String?
}

// →
nonisolated struct PartiallyGenerated: Identifiable, ConvertibleFromGeneratedContent {
    var id: GenerationID
    var name: String.PartiallyGenerated?        // == String?
    var age: Int.PartiallyGenerated?
    var tags: [String].PartiallyGenerated?
    var nickname: String?.PartiallyGenerated?
}
```

`representNilExplicitlyInGeneratedContent: true` emits explicit nulls for nil optionals instead
of omitting the key. **Outbound only** — it does not change the schema.

### Enums come in two shapes

**No associated values → a string enum:**

```swift
@Generable enum Mood { case happy, sad }
// → GenerationSchema(type: Self.self, anyOf: ["happy", "sad"])
```

**With associated values → a discriminated union.** The macro synthesizes a private
`Discriminated*` struct per case, each pinning a `type` field with `.constant`, and
`PartiallyGenerated` becomes an enum too:

```swift
@Generable enum Shape { case circle(radius: Double); case rect(w: Double, h: Double) }
// → anyOf: [DiscriminatedCircle.self, DiscriminatedRect.self]
// → enum PartiallyGenerated { case circle(radius: Double.PartiallyGenerated?) ; ... }
```

`@Generable enum Category: String, CaseIterable` works and keeps both `rawValue` and `allCases`
(compile-verified). That's the shape Apple's own tool samples use.

---

## 2. `@Guide`

```swift
@attached(peer) macro Guide<T>(description: String? = nil, _ guides: GenerationGuide<T>...) where T: Generable
@attached(peer) macro Guide<RegexOutput>(description: String? = nil, _ guides: Regex<RegexOutput>)
@attached(peer) macro Guide(description: String)
```

Because `description` defaults to `nil`, a bare constraint is legal:
`@Guide(.anyOf(["x","y"]))`, `@Guide(/\d+/)` (compile-verified).

**Stacked `@Guide` macros merge.** Verified via macro dump to produce a schema _identical_ to
the combined single-macro form:

```swift
@Guide(.minimumCount(1), .maximumCount(20))
@Guide(description: "Keyboard shortcuts for desktop")
var keyboardShortcuts: [String]
```

### `GenerationGuide` — the constraint surface

| Constraint                                | Signature                                      | Applies to                          |
| ----------------------------------------- | ---------------------------------------------- | ----------------------------------- |
| `.constant(_:)`                           | `(String) -> GenerationGuide<String>`          | `String`                            |
| `.anyOf(_:)`                              | `([String]) -> GenerationGuide<String>`        | `String`                            |
| `.pattern(_:)`                            | `<O>(Regex<O>) -> GenerationGuide<String>`     | `String`                            |
| `.minimum(_:)` / `.maximum(_:)`           | `(T) -> GenerationGuide<T>`                    | `Int`, `Float`, `Double`, `Decimal` |
| `.range(_:)`                              | `(ClosedRange<T>) -> GenerationGuide<T>`       | same four                           |
| `.minimumCount(_:)` / `.maximumCount(_:)` | `(Int) -> GenerationGuide<[E]>`                | arrays                              |
| `.count(_:)`                              | `(Int)` **and** `(ClosedRange<Int>)`           | arrays                              |
| `.element(_:)`                            | `(GenerationGuide<E>) -> GenerationGuide<[E]>` | arrays                              |

**Range bounds are inclusive.**

### Compatibility matrix — compile-verified, all 24 combinations

```
              String   Int    [Int]  [String]
.count(3)      FAIL    FAIL    OK      OK
.range(1...5)  FAIL    OK      FAIL    FAIL
.minimum(1)    FAIL    OK      FAIL    FAIL
.anyOf([…])    OK      FAIL    FAIL    FAIL
.pattern(/x/)  OK      FAIL    FAIL    FAIL
.element(…)    FAIL    FAIL    OK      OK*
```

\* `.element(.anyOf([…]))` works on `[String]`; `.element(.range(…))` doesn't, because `.range`
isn't a String guide.

**There is no `.anyOf` for non-String types.** To constrain a number or any other type to a
closed set of choices, use a `@Generable enum` — that constrains sampling structurally instead
of hoping a description lands.

Both regex spellings work: `@Guide(description: "d", /[A-Z]{3}-\d{4}/)` and
`@Guide(description: "d", .pattern(/[A-Z]{3}-\d{4}/))`.

Unsupported patterns throw `unsupportedGuide` (26.0) / `unsupportedGenerationGuide` (27.0).

---

## 3. Which types are actually `Generable`

**The doc site is misleading here** — the protocol page lists only `GeneratedContent` and
`ImageReference` as conforming types. The SDK interface is definitive:

```swift
extension Bool, String, Int, Float, Double, Decimal, Never : Generable {}
extension Array : Generable where Element : Generable {
    typealias PartiallyGenerated = [Element.PartiallyGenerated]
}
extension Optional where Wrapped : Generable {
    typealias PartiallyGenerated = Wrapped.PartiallyGenerated
}
```

Plus `GeneratedContent`, `ImageReference`, and your own `@Generable` types.

**Not supported** — each compile-checked and failing:

| Type                                                       |     |
| ---------------------------------------------------------- | --- |
| `[String: Int]` — **any Dictionary**                       | ✗   |
| `Set<String>`                                              | ✗   |
| `UInt`, `Int8`, `Int64` — **any integer that isn't `Int`** | ✗   |
| `Date`, `URL`, `UUID`, `Data`                              | ✗   |
| `CGFloat` — a distinct type from `Double`                  | ✗   |
| `GenerationID`                                             | ✗   |

No dictionaries and no `Date` are the two that bite hardest. Model a date as a `String` with a
format description, or as a `@Generable` struct of `Int` components. Model a dictionary as an
array of key/value structs.

> **Doc bug.** The `Generable` page's headline `SearchSuggestions` example declares
> `var id: GenerationID` with the comment _"Use a generation identifier for data structures the
> framework generates."_ **It does not compile** — `GenerationID` is `Sendable, Hashable`, not
> `Generable`.
>
> You never needed it: the generated `PartiallyGenerated` **already** has `var id: GenerationID`
> and conforms to `Identifiable`. `ForEach(partial?.days ?? [])` compiles with no `id:` argument.

Top-level primitives and arrays work as response types:
`respond(to:generating: Float.self)`, `Int.self`, `Bool.self`, `[Item].self`.

---

## 4. Streaming structured output

```swift
final func streamResponse<Content>(
    to prompt: Prompt,
    generating type: Content.Type = Content.self,
    includeSchemaInPrompt: Bool = true,
    options: GenerationOptions = GenerationOptions()
) -> sending LanguageModelSession.ResponseStream<Content> where Content: Generable

struct ResponseStream<Content>: AsyncSequence {
    struct Snapshot {
        var content: Content.PartiallyGenerated
        var rawContent: GeneratedContent
    }
    nonisolated(nonsending) func collect() async throws -> sending Response<Content>
}
```

**You get snapshots, not deltas.** WWDC25 session 286:

> _"Instead of raw deltas, we stream snapshots. As the model produces deltas, the framework
> transforms them into snapshots. Snapshots represent partially generated responses. Their
> properties are all optional. And they get filled in as the model produces more of the
> response."_

Optionality is recursive: each property becomes `T.PartiallyGenerated?`. Since
`String.PartiallyGenerated == String`, a `String` property is plain `String?`. A nested
`@Generable` property is `Nested.PartiallyGenerated?` — partial all the way down.

**For a top-level array** (`generating: [Item].self`), `PartiallyGenerated` is
`[Item.PartiallyGenerated]` — the array itself is _not_ optional, only its elements are partial.

`collect()` gives the fully-typed, non-optional result at the end.

`GeneratedContent.isComplete` reports whether a piece is finished, and `init(json:)` explicitly
tolerates truncation:

```swift
let partial = #"{"title": "A story of"#
let content = try GeneratedContent(json: partial)
print(try NovelIdea(content).title)   // "A story of"
```

**`includeSchemaInPrompt`** defaults to `true` and should usually stay there. Set it `false`
only _"when the model has knowledge about the expected response format, either because it has
been trained on it, or because it has seen exhaustive examples during this session."_ The schema
costs tokens against the 4,096 budget, so this is a real lever on long sessions.

### Rendering partials in SwiftUI

**The HIG says nothing about this** — verified: the generative-ai and machine-learning HIG pages
contain no mention of streaming, partial output, incremental rendering, or placeholders. The
guidance is in WWDC and sample code only.

WWDC25 session 286's three rules:

> _"First, get creative with SwiftUI animations and transitions to hide latency… Second, you'll
> need to think carefully about view identity in SwiftUI, especially when generating arrays.
> Finally, bear in mind that properties are generated in the order they are declared on your
> Swift struct."_

The concrete recipe from Apple's shipped sample:

- `.contentTransition(.opacity)` on each streamed text field
- `.animation(.easeOut, value:)` on the container
- `.geometryGroup()` then `.animation(.easeInOut, value:)` on each card — the standard
  layout-jump mitigation, though Apple never names it as such
- **pinned array identity**: `ForEach(days, id: \.title)`
- `.transition(.blurReplace)` on in-progress rows

Apple never uses the word "jitter" and never suggests `.redacted(reason: .placeholder)` in any
Foundation Models material.

Also worth deciding deliberately, per session 259: _"it's also good to think about which of your
properties are ok to show without the others."_

---

## 5. Property order changes output quality

Documented in three places, consistently. This is the highest-leverage thing in the file.

> _"The model generates `Generable` properties in the order they're declared."_

> _"This matters both for animations and for the quality of the model's output. For example, you
> may find that the model produces the best summaries when they're the last property in the
> struct."_ — WWDC25 286

> _"This order can be important, if you're expecting the value of a property to be influenced by
> another property."_ — WWDC25 301

**The corollary Apple spells out — give reasoning a home, and put it first:**

> _"Reasoning prompt techniques, like 'think through this problem step by step', can result in
> unexpected text being inserted into your Generable structure if the model doesn't have a place
> for its reasoning. To keep reasoning explanations out of your structure, try giving the model
> a specific field where it can put its reasoning. **Make sure the reasoning field is the first
> property so the model can provide reasoning details before answering the prompt**"_

```swift
@Generable
struct ReasonableAnswer {
    var reasoningSteps: String            // FIRST — the model thinks here
    @Guide(description: "The answer only.")
    var answer: MyCustomGenerableType
}
```

**Rule of thumb: inputs-to-thinking first, conclusions last.** A summary meant to reflect the
rest of the struct goes at the end. Scratch reasoning goes at the beginning. Reordering fields
is a free quality change — no prompt edit required.

`GeneratedContent.Kind.structure` even carries `orderedKeys` alongside its dictionary, so
generation order survives into the untyped representation.

---

## 6. Runtime schemas — `DynamicGenerationSchema`

When the shape isn't known at compile time:

```swift
struct DynamicGenerationSchema: Sendable
init(name:description:properties:)
init(name:description:anyOf: [DynamicGenerationSchema])
init(name:description:anyOf: [String])
init(arrayOf: DynamicGenerationSchema, minimumElements: Int? = nil, maximumElements: Int? = nil)
init(referenceTo name: String)
init<Value: Generable>(type: Value.Type, guides: [GenerationGuide<Value>] = [])
static var null: DynamicGenerationSchema      // 26.4+

struct Property { init(name:description:schema:isOptional: Bool = false) }
```

Resolve to a real schema, then respond against it:

```swift
let menuSchema = DynamicGenerationSchema(name: "Menu", properties: [
    .init(name: "dailySoup",
          schema: DynamicGenerationSchema(name: "dailySoup",
                                          anyOf: ["Tomato", "Chicken Noodle", "Clam Chowder"])),
    .init(name: "sides",
          schema: DynamicGenerationSchema(arrayOf: DynamicGenerationSchema(type: String.self),
                                          minimumElements: 1, maximumElements: 3),
          isOptional: true),
    .init(name: "price",
          schema: DynamicGenerationSchema(type: Int.self, guides: [.range(1...100)])),
])

let schema = try GenerationSchema(root: menuSchema, dependencies: [])
let response = try await session.respond(to: "Make a menu.", schema: schema)
let soup = try response.content.value(String.self, forProperty: "dailySoup")
```

Responses come back as `GeneratedContent` — untyped, read with `value(_:forProperty:)`.
Streaming works on this path too.

`init(referenceTo:)` plus the `dependencies:` array is how recursive or shared sub-schemas work;
references resolve at `GenerationSchema` construction. Failures surface as
`GenerationSchema.SchemaError`: `duplicateProperty`, `duplicateType`, `emptyTypeChoices`,
`undefinedReferences`.

_(Apple's rendered sample for `.null` has a syntax typo — `properties: []` followed by a stray
bracket. Don't copy it verbatim.)_

---

## 7. `Tool`

```swift
protocol Tool<Arguments, Output>: Sendable {
    associatedtype Output: PromptRepresentable
    associatedtype Arguments: ConvertibleFromGeneratedContent

    var name: String { get }                        // defaulted to the type name
    var description: String { get }
    var parameters: GenerationSchema { get }        // defaulted when Arguments: Generable
    var includesSchemaInInstructions: Bool { get }  // defaulted true

    @concurrent func call(arguments: Self.Arguments) async throws -> Self.Output
}
```

With the defaults, a minimal tool is just `description`, `call(arguments:)`, and an
`@Generable struct Arguments`.

### `Arguments` must be `Generable` or `GeneratedContent` — primitives are a hard error

The SDK ships **six poison-pill extensions** to make this unmistakable:

```swift
extension Tool where Self.Arguments == Swift.String {
    @available(*, unavailable,
      message: "'Tool' that uses 'String' as 'Arguments' type is unsupported. Use '@Generable' struct instead.")
    public var parameters: GenerationSchema { get }
}
// identical for Int, Double, Float, Decimal, Bool
```

`GeneratedContent` **is** allowed — that's how you build a tool whose schema is only known at
runtime, supplying `parameters` yourself (compile-verified):

```swift
struct DynamicTool: Tool {
    let name = "lookup"
    let description = "Looks something up"
    let parameters: GenerationSchema          // injected at init
    typealias Arguments = GeneratedContent

    func call(arguments: GeneratedContent) async throws -> String {
        let q = try arguments.value(String.self, forProperty: "query")
        return "result for \(q)"
    }
}
```

### `Output` must be `PromptRepresentable`

`String`, `GeneratedContent`, any `@Generable` type, and arrays of those (since
`Array: PromptRepresentable where Element: PromptRepresentable`).

> **Doc bug.** The article's `WeatherTool` returns `struct Forecast: Encodable`.
> `error: type 'WeatherTool' does not conform to protocol 'Tool'`. `Encodable` is not
> `PromptRepresentable`. Mark `Forecast` as `@Generable` instead.

### Attaching, and how many

Tools are passed at session construction and _"are available for all future interactions with
the session."_

No hard cap is documented, but Apple gives a budget:

> _"Provide no more than three to five tools per request."_
> _"Skip tool calling when you don't need the model to make decisions. If the model always needs
> specific information, retrieve it directly and include it in your prompt rather than relying
> on tool calling."_

Tool definitions and their schemas are charged against the same 4,096-token window.

**Parallel and repeated calls are supported.** _"The model can call a tool multiple times in
parallel… Tools must conform to `Sendable` so the framework can run them concurrently."_ And on
`call(arguments:)`: _"This method may be invoked concurrently with itself or with other tools."_

**You own tool lifetime**, so a tool can carry state between calls — which is why Apple's samples
use `@Observable final class …: Tool` accumulating a lookup history the UI renders live.

### `ToolCallingMode` — 27.0 beta only

```swift
static let allowed / disallowed / required     // GenerationOptions.ToolCallingMode
```

Not in the 26.x SDK, which has only
`GenerationOptions(sampling:temperature:maximumResponseTokens:)` — note `sampling:`, not
`samplingMode:`.

> **Important:** _"When you set the mode to required, you must define an exit condition by either
> throwing an error from a tool's `call(arguments:)` method or by changing the mode dynamically
> using a `DynamicProfile`; otherwise, the model continues to call the tool."_

`.required` without an exit condition is an infinite tool-call loop.

---

## 8. Errors in a tool — throw to abort, return a string to adapt

```swift
struct LanguageModelSession.ToolCallError: Error, LocalizedError {
    var tool: any Tool
    var underlyingError: any Error
}
```

> _"If errors are thrown in the body of this method, the framework wraps them in a
> `ToolCallError` and rethrows them at the call site of `respond(to:options:)`."_

**What the model sees when a tool throws: nothing.** The throw aborts generation and surfaces to
_your_ code. If you want the model to notice and route around the failure, return instead:

> _"You can throw errors from your tools to escape calls when you detect something is wrong…
> **Alternatively, your tool can return a string that briefly tells the model what didn't work,
> like 'Cannot access the database.'**"_

That's the design decision in one line: **throw to abort the request, return a string to let the
model recover.**

```swift
} catch let error as LanguageModelSession.ToolCallError {
    print(error.tool.name)
    if case .databaseIsEmpty = error.underlyingError as? SearchBreadDatabaseToolError { … }
}
```

**Transcript rollback:** _"When errors are thrown from a tool, the framework rolls back the
transcript to a previously known valid state."_ On 27.0, `transcriptErrorHandlingPolicy` picks
between `.preserveTranscript` (last entry may be partially generated) and `.revertTranscript`.

---

## 9. Naming tools

`name` — _"A unique name for the tool, such as 'get_weather', 'toggleDarkMode', or 'search
contacts'."_ Apple's examples mix snake_case, camelCase, and spaces, so no convention is
mandated; their sample code uses camelCase throughout.

`description` — _"A natural language description of **when and how** to use the tool."_ The
_when_ is what the model routes on. This string is the whole routing signal.

Apple's exemplar:

```swift
@Observable
final class FindPointsOfInterestTool: Tool {
    let name = "findPointsOfInterest"
    let description = "Finds points of interest for a landmark."

    @Generable
    enum Category: String, CaseIterable {
        case campground, hotel, cafe, museum, marina, restaurant, nationalMonument
    }

    @Generable
    struct Arguments {
        @Guide(description: "The type of destination to look up.")
        let pointOfInterest: Category
        @Guide(description: "The natural language query of what to search for.")
        let naturalLanguageQuery: String
    }

    func call(arguments: Arguments) async throws -> String { … }
}
```

Note the closed set is a `@Generable enum`, not a `String` with a description — structural
constraint beats hoping.

Apple's other guidance: keep descriptions and `@Guide` text to short phrases (they cost tokens
and add latency); **test without `@Guide` first**, then add guides only where the model needs
clarity; and _"if you have an unclear property name, it won't convey the right intent to the
model. Instead, consider renaming the property"_ — the property name is itself a prompt.

---

## 10. Tool calls in the `Transcript`

```swift
struct Transcript.ToolCalls: RandomAccessCollection { typealias Element = Transcript.ToolCall }
struct Transcript.ToolCall  { var id: String; var toolName: String; var arguments: GeneratedContent }
struct Transcript.ToolOutput { var id: String; var toolName: String; var segments: [Transcript.Segment] }
struct Transcript.ToolDefinition { init(tool: some Tool); var name: String; var description: String }
```

`ToolCalls` being a _collection_ is how parallel calls are represented: one `.toolCalls` entry
holding several `ToolCall`s. `Transcript.Instructions.toolDefinitions` holds the schemas the
framework injected on your behalf.

`LanguageModelSession` is `Observable`, so `List(session.transcript)` renders the live call graph
straight into SwiftUI — the cheapest debugging tool available here.
`tokenCount(for tools:)` budgets it.

---

## 11. Worked example (typechecks clean against the 26.x SDK)

```swift
@Generable(description: "A generated itinerary")
struct Itinerary {
    var rationale: String                                        // reasoning FIRST
    @Guide(description: "A fun title") var title: String
    @Guide(description: "Days", .count(3)) var days: [DayPlan]
    @Guide(description: "Budget USD", .range(100...5000)) var budget: Int
    var hotel: Hotel?
}

@Generable struct DayPlan {
    @Guide(description: "One-line summary") var summary: String
    @Guide(.minimumCount(1), .maximumCount(4)) var activities: [String]
}

@Generable enum Hotel {                    // associated values → discriminated union
    case named(name: String, stars: Int)
    case none
}

@Observable @MainActor
final class Planner {
    let session = LanguageModelSession(tools: [SearchTool()], instructions: "Plan trips.")
    private(set) var partial: Itinerary.PartiallyGenerated?

    func run() async throws {
        let stream = session.streamResponse(
            to: "Plan 3 days in Kyoto.",
            generating: Itinerary.self,
            options: GenerationOptions(sampling: .greedy)   // 26.x label; 27.0 uses samplingMode:
        )
        for try await snapshot in stream {
            partial = snapshot.content                      // every field optional
        }
        _ = try await stream.collect().content              // fully-typed Itinerary
    }
}

struct V: View {
    let p: Itinerary.PartiallyGenerated?
    var body: some View {
        VStack {
            if let t = p?.title { Text(t).contentTransition(.opacity) }
            ForEach(p?.days ?? []) { d in                   // PartiallyGenerated is Identifiable
                if let s = d.summary { Text(s) }
            }
        }
        .animation(.easeInOut, value: p?.title)
    }
}
```

---

## 12. Gotchas

1. **Three of Apple's own examples don't compile** (§0) — actors, `var id: GenerationID`, and
   `Encodable` tool output.
2. **No `Date`, no `URL`, no `UUID`, no dictionaries, no `Set`, no integer type but `Int`.**
   Model them as strings or nested `@Generable` structs.
3. **`CGFloat` is not `Double`** to the macro. Use `Double`.
4. **Declaration order changes output quality.** Reasoning first, summaries last.
5. **`.anyOf` is String-only.** Use a `@Generable enum` for closed sets of anything else.
6. **`@Generable` works on structs and enums only** — the docs say actors; they're wrong.
7. **Primitive `Arguments` on a `Tool` is a hard compile error**, deliberately, via unavailable
   extensions.
8. **Tool `Output` must be `PromptRepresentable`** — `Codable`/`Encodable` doesn't count.
9. **A tool that throws tells the model nothing.** Return a string if you want it to adapt.
10. **`.required` tool calling with no exit condition loops forever.**
11. **Schemas cost tokens** against the 4,096 window — `includeSchemaInPrompt: false` and
    shorter `@Guide` text are real levers; 3–5 tools is Apple's budget.
12. **26.x uses `sampling:`, 27.0 uses `samplingMode:`.** `ToolCallingMode` and `DynamicProfile`
    don't exist in the shipping SDK at all.
13. **Don't add your own `id` to a `@Generable` type** — `PartiallyGenerated` already supplies
    one and is `Identifiable`.
