---
semantic_id: "6O1LSWY3F52W4Zgiu6uP8kB7BidC4AAH"
related_ids:
  - "wO5ibXM3vZ3E7ZukiCPf8l17AiOK0AAL"
  - "sMDBZWYxNZ_2ybJjvmGvclTzEkda4AAH"
---
# Particles: the Particle Emitter component and Compute Graph

Source (Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/realitycomposerpro/creating-particle-systems-in-reality-composer-pro>
- <https://developer.apple.com/documentation/realitycomposerpro/introducing-compute-graph>
- <https://developer.apple.com/documentation/realitycomposerpro/building-a-working-compute-graph-example>
- <https://developer.apple.com/documentation/computegraph> and its namespace pages
  (`element`, `emitter`, `force`, `initialize`, `module`, `output`, `graph`, `group`,
  `texture`, `random`), plus `computegraphsimulation` and `elementspawnparameters`

Fetched: 2026-08-19

## Which one to use

**Particle Emitter** is a component with a fixed property set — the fast path for campfires,
explosions, rain. **Compute Graph** is a general-purpose GPU compute framework you author as
a node graph; particles are its headline use, not its limit.

Reach for Compute Graph when you need:

- Per-particle logic no emitter property exposes — sampling a texture to drive color,
  custom physics forces, terminating a particle on a condition you compute.
- A GPU compute pipeline that isn't particles at all.
- Explicit control over what runs in each stage rather than a fixed emitter property set.

---

# Particle Emitter component

Add a Particle Emitter to any entity: Inspector → **Add Component** → Particle Emitter
(type "particle" in the search box). Properties split across two Inspector tabs.

**Emitter tab** — the shape and geometry of the emitter itself:

- **Emitting** (on/off) and **Simulation State** (set to Play) — with both on, the emitter
  runs live in the Viewport while you edit. **Stop the simulation before moving the entity
  or editing anything outside the emitter.**
- **Loop** — emit continuously. When off, **Emission Duration** (seconds) governs, and
  **Emission Duration Variation** adds ± a random amount up to that value.
- **Shape** — sphere, cone, plane, torus, and others. **The emitter shape is independent of
  the entity shape** — a sphere entity can emit in a cone. Some properties are
  shape-specific (Torus Radius only applies to a Torus).
- **Shape Size** (meters) — the size of the *spawn region*, not of the particles.
- **Emission Direction** — used when `birthDirection` is World or Local. Default (0, 1, 0).
- **Birth Location** — emit from the surface, or from the vertices of the surface.
- **Inherit Transformation** — whether the entity transform also affects particles.
- **Field Simulation Space** — **Local**: particles move with the entity. **Global**:
  particles trail behind its movement.
- **Spawning Enabled** — turns on Secondary particles.

**Particles tab** — a **Main** / **Secondary** selector, each with its own full set.
Secondary particles are spawned by Main particles when a Main particle expires. Common
properties: **Life Span** (seconds), **Image**, **Size** (default `0.02`), **Start Color A**,
**End Color A** — the particle lerps start → end over its lifetime.

Full property reference: `ParticleEmitterComponent` and
`ParticleEmitterComponent.ParticleEmitter`.

> **Version note.** The preset menu (Fireworks, Impact, Magic, Rain, Snow, Sparks) was
> **missing in RCP 3 through Beta 3** and **restored in Beta 4** (165089607). On an earlier
> build, configure manually or apply `ParticleEmitterComponent.Presets` in code.

---

# Compute Graph

Create: Project Browser → **`+` → Compute Graph** (or Control-click a folder → **New →
Compute Graph**), name it, double-click to open. Attach: select an entity → Inspector →
**Add Component → Compute Simulation** → pick the graph. **Attach it to the entity that
generates the effect.**

## The four-stage run order

The default node has four stages that run **top to bottom**: **Emission → Initialization →
Simulation → Output**. A **Texture** stage type also exists for pipelines that generate
textures rather than driving particles.

Each stage starts with a **Constants** node injecting fixed values into that stage — the
Simulation stage's Constants is where capacity count and the loop toggle live; the Output
stage's holds the particle material properties.

Add nodes inside a stage with the node's own **`+`**. **Nodes within a stage run in the
order they appear**; reorder with the up/down arrows when a later node depends on an
earlier one. A `force::gravity` feeding `element_integrate` must run before a termination
check that reads the resulting position.

**Every parameter is static until you wire a node into its port.** There is no "dynamic
mode" toggle the way some tools have.

## Node namespaces

`element::` — read/write the current element; usable in **any** stage.

| Node | Returns |
| --- | --- |
| `position` `velocity` `size` `color` | Current per-particle values |
| `age` | Elapsed seconds |
| `ageOverLifetime` | Age normalized 0–1 — use this for anything that should animate consistently regardless of lifetime |
| `lifetime` | Total configured lifetime, seconds |
| `index` | Element index — deterministic per-particle variation |
| `terminate` | Ends the particle immediately when its boolean input is true |

`emitter::` — emission stage.

| Node | Behavior |
| --- | --- |
| `continuous` | Fixed rate |
| `burst` | One burst when the system spawns |
| `periodicBurst` | Repeating burst on an interval — periodic sparks vs. a smooth stream |
| `setGroup` | Assigns spawned particles to an element group so other nodes can target a subset |

`initialize::` — `sourceElementIndex` (the source particle's index when spawning from
another particle's event) and `spawnIndex` (sequential index of the spawn from that
emitter; for EventSource/CPU spawns, the index within the current spawn request).

`module::` — mutate per-particle state directly:
`setPosition` / `addPosition`, `setVelocity` / `addVelocity`, `setColor`, `setAlpha`,
`setSize` (meters), `setLifetime` (seconds). Plus a `module::debug` namespace.

`force::` — physics forces meant to feed an integration step:
`gravity`, `drag` (linear, slows over time), `noise` (organic motion — flickering flame,
drifting smoke), `twist` (around a vertical axis through a given origin, for vortices),
`add` (a constant force vector).

`output::` — **shape what's rendered without touching the underlying element data**, so
these are presentation-only and don't affect simulation physics:
`setColor`, `setOpacity`, `setScale`, `setSize`, `setOutputPosition`, `outputPosition`,
`outputIndex`, `fadeInOut` (usually driven by `element::ageOverLifetime`), `growIn`,
`setUVTransform`, and `setUV2` … `setUV7` for multi-texture sampling per particle.

`graph::` — any stage: `age` (graph age, seconds), `deltaTime`, `localToWorld`,
`worldToLocal`.

`group::` — requires a simulation stage configured as `strips` or `grouped`:
`elementIndexInGroup`, `elementActiveInGroup`, `elementMaximumInGroup`,
`groupIndexInSystem`, `maximumGroupsInSystem`.

`texture::` — texture stage only: `position` (current pixel), `uv` (pixel position in
[0,1]), `setPixel`.

`random::` — pseudo-random from the graph's RNG. Every type in both precisions, each with a
plain and a `_using` (explicit seed) variant: `float_01`, `float2_01`, `float3_01`,
`float4_01`, the `half*_01` equivalents, `integer`, and `seed` (reads the current seed
without incrementing). The editor's **Random (Float3)** is the one you'll reach for to keep
a burst from looking identical.

Standalone functions: `element_integrate`, `orient_to_velocity` (sets `axisY` to the
velocity direction), `texture_sample`, `texture_sample1d`, `viewpoint`, plus grid/line
helpers `gridFromPoints`, `gridDebugCells`, `linesFromNeighbors`,
`filteredLinesFromNeighbors`, and `spawn_demo`.

Also in the framework: `PortReference`, `BinaryOperation`, `UnaryOperation`,
`StandardLibraryFunction`, `ElementGrouping` (`ungrouped` / `grouped` / `strips`),
`Sorting`, `AddressSpace`, `CoordinateSpace` (`local` = relative to the Entity, `world` =
relative to the Scene), `StripOrientation`, `Viewpoint`, `MouseParams`.

## Compute Graph Bundles

Pre-built node compositions encapsulating common patterns. Add them at **Project Settings →
Compute Graph Bundle → `+`** → pick the bundle file; repeat for more. Once added, a bundle's
nodes appear in the insertion menu like any other — drop in a known-good spawn pattern or
force combination and customize locally instead of rebuilding it node by node.

## Worked example — falling snow colored from a gradient

1. **Emission** — `continuous` for steady snowfall, plus a `burst` so the effect doesn't
   start sparse.
2. **Initialization** — **Decompose float3** extracts each particle's spawn *x*; a `*` and a
   `+` rescale it into the texture's 0–1 sample space; **Sample Texture 2D** reads a
   six-color horizontal gradient. Result: snow colorized left-to-right across the emission
   volume from **one texture lookup**, no per-particle color logic.
3. **Simulation** — standard integration with gravity and drag updating position and
   velocity each tick.
4. **Output** — `fadeInOut`, rendered as billboard quads. The color sampled at
   initialization persists through the fade.

Swap the gradient PNG in the Sample Texture 2D node to restyle the whole effect without
touching a node.

## Optimization

- **Size capacity to the effect.** Roughly `emission rate × lifetime` plus burst headroom.
  Capacity far above what the effect uses is wasted GPU memory.
- **Prefer a gradient texture over computed gradient math.** Cheaper than equivalent shader
  math *and* an artist can iterate on it without opening the graph.
- **Keep Output-stage work presentation-only.** Output nodes run on every live particle
  every time the stage executes — push expensive computation into Simulation, or into
  Initialization if it never needs to change.
- **Use `element::terminate` deliberately.** Precise termination keeps the live particle
  count — and therefore GPU cost — closer to what's actually visible than a long fixed
  lifetime does.

## Wiring it to gameplay

Drive gameplay-reactive behavior through a **Public Input** on the graph, set from Swift or
from a Script Graph node via Set Variable or a component write. Keep the Compute Graph
focused on simulating and rendering; gameplay logic belongs in RealityKit systems or Script
Graph, feeding the graph through its exposed interface.

## The Swift API

Three-step compilation: describe the simulation as a `GraphDefinition` (typed nodes and
edges) → assemble into a `ComputeGraphAssembly` (resolves buffer/uniform/texture layout) →
compile into `ComputeGraphPipelines` (GPU shader code). **One set of pipelines can back
multiple concurrent `ComputeGraphSimulation` instances.** `Library` and
`SyntheticNodeLibrary` let you supply custom MSL functions as node definitions alongside
`ComputeGraphBuiltIns`.

`ComputeGraphSimulation` (`final class`) drives runtime execution:

- `init(pipelines:)` / `init(pipelines:commandQueue:)`
- **`advance(_:)`** — call each frame with `AdvanceParams` carrying the time delta, a Metal
  command buffer, a compute encoder, and optional world-space transforms. It encodes every
  simulation-stage dispatch into that buffer and encoder.
- Bind resources **before the first advance**: `setBuffer(…)`, `setBuffers(_:bufferOffsets:)`,
  `setTexture(_:at:)`, `setTextures(_:)`, `setUniform(_:named:)`, `setUniformValue(_:at:)`,
  `setUniformData(_:at:)`, `modifyUniforms(_:)` (read/write CPU access to the whole uniform
  buffer), `graphUniforms` (read-only copy).
- `spawn(elements:in:using:)` injects elements programmatically with `ElementSpawnParameters`.
- `fastForward()` / `fastForward(stepCount:stepDeltaTime:)`, `reset(encoder:)`,
  `resetRandomSeeds(using:)`, `simulationRate`, `setOutputEnabled(_:enabled:)` /
  `isOutputEnabled(_:)`, `addUserResource(_:)` / `setUserResources(_:)` for encoder
  residency.

```swift
let params = ElementSpawnParameters(
    position: SIMD3<Float>(0, 1, 0),
    velocity: SIMD3<Float>(0, -1, 0),
    size: SIMD2<Float>(0.02, 0.02),
    color: SIMD4<Float>(1, 0.5, 0, 1),
    lifetime: 2.0
)
```

These become the **initial** values entering the Initialization stage, which may read or
overwrite them.

At the RealityKit level: a `ComputeNodeGraph` attaches to an `Entity` through the Compute
Simulation component.

> **Known issue (all RCP 3 betas so far, 177674901):** `ComputeGraphComponent` instances
> stored in a `.reality` file **do not render** when the app loads that file.
