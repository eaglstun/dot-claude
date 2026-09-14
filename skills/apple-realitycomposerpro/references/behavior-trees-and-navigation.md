---
semantic_id: "8uxPZ85y98lUaRaxNaPn41B7AnZKgAAO"
related_ids:
  - "8sZP52pzF57GdRrgcqst0Xj4CnZioAAH"
  - "sOQJZW4xNQ3wybPiOGHnsNXbInZa8AAF"
---
# Behavior Trees and navigation meshes — NPC movement and decision-making

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/defining-a-behavior-with-behavior-trees>
- <https://developer.apple.com/documentation/realitycomposerpro/building-a-navmesh-in-reality-composer-pro>

Fetched: 2026-08-19

---

# Behavior Trees

A Behavior Tree is a **prioritized hierarchy of behavior** for an entity — which path the
duck takes across the pond. When traversal reaches the last leaf node the tree **resets to
the Root**, though you can modify that.

## Behavior Trees are not the decision layer

> **A Behavior Tree defines how an entity behaves. By itself it contains no autonomous
> decision-making.** The decision logic comes from outside: Swift app code, a Script Graph,
> your own state machine, or an LLM choosing which behaviors to run.

Whatever drives it, you drive a Behavior Tree by **setting the parameter values its nodes
understand**. The decision layer picks *what* behavior; the tree defines the *steps*.

## Create and attach

Project Browser → **`+` → Animation → Behavior Tree** (or Control-click a folder → **New →
Animation → Behavior Tree**) → double-click to open in the Behavior Tree editor.

Attach: select the entity → Inspector → **Add Component → Behavior Tree** → under **Behavior
Trees** click **`+`** to assign one or more trees → set **Default Tree**.

There is also a **Behavior Tree Parameters** tab (**Tab → New Tab**).

## How nodes report

Every node returns one of three statuses when traversed:

| Status | Meaning |
| --- | --- |
| **success** (`true`) | Completed |
| **failure** (`false`) | Did not complete |
| **running** | Still executing — the tree waits before advancing |

Other nodes use a node's **Return Value** to decide how traversal continues.

**Every node type**, regardless of category, has modifiers that let you:

- Apply a **precondition** on entering — if it fails, the tree **skips** the node.
- **Loop** the node a fixed number of times, or until a condition is met.
- **Modify the returned status** — force success, force failure, or **invert** it.

## The three categories

**Root** — the first node in a new tree, the starting point for traversal. **Exactly one per
tree.**

**Action** — directly affect the entity or scene:

| Node | Does |
| --- | --- |
| **Action** | Sends entity action events on enter/update/return. Write custom actions in Swift with different event handlers |
| **Move To** | Straight line to a position, with direction and speed |
| **Move on Navigation Mesh** | Navigates to a position along a navmesh, routing around obstacles |
| **Rotate to Face** | Rotates around the y-axis to face a position |
| **Wait** | Pauses for a duration or until a condition, optionally randomized |
| **Parameter Setter** | Assigns values to parameters that other graphs consume — **this is how a tree triggers an Animation Graph state or plays audio** |
| **Set Tree** | Exits this tree and starts another. Use it to build interconnected collections of trees, each controlling a different behavior |
| **Debug** | Writes custom text to the **Console** |
| **NoOp** | Nothing but its own modifier processing |

**Composite** — control how children are traversed:

| Node | Logic |
| --- | --- |
| **Sequence** | **AND.** Children left to right; as soon as one fails, the Sequence exits and the tree advances |
| **Selector** | **OR.** Children left to right; moves past each failure until one returns `true`, then finishes. Returns `false` only if **all** children fail |
| **Parallel** | All children run **concurrently** — all subtrees update in the same frame |

Sequence and Selector can both **randomize their children**: at runtime the tree reshuffles
the children each time it enters the node, then visits them left-to-right in the new order.

