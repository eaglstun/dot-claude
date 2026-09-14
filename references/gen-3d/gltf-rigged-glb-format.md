---
topic_id: "v2:DGIP"
topic_path: "model-runners/gen-3d-contracts"
semantic_id: "TgKiPAXXGEUvsUJtdVnAAXfw9aklMAAH"
related_ids:
  - "Xk0bvdbWEkcN1WJodG5DB2NydLaMMAAO"
  - "XnxTGf_GEgctzVJodntHVXF0dbSEEAAB"
---
# glTF 2.0 / GLB rigged-model format contract

What a vendor's "rigged GLB" output actually _contains_ — the bridge between the generate-and-rig
APIs (`tripo-api.md`, `meshy-api.md`) and the runtime that plays it (`native-skinning-runtime.md`).
This is the on-disk data model the minimal loader must parse: the GLB container, accessors, the
skin/skeleton, the skinned-mesh attributes, and the animation channels. Read it to know exactly
what bytes a rig endpoint hands back and which the loader keys off.

**Grounded in the Khronos glTF 2.0 spec + official tutorials** — the canonical spec HTML at
`registry.khronos.org`/`khronos.org/registry` returns **403/blocked to WebFetch** (a common SPA/CDN
gate; noted per CLAUDE.md), so claims here are read from the **spec source on GitHub**
(`KhronosGroup/glTF .../Specification.adoc`) and the **glTF-Tutorials** repo, which mirror the spec
verbatim (read 2026-06-29). Where a number is load-bearing (magic, component-type constants) it was
quoted from the adoc source, not memory.

## GLB binary container (the file the loader opens)

A `.glb` is a 12-byte header + a sequence of chunks:

- **Header (12 bytes):** `magic` = **`0x46546C67`** (ASCII `glTF`) · `version` = `2` (u32) ·
  `length` = total file size in bytes (u32). Reject anything whose magic isn't `glTF`.
- **Chunk 0 — JSON:** `chunkLength` (u32) · `chunkType` = **`0x4E4F534A`** (ASCII `JSON`) ·
  `chunkData` = the UTF-8 glTF JSON document (the whole node/mesh/skin/animation tree).
- **Chunk 1 — BIN:** `chunkLength` · `chunkType` = **`0x004E4942`** (ASCII `BIN\0`) · `chunkData`
  = the raw little-endian binary blob that every `buffer` of index 0 points into.

Each chunk is `{chunkLength:u32, chunkType:u32, chunkData[chunkLength]}`. In a GLB, buffer 0 has no
`uri`; its bytes ARE the BIN chunk. (`.gltf` instead externalizes buffers/images to files or base64
data URIs — the loader spec only needs the self-contained GLB case.)

## buffers → bufferViews → accessors (how typed arrays are addressed)

Three-level indirection from raw bytes to typed vertex/keyframe data:

- **`buffer`** — a contiguous byte blob (`byteLength`; in GLB, the BIN chunk).
- **`bufferView`** — a window into a buffer: `buffer`, `byteOffset`, `byteLength`, optional
  `byteStride` (for interleaved attributes), optional `target`.
- **`accessor`** — typed view over a bufferView: `bufferView` · `byteOffset` (within the view) ·
  **`componentType`** · `count` (number of elements) · **`type`** · optional `normalized` ·
  optional `min`/`max`.
  - `componentType` constants: **`5120`** BYTE · **`5121`** UNSIGNED_BYTE · `5122` SHORT ·
    **`5123`** UNSIGNED_SHORT · **`5125`** UNSIGNED_INT · **`5126`** FLOAT (IEEE-754 single).
  - `type`: `SCALAR` · `VEC2` · `VEC3` · `VEC4` · `MAT2` · `MAT3` · `MAT4`.

