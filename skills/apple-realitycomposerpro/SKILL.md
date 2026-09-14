---
name: apple-realitycomposerpro
description: Reality Composer Pro 3 reference for scene authoring, entities, materials, Shader and Compute Graphs, particles, animation, behaviors, navigation, and spatial audio. Use when building or debugging RCP content or integrating its scenes with Swift.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: MmXDYy1zPYfSSbJLeBqr4lTFEld6cAAA
  related_ids: '["sMDBZWYxNZ_2ybJjvmGvclTzEkda4AAH","sOQJZW4xNQ3wybPiOGHnsNXbInZa8AAF"]'
---

# Reality Composer Pro

Trimmed markdown digests of Apple `developer.apple.com` documentation for **Reality Composer
Pro 3** and the two frameworks it authors into — `ShaderGraph` and `ComputeGraph`. Each page
starts with its source URLs and fetch date, keeps symbol names and exact property values, and
drops the navigation boilerplate.

Pulled via Apple's JSON doc endpoints
(`developer.apple.com/tutorials/data/documentation/<path>.json`), which return structured
content and signatures where the rendered HTML comes back thin. Reuse what's here before
re-fetching.

## Read this before anything else

**Reality Composer Pro 3 is a standalone app, not part of Xcode.** Download it from the Apple
Developer website. Requires an **Apple silicon** Mac on **macOS Tahoe 26.5+**, with **Xcode
27** for the project link. It is **in beta** — Beta 4 is the newest release note published.

Two corollaries that invalidate older habits:

- Any instruction of the form "open the `.rkassets` package in Xcode to launch Reality
  Composer Pro" describes **version 1 or 2**.
- **RCP is no longer a visionOS tool.** "Run with Xcode" generates a Universal app for every
  RealityKit platform — iOS, iPadOS, macOS, visionOS, and tvOS.

Because it's beta software, **check `references/release-notes.md` when something doesn't
work.** Several current bugs fail silently rather than erroring.

## References — load on demand

- **[workspace-and-xcode.md](references/workspace-and-xcode.md)**
  - the app's requirements and version-3 identity, the four panes, viewport debug and
    rendering visualization modes, lightmap baking, workspaces and tabs, the shared Graph
    Editor controls, linking an Xcode project, the plugin directory, Preview vs. Simulate vs.
    Run, loading a scene from `RealityView`, and the AI Assistant. _Start here._

- **[scenes-entities-prototypes.md](references/scenes-entities-prototypes.md)**
  - entities and components, asset import behavior, what does and doesn't ship in the app
    bundle, and the **prototype / instance / override** model. _Read before wondering why an
    edit changed every copy of something._

- **[materials-and-shader-graph.md](references/materials-and-shader-graph.md)**
  - the five material types, the full Inspector property surface, Surface Shader vs.
    Geometry Modifier output pins, and **promoted inputs** (uniform vs. constant vs. function
    constant) for changing materials at runtime.

- **[shader-graph-nodes.md](references/shader-graph-nodes.md)**
  - the complete `ShaderGraph` node catalog by category, every entry linked to its signature
    page. MaterialX 1.38 plus the RealityKit-only additions. _An index — reach for it for
    "which node does X?"_

- **[particles-and-compute-graph.md](references/particles-and-compute-graph.md)**
  - Particle Emitter properties (emitter vs. main vs. secondary particles), and **Compute
    Graph**: the four-stage run order, every built-in node namespace, a worked example, the
    optimization rules, and the `ComputeGraphSimulation` Swift API.

- **[animation-sequences.md](references/animation-sequences.md)**
  - the Sequence timeline: tracks and sub-tracks, the five actions, Custom Action bind
    targets, Motion Path and its Orbit/Spin shapes, the 0.75 s cross-fade ceiling, and the
    **Root Entity rule** that silently decides whether auto-play works at all.

- **[animation-graph.md](references/animation-graph.md)**
  - character state machines: skeleton definitions, inputs, states, conduits and conditions,
    tags, blend and IK nodes, the three preview surfaces, and reading
    `AnimationGraphComponent` from Swift.

- **[script-graph.md](references/script-graph.md)**
  - the event-driven scripting surface: Flow vs. Data connections, entry points, node
    categories, `ScriptingComponent`, and the `RealityKitScripting` link a plain RealityKit
    app has to make itself.

- **[behavior-trees-and-navigation.md](references/behavior-trees-and-navigation.md)**
  - Behavior Tree node categories and traversal semantics (Sequence / Selector / Parallel),
    and navmesh generation — named layers, shapes, off-mesh connections, generation
    parameters, and Area/Flag tags.

- **[audio.md](references/audio.md)**
  - Spatial vs. Ambient vs. Channel components and what each costs, loading strategies,
    reverb (including the visionOS immersion-style exception), Audio File Groups vs. Audio
    Mix Groups, and the preparation power cost.

- **[release-notes.md](references/release-notes.md)**
  - what's broken right now, what got fixed in which beta, and the two documentation pages
    Apple links but hasn't published.

## The five graph types, and which is which

They share one editor and are constantly confused for each other.

| Graph               | Authors                                             | Connections carry                       |
| ------------------- | --------------------------------------------------- | --------------------------------------- |
| **Shader Graph**    | A material — surface appearance and vertex geometry | Typed values                            |
| **Script Graph**    | Runtime event logic                                 | **Flow** (blue) and **Data** (gray)     |
| **Animation Graph** | A character animation state machine                 | **Pose data only** — no execution flow  |
| **Behavior Tree**   | The _steps_ of one NPC behavior                     | Traversal, with success/failure/running |
| **Compute Graph**   | A GPU compute / particle simulation                 | Stage-ordered node inputs               |

The division of labor: **Script Graph or Swift decides _what_ should happen. Animation Graph
decides how the character moves given that. Behavior Tree carries out the steps. Compute
Graph simulates and renders the effect. SwiftUI builds the UI** — Script Graph explicitly
cannot.

## Scope

**In** — Reality Composer Pro itself, plus the two frameworks that exist to serve it:
`ShaderGraph` and `ComputeGraph`. RealityKit types are named wherever RCP produces or
consumes them (`ShaderGraphMaterial`, `AnimationGraphComponent`, `SpatialAudioComponent`, …)
without re-documenting RealityKit.

**Out** — owned elsewhere:

| Topic                                                           | Where it lives                                                                                                |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Hand-rolled Metal renderers, MSL shaders, render passes         | **`apple-metal`**                                                                                             |
| Metal API surface, GPU compute, MPS, capture and validation     | **`apple-silicon`**                                                                                           |
| ARKit sensing, world/face tracking, scene depth, camera capture | **`apple-arkit`**                                                                                             |
| SceneKit — `SCNScene`, shader modifiers, SCNMaterial            | **`scenekit`**. A different, older scene graph; do not mix its vocabulary in                                  |
| Swift language mechanics — concurrency, generics, `Sendable`    | **`swift`**                                                                                                   |
| Apple's on-device models, App Intents, Writing Tools            | **`apple-intelligence`**. The RCP Assistant talks to _your_ configured provider and is not Apple Intelligence |

The boundary worth stating: **RealityKit itself has no skill here.** These pages cover the
authoring tool and stop at the component boundary. If RealityKit runtime material
accumulates, it earns its own skill rather than sprawling into this one.
