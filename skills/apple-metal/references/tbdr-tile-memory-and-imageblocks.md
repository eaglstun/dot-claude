---
semantic_id: "wnt_Tn4JqBXb450Hpoe4Bts1WB4LsAAI"
related_ids:
  - "3nN0TN88O9zsrjAZitSwI9JwW5qMsAAO"
  - "--0lTj89Q9OCaLOHo46M8mo2H04CkAAH"
---

# TBDR: tile memory, imageblocks, tile shaders, raster order groups

Sources:

- Apple DocC article, "Tailor your apps for Apple GPUs and tile-based deferred rendering"
  <https://developer.apple.com/documentation/metal/tailor-your-apps-for-apple-gpus-and-tile-based-deferred-rendering>
  (fetched via the DocC JSON endpoint, 2026-08-19)
- See-also from that page: "Porting your Metal code to Apple silicon"
  <https://developer.apple.com/documentation/apple-silicon/porting-your-metal-code-to-apple-silicon>

**Provenance:** everything below is **[Apple doc]** unless marked otherwise. Apple's article
gives **no numbers at all** — every bandwidth, latency, and energy claim in it is
comparative ("many times faster", "significantly less"). Nothing here has been measured;
re-measure before budgeting against any of it.

Fetched: 2026-08-19

**Boundary:** the _compute-kernel_ reading of this same article lives in
`apple-silicon/references/apple-gpu-architecture-for-compute.md`, which correctly notes
that a pure-compute backend touches almost none of this machinery. **This card is the
render half** — the part that a hand-rolled renderer actually stands on.

## The pipeline, and why it changes what's expensive

An **immediate-mode (IM) GPU** fully processes each primitive whether or not it ends up
visible. A **TBDR GPU** does not:

1. Split the render destination into a grid of **tiles**.
2. Process **all** the geometry of the render pass at once, per tile, in parallel across
   cores — everything that intersects a given tile is considered together.
3. **Discard occluded primitives** before shading them.
4. Generate fragments only from the surviving visible primitives, run the fragment shader,
   and write results into **tile memory** — fast, temporary, on-GPU storage.
5. When the tile is finished, write the final result out to device memory.

Two consequences worth internalizing:

- **Hidden-surface removal is free and automatic.** The GPU defers fragment shading until
  it has seen all geometry for the tile, so overdraw of _opaque_ geometry costs vertex work
  and not fragment work. This is why a depth prepass — mandatory on IM GPUs — is a much
  weaker win here, and why the prepass in `depth-prepass-occludes-virtual-content.md` earns
  its place for _occlusion correctness against real-world depth_, not for saving fragment
  shading.
- **Passes overlap.** While the GPU runs the final stages of one render pass into tile
  memory, it can start the **vertex stage of a future render pass**. The two use different
  compute and memory hardware blocks, so they run in parallel. Long dependency chains
  between passes give that up.

Tile memory's advantages over device memory, as stated (no figures given):

- bandwidth **many times faster**
- access latency **many times lower**
- energy consumption **significantly less**

That, not raw FLOPs, is the lever this architecture hands you: **keep intermediate results
on-chip.**

## What A11 and later added

Starting with **A11**, Apple GPUs expose the TBDR machinery through Metal rather than only
using it internally:

- **imageblocks** — full shader-side control over tile-memory data structures
- **tile shading** — compute or fragment functions running inside a render pass
- **raster order groups** — ordered memory access from fragment shaders
- **imageblock sample coverage control** — custom MSAA resolve

A11+ also **improves fragment-discard performance**, and Apple calls out three techniques
these features simplify: **subsurface scattering, order-independent transparency, and
tile-based lighting algorithms.**

## Imageblocks

An imageblock is a **2D structure with a width, a height, and a pixel depth**, living in
high-bandwidth imageblock memory. Each pixel can hold multiple components, and **each
component is addressable as its own image slice** — e.g. three slices for albedo, specular,
and normal.

Facts that determine how you can use them:

- **Metal has always rendered to imageblocks on Apple silicon.** What A11 added is _your_
  control over the layout. Your existing code already creates imageblocks matching the
  render attachment formats, implicitly.
- **Imageblocks you define yourself can be far more sophisticated than attachment-derived
  ones** — additional channels, arrays, nested structures — and you can reuse one imageblock
  for different purposes across phases of a computation.
- **They persist for the lifetime of a tile, across draws and dispatches.** This is the
  property that makes mixing render and compute in one pass possible: both stages address
  the same local memory.
- **Access scope differs by function type.** In a **fragment** shader, the current fragment
  sees **only the imageblock data at its own position in the tile**. In a **compute**
  function, a thread can access **all** of the imageblock data.
- **Imageblock vs. threadgroup memory:** threadgroup memory suits _unstructured_ data;
  an imageblock suits _image_ data.

### The read/write rule that catches people

- **With attachments**, load and store actions still read and write tile memory for you —
  the familiar path.