The loader resolves every attribute/keyframe stream by walking accessor → bufferView → buffer(BIN).
**`native-skinning-runtime.md` rejects sparse accessors** — a glTF feature where an accessor stores
only a delta set of indices/values over a base; the minimal loader doesn't implement it, so a rig
that emits one must be re-exported.

## The skinned mesh — primitive attributes

A `mesh` is a list of `primitives`; each primitive has an `attributes` map (accessor per stream) +
optional `indices` accessor + a `material`. For a rigged character the loader needs exactly these
attributes (all per-vertex, same `count`):

- **`POSITION`** — `VEC3`/`FLOAT`, bind-pose vertex position.
- **`TEXCOORD_0`** — `VEC2`, UV for the base-color texture.
- **`JOINTS_0`** — `VEC4`, **UNSIGNED_BYTE or UNSIGNED_SHORT only** (spec-mandated). Each component
  is an **index into `skin.joints`** (NOT a node index directly) naming the 4 joints that influence
  this vertex. (Runtime widens UNSIGNED_BYTE → `ushort4`.)
- **`WEIGHTS_0`** — `VEC4`, FLOAT or normalized UNSIGNED_BYTE/UNSIGNED_SHORT. The 4 influence
  weights; **their linear sum SHOULD be ~`1.0`** (255/65535 before normalization for quantized).
  The runtime **renormalizes** defensively.
- `indices` — usually `UNSIGNED_SHORT`/`UNSIGNED_INT` (runtime draws UInt32 indexed).

More than 4 influences per vertex would appear as additional `JOINTS_1/WEIGHTS_1` sets — the
minimal runtime assumes a **single set** (4 influences), which Tripo/Mixamo/Meshy rigs satisfy.
**No morph targets** (`primitive.targets`) — rejected by the runtime spec.

## The skeleton + skin (where the rig lives)

The skeleton is **just nodes** — there is no separate "bone" type. A `node` has a local transform
(either a `matrix`, or TRS: `translation`/`rotation`(quaternion xyzw)/`scale`), a `children` array,
and optionally `mesh` and/or `skin` indices. Global transform = parent-chain product of locals.

A **`skin`** object ties geometry to those nodes:

- **`joints`** — array of **node indices**; ordinal position in this array is the "joint index"
  that `JOINTS_0` components reference.
- **`inverseBindMatrices`** — an accessor of `MAT4`/`FLOAT`, **one matrix per joint** (same length
  as `joints`). Each transforms a vertex from mesh/model space into the joint's local bind space —
  i.e. it undoes the joint's bind-pose global transform.
- **`skeleton`** (optional) — node index of the common root of the joint hierarchy. (The Skins
  tutorial doesn't exercise it; the loader can ignore it and derive globals from the node tree.)

A node carrying the mesh references the skin via **`node.skin`** (and the geometry via `node.mesh`).
That mesh-node's own transform matters: the skinning formula uses its inverse (see below) because
generators (Tripo/Mixamo) typically nest the skinned mesh under a non-identity node.

### Joint matrix + skinned position (what the VS computes)

Spec/tutorial formula (the tutorial states the simple form; the runtime adds the mesh-node term the
full spec requires):

```
jointMatrix(j) = inverse(globalTransform(meshNode))
               · globalTransform(skin.joints[j])
               · inverseBindMatrices[j]
```

Then per vertex, with `j = JOINTS_0`, `w = WEIGHTS_0`:

```
skinMat = w.x·jointMatrix(j.x) + w.y·jointMatrix(j.y)
        + w.z·jointMatrix(j.z) + w.w·jointMatrix(j.w)
skinnedPosition = skinMat · vec4(POSITION, 1.0)
```

The tutorial's minimal example omits the `inverse(globalTransform(meshNode))` factor (its mesh node
is identity); the runtime spec keeps it because real rigs nest the mesh. `inverseBindMatrices`
exists precisely so a vertex authored in mesh space lands in each joint's frame before the joint's
_current_ (animated) global transform re-poses it.

## Animation (what makes it move)

