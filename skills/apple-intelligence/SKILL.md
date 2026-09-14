---
name: apple-intelligence
description: Apple Intelligence framework reference covering Visual Intelligence, App Intents, Foundation Models, Writing Tools, and beta AI surfaces. Use when integrating system AI experiences, adopting App Intents, running Apple on-device models, or checking API availability.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: bu9tAf1kt5uOXYOSEJ_GIAofVAb8UAAG
  related_ids: '["fOgpDf1clpuczYuwEKbdcwgfGAb8kAAG","Tq17nc3n_9kI1eGSKGfEKSNndGROMAAN"]'
---

# Apple Intelligence

Trimmed markdown digests of Apple `developer.apple.com` documentation for the **Apple
Intelligence** framework family. Each page starts with its source URL(s) and fetch date and
keeps symbol names, signatures, and platform availability markers, with the navigation
boilerplate dropped.

Pulled via Apple's JSON doc endpoints
(`developer.apple.com/tutorials/data/documentation/<path>.json`), which return structured
signatures and availability when the rendered HTML comes back thin. Reuse what is here before
re-fetching; re-pull if Apple has likely changed the surface.

**These are new, fast-moving, mostly-26.0 frameworks**, and several carry beta markers or
contradictory availability metadata. Every page records what could not be verified rather
than smoothing it over — trust the flags.

## References — load on demand

- **[foundation-models.md](references/foundation-models.md)**
  - the on-device LLM: `SystemLanguageModel` availability gating,
    `LanguageModelSession`, `Instructions` vs `Prompt` (and the prompt-injection
    rule), `GenerationOptions`, the 4,096-token context window and its recovery
    pattern, the iOS 27 error rework, guardrails and refusals. _Read first for
    anything Foundation Models. Note `GenerationError` is deprecated._

- **[foundation-models-guided-generation.md](references/foundation-models-guided-generation.md)**
  - `@Generable` / `@Guide`, which Swift types are actually supported, streaming
    `PartiallyGenerated` snapshots, runtime `DynamicGenerationSchema`, and the
    `Tool` protocol. _Read for structured output or tool calling. Property
    declaration order changes output quality; three of Apple's examples don't
    compile._

- **[visual-intelligence-search.md](references/visual-intelligence-search.md)**
  - `SemanticContentDescriptor` (`labels`, `pixelBuffer`) and the full adoption flow:
    `IntentValueQuery` → `AppEntity` display → `OpenIntent` → the `semanticContentSearch`
    schema. _Read before integrating with visual search. The system calls you, not the
    reverse; labels are categories, never names._

## Scope

**In** — what Apple's own technologies index tags `"Apple Intelligence"`:

Visual Intelligence · Foundation Models · App Intents (the connective tissue — most of these
frameworks are unreadable without it) · Writing Tools · Private Cloud Compute · and the beta
Core AI, Media Intelligence, Suggested Actions, and Evaluations surfaces.

**Out** — owned elsewhere, or not actually under the umbrella:

| Topic                                                                          | Why not here                                                                                                     |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| **Core ML**, Vision, Create ML, Natural Language, Speech, Sound Analysis       | Apple tags these `Machine Learning` **only** — no `Apple Intelligence`. They're the ML layer below.              |
| **Image Playground**                                                           | Tagged `Imaging`/`Graphics`, not `Apple Intelligence`. Surprising, but it's Apple's own filing.                  |
| GPU compute, MPSGraph, Metal numerics                                          | **`apple-silicon`**                                                                                              |
| BNNS, vDSP, CPU vectorized math                                                | **`apple-accelerate`**                                                                                           |
| Swift language mechanics — `some`/`any`, `Sendable`, macros like `@UnionValue` | **`swift`**. Reference it; don't re-explain it here.                                                             |
| ARKit, camera capture, `AVCaptureSession`                                      | **`apple-arkit`**. Visual Intelligence hands you a buffer from the _system's_ camera — your app never opens one. |

The boundary that matters most: **Core ML is not Apple Intelligence.** If Core ML material
accumulates, it earns its own skill rather than landing here.
