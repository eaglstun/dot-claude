---
semantic_id: "TqVrn8zj_9lY3WGCOCfELQNnEWDGsAAO"
related_ids:
  - "Tq17nc3n_9kI1eGSKGfEKSNndGROMAAN"
  - "bu9tAf1kt5uOXYOSEJ_GIAofVAb8UAAG"
---

# Foundation Models — session, model, context window, errors, safety

Guided generation (`@Generable`, `@Guide`) and tool calling live in a sibling file;
this one is the session/model core.

Source (API reference + articles, fetched via Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/foundationmodels>
- <https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel>
- <https://developer.apple.com/documentation/foundationmodels/languagemodelsession>
- <https://developer.apple.com/documentation/foundationmodels/instructions>
- <https://developer.apple.com/documentation/foundationmodels/prompt>
- <https://developer.apple.com/documentation/foundationmodels/transcript>
- <https://developer.apple.com/documentation/foundationmodels/generationoptions>
- <https://developer.apple.com/documentation/foundationmodels/languagemodelerror>
- <https://developer.apple.com/documentation/foundationmodels/languagemodelsession/generationerror> _(deprecated)_
- <https://developer.apple.com/documentation/foundationmodels/managing-the-context-window>
- <https://developer.apple.com/documentation/foundationmodels/improving-the-safety-of-generative-model-output>
- <https://developer.apple.com/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models>
- <https://developer.apple.com/documentation/foundationmodels/prompting-an-on-device-foundation-model>
- <https://developer.apple.com/documentation/foundationmodels/supporting-languages-and-locales-with-foundation-models>
- <https://developer.apple.com/documentation/foundationmodels/updating-prompts-for-new-model-versions>
- <https://developer.apple.com/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute>
- <https://developer.apple.com/documentation/updates/foundationmodels>

Model identity, parameter counts, and the adapter toolkit are not in the API reference;
those come from:

- <https://developer.apple.com/apple-intelligence/foundation-models-adapter/>
- <https://machinelearning.apple.com/research/apple-foundation-models-2025-updates>
- <https://machinelearning.apple.com/research/introducing-third-generation-of-apple-foundation-models>

Fetched: 2026-08-19

---

## 0. Read this first — the docs are the iOS 27 generation now

Apple reworked this framework at WWDC 2026. **Anything written against the iOS 26 API is
partially stale**, including most tutorials and most of what a model recalls from training.
Two breaks matter more than the rest:

1. **`LanguageModelSession.GenerationError` is DEPRECATED.** Replaced by three types:
   `LanguageModelError`, `SystemLanguageModel.Error`, `LanguageModelSession.Error`. Apple,
   verbatim: _"Apps built with Xcode 26 will continue to catch this error until you rebuild
   with Xcode 27. You must update to Xcode 27 to catch the new error types before submitting
   your app."_ A rebuild silently changes which `catch` clauses fire. See §7.
2. **`SystemLanguageModel.Adapter` is gone.** `/systemlanguagemodel/adapter` returns 404, and
   neither `adapter` nor `init(adapter:)` appears in the symbol index. The adapter training
   toolkit is end-of-lifed (§9).

Also: **the on-device model itself changes when a person updates to 27.** Apple says to retest
prompts. There are three known model versions — 26.0–26.3, 26.4, and 27.0 — and Apple documents
gating prompts on them:

```swift
if #available(iOS 26.4, macOS 26.4, visionOS 26.4, *) {
    // The prompt you updated for the newer model.
} else {
    // The prompt for 26.0–26.3.
}
```

### Availability

|                                                | Framework     | `SystemLanguageModel` | `LanguageModelSession` |
| ---------------------------------------------- | ------------- | --------------------- | ---------------------- |
| iOS / iPadOS / Mac Catalyst / macOS / visionOS | 26.0          | 26.0                  | 26.0                   |
| watchOS                                        | **27.0 beta** | **absent**            | **27.0 beta**          |

**That watchOS gap is real, not an extraction artifact** — verified by re-fetching the symbol's
own JSON. The framework and `LanguageModelSession` list watchOS 27.0 beta; `SystemLanguageModel`
lists no watchOS at all, with no doc text explaining it. Don't assume the default model is
reachable on watchOS.

**The hardware requirement is stated in prose, not in any availability annotation:** _"To use
Apple Foundation Models, people need a device that supports Apple Intelligence."_ There is no
symbol to check it with — you check `availability` at runtime (§2) and design for the
unavailable case.

---

## 1. What the model is, and what it is bad at

> _"The Foundation Models framework provides access to any large language model, like the
> on-device and Private Cloud Compute models designed for Apple Intelligence."_

**The developer docs never state a parameter count.** From Apple ML Research: the iOS 26
generation is a **~3B on-device model**; the iOS 27 generation (AFM 3) adds **AFM 3 Core**
(~3B dense) and **AFM 3 Core Advanced** (20B sparse, 1–4B active, gated to the most capable
Apple silicon). Those two map onto `SystemLanguageModel.Variant.core3` / `.coreAdvanced3`.

The blunt framing is also ML Research, not the developer docs:

> _"It is not designed to be a chatbot for general world knowledge."_

The developer-doc equivalent is a pair of tables:

| Good at                                                                                                                           | Avoid                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Summarize · extract entities · understand text · refine/edit · classify or judge · creative writing · generate tags · game dialog | **Basic math** ("How many b's in bagel?") · **writing code** · **logical reasoning** ("facing Canada, what direction is Texas?") |

> _"Because of their smaller size, on-device models have limited reasoning abilities."_

### On-device vs Private Cloud Compute

|              | `SystemLanguageModel` | `PrivateCloudComputeLanguageModel` |
| ------------ | --------------------- | ---------------------------------- |
| Private      | ✅                    | ✅                                 |
| Offline      | ✅                    | 🚫                                 |
| Usage limits | Unlimited             | **Limit per day**                  |
| Reasoning    | Not supported         | Multiple levels                    |
| **Context**  | **4K**                | **32K**                            |

PCC needs the managed entitlement `com.apple.developer.private-cloud-compute`. Both conform to
the iOS 27 `LanguageModel` protocol, so switching is one line:
`LanguageModelSession(model: PrivateCloudComputeLanguageModel())`.

---

## 2. `SystemLanguageModel` — and always checking availability first

```swift
final class SystemLanguageModel        // iOS 26.0+ (no watchOS)
static var `default`: SystemLanguageModel { get }
```

```swift
final var isAvailable: Bool { get }
final var availability: SystemLanguageModel.Availability { get }

@frozen enum Availability {
    case available
    case unavailable(Availability.UnavailableReason)
}
enum UnavailableReason {
    case appleIntelligenceNotEnabled   // user hasn't turned it on
    case deviceNotEligible             // hardware can't
    case modelNotReady                 // downloading, or other system reasons
}
```

Apple's canonical shape — note it is `@Observable`, so a SwiftUI view re-renders when
availability flips mid-session:

```swift
struct GenerativeView: View {
    private var model = SystemLanguageModel.default

    var body: some View {
        switch model.availability {
        case .available:                         // Show your intelligence UI.
        case .unavailable(.deviceNotEligible):   // Show an alternative UI.
        case .unavailable(.modelNotReady):       // Downloading, or other system reasons.
        case .unavailable(let other):            // Unknown reason.
        }
    }
}
```

> _"It can take some time for the model to download and become available when a person turns on
> Apple Intelligence."_

`.modelNotReady` is therefore a **transient** state, not a permanent failure — treat it
differently from `.deviceNotEligible`.

### Specialized use cases

```swift
convenience init(useCase: SystemLanguageModel.UseCase = .general,
                 guardrails: SystemLanguageModel.Guardrails = .default)     // iOS 26.0+

struct UseCase
static let general: UseCase
static let contentTagging: UseCase
```

`contentTagging` _"always responds with tags"_ — topics, emotions, actions, objects. If you want
tags, this beats prompting the general model for them.

### Capabilities

```swift
@backDeployed(before: iOS 26.4, macOS 26.4, visionOS 26.4)
final var contextSize: Int { get }                       // tokens, input + output

final var supportedLanguages: Set<Locale.Language> { get }
final func supportsLocale(_ locale: Locale = .current) -> Bool

nonisolated(nonsending)
final func tokenCount(for instructions: Instructions) async throws -> Int   // iOS 26.4+

final var variant: SystemLanguageModel.Variant { get }   // iOS 27.0 BETA
// Variant.core3 ("AFM 3 Core") / .coreAdvanced3 ("AFM 3 Core Advanced"), + displayName
```

**Prefer `supportsLocale(_:)` over `supportedLanguages`** — it accounts for language fallbacks,
so `en-AU` matches against `en-NZ`. The supported-language list is not in the framework docs at
all; Apple defers to support.apple.com/en-us/121115.

_(Doc inconsistency, reproduced as found: `contextSize` carries a "Throws" note describing an
error when the model is unavailable, but is declared as a non-throwing `Int` getter.)_

---

## 3. `LanguageModelSession`

```swift
final class LanguageModelSession        // iOS 26.0+, watchOS 27.0 beta
```

> _"A session is a single context that you use to generate content with, and maintains state
> between requests."_

### Initializers

Six overloads of the instructions form. The one nearly every Apple sample uses is the plain
`String`:

```swift
convenience init(model: SystemLanguageModel = .default,
                 tools: [any Tool] = [],
                 instructions: String? = nil)

convenience init(model: SystemLanguageModel = .default,
                 tools: [any Tool] = [],
                 @InstructionsBuilder instructions: () throws -> Instructions) rethrows

convenience init(model: SystemLanguageModel = .default,
                 tools: [any Tool] = [],
                 instructions: Instructions? = nil)
```

iOS 27 adds `model: some LanguageModel` variants of each (so PCC or any conforming model drops
in) plus a typed-throws builder form.

**Resuming from history** — the escape hatch for context overflow (§6):

```swift
convenience init(model: SystemLanguageModel = .default,
                 tools: [any Tool] = [],
                 transcript: Transcript)
```

### Responding

```swift
@discardableResult nonisolated(nonsending)
final func respond(to prompt: String,
                   options: GenerationOptions = GenerationOptions())
    async throws -> LanguageModelSession.Response<String>

final func streamResponse(to prompt: String,
                          options: GenerationOptions = GenerationOptions())
    -> sending LanguageModelSession.ResponseStream<String>
```

Both have `Prompt` and `@PromptBuilder` forms. iOS 27 adds a parallel
`contextOptions:metadata:` family across all six.

> **Important (Apple's own callout on both streaming methods):** _"If running in the background,
> use the non-streaming `respond(to:options:)` method to reduce the likelihood of encountering
> `rateLimited(_:)` errors."_

```swift
struct Response<Content> {
    let content: Content
    let rawContent: GeneratedContent
    let transcriptEntries: ArraySlice<Transcript.Entry>
    let usage: LanguageModelSession.Usage        // iOS 27 beta
}
```

### `isResponding` — one request at a time, enforced by crash

```swift
final var isResponding: Bool { get }
```

> _"You should not call any of the respond methods while this property is `true`."_
> _"A session can only handle a single request at a time, and causes a **runtime error** if you
> call it again before the previous request finishes."_

Not an exception you can catch on the old API — a runtime error. Gate the UI:

```swift
Button("Generate joke") { … }
    .disabled(session.isResponding)
```

(iOS 27 does add `LanguageModelSession.Error.concurrentRequests` as a catchable case.)

### `prewarm`

```swift
final func prewarm(promptPrefix: Prompt? = nil)
```

> _"You should only use prewarm when you have a window of at least 1 second before the call to a
> respond method."_

Call it when someone starts typing into the field, not on view appear. Passing a known prefix
lets the system process it eagerly. No guarantee of immediate loading, especially backgrounded.

### `transcript`

```swift
final var transcript: Transcript { get set }
```

**Settable**, which is what makes the trim-and-continue pattern in §6 possible. Entries:

```swift
enum Transcript.Entry {
    case instructions(Transcript.Instructions)
    case prompt(Transcript.Prompt)
    case response(Transcript.Response)
    case reasoning(Transcript.Reasoning)        // iOS 27 BETA
    case toolCalls(Transcript.ToolCalls)
    case toolOutput(Transcript.ToolOutput)
}
```

### Feedback to Apple

```swift
@discardableResult
final func logFeedbackAttachment(sentiment: LanguageModelFeedback.Sentiment?,
                                 issues: [LanguageModelFeedback.Issue] = [],
                                 desiredOutput: Transcript.Entry? = nil) -> Data
```

Returns JSON to write to a `.json` file and attach to Feedback Assistant. Issue categories:
`didNotFollowInstructions`, `incorrect`, `stereotypeOrBias`, `suggestiveOrSexual`, `tooVerbose`,
`triggeredGuardrailUnexpectedly`, `unhelpful`, `vulgarOrOffensive`.

---

## 4. `Instructions` vs `Prompt` — and the prompt-injection rule

```swift
struct Instructions        // iOS 26.0+
struct Prompt              // iOS 26.0+
```

**Instructions outrank prompts.** _"The model obeys prompts at a lower priority than the
instructions you provide."_ That priority is exactly why instructions are dangerous:

> **"Don't include untrusted content in instructions: the model is typically trained to obey
> instructions over any commands it receives in prompts."**

> _"A session obeys instructions over a prompt, so don't include input from people or any
> unverified input in the instructions. Using unverified input in instructions makes your app
> vulnerable to prompt injection attacks, so write instructions with content you trust."_

**The rule in one line: user input goes in the prompt, never the instructions.** If you need to
frame user input, wrap it in your own template _inside the prompt_.

What instructions should carry: the model's role, what it should do, style preferences, and
safety measures. Aim for **one to three paragraphs** — instructions are tokens, and they are
charged against the same 4,096 (§6).

Both types have result builders, so conditionals work:

```swift
let prompt = Prompt {
    "Answer the following question: Do Siberian Huskies love cold weather?"
    if responseShouldRhyme {
        "Your response MUST rhyme!"
    }
}
```

---

## 5. `GenerationOptions`

```swift
struct GenerationOptions
init(samplingMode: SamplingMode? = nil,      // was `sampling:` in iOS 26; back-deployed rename
     temperature: Double? = nil,
     maximumResponseTokens: Int? = nil)
```

**Every option defaults to `nil`, meaning "let the system choose."** That is usually the right
answer — Apple says so explicitly for both temperature and sampling.

- `temperature`: **0…1 inclusive**, not 0…2. `1` means no adjustment; lower is sharper and more
  predictable.
- `maximumResponseTokens`: hitting it terminates the response early **without throwing**.

  > _"Only use `maximumResponseTokens` when you need to protect against unexpectedly verbose
  > responses. Enforcing a strict token response limit can lead to the model producing malformed
  > results or grammatically incorrect responses"_ — Apple's own example of the damage:
  > _"A cat is a small."_

```swift
static var greedy: SamplingMode                                          // deterministic
static func random(probabilityThreshold: Double, seed: UInt64? = nil)    // top-p / nucleus
static func random(top k: Int, seed: UInt64? = nil)                      // top-k
```

> _"Setting a random seed is not guaranteed to result in fully deterministic output. It is best
> effort."_

Only `greedy` _"always produces the same output for a given input."_ If you need reproducibility
for a test, use `greedy`, not a seed.

---

## 6. The context window — 4,096 tokens

> _"Apple's on-device foundation model has a context window of **4096 tokens per session**, with
> a token representing each word, or partial word."_

**Input and output share it.** Instructions + every prompt + every response + tool definitions +
`@Generable` schemas, all counted against one budget, for the life of the session.

Token density: ~3–4 characters per token in Latin-alphabet languages; **~1 character per token
for Chinese, Japanese, Korean, and Vietnamese** — a CJK app burns the window roughly 3–4× faster
for the same visible text.

Overflow throws. The documented recovery is **start a new session carrying a condensed
transcript**:

```swift
func newContextualSession(with originalSession: LanguageModelSession) -> LanguageModelSession {
    let allEntries = originalSession.transcript
    let condensedEntries = [allEntries.first, allEntries.last].compactMap { $0 }
    let condensedTranscript = Transcript(entries: condensedEntries)
    let newSession = LanguageModelSession(transcript: condensedTranscript)
    newSession.prewarm()
    return newSession
}
```

> _"The first transcript entry often contains important instructions and the last entry contains
> the most recent context. By preserving the first and last entry, you maintain continuity while
> dramatically reducing token usage."_

Other budget levers Apple names: profile with the **Foundation Models instrument** (Product ▸
Profile ▸ Foundation Models) for per-interaction token counts; keep prompts to ≤3 paragraphs;
constrain output length in the prompt text itself; **simplify `@Generable` types and use
`@Guide` sparingly, since schemas are sent as tokens**; and _"provide no more than three to five
tools per request."_ Xcode's `#Playground` macro shows input and response token counts against
the 4,096.

---

## 7. Errors — the iOS 27 replacement, and the old names

### Current: `LanguageModelError` (iOS 27 beta)

```swift
enum LanguageModelError {
    case contextSizeExceeded(ContextSizeExceeded)   // .contextSize, .tokenCount
    case rateLimited(RateLimited)                   // .resetDate: Date?
    case refusal(Refusal)                           // .explanation, .explanationStream
    case timeout(Timeout)
    case guardrailViolation(GuardrailViolation)
    case unsupportedCapability(UnsupportedCapability)
    case unsupportedTranscriptContent(UnsupportedTranscriptContent)
    case unsupportedGenerationGuide(UnsupportedGenerationGuide)
    case unsupportedLanguageOrLocale(UnsupportedLanguageOrLocale)
}

enum LanguageModelSession.Error {
    case concurrentRequests
    case transcriptMutationWhileResponding
}

enum SystemLanguageModel.Error {
    case assetsUnavailable(AssetsUnavailable)
}
```

Every payload carries `debugDescription: String` and `metadata: [String: any Sendable]`. The
useful specifics: `ContextSizeExceeded` gives you both `contextSize` and actual `tokenCount`;
`RateLimited` gives `resetDate`.

### Deprecated: `LanguageModelSession.GenerationError` (iOS 26)

`assetsUnavailable` · `decodingFailure` · `exceededContextWindowSize` · `guardrailViolation` ·
`rateLimited` · `refusal` · `concurrentRequests` · `unsupportedGuide` ·
`unsupportedLanguageOrLocale`, each carrying a `Context` with a `debugDescription`.

| Old (iOS 26)                                | New (iOS 27)                                    |
| ------------------------------------------- | ----------------------------------------------- |
| `GenerationError.exceededContextWindowSize` | `LanguageModelError.contextSizeExceeded`        |
| `GenerationError.unsupportedGuide`          | `LanguageModelError.unsupportedGenerationGuide` |
| `GenerationError.concurrentRequests`        | `LanguageModelSession.Error.concurrentRequests` |
| `GenerationError.assetsUnavailable`         | `SystemLanguageModel.Error.assetsUnavailable`   |
| `GenerationError.decodingFailure`           | _no direct replacement listed_                  |

**Rate limits are only ever documented qualitatively.** _"This error will only happen if your app
is running in the background and exceeds the system defined rate limit."_ **No numeric limit
appears anywhere in the docs** — no requests/minute, no requests/hour. `RateLimited.resetDate`
is the only programmatic handle. Don't hardcode a budget against a number you think you know.

---

## 8. Safety — guardrails and the refusal asymmetry

Two built-in layers: models trained to handle sensitive topics carefully, plus **guardrails**
checking both prompt input and model output.

```swift
static let `default`: Guardrails                            // everything on
static let permissiveContentTransformations: Guardrails     // for summarizing existing content
```

`permissiveContentTransformations` exists for the legitimate case of _"summarizing a news
article"_ that happens to be about something grim. In that mode, **`String` generations stop
throwing `guardrailViolation`** — but structured generations still throw, and the model may
still emit a refusal _as text_.

> _"even with the `SystemLanguageModel` guardrails off, the on-device system language model still
> has a layer of safety."_

### The asymmetry that shapes your error handling

| Generating         | A refusal arrives as…                                                |
| ------------------ | -------------------------------------------------------------------- |
| `String`           | **ordinary text** in the response — "Sorry, I can't help with that…" |
| A `Generable` type | **a thrown** `LanguageModelError.refusal(_:)`                        |

> _"You might not be able to programmatically determine whether a string response is a normal
> response or a refusal, so design the experience to anticipate both. If it's critical to
> determine whether the response is a refusal message, initialize a new `LanguageModelSession`
> and prompt the model to classify whether the string is a refusal."_

So: **string generation has no reliable refusal signal.** If your feature must distinguish, that
is an argument for guided generation over free text.

```swift
} catch LanguageModelError.refusal(let refusal) {
    do {
        let explanation = try await refusal.explanation.content   // async — model generates it
    } catch {
        let explanation = refusal.debugDescription
    }
}
```

### Guardrails don't cover unsupported languages

> **Important:** _"Guardrails for model input and output safety are only for supported languages
> and locales. If a prompt contains sensitive content in an unsupported language, which
> typically is a short phrase mixed-in with text in a supported language, it might not throw a
> `unsupportedLanguageOrLocale(_:)` error. If unsupported-language detection fails, the
> guardrails may also fail to flag that short, unsupported content."_

A short foreign-language phrase embedded in supported-language text can slip both checks.

Apple's prescribed additional layers: bound the input (a fixed set of prompts is the safest);
bound the output with a `@Generable enum`; keep a deny list you can update server-side without
an app release; write a risk-assessment table; and test against nonsense, code snippets, and
random characters.

---

## 9. Adapter training is end-of-lifed

The toolkit page carries this banner:

> **"Version 26.0.0 is the last release of this toolkit and is not compatible with macOS, iOS,
> iPadOS, or visionOS 27 and later."**

Consistent with `SystemLanguageModel.Adapter` returning 404 and the adapter-loading article also
404ing. Historical shape, for context: ~160 MB per adapter, one adapter per **specific system
model version**, rank-32 LoRA, shipped via Background Assets, gated behind a requested
entitlement. Apple's own advice was always _"Before considering adapters, try to get the most
out of the system model using prompt engineering or tool calling."_

**Unverified:** whether adapters still load at runtime on 26.x devices from an app built with
the 27 SDK. No API, no migration note.

---

## 10. Gotchas

1. **Rebuilding with Xcode 27 changes which errors you catch.** `GenerationError` keeps working
   until you rebuild, then stops. Apple requires the update before submission.
2. **The model itself changes on OS update.** Three versions so far (26.0–26.3, 26.4, 27.0).
   Retest prompts; gate with `#available` if behavior diverges.
3. **Never put user input in `Instructions`.** They outrank prompts by design, which is exactly
   what makes them a prompt-injection surface.
4. **4,096 tokens covers input _and_ output**, for the whole session, including schemas and tool
   definitions. CJK text burns it ~3–4× faster per visible character.
5. **A second concurrent request is a runtime error on iOS 26**, not a catchable throw. Bind
   `isResponding` to your UI.
6. **`maximumResponseTokens` truncates silently** and can produce grammatically broken output.
   It's a safety valve, not a length control.
7. **`temperature` is 0…1**, not the 0…2 range other providers use.
8. **A seed does not guarantee determinism** — "best effort." Only `greedy` is deterministic.
9. **String refusals are indistinguishable from real answers.** Structured generation is the only
   path that turns a refusal into a catchable error.
10. **Guardrails miss short unsupported-language phrases**, including sensitive ones.
11. **`SystemLanguageModel` has no watchOS availability** even though the framework and
    `LanguageModelSession` claim watchOS 27 beta.
12. **No numeric rate limit is documented.** Background-only, "system defined." Use
    `RateLimited.resetDate`.
13. **Use `supportsLocale(_:)`, not `supportedLanguages`** — only the former handles fallbacks.
14. **Prewarm needs a ≥1 second lead** to be worth calling.
