---
topic_id: "v2:LBFF"
topic_path: "metal-renderer/threejs-api"
semantic_id: "3_SU5xJ60Aeh6RtLdnKw1uHIMO6w0AAC"
related_ids:
  - "y_ckZw6mcieLdTtXZj5R9MhIE-mqoAAL"
  - "B_QgbjDv0zcp1Q8HYjii1LTZAMObQAAJ"
---
# Performance on a Phone GPU Rendering Stereo (r132)

> **Pinned to Three.js r132 (0.132.2).** The governing fact: the scene is rendered **twice per
> frame**, one viewport per eye, by hand (`karaoke/scene/stereo.js`),
> on an iPhone-class GPU with no active cooling. Every cost below is paid **per eye, ~2×**.

## The hard ceiling: no full-screen post-processing

Because stereo is two scissored viewports in one canvas, any **framebuffer-feedback / full-frame
post pass** (`AfterimagePass`, bloom/`UnrealBloomPass`, motion blur, `EffectComposer` in general)
smears both eyes into one buffer and **breaks stereo fusion**. This isn't just a perf call, it's
a correctness call.

- **Do** build effects as **geometry + material in the scene** (glow tubes, additive sprites,
  emissive meshes). They render correctly in each eye for free. See the effects doc.
- **Do not** reach for `EffectComposer` / `examples/jsm/postprocessing/*`. The same reason the UI
  lives in 3D, not as an HTML overlay.

## Fill-rate is the scarcest resource (additive overdraw)

The glow idiom (`MeshBasicMaterial` + `AdditiveBlending` + `depthWrite:false`) is cheap per
fragment but every transparent fragment is **overdraw** — `depthWrite:false` means no early-Z
rejection, so stacked halos all shade. Big soft additive sprites that overlap and fill the view
are the most likely thing to tank framerate, doubled across eyes.

- **Do** keep corona/halo geometry tight (the neon sign uses radius multipliers ~2.4–4.2, not 10).
- **Do** prefer a few bright sprites over many large faint ones covering the same pixels.
- **Watch** any additive layer that can fill a large solid angle of view (full-screen "flash"
  planes are the worst case — they're 100% overdraw, twice).

## Pixel ratio: cap it

Fill-rate scales with the square of `devicePixelRatio`. A modern iPhone reports DPR 3.

- **Do** cap: `renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))`
  (as in `lit-textures/main.js`).
- **Note:** `karaoke/main.js` currently sets `setPixelRatio(window.devicePixelRatio || 1)`
  **uncapped** — if that scene ever gets fill-rate bound, capping at 2 (or even 1.5) is the
  first, biggest lever, and it's invisible through the lenses.

## Draw calls: one per (mesh × material), then ×2 eyes

Each `Mesh` with its own material is a draw call **per eye**. The asset library leans on `Group`s
of many small meshes (e.g. `assets/threejs/disco-ball.js`, the trucks), which is fine at a handful of
props but adds up if you instantiate dozens.

- **Merge** static geometry that shares a material:
  `mergeBufferGeometries([...], false)` from
  `three/examples/jsm/utils/BufferGeometryUtils.js`. **r132 name is `mergeBufferGeometries`** —
  it was renamed `mergeGeometries` _after_ r132, so newer snippets will import the wrong name.
- **Instance** a prop repeated many times with `THREE.InstancedMesh(geo, mat, count)` +
  `setMatrixAt(i, matrix)` then `instanceMatrix.needsUpdate = true`. Per-instance tint via
  `setColorAt(i, color)` (RGB only — there is no per-instance alpha in r132). One draw call for
  the whole batch, per eye. (No InstancedMesh in the repo yet; it's the right tool the first time
  you need, say, 50 identical crowd figures or stars.)
- Materials sharing isn't free of state changes, but reusing one material instance across meshes
  still helps the renderer batch and cuts GC.

## Per-frame geometry rebuilds — when they're fine

The trails rebuild a `TubeGeometry` every frame (`karaoke/scene/truck-trails.js`,
`buildTube`). Worst-case vertex count there:
`seg = (MAXP-1)*3 ≈ 75` rings × `(radial+1) = 7` ≈ **~525 verts** for the core, plus the same for
the halo, **per truck**. At the scene's ~handful of arcing trucks that's a few thousand verts
rebuilt per frame — **cheap**, dwarfed by fill-rate. The rainbow ribbon is smaller still
(`26 × 8 ≈ 208` verts).

- **Do** `geometry.dispose()` the old geometry before swapping (the trail does), or you leak GPU
  buffers fast at 60fps.
- **Caution** if you scale this pattern to _dozens_ of simultaneous rebuilt tubes, or raise
  `MAXP`/`radial` — vertex count and per-frame allocation grow linearly and you'll start to feel
  it. Prefer updating a fixed-size buffer in place (see the Points pool) over rebuild-and-dispose
  at high object counts.
- **Better, when shape variety is limited:** pre-build a few geometry **variants** once and
  toggle `.visible` / swap per frame — the electric-moon arcs do exactly this
  (`assets/threejs/moon.js`), zero per-frame allocation.

## Fog: atmosphere _and_ a soft culling aid

`scene.fog` dissolves distant geometry into the background color, so you can keep the far plane
modest and let things fade rather than pop. `Fog` (linear) and `FogExp2` (exponential, more
atmospheric) both exist in r132.

- The lit-textures scene matches `scene.background` to the fog color so edges vanish seamlessly.
- The karaoke scene uses dark fog (`new THREE.Fog(0x070709, 6, 40)`) so distant props read as
  backlit silhouettes — fog as art direction.
- **Glow/light sources opt out** with `fog: false` so they punch through the haze like real
  lights (every additive idiom in `assets/*` sets this). Fog only helps cull/atmosphere the
  _solid_ world.

## Other phone-budget rules (from the skill notes)

- **Shadows are the first cut.** The shadow map is rendered once (not per eye) but **sampled per
  eye**, and re-rendering all casters every frame for moving objects is pricey. Prefer baked
  `aoMap` + `scene.environment` over `castShadow`. If you must, one `DirectionalLight` at
  `shadow.mapSize = 512`.
- **Textures ≤ 1024²** (2048² only when truly needed); keep mipmaps on.
- **Anisotropy** is a cheap, high-value win for floors/walls you look across — read the cap from
  `renderer.capabilities.getMaxAnisotropy()`, never hardcode 16.
- **Material choice:** `MeshStandardMaterial` is the workhorse but is the heaviest lit shader;
  `MeshLambertMaterial` / `MeshPhongMaterial` are cheaper if a surface doesn't need PBR.
  `MeshBasicMaterial` (unlit) is cheapest of all — which is exactly why the glow effects use it.
