---
topic_id: "v2:DGJA"
topic_path: "model-runners/gen-3d-contracts"
semantic_id: "Xhb3HHqXUIR_5UFlKIfSJTncR68pEAAK"
related_ids:
  - "VvYbmej2UAwsrQBwdBLWMXnYZLaAEAAO"
  - "znHumH7cEoVt0WL9TLNoIzqYF66NsAAP"
---
# Skinned (rigged + animated) GLB runtime — native Metal LBS

Built 2026-06-28 alongside the first skinned mesh in the app (the dancer). Sources:

- Spec: `.claude/references/gen-3d/native-skinning-runtime.md`
- glTF 2.0 spec §3.6 (Accessors), §5.21 (skin), §3.7 / §5.16 (animation), §3.6.2.2 (cubic spline)
- In-repo: `ios/KaraokeVR/GltfSkinnedLoader.swift`, `SkinnedModel.swift`, `GlbCore.swift`,
  `Passthrough.metal` (`skinnedVertex`/`skinnedFragment`), `StereoARRenderer.swift` (`drawDancer`)

## Shared GLB parser

There is ONE copy of GLB container + accessor + base-colour-image parsing: `GlbCore` (an enum
namespace of static funcs). Both the static prop loader (`GlbMesh`) and the skinned loader
(`GltfSkinnedLoader`) call into it — do not re-derive chunk/accessor parsing. `GlbCore` adds, over
the static subset: `readJointsU16` (widens UNSIGNED_BYTE/SHORT VEC4 → ushort4), `readFloatElements`
(generic vecN/matN float → flat array + component count), `readMat4` (inverse-bind), reused by the
skinned loader.

## Stride-48 skinned vertex (no float3 desync)

Host `SkinnedModel.SkinnedVertex` / MSL `SkinnedVertexIn` must agree at **48 bytes**:
`float4 position @0` · `float2 uv @16` · `ushort4 joints @24` · `float4 weights @32`. Swift's natural
layout of that struct _is_ 48 (SIMD4<Float> forces 16-align; 24/32 land on their natural alignment),
but the loader still guards `MemoryLayout<SkinnedVertex>.stride == 48` and bails+logs if a future
edit perturbs it. `ushort4 joints` indexes the palette directly in the VS.

## Joint matrix formula (the gotchas that matter)

`jointMatrix[j] = inverse(global(meshNode)) · global(skin.joints[j]) · inverseBind[j]`

- `global(node) = global(parent) · local(node)`, `local = T·R·S` from the node's (animated) TRS.
- Use **inverse(global(meshNode))**, NOT identity — Tripo/Mixamo (and CesiumMan) nest the mesh under
  transformed parents; identity skews/offsets the whole character. Compute it once at BIND pose.
- Node indices are NOT topologically ordered in glTF; a child can have a lower index than its parent.
  Build parent[] from `children`, then DFS from roots for a parents-before-children walk order.
- Renormalize WEIGHTS_0 to sum 1 per vertex (degenerate all-zero → (1,0,0,0)).
- JOINTS_0 is often UNSIGNED_BYTE (dino) or UNSIGNED_SHORT (CesiumMan) — widen to ushort.
- Quaternion LINEAR: flip the 2nd quat if `dot < 0` (shortest path) before slerp; nlerp/normalize is
  the fast-math-safe fallback. CUBICSPLINE values are [inTangent, value, outTangent] triplets per key
  → Hermite (tangents scaled by the key delta); quats Hermite'd in 4D then renormalized.
- The clip clock is free-running off `frame.timestamp` (loops on `duration`). The pose is a pure
  function of time+clip → both eyes get the identical palette → **fusion-safe**, computed once/frame.

## Grounding a full-body character to the floor (NOT the anchor)

`sceneAnchor` is yaw-only at the **camera's launch position**, so anchor y=0 ≈ device/eye height,
NOT the floor. The static mannequin grounds its bottom to anchor y=0 (fine for a small head at
stage height), but a full-body character grounded there **floats ~a phone's-height above the real
floor**. Two-part fix (`StereoARRenderer.dancerModel` + `updateFloorY`):

1. **Floor reference**: take ARKit's lowest horizontal `ARPlaneAnchor` world Y (running min, so a
   tabletop can't win) as `floorWorldY`; fall back to `anchorY − assumedCameraHeight` (~1.4 m) until
   a plane is seen. `planeDetection = [.horizontal]` must be on (it is, in ARLiveView).
2. **Posed feet, not bind bbox**: a rig's bind-pose bounding box is NOT its posed feet. Use
   `SkinnedModel.groundContactMinY()` — the min skinned vertex Y sampled across the clip (retain CPU
   positions/joints/weights to skin on the CPU once at load). For the Tripo dino both happen to be
   ≈0 (rotation-only clips, bind feet at model 0), so the visible float was entirely the anchor =
   eye-height reference, not the bind/posed gap — but the posed term is the correct general fix.
   Final lift (anchor-local): `groundLift = (floorWorldY − anchorY) − posedMinY·scale + manualNudge`.

## Multi-clip

The loader keeps ALL `animations` as `Clip`s and plays one by index (`SkinnedModel.clipIndex`,
default 0). Dino: #0 idle, #1 walk. CesiumMan: single clip (index harmless).

## GPU plumbing + draw

- Palette upload: a **3-deep ring** of `storageModeShared` buffers (`frameIndex % 3`), memcpy the
  `[float4x4]` from `updatePose`, bind at vertex **buffer(2)**. No semaphore — the ring covers the ~3
  in-flight frames so a CPU write can't race a GPU read.
- `skinnedPipeline` is a plain opaque bgra8 + depth32 pipeline (like the cube/static-mesh), drawn with
  `sceneDepth` (lessEqual+write) → occludes free; `drawIndexedPrimitives` uint32.
- Same per-eye chain as every 3D prop: `proj · eyeView · (sceneAnchor ?? I) · dancerModel`, with the
  `clip.xy += offset·clip.w` lensShift in the VS. Material is **unlit** base-colour×factor → normals
  unused (NORMAL is parsed-tolerant but dropped), sidestepping the non-uniform-scale-normal bug class.
- Cost: one CPU pose walk (≤ jointCount matrices) + one skinned indexed draw **× two eyes**.

## Validated asset shapes (offline JSON inspect, confirmed against the loader)

- CesiumMan: 1 skin / 19 joints / 1 LINEAR clip (T+R+S, 57 channels) / JOINTS_0 ushort / no morph+sparse.
- dino-lowpoly: 1 skin / 41 joints / 2 LINEAR clips (rotation-only, idle+walk) / JOINTS_0 ubyte.
