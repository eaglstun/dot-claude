---
topic_id: "v2:LHDA"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "xfMyKG4UYqd1lnJjWlk5ZuGwIr6IcAAC"
related_ids:
  - "x_M0SG8UQreJxDok6QwK95WYS4xEcAAD"
  - "z_cmaC6RULdRHuwjVZ2aIRR4G0DrcAAG"
---
# Giving the procedural props material/"skin" richness (cube-pipeline props)

How to lift the hand-built procedural props (TV, mic-stand, par-can, muffler-man, disco ball,
semi-truck, ghost) out of flat vertex-colour fill into shaded, materially-rich surfaces —
**without UVs and mostly without assets**, on a phone GPU that draws everything twice.

Sources (ground truth = this repo + cited technique refs):

- `ios/KaraokeVR/Passthrough.metal` — `cubeVertex`/`cubeFragment` (L845-860, the flat prop path:
  `CubeVertex{float4 position; float4 color}`, NO vertex descriptor, indexed by `vertex_id`);
  `texturedVertex`/`texturedFragment` (L709-735, the model-space half-lambert precedent, normal +
  uv + `baseColor` tap at `texture(3)`); `discoVertex`/`discoFragment` (L893-937, the view-space
  radial-normal camera-env reflection — the fusion precedent for view-dependent per-facet effects).
- `ios/KaraokeVR/Models/MeshBuilder.swift` — emitters ALREADY compute smooth per-vertex normals
  (`n00..n11` in `ellipsoid` L105, `facet` radial normal in `tube` L144) and a static half-lambert
  `shade()` (L159-165); the normals are used to bake a per-facet colour then **discarded** (not
  stored in the vertex).
- `ios/KaraokeVR/StereoARRenderer.swift` — `makePipeline` (L1252, no vertex descriptor: every prop
  pipeline just names a vertex/fragment fn), `drawMesh` (L2694, the shared cube-format draw),
  `texturedPipeline`/`skinnedPipeline`/`discoPipeline` are all separate pipelines beside `cubePipeline`.
- `.claude/references/metal/fragment-effect-fusion-and-cost.md` — the mode-2 blur (~17 taps/eye ×2)
  cost anchor; `float3`-in-uniform padding trap; per-eye fusion rules.
- `.claude/references/metal/depth-stylization.md` — fast-math `normalize(0)` NaN guard (default
  fast-math is ON in these pipelines).
- Matcap technique: Quentin King, "Faking PBR on Mobile using MatCaps"
  <https://quentinking.com/shaders/matcaps/>; viclw17, "MatCap Shader Showcase"
  <https://viclw17.github.io/2016/05/01/MatCap-Shader-Showcase>. View-space normal →
  `uv = N_view.xy*0.5+0.5` → one texture tap, no lights, no UVs.
- Triplanar: Ben Golus, "Normal Mapping for a Triplanar Shader"
  <https://bgolus.medium.com/normal-mapping-for-a-triplanar-shader-10bf39dca05a>; Catlike Coding,
  "Triplanar Mapping" <https://catlikecoding.com/unity/tutorials/advanced-rendering/triplanar-mapping/>.
  Blend weights `b = pow(abs(N),k); b /= dot(b,1)`, 3 samples along world X/Y/Z, no UVs.

Fetched / verified: 2026-06-30.

## The one structural fact that makes this cheap