An **`animation`** object has two parallel arrays:

- **`samplers`** — each: `input` (accessor of keyframe **times**, `SCALAR`/`FLOAT`, seconds) ·
  `output` (accessor of **values**) · `interpolation`:
  - **`LINEAR`** — lerp for vec, **slerp for quaternion rotations**.
  - **`STEP`** — hold previous keyframe (no interpolation).
  - **`CUBICSPLINE`** — `output` holds **triplets per keyframe** (in-tangent, value, out-tangent);
    Hermite interpolation. (3× the value count — the loader must handle the stride.)
- **`channels`** — each: `sampler` (index into the samplers above) · `target` =
  `{node, path}` where **`path`** ∈ `translation` | `rotation` | `scale` | `weights`. Each channel
  drives ONE TRS component of ONE node. `weights` targets morph weights — the runtime rejects morphs,
  so only T/R/S channels are consumed.

Playback: advance a clip clock, binary-search the sampler `input` for the active interval,
interpolate the `output`, write the result into the target node's local TRS, recompute node
globals, then rebuild `jointMatrix(j)`. Rotation output is a quaternion (`VEC4`); **slerp shortest
path** (negate one quat if `dot<0`).

## Material — what the unlit runtime reads

A `material` carries `pbrMetallicRoughness` with **`baseColorFactor`** (RGBA) and
**`baseColorTexture`** (a `{index}` into `textures` → `images`, with a `sampler`). In a GLB the image
is an embedded PNG/JPEG referenced by a bufferView. The runtime is **unlit**: it samples
`baseColorTexture × baseColorFactor` and **ignores** metallic/roughness/normal/emissive/occlusion.
No base-color texture → fall back to `baseColorFactor` (or a 1×1 white + tint).

## The output contract in one line (what to demand from a rig endpoint)

A **GLB** with: one `mesh` whose primitive has `POSITION/TEXCOORD_0/JOINTS_0/WEIGHTS_0` (single
joint set, ≤4 influences) + indices; exactly **one `skin`** (`joints` + `inverseBindMatrices`); a
plain node tree (TRS or matrix nodes); a **base-color** material; and `animation` channels/samplers
on T/R/S paths. **No sparse accessors, no morph targets, no second JOINTS/WEIGHTS set.** Validation
reference: Khronos **`CesiumMan.glb`** (1 skin, ~22 joints, 1 looping clip, 1 base-color texture).
This is the same contract `native-skinning-runtime.md` parses and `tripo-api.md`/`meshy-api.md`
generate toward (request `glb`, base color, Mixamo/Tripo-native bones).

## Sources

- `github.com/KhronosGroup/glTF` → `specification/2.0/Specification.adoc` (GLB header magic
  `0x46546C67`, chunk types `0x4E4F534A`/`0x004E4942`, accessor `componentType` constants,
  JOINTS_0/WEIGHTS_0 component-type rules + weight-sum ~1.0) (read 2026-06-29).
- `github.com/KhronosGroup/glTF-Tutorials` → `gltfTutorial_019_SimpleSkin.md`,
  `gltfTutorial_020_Skins.md` (skin object, `joints`/`inverseBindMatrices`, `node.skin`+`node.mesh`,
  `jointMatrix`/`skinMat` formulas), `gltfTutorial_007_Animations.md` (channels/samplers,
  `target.path`, LINEAR/STEP/CUBICSPLINE) (read 2026-06-29).
- **Could not fetch:** the canonical spec HTML at `registry.khronos.org/glTF/specs/2.0/glTF-2.0.html`
  (HTTP 403 to WebFetch) and `khronos.org/registry/.../README.md` (only links, no spec body) —
  used the GitHub spec/tutorial sources above instead, which mirror it.
- Companions: `native-skinning-runtime.md` (the loader/runtime that consumes this) · `tripo-api.md`
  / `meshy-api.md` (the rig endpoints that emit it).
