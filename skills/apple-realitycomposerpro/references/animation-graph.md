---
semantic_id: "csRLRSdXOYycaY_o4KFj03A9CidqwAAB"
related_ids:
  - "sOdjSW41uZ3G7ZqgsCHn4tV8GiZL0AAP"
  - "8kVrJSZRNU8EEdLipCPp8zQ7GhRj4AAC"
---
# Animation Graph — character state machines

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/working-with-the-animation-graph>
- <https://developer.apple.com/documentation/realitycomposerpro/building-an-advanced-animation-graph>

Fetched: 2026-08-19

An Animation Graph is a node-based description of **how a character animates**: which clips
play, how they blend, and when the character switches motions. It replaces hand-coded
transition logic. Contrast with a Sequence (`animation-sequences.md`), which is a fixed
timeline rather than a runtime decision structure.

> **Vocabulary that matters:** Animation Graph nodes pass **pose data along typed pins**.
> There is no execution-flow or event pin here. That vocabulary belongs to **Script Graph**,
> which is a different graph type — see `script-graph.md`.

## Create and configure

Project Browser → Control-click a folder → **New → Animation → Animation Graph** → name it →
double-click. Opening it switches RCP into the **Animation Workspace**, a layout
pre-configured for this asset type.

**Set the asset-level Skeleton Definition first.** Every Animation Clip and pose node
resolves its joints against it. For imported entities RCP creates the skeleton definition at
import time, including dependencies like blend masks and IK rigs. **Preview Entity**
populates automatically once a skeleton is set; change it to preview the same graph on
different entities sharing that skeleton.

If your project already has retargeted clips in an animation library referencing the same
Skeleton Definition, drop them straight into the graph as Source nodes with no extra setup.

## Inputs

Runtime parameters that control which animation plays. Inspector → **Inputs** → **`+`**.
Types: **Bool, Float, Int, Option, Rotation, Trigger, Vector**. Each takes a name, a
**Default Value**, and a **Read Only** toggle.

## Node categories

**Source**

- **Animation Clip** — plays an animation resource from keyframes; the edit-time
  representation of a clip.
- **Bind Pose** — the current skeleton's bind pose.

**Modifier / Blend**

- **Blend 1D** — blends samples from child nodes distributed along a single axis.
- **Blend Mask** — filters a pose by per-joint weights from a blend mask.
- **Add** / **Subtract** — add or subtract two poses.
- **Motion Warping** — adjusts playback speed so root motion reaches a target position.
- **Root Motion Generation** — moves the root joint to a desired position and orientation
  over time.

**Control Flow**

- **State Machine** — evaluates a state machine.

**Inverse Kinematics**

- **Full Body IK Node** — full-body solver, output pose from the child pose plus
  rig-defined constraints.
- **Foot Placement** — adjusts foot positions on terrain via IK and constraints.
- **Constraint Parameters** / **Joint Parameters** — parameters for one named rig
  constraint or joint.

**Output**

- **Final Pose** — hands the resolved pose to the entity's skeleton. **Every graph
  terminates here.**

## State Machines

Add a **State Machine** node (**N** or Space), then double-click it to open the empty space
inside where states and conduits live.

Control-click inside → **Add State**. In the Inspector, name it and set **Start State**,
**End State**, or **Pass Through** as applicable.

**Transitions:** click the edge of a state and drag the arrow to another state.

**Conduits** are transition states that let several states route through one shared
condition — define the condition once instead of repeating it on every state-to-state
transition. A conduit can also branch to multiple destinations. Control-click empty space →
**Add Conduit**, drag an arrow from its edge to a state, then Control-click the conduit
connector → **Add Condition** and pick a type (Bool, Finished, Float, …). Configure the
comparison operator (`==`, `!=`, …) in the Inspector, and use **Settings** to compare against
a fixed value or against a parameter.

The editor color-codes condition types — trigger conditions blue, boolean conditions green.

## Tags

Tags let a state announce its playback status so both the graph itself and outside systems
can react.

Add one: Inspector → **Tags** → **`+`** → choose **Type**: **Internal**, **Play Audio**, or
**Enable/Disable Entity** → name it. Attach it to a state via the state's own Tags list, then
choose **when** it activates:

| Mode | Activates |
| --- | --- |
| **On Enter** | Entering the state |
| **On Exit** | Leaving the state |
| **On Enter and Exit** | Both |
| **While Active** | Stays active as long as the entity is in the state |

Example: while an entity is in `CarryingHeavyObject`, tag it `HeavilyEncumbered`; other
transitions then use that tag as a condition.