The cube pipeline has **no `MTLVertexDescriptor`**. `cubeVertex` reads
`const device CubeVertex *verts [[buffer(0)]]` and indexes by `[[vertex_id]]`; the layout is
defined ENTIRELY by the MSL struct (`float4 position; float4 color` = 32 B) mirrored by the Swift
`[Float]` packing `[x,y,z,1, r,g,b,a]`. So **adding a normal/pos varying is a struct + packing +
fragment edit — zero descriptor plumbing.** Do NOT widen the shared `CubeVertex` (it's used by the
reticle, confetti, beam, pole, markers, and every buffer's byte-sizing). Add a **parallel "lit prop"
format + pipeline** beside `cubePipeline`, exactly how `texturedPipeline`/`skinnedPipeline`/
`discoPipeline` already sit beside it. And note: **MeshBuilder already has the normals** — the win
is just to stop discarding them.

Key transform choice, from the `texturedFragment` precedent: shade in **MODEL space** with a baked
key-light direction (L729 `keyDir`). The light is model-space, so it's stable wherever the user
stands, and **no normal matrix is needed** (dodges the non-uniform-scale normal bug the
`skinnedFragment` note calls out). Only the _view-dependent_ effects (rim, matcap, spec) need a
view-space normal (upper-3×3 of `eyeView·anchor·model`), which differs per eye — that's **correct
parallax** and fuses, same argument as the disco ball (`Passthrough.metal:869`).

## Ranked for THIS renderer (bang-for-buck)

### 1. Per-fragment lighting with SMOOTH normals — cheapest, biggest form win

The props are baked FLAT per facet today (one `shade()` value per quad → visible facet steps, no
highlight travel). Carry the **smooth per-vertex normal** (`dir(lat,lon)` / radial `tube` normal —
already computed in MeshBuilder) into a `litPropFragment` and do half-lambert there. Low-poly
spheres/cylinders read as rounded volumes; the shade gradient moves as props rotate. Add **rim**
(`pow(1 - saturate(N_view.z), k)`) and a cheap **Blinn spec** (`pow(saturate(dot(N,H)), s)`) for a
material sheen. **Cost: ZERO extra texture taps** — pure ALU on small on-screen props. This is the
single biggest jump from "fill" to "form". Needs added: `float4 normal` in the lit-prop vertex
(emit smooth normal, not facet); a view-space normal for rim/spec (one normal-matrix uniform).

### 2. Procedural fragment patterns (noise / stripes / brushed-metal / checker) — no assets

Once model-space position is a varying, generate the surface in the fragment: **brushed metal** =
anisotropic streaks along the prop axis (`sin(dot(pos, axis)*freq)` + value-noise, reuse the
`fogFbm` hash-noise at `Passthrough.metal:493`); **grunge/fabric** = fbm multiply; **stripes/
checker/panel lines** = `fract(pos*freq)` + `fwidth`-AA (the contour-line trick already in the
repo). Resolution-independent, no seams, no assets, cheap ALU. Pattern chosen per-material by a
uniform id. Best for the metal props (muffler, par-can shell, mic stand, truck). Needs added:
model-space `pos` varying (+ a `patternId`/scale uniform). **Cost: ~free** (a few ALU ops/px).

### 3. Matcaps — instant chrome/plastic/clay pop, 1 tap

View-space normal → `uv = N_view.xy*0.5+0.5` → sample a small pre-lit sphere PNG. Gives believable
chrome / glossy plastic / waxy clay with **no lights and no UVs**, just 1 texture tap + a handful of
tiny (256²) matcap PNGs in the bundle. **View-space normal differs per eye → correct for a 3D
object at real depth → fuses (disco-ball precedent).** Multiply the matcap by the prop's vertex
colour to keep per-part tinting. Best for disco hardware, mic chrome, muffler chrome, TV bezel.
Needs added: view-space normal varying + one `matcap` texture bound at `texture(3)` (free slot,
same as textured/lyric). **Cost: 1 tap/px ×2 eyes** — trivial vs the mode-2 anchor.

### 4. Triplanar mapping — real textures, still no UVs (fallback)

3 samples along world/model X/Y/Z, blended by `pow(abs(N),k)` weights; no unwrap. Great for _large_
surfaces, but for these small stage props it costs **3 taps** for a look #2 approximates for free,
and it needs authored tileable texture assets. Reach for it only when you want genuine photographic
material (e.g. a wood stage floor, a brick backdrop). **Cost: 3 taps/px ×2 eyes.**

### 5. UV image textures — highest asset burden

Auto-UV of these _parametric_ primitives is actually tractable (box → 6 planar; cylinder/tube →
angle→u, t→v; sphere/ellipsoid → lat/lon→uv — all params MeshBuilder already has), so unwrap isn't
the blocker. The blocker is **authoring a texture atlas per material + seams**, for a payoff
triplanar/procedural already deliver. Do this only for a hero prop that must look photographic.
Needs added: `float2 uv` in the vertex (generate in each emitter) + texture assets.

### 6. Normal maps / detail textures — SKIP

Needs UVs + tangents + normal-map assets, and the scene has **one baked key light, no dynamic
lights**, so tangent-space detail barely reads on small low-poly props. Cost/benefit is bad. The
smooth-normal shading in #1 buys the "rounded" read that matters here; skip normal maps.

## Suggested phased build (cheapest high-impact first)

1. **Lit-prop pipeline** (`litPropVertex`/`litPropFragment` beside `cubePipeline`): 12-float vertex
   `[x,y,z,1, r,g,b,a, nx,ny,nz, patternId]`; MeshBuilder emits the smooth normal it already
   computes. Model-space half-lambert (copy `texturedFragment`'s `keyDir`/floor) → instantly
   rounds every faceted prop. **Zero taps.**
2. **Rim + Blinn spec** in the same fragment via a view-space normal (one normal-matrix uniform).
   Materials start reading as metal/plastic, not paint. **Zero taps.**
3. **Procedural patterns** keyed off the model-space `pos` varying + `patternId` (brushed metal,
   grunge, stripes) — per-material surface variation. **~free.**
4. **Matcaps** for the props that want true chrome/clay (opt-in `matcapId`, 1 tap + small PNGs).
5. Triplanar / UV textures only if a specific prop needs photographic material later.

## Cost & fusion summary (phone GPU, drawn twice, 0.75 scale / 30 fps)

- Props are **small in screen coverage**, so even +1 (matcap) or +3 (triplanar) taps ×2 eyes is
  far under the mode-2 blur anchor (~17 taps/eye full-screen). Phases 1-3 add **no taps at all**.
- Model-space half-lambert / procedural patterns are **identical geometry math per eye → fuse
  trivially** (no view dependence). Rim, spec, matcap use **view-space normals that differ per eye
  → correct binocular parallax, fuses like the disco reflection**; do NOT try to force them
  eye-identical (that would be the wrong, flat look).
- **Fast-math guard:** the props use the default-fast-math pipelines. Guard every `normalize` of a
  possibly-zero vector: `float l = length(v); n = l > 1e-5 ? v/l : float3(0,0,1);`.
- **Uniform layout:** keep the new material uniforms scalar `Float`/`float4`/`float4x4` — no bare
  `float3` (pads to 16 B and desyncs Swift↔MSL), per the cost-note's standing rule.

## Relevance to this renderer

The props are the one part of the AR scene still rendered as flat fill while the camera modes got
rich. Because the cube path has no vertex descriptor and MeshBuilder already computes the normals,
a parallel lit-prop pipeline is a small, additive change that mirrors the existing
`texturedPipeline` idiom — and Phases 1-3 buy most of the "skin" for essentially zero per-pixel
cost, sidestepping the UV problem entirely, exactly matching the procedural philosophy.
