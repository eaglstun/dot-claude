---
topic_id: "v2:DHJM"
topic_path: "model-runners/metal-skinning"
semantic_id: "VvYbmej2UAwsrQBwdBLWMXnYZLaAEAAO"
related_ids:
  - "XnxTGf_GEgctzVJodntHVXF0dbSEEAAB"
  - "Xhb3HHqXUIR_5UFlKIfSJTncR68pEAAK"
---
# Native Metal skinning runtime — build spec

Spec'd 2026-06-28 (Plan agent, grounded in-repo). Goal: play an AI-generated **rigged + animated
character** (a dancing figure) in the hand-rolled stereo renderer, dropped into the
**recording-focused AR scene** (`ARLiveView(record: true)`) so it's captured in karaoke takes.
First animated/skinned mesh in the app. Decision basis + iOS-runtime analysis: `rig-and-animate-apis.md` (PART B).

## Locked decisions

- **Native Metal linear-blend skinning** (NOT RealityKit/SceneKit/USDZ). Draws as geometry in the
  existing per-eye pass → reuses `mvp = proj·eyeView·sceneAnchor·model`, fuses + depth-occludes
  free. (iOS target is 16; RealityKit's `RealityRenderer` needs 18 — another reason native wins.)
- **Parser: a minimal purpose-built Swift GLB reader (`GltfSkinnedLoader.swift`), NOT GLTFKit2.**
  Project has ZERO SPM deps today; we bake into a native struct anyway (no portability tax), and
  GLTFKit2-as-parser still needs an adapter. ~400–600 LOC: GLB header/JSON/BIN chunks, accessors
  (POSITION/TEXCOORD_0/JOINTS_0/WEIGHTS_0/indices), `skin` (inverseBind + joints), node tree,
  baseColor material, `animation` channels/samplers. Reject+log sparse accessors / morph targets.
  **Request GLB from Tripo, never FBX** (far harder to parse).
- **Validation asset: Khronos `CesiumMan.glb`** (humanoid, ONE skin + ONE looping clip, ~22 joints,
  single base-color texture, ~human scale). Beats Fox (3 clips → premature clip-select; ~70u scale).
  Bundled in `ios/KaraokeVR/` (synchronized folder auto-includes resources).

## Skinned-vertex format (stride 48, no float3 desync)

`SkinnedVertex { position:SIMD4<Float> @0; uv:SIMD2<Float> @16; joints:SIMD4<UInt16> @24; weights:SIMD4<Float> @32 }`
MSL `SkinnedVertexIn { float4 position; float2 uv; ushort4 joints; float4 weights; }`. Indexed like
`reprojectVertex` (`device …*verts [[buffer(0)]]`, `verts[vid]`, `drawIndexedPrimitives`, UInt32 indices).
Joint matrices in a **`device float4x4*` at buffer(2)** — a **3-deep ring** of `storageModeShared`
buffers (`frameIndex%3`) so CPU writes don't race the ~3 in-flight frames; no semaphore. `maxJoints`
~256 (Tripo/Mixamo ~65) → tiny buffer.

## Skinning + animation math (CPU, once/frame, eye-independent)

`jointMatrix[j] = inverse(global(meshNode)) · global(skin.joints[j]) · inverseBind[j]`, where
`global(node) = global(parent)·local(node)`, `local = T·R·S` from (animated) node TRS. Precompute
parent-index + topo-ordered node list at load → single linear walk. VS:
`skinned = Σ wᵢ·jointMatrix[jᵢ]·pos; clip = mvp·skinned; clip.xy += offset·clip.w` (lensShift like cubeVertex).
Animation: per channel (node + TRS path) + sampler (times/values, STEP/LINEAR/CUBICSPLINE), advance a
clip clock, binary-search the interval, interpolate (lerp T/S, **shortest-path slerp/nlerp** R, Hermite
for cubicspline), write node-local TRS → recompute globals → joint matrices.
**Gotchas:** renormalize weights to 1; use `inverse(global(meshNode))` (not identity — Tripo/Mixamo nest
the mesh); quat shortest-path before slerp; widen UNSIGNED_BYTE joints. **Unlit → normals unused → the
whole non-uniform-scale-normal class of bug vanishes.**
**Clock:** free-running loop off `frame.timestamp` first; LATER swap to `songTime?()` so it dances to the track.

## Material — unlit single base-color texture

New skinned pipeline samples `baseColorTexture × baseColorFactor`, **opaque, unlit** (drop
metallic/roughness/normal/emissive — no lighting). Decode embedded GLB image via `CGImageSource` →
**raw `rgba8Unorm` (NON-`_srgb`)** to match the unlit scene's raw-sRGB writes (bridge landmine #5).
No texture → 1×1 white + `dancerBaseTint`. `sceneDepth` (lessEqual+write) → occludes free.

## Placement & recording scene

Grounded dancer on the stage facing the viewer: `dancerModel = translation(dancerStageX,
dancerGroundOffset, dancerStageZ) · rotationY(rad(dancerFacingYaw)) · uniformScale(dancerScale)`;
`mvp = proj·eyeView·(sceneAnchor ?? I)·dancerModel`. Auto-scale `dancerScale = dancerTargetHeight /
bindPoseHeight`. Draw in the **PLAYING** branch right after the `sceneItems` loop, before `drawHUD`,
with `sceneDepth`, wrapped `if effectiveMode != 3` (mirror the static mode-3 exclusion). Same captured
encoder → **ReplayKit records it automatically.** `ARLiveController.viewWillAppear` calls
`renderer.loadDancer(named:"CesiumMan")` only when `recordExperience` (keeps it out of the normal view
for now; promotable later). Present through countdown → record → save.

## Tuning constants (house style)

`dancerTargetHeight 1.7` · `dancerStageX 0` · `dancerStageZ -2.8` (m, −Z forward) · `dancerFacingYaw 180`°
· `dancerGroundOffset 0` · `dancerClipRate 1.0` · `dancerLoop true` · `dancerBaseTint (1,1,1,1)`.

## Files

**Add:** `SkinnedModel.swift` (runtime data + `updatePose(time:)→[float4x4]` + TRS/slerp/Hermite/walk),
`GltfSkinnedLoader.swift` (the minimal GLB reader), `CesiumMan.glb` (bundled).
**Change:** `Passthrough.metal` (+`SkinnedVertexIn`/`SkinnedUniforms`/`skinnedVertex`/`skinnedFragment`),
`StereoARRenderer.swift` (`skinnedPipeline` like `cubePipeline`, joint-buffer ring, `dancer:SkinnedModel?`,
`loadDancer`, per-frame `updatePose`→memcpy, `drawDancer` + its call, tuning consts),
`ARLiveView.swift` (`loadDancer` on appear when `recordExperience`).
**Untouched:** `ModelRegistry`/`SceneManifest`/`MeshBuilder` (dancer is a separate skinned path), cube/
reproject pipelines, depth states + prepass (reused for free occlusion).

## Phased de-risk build order

1. **Parse + skin + play CesiumMan in ONE eye** (flat tint, hardcoded ~2 m in front) — validates loader
   - joint math + skinning VS in isolation.
2. **Both eyes** via the existing `eyes` loop (`proj·eyeView·dancerModel`) — fuses free.
3. **Depth occlusion + stage placement** (`sceneAnchor`, grounded, auto-scaled, faced).
4. **Base-color texture** (raw non-sRGB) + 1×1-white fallback.
5. **Drop into the recording scene** — `loadDancer` on appear when `recordExperience`, draw in PLAYING
   (excl. mode 3); confirm ReplayKit captures it through countdown→record→save.
6. **LATER — Tripo GLB ingestion** (needs API key): fetch → temp `.glb` → same loader; handle Mixamo-spec
   rigs. Runtime unchanged.
