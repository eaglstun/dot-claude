---
semantic_id: "8kVrJSZRNU8EEdLipCPp8zQ7GhRj4AAC"
related_ids:
  - "csRLRSdXOYycaY_o4KFj03A9CidqwAAB"
  - "sMDBZWYxNZ_2ybJjvmGvclTzEkda4AAH"
---
# Script Graph — no-code runtime logic

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/getting-started-with-script-graphs>
- <https://developer.apple.com/documentation/realitycomposerpro/building-an-advanced-animation-graph> (the Script Graph bridge section)

Fetched: 2026-08-19

Script Graph is RCP's **event-driven** visual scripting surface — the code-free way to build
common RealityKit behaviors and interactions. A **Scripting component** hosts each graph,
either directly or as an asset, and the graph primarily operates on the owning entity.

> **It cannot build a user interface.** Only simple text layouts through a Text component.
> **Use SwiftUI for your app's UI.** Don't try to fake it in nodes.

## The two connection types

| Line | Carries |
| --- | --- |
| **Blue — Flow** | Execution order between nodes |
| **Gray — Data** | Values and computed results |

That distinction is the whole model. Compare with Animation Graph, where pins carry **pose
data only** and there is no execution flow at all.

## Entry points

Graphs start from an entry-point node. These have a **blue Flow output but no Flow input** —
they initiate execution rather than receive it. Documented entry points: **On Initialize**,
**On Update**, **On Collision**, **On Tap**, and **Custom Events**.

> **Known issue (Beta 4, 182533099): "On Initialize" can fail to start animation or audio on
> build and run. Use "On Activate" instead** to kick off audio and animation events.

## Node categories

- **Entry points** — On Initialize, On Update, On Activate, On Collision, On Tap, Custom
  Events.
- **Control flow** — IF/THEN, AND, OR, and nodes that delay execution.
- **Array** — create and manipulate collections.
- **Entity** — find entities by name, read and write entity properties, enable/disable
  entities, check for and assign components.
- **Component** — **Get Component**, **Set Component**, **Has Component**. This is the bridge
  to an Animation Graph component, a Compute Graph's public inputs, or anything else on the
  entity.
- **Collision** — On Collision Began, On Collision Ended. **Most RealityKit events have a
  matching node.**
- **Math and operational** — simple through complex math.
- **Animation and audio** — start and stop animations and audio playback.
- **Input** — keyboard, mouse, gestures, and **ARKit**.
- **Material** — tell a Shader Graph to adjust itself in response to scene interactions.

The Scripting component also lets you **declare variables that persist and update across
frames**. Subgraphs work as in any RCP graph.

## Building one

Project Browser → Control-click a folder → **New → Script Graph** → name → double-click.

Minimum working graph: an **On Update** entry point, plus a functional node such as **Set
Relative Transform**; drag the blue Flow output to the blue Flow input. The line turns blue
to confirm a valid Flow connection.

## Attaching it

**Directly** — select the entity → Inspector → **Add Component → Scripting** → **Script** →
**Graph Script Source** → **Edit** opens an empty Script Graph.

**As a Prototype** — if the script needs to be shared across multiple entities or
encapsulated as a subgraph, make it a Prototype instead. It can then be reused in other
graphs, or as a subgraph of a component-owned entity. (See `scenes-entities-prototypes.md`
for the prototype/instance/override rules — they apply here too.)

## Previewing

Click **Simulate** in the toolbar. **On Initialize** fires immediately, **On Update** runs
each frame. Confirm execution here before deploying to a device.

## The runtime component

Authoring a Script Graph produces a **`ScriptingComponent`** — the editor and its
JavaScript-facing API call it **`ReScriptingComponent`**.

> **RCP links `RealityKitScripting` automatically. A plain RealityKit app project must link
> it manually** so its `ScriptingSystem` can execute `ScriptingComponent` instances at
> runtime. This is the thing that silently does nothing if you forget it.

## Where Script Graph sits relative to everything else

| Job | Owner |
| --- | --- |
| React to gameplay events; decide *what* should happen | **Script Graph** (or Swift) |
| How a character animates given that decision | **Animation Graph** |
| The steps to carry out a behavior | **Behavior Tree** |
| Simulating and rendering an effect | **Compute Graph** |
| User interface | **SwiftUI** |

Script Graph reads a Tag or drives an Input to change what an Animation Graph does next; it
sets a Public Input to steer a Compute Graph; it sets parameters a Behavior Tree understands.
It is the wiring, not the destination.

> **Known issue (all RCP 3 betas, 178279067):** using **world position** in scripts or
> shaders shifts RCP content relative to the world origin in **shared space** apps. Use
> relative position, or compute your content's relationship to the world origin and adjust.
> Apple points at the *Squirrel* sample for examples.
