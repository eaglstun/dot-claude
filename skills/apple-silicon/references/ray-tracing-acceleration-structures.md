---
semantic_id: "2vv9gs8_V7auhb-4462DgDi8Wy3KoAAC"
related_ids:
  - "2r0NQtMtUhCqaTuFKuiN3n7-Sz_DwAAH"
  - "3P98iM8kgN72r6S4Xs_jE2J1XwQb4AAL"
---

# Metal ray tracing — acceleration structures, intersectors, intersection functions

Sources (Apple DocC JSON, `https://developer.apple.com/tutorials/data/documentation/<path>.json`):

- `metal/accelerating-ray-tracing-using-metal` · `metal/ray-tracing-with-acceleration-structures`
- `metal/improving-ray-tracing-data-access-using-per-primitive-data`
- `metal/control-the-ray-tracing-process-using-intersection-queries`
- `metal/mtlaccelerationstructure` + all descriptor/geometry/instance subclasses
- `metal/mtlaccelerationstructurecommandencoder` (`build`, `refit`, `copyAndCompact`, `writeCompactedSize`)
- `metal/mtlaccelerationstructureusage` · `metal/mtlintersectionfunctiontable` · `metal/mtllinkedfunctions`
- `metal/mtldevice/supportsraytracing` + `/supportsraytracingfromrender` · `metal/mtlgpufamily`
- `metal/mtl4*acceleration*` · `metalperformanceshaders/mpsrayintersector` _(deprecated)_

Specs and tables (the MSL side has **no DocC pages**, so availability comes from these):

- Metal Feature Set Tables PDF, revision **2026-05-21**
- Metal Shading Language Specification **v4.1, 2026-06-04**
- Toolchain header `Metal.xctoolchain/usr/metal/32023/lib/clang/32023.883/include/metal/metal_raytracing`
  (Apple metal 32023.883, MacOSX 26.5 SDK) — the authoritative MSL declarations, which
  **disagree with the spec in places** (§4).

