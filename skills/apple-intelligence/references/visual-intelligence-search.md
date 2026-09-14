---
semantic_id: "fOgpDf1clpuczYuwEKbdcwgfGAb8kAAG"
related_ids:
  - "bu9tAf1kt5uOXYOSEJ_GIAofVAb8UAAG"
  - "_-bsBuV9l9rySMOYA7aN4ChjXm7U8AAI"
---
# Visual Intelligence — putting your app's content in system visual search

Source (API reference + article, fetched via Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/visualintelligence>
- <https://developer.apple.com/documentation/visualintelligence/semanticcontentdescriptor>
- <https://developer.apple.com/documentation/visualintelligence/semanticcontentdescriptor/labels>
- <https://developer.apple.com/documentation/visualintelligence/semanticcontentdescriptor/pixelbuffer>
- <https://developer.apple.com/documentation/visualintelligence/integrating-your-app-with-visual-intelligence>
- <https://developer.apple.com/documentation/updates/visualintelligence>
- <https://developer.apple.com/documentation/appintents/intentvaluequery>
- <https://developer.apple.com/documentation/appintents/assistantschemas/visualintelligenceintent>
- <https://developer.apple.com/documentation/appintents/assistantschemas/visualintelligenceintent/semanticcontentsearch>
- <https://developer.apple.com/documentation/appintents/adopting-app-intents-to-support-system-experiences>

Guidance and platform claims cross-checked against:

- WWDC26 session 297, "Best practices for integrating visual intelligence in your app"
  <https://developer.apple.com/videos/play/wwdc2026/297/>
- Apple Support, "Use visual intelligence on iPhone"
  <https://support.apple.com/guide/iphone/use-visual-intelligence-iph12eb1545e/26/ios/26>

Fetched: 2026-08-19

## What this is

**The system calls into your app. You never call it.** There is no "run visual intelligence"
API. A person points the visual intelligence camera at something (iOS) or selects an object in
a screenshot (iPadOS/macOS); the system classifies the scene, then hands the capture to an
App Intents query **you** implemented, and renders whatever app entities you return directly
inside the visual intelligence UI.

`SemanticContentDescriptor` is the payload the system pushes at you. The framework is thin —
essentially this one struct plus an article. **All the actual machinery is App Intents.**

### Availability

| Platform | Introduced | Beta |
| --- | --- | --- |
| iOS | 26.0 | no |
| iPadOS | 26.0 | no |
| macOS | 27.0 | **yes** |
| Mac Catalyst | 26.0 or 27.0 — **see below** | unclear |

Two things in Apple's metadata do not reconcile, and both are recorded here rather than
smoothed over:

1. **Mac Catalyst.** The *framework* page reports `26.0`, non-beta. Every *symbol* page under it
   reports `27.0`, **beta**. The `semanticContentSearch` App Intents schema sides with the
   framework page (`26.0`, non-beta). Treat Mac Catalyst as **unverified** and check against the
   SDK you're building with.
2. **visionOS.** Every symbol page carries a visionOS entry with **no `introducedAt` version at
   all**, and the framework page has no visionOS entry whatsoever. A platform row with no
   version is almost always a DocC artifact. WWDC26 session 297 says only *"This year, Visual
   Intelligence is also available on iPadOS and macOS."* **Do not claim visionOS support.**

The macOS arrival is confirmed by `updates/visualintelligence`, dated June 2026: *"Use
SemanticContentDescriptor to integrate your macOS app with visual intelligence."*

**Device requirement is not documented at the framework level.** Apple's developer docs state no
hardware gate. Apple Support says visual intelligence *"builds on Apple Intelligence"* and is
available on *"any Apple Intelligence-enabled iPhone"* — practically iPhone 15 Pro / iPhone 16
or later. That's a support-page inference, not an API guarantee; don't quote it as one.

---

## 1. `SemanticContentDescriptor`

```swift
struct SemanticContentDescriptor        // iOS 26.0+, iPadOS 26.0+, macOS 27.0 beta
```

> *"A type that represents a scene that visual intelligence captures, for example, a screenshot,
> photo, or photo and video stream."*

**There are no initializers.** The type has no Initializers section at all — the value is only
ever constructed by the system and delivered to your query. You cannot fabricate one, including
in tests.

```swift
let labels: [String]
var pixelBuffer: CVReadOnlyPixelBuffer? { get }
```

That is the entire useful surface. The rest is App Intents conformance plumbing you never call:

```swift
static var defaultResolverSpecification: some ResolverSpecification { get }
typealias Specification  = some ResolverSpecification
typealias ValueType      = SemanticContentDescriptor
typealias UnwrappedType  = SemanticContentDescriptor
```

Conforms to `Sendable`, `Codable`, `CustomStringConvertible`,
`CustomLocalizedStringResourceConvertible`, and the App Intents set (`DisplayRepresentable`,
`InstanceDisplayRepresentable`, `TypeDisplayRepresentable`, `IntentValueConvertible`,
`IntentValueExpressing`, `PersistentlyIdentifiable`).

**`pixelBuffer` is `CVReadOnlyPixelBuffer?`, not `CVPixelBuffer`** — a Swift 6 non-copyable
read-only wrapper, and it is Optional. Apple's own sample guards it and returns `[]`.

### `labels` — the thing everyone gets wrong

Apple, verbatim:

> *"Labels are general, high-level terms in the `en_US` locale and might change over time. The
> Visual Intelligence framework doesn't translate them or include synonyms. For example,
> SemanticContentDescriptor might provide the labels `tower` or `building` for a well-known
> building. It won't provide the building's actual name as a label."*

Consequences, each of which bites:

- **Labels are categories, not names.** No entity resolution has happened. `tower`, not
  `Eiffel Tower`.
- **Never key a lookup table on them.** They "might change over time" — Apple reserves the right
  to alter the vocabulary between releases.
- **Never localize off them.** They are always `en_US`, never translated, no synonyms.

Labels are a cheap pre-filter to decide whether your app has anything to say. The real matching
happens on the pixels.

---

## 2. Adopting it, end to end

### Step 1 — one `IntentValueQuery`, typed to the descriptor

```swift
struct LandmarkIntentValueQuery: IntentValueQuery {
    @Dependency var modelData: ModelData

    func values(for input: SemanticContentDescriptor) async throws -> [VisualSearchResult] {
        guard let pixelBuffer = input.pixelBuffer else { return [] }
        return try await modelData.search(matching: pixelBuffer)
    }
}
```

`IntentValueQuery` is App Intents, iOS/iPadOS/macOS/Mac Catalyst/tvOS/visionOS/watchOS **26.0**,
all non-beta — a wider surface than Visual Intelligence itself.

> **Hard limit:** *"Your app can't contain more than one `IntentValueQuery` that takes a
> `SemanticContentDescriptor`."* One per app. Not one per entity type — one, total.

### Step 2 — turn the buffer into something matchable

```swift
private func createImage(_ pixelBuffer: CVReadOnlyPixelBuffer) -> CGImage? {
    let context = CIContext()
    let image = CIImage(cvPixelBuffer: pixelBuffer)
    return context.createCGImage(image, from: image.extent)
}
```

Session 297's performance guidance: **precompute feature prints for your catalog** ahead of
time, rank candidates by similarity, and match against **thumbnails, not full-resolution
assets**. This runs while a person is holding a camera up — latency is the feature.

### Step 3 — return `AppEntity` values, because their display *is* the UI

The entity's `DisplayRepresentation` (title, subtitle, image) **is** the result card the person
sees inside visual intelligence. There is no separate view to write and no styling hook. A weak
or unlocalized `DisplayRepresentation` is a weak feature, full stop. The sample uses
`IndexedEntity` with both `typeDisplayRepresentation` and `displayRepresentation`.

**Return roughly 100 results maximum.** If you have hundreds of matches, put the remainder behind
the "More results" intent in step 5.

### Step 4 — an `OpenIntent` so a tap opens your app

```swift
struct OpenLandmarkIntent: OpenIntent {
    static let title: LocalizedStringResource = "Open Landmark"

    @Parameter(title: "Landmark", requestValueDialog: "Which landmark?")
    var target: LandmarkEntity
}
```

### Multiple entity types — `@UnionValue`

One query, but it can return a union:

```swift
@UnionValue
enum VisualSearchResult {
    case landmark(LandmarkEntity)
    case collection(CollectionEntity)
}
```

**If you use `@UnionValue`, you need a separate `OpenIntent` for every entity type in the
union.** Miss one and results of that type simply don't open, silently.

### Step 5 — optional "More results" button

An app intent conforming to the `semanticContentSearch` schema:

```swift
var semanticContentSearch: some AssistantSchemas.Intent { get }
```

`AssistantSchemas.VisualIntelligenceIntent.semanticContentSearch` — **iOS 26.0 / iPadOS 26.0 /
Mac Catalyst 26.0 only. No macOS entry, no visionOS entry.** So on macOS you get the inline
results but not the escape hatch to a fuller in-app search.

Xcode autocomplete trigger for the schema macros: type `visualintelligence_`.

---

## 3. Requirements

**No entitlement. No Info.plist key.** The article JSON has zero hits for `entitlement`,
`Info.plist`, `NS…`, or `com.apple.developer`. Adoption is purely code — implement the App
Intents conformances and you're in. This is genuinely unusual for a system-integration feature
and worth not over-engineering around.

---

## 4. Gotchas

1. **Labels are categories, never names, always `en_US`, and may change between OS releases.**
   Pre-filter with them; match on pixels.
2. **`pixelBuffer` is Optional and is `CVReadOnlyPixelBuffer`**, not `CVPixelBuffer`. Guard it.
3. **One `IntentValueQuery` per app** taking a `SemanticContentDescriptor`. Use `@UnionValue` for
   multiple entity types — and then one `OpenIntent` per type in the union.
4. **`SemanticContentDescriptor` has no initializer.** System-constructed only, which shapes how
   you can test: the query's matching logic has to be extractable and testable on its own,
   because you cannot synthesize its input.
5. **macOS pixel buffers are much larger than iPhone ones** (session 297). Resize before matching
   or latency tanks on exactly the platform where people expect desktop-fast.
6. **The entry point differs by platform** — iOS is the camera, iPadOS and macOS are screenshots.
   Same code path, very different input characteristics (motion blur and framing vs. crisp
   synthetic pixels).
7. **Your `DisplayRepresentation` is the entire user-visible surface.** Localize it; make it
   concise and high-quality.
8. **Mac Catalyst availability is contradictory in Apple's own metadata** (§Availability). Verify
   against your SDK.
9. **Don't claim visionOS support** on the strength of that version-less platform row.
10. **The sample project "Adopting App Intents to support system experiences" is marked beta,
    Xcode 27.0.** Its code will not build against a 26.0 toolchain as-is.
