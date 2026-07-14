---
topic_id: "v2:DHJA"
topic_path: "model-runners/metal-skinning"
semantic_id: "znHumH7cEoVt0WL9TLNoIzqYF66NsAAP"
related_ids:
  - "Xhb3HHqXUIR_5UFlKIfSJTncR68pEAAK"
  - "5vWmDHeIAvVVgD3FZPhzrTsgE4gIIAAH"
---
# Static GLB mesh → Metal (no rig)

How a static binary glTF prop is parsed and drawn in this renderer (the AI mannequin head).
Source of truth in-repo: `ios/KaraokeVR/GlbMesh.swift`, `ios/KaraokeVR/Passthrough.metal`
(`texturedVertex`/`texturedFragment`), `ios/KaraokeVR/StereoARRenderer.swift` (`texturedPipeline`,
`drawMannequin`). Spec context: `.claude/references/gen-3d/native-skinning-runtime.md` (Material +
Placement sections; the skin/joint/anim parts do NOT apply to a static mesh).

## GLB container (glTF 2.0 §3.3, little-endian)

- 12-byte header: magic `0x46546C67` ("glTF") @0, `version`==2 @4, total `length` @8.
- Then length-prefixed chunks: `[u32 chunkLength][u32 chunkType][bytes]`. Types:
  `0x4E4F534A` = "JSON", `0x004E4942` = "BIN\0". The JSON is the glTF doc; the BIN chunk is buffer 0.
- Accessor → slice = `bufferViews[bv].byteOffset + accessor.byteOffset`, element stride =
  `bufferView.byteStride` if present else tightly packed (vec3 f32 → 12, vec2 f32 → 8). Every
  bufferView in a GLB indexes buffer 0 (no `uri`), so the BIN chunk is the only backing store.
- componentType ints: 5121 U8, 5123 U16, 5125 U32, 5126 F32. Index accessor is SCALAR of U8/U16/U32
  → widen all to UInt32 and `drawIndexedPrimitives(indexType: .uint32)`.
- Embedded image: `materials[m].pbrMetallicRoughness.baseColorTexture.index` → `textures[t].source`
  → `images[i].bufferView` → raw PNG/JPEG bytes in the BIN chunk. `baseColorFactor` (rgba) multiplies
  the sampled texel.

## The two host/shader landmines that bit here

1. **Vertex struct stride padding.** MSL `struct { float4 position; float2 uv; }` has 16-byte
   alignment, so its _array stride_ rounds **24 → 32 bytes** (8 floats), NOT 24. A tightly-packed
   24-byte interleave silently desyncs `verts[vid]`. Fix: bake **8 floats/vertex**
   `[x,y,z,1, u,v, 0,0]` — the same 32-byte layout as `CubeVertex` — and read it with that struct.
   (Same float3/float4 padding trap the apple-silicon skill flags for uniform buffers.)
2. **Texture sRGB.** This renderer writes raw sRGB to a non-`_srgb` drawable (the unlit scene draws
   the camera bytes straight). Decode the base-colour image **`rgba8Unorm` (NON-`_srgb`)** so it
   matches — via `MTKTextureLoader` option `.SRGB: false`. `.origin: .topLeft` keeps glTF's
   top-left UV convention. No texture → 1×1 white so `baseColorFactor` still tints.

## Placement (static prop)

- Mesh is ~1 unit tall, origin-centred. Auto-scale `scale = targetH / (boundsMax.y - boundsMin.y)`;
  ground by lifting `-boundsMin.y * scale` (puts the bottom on y=0). Draw under the shared
  `sceneAnchor`: `mvp = proj · eyeView · sceneAnchor · (translate · rotY(faceYaw) · uniformScale)`,
  with the lensShift `clip.xy += offset·clip.w` in the vertex stage and `sceneDepth` (lessEqual+write)
  so it occludes free and ReplayKit captures it.
- **Facing is a guess:** glTF +Z is nominally "front" but exporter-dependent. Constant
  `mannequinFacingYaw` (deg) flips it 180° if the back of the head shows on-device.

## Cost

One indexed draw per eye (the head is ~4k tris → ~8k tris/frame across both eyes), one base-colour
texture tap in the fragment, opaque/unlit. Negligible next to the multi-tap depth fragment passes.

## Bundling

`.glb` under the synchronized root group `ios/KaraokeVR/` (e.g. `GenAssets/`) is auto-added as a
bundle resource — load with `Bundle.main.url(forResource:withExtension:"glb")`. No `project.pbxproj`
edit. (Caveat: a 14 MB sibling `mannequin-head.glb` also bundles — prune if app size matters.)