Every tag anywhere in the graph also appears in the **graph-level Tags panel** with Name,
Type, and current Status. Read a tag two ways: **inside** the state machine via a Tag-type
Transition Condition, or **outside** it from Swift or a Script Graph.

## Worked shape — a locomotion graph

1. Two **Animation Clip** Source nodes → Walk and Run.
2. A **Blend 1D** Modifier taking both. It opens an embedded **Blend Space** grid; place
   Walk at the low end of the axis, Run at the high end. It needs **at least two samples**;
   samples can be added, removed, renamed, or repositioned any time.
3. A graph-level **Float** Input named `Speed` wired to the Blend 1D blend parameter. As
   Speed rises, the node crossfades Walk → Run.
4. A **State Machine** with Idle / Walk / Run. Idle sources a standing clip directly; Walk
   and Run both route through the Blend 1D node. Transitions Idle→Walk and Walk→Run each
   carry a **Float** condition on `Speed`, with a small threshold and a higher one — so
   state advances in step with the same value driving the blend.
5. State machine output → **Final Pose**.
6. On the Run state, an **Internal** Tag `IsSprinting` set to **OnEnter**.

## Assigning it to an entity

Hierarchy → select the character → Inspector → **Add Component → Animation Graph** (listed
under the **Animation** heading alongside Animation Library and Skeleton Debug) → bind the
graph asset.

> **Confirm the component's bound graph shares the same Skeleton Definition as the
> character's rig. A mismatch here is the single most common reason a correctly wired graph
> produces no visible motion** — the graph's clip and pose nodes resolve joints against
> whichever skeleton the *graph* declares.

## Three preview surfaces, three questions

| Surface | Answers |
| --- | --- |
| **Animation Graph editor's Preview Viewport** | Real-time feedback while wiring nodes or adjusting a threshold |
| **Preview Tab** (shared by all asset types) | How the character looks, with its own camera and lighting environment, independent of the graph editor |
| **Simulate Tab** | Behavior **over time** — Play / Pause / Restart plus Playback Speed from 1/10× to 10×. Scrub the `Speed` input here to confirm the blend and transitions before touching gameplay |

Also: in the Animation Graph, **Debug Graph → Play** animates the connectors as the entity
enters and exits states, and pulses dots next to tag names in the Tags panel as they
activate.

## Driving it from a Script Graph

Everything above lives inside the Animation Graph editor. Making a Trigger input or a Tag
respond to *gameplay* requires a **Script Graph** — a second, separate graph type.

Authoring one produces a `ScriptingComponent` (the editor and its JavaScript-facing API call
it `ReScriptingComponent`) that you attach alongside the Animation Graph component.

> **RCP links `RealityKitScripting` automatically. A plain RealityKit app project must link
> it manually** so its `ScriptingSystem` can execute `ScriptingComponent` instances at
> runtime.

A Script Graph starts from an **Events** node — Collision, Input — then reaches into the
entity's components via the **Component** category: **Get Component** retrieves the Animation
Graph component, **Set Component** writes back, **Has Component** checks before use. For the
locomotion graph: start from a Collision event, Get Component on the character, then either
read whether `IsSprinting` is active or set a `Jump` Trigger input.

## Observing from Swift

`AnimationGraphComponent` is the same component the Add Component menu and Script Graph's Get
Component node work with. Attach with `init(graph:)` or read it back:

```swift
if let animationGraph = character.components[AnimationGraphComponent.self] {
    let isSprinting = animationGraph.activeTags.contains { $0.name == "IsSprinting" }
    if isSprinting {
        logger.info("Character is sprinting")
    }
}
```

- **`activeTags`** — every Tag that fired or was active during the graph's most recent
  evaluation tick.
- **`activeStateMachineNodes`** — each State Machine node's current and previous state IDs,
  for debugging.

**Both are read-only views onto the last tick.** Changing what a character animates still
means editing the graph or driving its Inputs and Tags from the editor or a Script Graph.

### The simpler clip-playback surface

If your app plays clips directly, independent of any Animation Graph:

- `AnimationLibraryComponent` — the entity's named animation resources.
- `playAnimation(_:transitionDuration:startsPaused:)` — returns an
  `AnimationPlaybackController`.
- `AnimationEvents` — playback notifications through Combine.
- `BindTarget` — identifies an animatable property, e.g. `BindTarget.jointTransforms` or
  `BindTarget.parameter(_:)`.

> These act on individual clips. **Apple's documentation does not specify how they behave
> when combined with an Animation Graph's state machine, Tags, or Inputs on the same
> entity** — test that combination before relying on it.