**Parallel** success is configurable: after **one** child succeeds, after ***n*** children
succeed, or by a **Success Percentage** field setting the minimum share of children that
must succeed. On success, Parallel **interrupts and stops currently running children
immediately**. Use it for simultaneous actions — turning and moving at once.

---

# Navigation meshes

A navmesh represents a scene's navigable surfaces, so pathfinding for AI-driven NPCs doesn't
have to reason about raw geometry.

## Named Layers file — do this first

Create a **Navigation Named Layers** file to store index→name mappings; Navigation Mesh and
Navigation components then reference entries **by name**. **On export to a `.reality` file
the indexes match the structs in Swift code**, so you can reference them from code.

Project Browser → Control-click → new file → **Navigation Named Layers**. Expand **Layers**,
**Areas**, and **Flags** to add, remove, and rename entries.

## Create a navmesh

Hierarchy → Control-click a scene entity (e.g. `World`) → **Add Component → Navigation
Mesh** → in the Inspector click **`+`** to add a mesh → assign the Named Layers file, which
populates the Layers / Areas / Flags dropdowns → add a **Layer** identifying this mesh.
Entities reference that layer to access the map of available paths.

> **If Navigation Mesh Layer is left blank, entities default to the first mesh used in the
> scene.**

Configure Shapes, Off Mesh Connections, Generation Parameters, and Tags, then click
**Generate Navigation Mesh**.

**Batch generation:** Inspector → **Lighting Tools** (the shaded circle icon) → Baking
options → **Selected Navigation Mesh** → pick one or choose **All** → **Generate Navigation
Mesh**. No need to open each component.

## Shapes — what geometry is covered

By default the shape encompasses the whole scene; drag the bounding box to restrict it.

**Shape selection only includes entities at or below the component's hierarchy level.**

```
World
- Entity 1
- Entity 2
  - Entity 3
```

Put the component on **Entity 2** and it covers Entity 2 and Entity 3 only. Put it on
**World** and it covers everything.

## Off-mesh connections

Link points the normal geometry doesn't connect — a jump, a ladder, a gap only certain
entities can cross. Click **`+`**, then position with the Move tool. Unlimited, and each can
be **named** so other components and graphs reference it — e.g. to trigger a specific
animation while an entity traverses it.

## Generation parameters

**Basic** — the ones you actually tune:

| Parameter | Controls |
| --- | --- |
| **Cell Size** / **Cell Height** | World-unit sampling resolution of the source geometry |
| **Character Height** | Minimum floor-to-ceiling height for a floor to count as walkable |
| **Walkable Climb Height** | Maximum ledge height still considered walkable |
| **Walkable Slope Angle** | Maximum walkable slope — **lower it to keep the mesh off steep terrain** |
| **Character Radius** | Erodes the walkable area away from obstructions — **raise it to support larger characters** |

**Advanced** — Max Edge Length, Max Simplification Error, Min Cells per Region (smallest
isolated island allowed), Min Cells to Merge Regions, Detail Sample Distance, Detail Sample
Max Error, Max Vertices per Polygon.

**Partition Method** — the height-field partitioning algorithm:

| Method | Trade-off |
| --- | --- |
| **Watershed** *(default)* | Best meshes |
| **Monotone** | Fastest meshes |
| **Layer** | Fast, and handles open regions better than Monotone |

## Tags — Areas and Flags

Two kinds, both used to control *who* may traverse *what*:

- **Area** — assigns an area type to a region, which entities use when computing paths.
  **Areas can carry a cost.**
- **Flag** — a binary tag entities use to selectively include or exclude areas.

Add with **`+`**, then position the selection area with the Move tool over the region to tag;
adjust **Position**, **Height**, and **Radius**. Unlimited tags per region.

**Use a Navigation Component** on the entity to assign that entity's per-area traversal
costs and which flags it includes or ignores. That's the pairing: the *mesh* labels regions,
the *entity's* Navigation Component decides what those labels mean to it.

> Apple's pages link a `NavigationMeshLayers` article for the details on adding Layer, Area,
> and Flag tags. **That page is not published — it 404s as of this fetch.**