Video: [WWDC20/10012](https://developer.apple.com/videos/play/wwdc2020/10012/) ·
[WWDC21/10149](https://developer.apple.com/videos/play/wwdc2021/10149/) ·
[WWDC22/10105](https://developer.apple.com/videos/play/wwdc2022/10105/) ·
[WWDC23/10128](https://developer.apple.com/videos/play/wwdc2023/10128/) ·
[Tech Talk 111375 — Explore GPU advancements in M3 and A17 Pro](https://developer.apple.com/videos/play/tech-talks/111375/) ·
[WWDC25/211](https://developer.apple.com/videos/play/wwdc2025/211/)

Fetched: 2026-08-19

## The model in one pass

Apple's framing, verbatim:

> _"Intersectors work with compute kernels on all GPUs, and with render shaders only on Apple
> silicon GPUs. Alternatively, your app can use intersection queries on non-Apple GPUs, or for
> porting code from other graphics APIs."_

**CPU, on geometry change:** fill geometry descriptors → wrap in a _primitive_ (bottom-level)
descriptor → ask `device.accelerationStructureSizes(descriptor:)` → allocate structure +
scratch buffer → repeat for an _instance_ (top-level) descriptor.

**GPU, build pass:** `makeAccelerationStructureCommandEncoder()` → `build(...)`. Builds run
entirely on the GPU timeline — no CPU sync point.

**GPU, trace pass:** bind the top-level structure (`setAccelerationStructure(_:bufferIndex:)`),
plus an intersection function table if you use custom intersection functions, plus
`useResource`/`useHeap` for everything the structure references. In MSL, build a `ray`, build an
`intersector<tags...>`, call `intersect()`.

Two shading-side styles, and the choice matters for performance (§8):

- **`intersector<>`** — Metal drives traversal; non-opaque and procedural hits call _back into_
  your `[[intersection(...)]]` functions via a function table.
- **`intersection_query<>`** — you drive traversal yourself with `next()` in a loop and commit
  candidates inline. No function table, no linked functions, no pipeline changes.

---

## 1. Acceleration structures

```swift
protocol MTLAccelerationStructure : MTLResource     // iOS 14 / macOS 11 / tvOS 16 / visionOS 1
var size: Int
var gpuResourceID: MTLResourceID
```

> _"Metal provides acceleration structures with a two-level hierarchy. The bottom layer consists
> of primitive acceleration structures, which instance acceleration structures in the top level
> reference."_

| Descriptor                                              | Purpose                                            |
| ------------------------------------------------------- | -------------------------------------------------- |
| `MTLAccelerationStructureTriangleGeometryDescriptor`    | a list of triangles                                |
| `MTLAccelerationStructureBoundingBoxGeometryDescriptor` | a list of AABBs (procedural geometry)              |
| `MTLAccelerationStructureCurveGeometryDescriptor`       | curves — iOS 17 / macOS 14                         |
| `…Motion{Triangle,BoundingBox,Curve}GeometryDescriptor` | keyframed motion — iOS 15 / macOS 12               |
| `MTLPrimitiveAccelerationStructureDescriptor`           | **bottom level** — a union of geometry descriptors |
| `MTLInstanceAccelerationStructureDescriptor`            | **top level** — instances of primitive structures  |
| `MTLIndirectInstanceAccelerationStructureDescriptor`    | GPU-populated instances — iOS 17 / macOS 14        |

### Sizing and allocation

```swift
struct MTLAccelerationStructureSizes {
    var accelerationStructureSize: Int
    var buildScratchBufferSize: Int
    var refitScratchBufferSize: Int
}

func accelerationStructureSizes(descriptor:) -> MTLAccelerationStructureSizes
func makeAccelerationStructure(descriptor:) -> (any MTLAccelerationStructure)?
func makeAccelerationStructure(size:) -> (any MTLAccelerationStructure)?
// heap-backed, iOS 16 / macOS 13:
func heapAccelerationStructureSizeAndAlign(descriptor:) -> MTLSizeAndAlign
```

_Availability note, verified rather than assumed:_ `MTLAccelerationStructureSizes`'s DocC block
carries **no `introducedAt` on any platform**. It's a plain C struct in `MTLDevice.h` with no
annotation — the _method_ is `API_AVAILABLE(macos(11.0), ios(14.0), tvos(16.0))`. Missing
metadata, not inherited metadata.

### The two flags that decide whether your shader gets called

On every geometry descriptor:

- **`opaque`** — verbatim: _"If you specify that triangle geometry is opaque, Metal skips the
  intersection function and processes any intersection as a hit. If you are using bounding box
  geometry, Metal calls your intersection function, passing a Boolean value that indicates that
  the bounding box that the ray intersected with is opaque."_ So `opaque` is a real fast path for
  triangles and merely an _input_ for AABBs.
- **`allowDuplicateIntersectionFunctionInvocation`** — barely documented, but the MSL spec
  explains the underlying truth: _"Intersection functions may be invoked even if the ray does not
  intersect the primitive's bounding box."_ Implementations group primitives into leaf nodes.
  **Write intersection functions that tolerate being called spuriously.**

---

## 2. Building, refitting, compacting

```swift
func build(accelerationStructure:descriptor:scratchBuffer:scratchBufferOffset:)
func refit(sourceAccelerationStructure:descriptor:destinationAccelerationStructure:
           scratchBuffer:scratchBufferOffset:options:)          // options: iOS 16 / macOS 13
func copy(sourceAccelerationStructure:destinationAccelerationStructure:)
func copyAndCompact(sourceAccelerationStructure:destinationAccelerationStructure:)
func writeCompactedSize(accelerationStructure:buffer:offset:)
```

**Synchronization is automatic for tracked resources**, verbatim: _"you can use a single encoder
to build multiple geometry acceleration structures and then build the instanced structure that
uses them."_ With untracked resources it's on you.

### Refit vs. compact — different tools, different costs

**Refit** — same topology, small motion:

> _"Refitting performs much faster than rebuilding an acceleration structure from scratch.
> However, ray-tracing performance may degrade, based on how many changes you make to the
> geometry data."_
> _"**You can't use refitting to add or remove geometry in the acceleration structure.**"_

Requires `MTLAccelerationStructureUsage.refit` at build time — **and that flag itself costs
you**: _"By default, the framework builds immutable acceleration structures for performance. When
you apply the refit option, the framework builds an acceleration structure more conservatively,
which can reduce its intersection performance."_ You pay for refit whether or not you refit.
`destinationAccelerationStructure` may be `nil` or the source to refit in place.

**Compaction** — memory only, never speed, and it costs a CPU round trip:

> _"When you first build an acceleration structure, Metal can't know exactly how much memory it
> needs, so it has to make a conservative estimate… **This is especially valuable for primitive
> acceleration structures.**"_ — WWDC23/10128

Sequence: `writeCompactedSize` → wait → read a `UInt32` → allocate ≥ that → `copyAndCompact`.
Source and destination must not overlap.

### Usage flags and their trade-offs

```swift
static var refit                    // iOS 14 / macOS 11
static var preferFastBuild          // iOS 14 / macOS 11
static var extendedLimits           // iOS 15 / macOS 12
static var preferFastIntersection   // OS 26.0, all platforms — Apple9
static var minimizeMemory           // OS 26.0, all platforms — Apple9
```

Every one of these is a trade, and Apple states each cost explicitly:

| Flag                     | Costs you                                                                |
| ------------------------ | ------------------------------------------------------------------------ |
| `refit`                  | reduced intersection performance                                         |
| `preferFastBuild`        | reduced intersection performance                                         |
| `preferFastIntersection` | increased build time                                                     |
| `minimizeMemory`         | increased build time **and** reduced intersection performance            |
| `extendedLimits`         | "can affect their performance because they support more data complexity" |

`extendedLimits` raises the caps:

|                             | Standard | Extended |
| --------------------------- | -------- | -------- |
| Primitives per primitive AS | 2²⁸      | 2³⁰      |
| Geometries per primitive AS | 2²⁴      | 2³⁰      |
| Instances per instance AS   | 2²⁴      | 2³⁰      |

Per WWDC25/211: _"Usage flags can be set per acceleration structure build, and don't have to be
the same for all acceleration structures."_ Static geometry and dynamic geometry want different
flags.

---

## 3. Instance descriptors

```swift
struct MTLAccelerationStructureInstanceDescriptor {
    var transformationMatrix: MTLPackedFloat4x3
    var options: MTLAccelerationStructureInstanceOptions   // .opaque / .nonOpaque /
                                                           // .disableTriangleCulling /
                                                           // .triangleFrontFacingWindingCounterClockwise
    var mask: UInt32
    var intersectionFunctionTableOffset: UInt32
    var accelerationStructureIndex: UInt32
}
```

Variants: `…UserIDInstanceDescriptor` (+`userID`), `…MotionInstanceDescriptor` (**no
`transformationMatrix` — transforms come from the motion buffer**), and the iOS 17
`MTLIndirectAccelerationStructureInstanceDescriptor`, which carries a GPU-writable
`accelerationStructureID: MTLResourceID` instead of an index.

**The mask is effectively 8 bits.** The field is `UInt32`, but: _"Metal reserves the top 24 bits
for future use."_ Widening it is one of the things `extendedLimits` buys (WWDC21/10149).
Shader side, `intersect(ray, as, uint mask, …)`; queries default to `~0U`.

> **Doc bug, flagged.** The _instance_ descriptor's `intersectionFunctionTableOffset` discussion
> reads _"Metal adds this property to the value in the instance's `intersectionFunctionTableOffset`"_
> — self-referential and clearly wrong. The intent is **geometry offset + instance offset**;
> WWDC25/211 confirms the two-part scheme. Apple's DirectX comparison: _"while the geometry
> offset index is generated automatically in DirectX, Metal gives you the flexibility to set this
> geometry offset yourself."_ **The exact index formula is not clearly stated anywhere in the
> docs** — verify empirically before relying on it.

---

## 4. MSL — `intersector<>`, tags, and results

MSL types have no DocC pages. Availability comes from the spec's MSL-version→OS table:
`metal2.3` = iOS 14/macOS 11, `2.4` = iOS 15/macOS 12, `3.0` = iOS 16/macOS 13, `3.1` = iOS
17/macOS 14, `3.2` = iOS 18/macOS 15 (_"Only Apple silicon supports new features in language
standard 3.2 and above"_), `4.0` = OS 26, `4.1` = OS 27.

> Spec §2.17: _"Metal 2.3 and later support ray-tracing types… only supported in a compute
> function (kernel functions) except where noted. **In Metal 2.4 and later, they are also
> supported in vertex, fragment, and tile functions.**"_

```cpp
struct ray {
    float3 origin;       float3 direction;
    float  min_distance; float  max_distance;   // default 0.0f / INFINITY
};
```

**World space outside intersection functions; object space inside them.** Spec, verbatim: _"The
ray's `origin` and `direction` field are in world space… **Within intersection functions, the
`origin` and `direction` are in object space.**"_ `max_distance` narrows as candidates commit.

Invalid rays (all yield `intersection_type::none`): INF/NaN in origin or direction, NaN
distances, `min_distance == INF`, zero-length direction, `min > max`, negative distances.
Direction need not be normalized, but must be nonzero.

### Tags

`instancing` · `triangle_data` · `world_space_data` · `primitive_motion` (2.4) ·
`instance_motion` (2.4) · `extended_limits` (2.4) · `curve_data` (3.1) · `max_levels<N>` (3.1) ·
`intersection_function_buffer` (4.0) · `user_data` (4.0).

> _"The `intersection_tags` must match in tag type and order between related uses of
> `intersection_function_table`, `intersection_result`, `intersector`, and `intersection_query`,
> or the compiler will generate an error… When calling intersection functions in an intersection
> function table, you need to ensure they use the same ordered set of tags, or else the result is
> undefined."_

`max_levels<N>` range differs by consumer: **[2,32] for `intersector`, [2,16] for
`intersection_query`.** The count includes one level for the primitive structure.

An `acceleration_structure<instancing>` binding accepts a structure declared with _more_ motion
tags — _"at the cost of the ray tracing runtime checking for primitive motion. To avoid this
cost, write two functions."_

### Traversal settings and their defaults

```cpp
intersector<triangle_data, instancing> it;
it.accept_any_intersection(bool);          // default false
it.assume_geometry_type(geometry_type);    // default triangle|bounding_box — CURVES EXCLUDED
it.force_opacity(forced_opacity);          // default none
it.set_triangle_cull_mode(...);            // default none
it.assume_identity_transforms(bool);       // default false
```

**Curves are off by default**, deliberately: _"By default, Metal assumes acceleration structure
will not contain curve geometry to improve performance. Call `assume_geometry_type` with a value
that includes `geometry_type::curve` to enable curves to be intersected."_ A curve scene that
silently misses every hit is usually this.

**Opacity precedence:** `force_opacity()` > per-instance flags > per-geometry flag. And _"If
`intersector.force_opacity()` is set to `opaque` or `non_opaque`, then
`intersector.set_opacity_cull_mode()` must be `none`. The reverse is also true… The results of
illegal combinations are undefined."_

**`accept_any_intersection(true)` is the shadow-ray setting** — _"One use of this function is
when you only need to know if one point is visible from another, such as when rendering shadows
or ambient occlusion."_

### Two places the spec is wrong

1. **The result typedef is `result_type`, not `result`.** Spec §2.17.6 calls it `::result`; only
   `result_type` exists in the header, and Apple's own samples use `result_type`.
2. **`intersect()` has no default arguments.** The spec shows `uint mask = ~0U` and
   `float time = 0.0f`; the header declares them as separate overloads.

```cpp
intersector<triangle_data, instancing>::result_type hit =
    it.intersect(r, accel, 0xFF /*mask*/, functionTable, payload);
```

`intersection_result<Tags...>` fields: `type`, `distance` (**world space**), `primitive_id`,
`geometry_id`, `primitive_data` (Metal 3), plus tag-gated `instance_id` / `user_instance_id`,
`triangle_barycentric_coord`, `triangle_front_facing`, `object_to_world_transform` /
`world_to_object_transform`, `curve_parameter`.

Barycentric reconstruction, per the spec:

```
v1*bc.x + v2*bc.y + v0*(1 - bc.x - bc.y)
```

_(`function_id` is in MSL spec 4.1 but **absent from the 32023.883 header** shipping with macOS
26.5 — expect it only on a 27-era toolchain.)_

---

## 5. Intersection functions

> Spec §5.1.6: _"Metal calls intersection functions when the shader calls `intersect()`…
> **Note that intersection functions can't start new rays.**"_

Hard restrictions: `device`/`constant` buffers only; **no texture arguments** (_"However, you can
pass a texture using an argument buffer"_); **no threadgroup memory**; **no barriers**. And:
_"Intersection functions may or may not be run in the same SIMD-group as the thread which
launched the intersection operation."_

Return: for triangles, **a bare `bool` is treated as `[[accept_intersection]]`**. Bounding-box
functions must also return `[[distance]]`, which must lie within `[min_distance, max_distance]`
and inside the box, "or the results are undefined."

`[[continue_search]]` **defaults to true**; returning false stops the search. Even true halts
immediately when `accept_any_intersection()` is set.

> **The side-effect rule.** _"**Any changes made to the ray payload take effect regardless of how
> the intersection function returns**: Rejected primitives can have side effects to memory that
> are observed by future intersection shader threads."_ Combined with spurious invocation
> (§1), a payload write in a rejected function is visible. Don't accumulate into the payload
> unconditionally.

```cpp
struct BoundingBoxIntersection {
    bool  accept   [[accept_intersection]];
    float distance [[distance]];
};

[[intersection(bounding_box, triangle_data, instancing)]]
BoundingBoxIntersection sphereIntersectionFunction(
        float3 origin              [[origin]],        // OBJECT space
        float3 direction           [[direction]],     // OBJECT space
        float  minDistance         [[min_distance]],
        float  maxDistance         [[max_distance]],
        unsigned int primitiveIndex[[primitive_id]],
        ray_data float3 &normal    [[payload]],
        device Sphere *spheres     [[buffer(0)]]) { … }
```

The **`ray_data` address space** is copy-in/copy-out: _"the system copies the payload to the
`ray_data` address space, calls the intersection function, and when the intersection function
returns, it copies the payload back out."_ No `atomic<T>` or `imageblock<T>` inside a payload.

---

## 6. Binding from the host

```swift
let linked = MTLLinkedFunctions()
linked.functions = [sphereFn]

let pDesc = MTLComputePipelineDescriptor()
pDesc.computeFunction = kernelFn
pDesc.linkedFunctions = linked
let pipeline = try device.makeComputePipelineState(descriptor: pDesc, options: [], reflection: nil)

let tblDesc = MTLIntersectionFunctionTableDescriptor()
tblDesc.functionCount = 1
let table = pipeline.makeIntersectionFunctionTable(descriptor: tblDesc)!
table.setFunction(pipeline.functionHandle(function: sphereFn), index: 0)
table.setBuffer(sphereBuffer, offset: 0, index: 0)   // becomes [[buffer(0)]] in the function
```

> _"**If you use the same ray-tracing functions with more than one pipeline, make a separate
> table for each.**"_

---

## 7. Where it runs, and on what

|                   | Compute                                    | Render (vertex/fragment/tile)                  |
| ----------------- | ------------------------------------------ | ---------------------------------------------- |
| MSL               | **2.3** — iOS 14 / macOS 11                | **2.4** — iOS 15 / macOS 12                    |
| Device flag       | `supportsRaytracing`                       | `supportsRaytracingFromRender`                 |
| Function pointers | `supportsFunctionPointers`                 | `supportsFunctionPointersFromRender`           |
| Bind AS           | `setAccelerationStructure(_:bufferIndex:)` | `setVertex/FragmentAccelerationStructure(...)` |

**Mesh shading is incompatible.** Feature-tables footnote 6: _"Support for function pointers and
ray tracing in render pipelines isn't compatible with mesh shading."_

Indirect command buffers support it via `MTLIndirectCommandBufferDescriptor.supportRayTracing`
(iOS 16 / macOS 13).

### Hardware vs software — the distinction that matters

**There is no API that tells them apart.** `MTLDevice` has exactly two ray-tracing properties,
both boolean capability flags. The practical check is `device.supportsFamily(.apple9)` — which is
**inference, not an Apple-stated contract**.

Feature Set Tables (2026-05-21):

| Feature                                                                           | Family           |
| --------------------------------------------------------------------------------- | ---------------- |
| Ray tracing in compute pipelines                                                  | **Apple6** (A13) |
| Ray tracing in render pipelines                                                   | **Apple6**       |
| Acceleration structure build options (`preferFastIntersection`, `minimizeMemory`) | **Apple9**       |
| Row-major matrices in acceleration structures                                     | **Apple9**       |
| Per-component motion interpolation                                                | **Apple9**       |
| Direct access to on-chip ray-intersection result storage                          | **Apple9**       |
| Intersection function buffers                                                     | **Apple9**       |
| Address-driven acceleration structure builds (Metal 4)                            | **Apple9**       |

Family map: `apple6` = A13 · `apple7` = A14/M1 · `apple8` = A15/A16/M2 · **`apple9` = A17 Pro,
M3, M4** · `apple10` = A19/M5.

So ray tracing _works_ back to A13; **hardware acceleration starts at Apple9.** From Tech Talk
111375, verbatim:

> _"The first major improvement is that **the hardware intersector is able to run each traversal
> completely independently using fixed function hardware.**"_

> _"**because the hardware intersector executes each ray independently, it is free to group
> together the intersection function calls from rays that originated from separate SIMDgroups.
> This is the role of the reorder stage.**"_

Two accelerated things: fixed-function BVH traversal, and a **reorder stage** that re-packs
divergent intersection-function calls into coherent SIMD-groups. Neither is exposed by any API —
identical `intersector<>` code, faster silicon.

> **Worth knowing:** the 2026 Feature Set Tables enumerate **only Apple families 1–10**.
> `Mac1`/`Mac2` (Intel + AMD Mac GPUs) have been removed from the document entirely, though
> `MTLGPUFamily.mac1`/`.mac2` still exist in the API. Apple no longer publishes ray-tracing
> availability for Intel Macs. _(That the removal means what it appears to mean is inference —
> Apple gives no reason.)_

---

## 8. Performance — what Apple actually says

**Prefer `intersector` over `intersection_query`.** The strongest and most repeated guidance, and
it is hardware-motivated. Tech Talk 111375, verbatim:

> _"Our first suggestion is to **use the intersector object API whenever possible**. Metal also
> allows ray tracing to be performed using the intersection query API, but **this API increases
> the amount of ray trace scratch memory that must be read and written, as well as disables the
> reorder stage.**"_

The per-primitive-data article repeats it as a Tip. (WWDC21/10149, predating the hardware, is
more even-handed and suggests measuring both.)

**Many small intersection functions beat one big one** — the opposite of usual advice, and it
falls straight out of the reorder stage:

> _"**avoid creating one uber function that is capable of executing many different logical
> intersection routines. Instead, create one Metal intersection function for each logical
> intersection routine. This increases the benefits of the reorder stage.**"_

**Keep the payload small:** _"**try to minimize the size of the ray payload structure**… This will
decrease your shader's latency and potentially increase its thread occupancy."_

**Batch builds into one encoder.** WWDC22/10105:

> _"**multiple builds are now automatically performed in parallel whenever possible on Apple
> Silicon. This results in up to 2.8 times faster builds when they run in parallel.**"_
> _"To build them in parallel, you will need to ensure that you **use the same acceleration
> structure command encoder for many builds. Additionally, builds which use the same scratch
> buffer can't run in parallel.**"_

That second sentence is the trap: sharing one scratch buffer across builds serializes them.

**Split static from dynamic**, and don't over-instance: _"using 3 levels of instancing allows you
to reduce build time with only minor impact on trace time."_

**Heaps beat per-structure `useResource`:** _"For large scenes, this could require thousands of
calls to `useResource:`… Instead, you can allocate all of these primitive acceleration structures
from the same heap… a single call to the `useHeap:` method."_

**Per-primitive data** (Metal 3) — copy shading data into the structure and read it via
`hit.primitive_data`, skipping a `primitive_id` indirection: _"we found in one of our own test
applications that using per-primitive data resulted in a **10% to 16% performance
improvement**."_ Cost: _"acceleration structures with large primitive data may need significantly
more memory and take longer to create, copy, and refit."_ Store only what's shared across
instances.

**Occupancy:** _"if you combine [intersection] with complex shading code, you may end up with a
compute kernel that runs at lower occupancy."_

**Motion blur** is sampled stochastically per ray, so clean images need many samples — Apple's
own figure is _"256 randomly timed samples"_ per frame. Instance animation is cheaper than
primitive animation but can't deform.

---

## 9. `MPSRayIntersector` is deprecated

Deprecated **macOS 14.0 / iOS 17.0 / tvOS 17.0**, born-deprecated on visionOS 1.0. The
replacement message lives only in the SDK header — DocC's `deprecationSummary` is `null` on every
page, so the rendered site shows a badge with no text:

```objc
MPS_AVAILABLE_STARTING_BUT_DEPRECATED("Use Metal ray tracing API instead", …)
```

Deprecated alongside it: `MPSAccelerationStructure`, `MPSTriangleAccelerationStructure`,
`MPSInstanceAccelerationStructure`, `MPSAccelerationStructureGroup`, `MPSPolygonAccelerationStructure`,
`MPSQuadrilateralAccelerationStructure`, `MPSPolygonBuffer`.

_(Doc inconsistency: `MPSRayDataType`, `MPSIntersectionDataType`, `MPSIntersectionType` have no
`deprecatedAt` in the JSON but **are** deprecated in the headers. Trust the header.)_

**Why it died** — WWDC20/10012, verbatim:

> _"This works great, but it requires us to split up our code into three separate compute
> kernels. It also requires us to pass rays and intersections through memory."_
> _"In contrast, in the new Metal ray tracing API, this intersector object is now available
> directly from the shading language."_

**MetalPerformanceShaders itself is not deprecated**, and **the denoisers survive**: `MPSSVGF`,
`MPSSVGFDenoiser`, `MPSTemporalAA` carry no deprecation. They take plain `MTLTexture` inputs and
have no `MPSRayIntersector` dependency, so they compose with a native ray tracer — _though Apple
states no such guidance and doesn't file them under "Ray Tracing" at all, so treat composability
as reasonable inference rather than documented._

---

## 10. Metal 4 (`MTL4*`)

All `MTL4` acceleration-structure types are OS **26.0**, non-beta, on all six platforms. The
shape changes in two ways: buffers become `MTL4BufferRange` (GPU address + length rather than
buffer + offset), and building moves into the **unified `MTL4ComputeCommandEncoder`** —
_"Metal 4 consolidates existing command encoders. With the new unified compute encoder, your app
can also manage blit and acceleration structure command encoding."_

Residency becomes explicit: _"**Use a `MTLResidencySet` to mark residency of all buffers and
acceleration structures this descriptor references when you build this acceleration
structure.**"_

**Intersection function buffers** (Metal 4, Apple9) are the DXR shader-binding-table analogue:
_"An intersection function buffer is an argument buffer that contains handles to your scene's
intersection functions."_ Note the porting difference — _"In DirectX, you set the Intersection
Function Buffer address and stride on the host… In Metal, you set this in the shader."_ MSL side
adds `set_base_id(uint)` and `set_geometry_multiplier(uint)`.

---

## 11. Gotchas

1. **Curves are excluded from `assume_geometry_type` by default.** Opt in or every curve hit
   silently misses.
2. **The instance `mask` is 8 usable bits**, not 32 — the top 24 are reserved unless
   `extendedLimits`.
3. **Intersection functions can be invoked for rays that miss the bounding box**, and **payload
   writes persist even when the function rejects the hit.**
4. **A bare `bool` return from a triangle intersection function means `[[accept_intersection]]`.**
5. **`intersector<>::result_type`, not `::result`** — the MSL spec is wrong here.
6. **`intersect()` has no default arguments** despite what the spec shows; they're overloads.
7. **`refit` costs intersection performance even before you refit** — the build itself is more
   conservative.
8. **Refit cannot add or remove geometry.** Topology changes mean a rebuild.
9. **Builds sharing one scratch buffer cannot run in parallel** — the single most common reason
   batched builds don't speed up.
10. **Prefer `intersector` over `intersection_query`** — the query path disables the Apple9
    reorder stage.
11. **Many small intersection functions beat one uber-function**, for the same reason.
12. **Ray tracing works from Apple6; hardware acceleration starts at Apple9**, and no API
    distinguishes them.
13. **Mesh shading and render-pipeline ray tracing are mutually exclusive.**
14. **Intersection functions get no textures and no threadgroup memory** — pass textures through
    an argument buffer.
15. **`MTLAccelerationStructureSizes` genuinely has no availability metadata** — it's an
    unannotated C struct, not a DocC inheritance artifact.
16. **The geometry+instance intersection-function-table index formula is not correctly documented.**
    Verify empirically.