- **With explicit imageblocks, use a compute function to explicitly read and write device
  memory.** The GPU may still flush tile memory to system memory automatically as an
  efficient block transfer that exploits the memory hardware, but you don't get the
  attachment machinery for free.

## Tile shaders

**Tile shaders are compute or fragment functions that execute as part of a render pass**,
computing into tile memory that persists on the GPU between passes.

The problem they solve: traditional GPUs separate render and compute into distinct passes
that can't talk directly, so apps round-trip intermediate results through device memory —
sometimes many times in a multiphase algorithm. Tile shading collapses that. **Rendering
and compute in one render pass, sharing local memory, with no intermediate store to device
memory.**

Any algorithm in your renderer currently structured as _render → store texture → compute →
load texture → render_ is a candidate.

## Raster order groups

Metal guarantees the GPU **blends in draw-call order**, giving the illusion of sequential
rendering. But the fragment shaders themselves run **concurrently on their own threads** —
the shader for a rear triangle may not execute before the one for the front triangle
overlapping it. Any shader that needs another triangle's shader result (a custom blend
function reading what's already there) has a **read-modify-write race**.

**Raster order groups synchronize threads targeting the same pixel coordinates** — and the
same _sample_, if per-sample shading is on.

Mechanically: **annotate pointers to memory with an attribute qualifier.** Shaders
accessing pixels through those pointers proceed in **per-pixel submission order**; the
hardware makes the current thread wait for any older overlapping fragment threads to
finish.

### Multiple groups, and the single-pass deferred shading win

Recent Apple GPUs extend raster order groups to **synchronize individual channels of an
imageblock and threadgroup memory**, and to support **multiple order groups** — finer
granularity, so threads wait less often.

The worked example Apple gives is **deferred shading**, which is a lighting technique
unrelated to TBDR despite the shared word "deferred". Traditionally two phases:

1. Fill a **g-buffer**, producing multiple textures.
2. Render light volumes, shading from those textures.

That's bandwidth-heavy: phase 1 writes textures to device memory, phase 2 reads them back.
**Keep the g-buffer in tile-sized chunks so it stays in local imageblock memory, and use
multiple order groups to coalesce both phases into one pass** — the intermediate textures
disappear.

Why _multiple_ groups specifically: with a single ordering domain, a thread handling a
secondary light waits for all previous threads to complete before it can begin, forcing
serial execution **even when the memory operations don't conflict**. Split them:

| Group | Contents                                          |
| ----- | ------------------------------------------------- |
| **1** | the three g-buffer fields — albedo, normal, depth |
| **2** | the accumulated lighting result                   |

Apple GPUs order the two groups separately, so **outstanding writes into group 2 don't
block reads from group 1**. The nonconflicting reads run concurrently; the two threads
synchronize only at the end, to accumulate the lights.

Also simplified by raster order groups, per Apple: **order-independent transparency,
dual-layer geometry buffers, and voxelization.**

## MSAA and imageblock sample coverage control

MSAA improves primitive edges by taking **multiple depth and color samples per pixel** —
with one sample position per pixel, a triangle either covers it or doesn't, which is where
jagged edges at certain angles come from. 4× MSAA samples each pixel at four positions and
averages them.

**Apple's implementation tracks whether each pixel contains a primitive's edge, and runs
per-sample blending only when it has to.** If another primitive covers all the samples in a
pixel, the GPU blends **once for the whole pixel**.

More precisely, the hardware tracks the number of **unique samples (colors)** per pixel and
updates it as new primitives render:

- Take a pixel holding the edges of two overlapping triangles, whose sample positions
  represent **three unique colors**.
- **Pre-A11 GPUs blend all three covered samples.**
- **A11 and later blend twice**, because two of the samples share a color.
- If an opaque triangle then covers every sample, the GPU **merges the three colors into
  one** and represents the pixel by a single color.

**You can implement a custom resolve by modifying the sample coverage data from a tile
shader.** Apple's example: a scene with separate opaque and translucent phases, where a tile
shader **resolves the opaque geometry's sample data before the translucent geometry
blends** — working entirely in local memory, as part of the opaque phase.

## What to take away for a hand-rolled renderer

1. **Overdraw of opaque geometry is cheap; bandwidth is not.** Optimize for staying on-chip,
   not for minimizing fragments.
2. **Every device-memory round trip between passes is a target.** Tile shaders plus explicit
   imageblocks are the mechanism for deleting them.
3. **Don't reach for raster order groups until you have an actual read-modify-write race on
   the same pixel.** They cost ordering, and a single coarse group can serialize threads
   whose accesses never conflict — split into multiple groups when that happens.
4. **`discard` is cheaper on A11+ than the old lore says**, but Apple gives no figure —
   measure it.
5. **Nothing on this page is a number.** Apple's comparisons are all qualitative. Anything
   you budget against must come from Instruments on your own hardware — see
   `apple-silicon/references/instruments-gpu-profiling.md` and `gpu-counters-and-timestamps.md`.
