---
topic_id: "v2:LBAF"
topic_path: "metal-renderer/threejs-api"
semantic_id: "B8vc70Ea8gHZ-AsBpTvikNFJIsM8QAAP"
related_ids:
  - "BODE5nU53h-bmQtYcEqiUtlY-qO2AAAC"
  - "QUuwsXVf_be82AMiVDnhErj_Is-9YAAD"
---
# r132 API Surface & Migration Gotchas

> **Pinned to Three.js r132 (0.132.2).** All facts below verified against `node_modules/three`
> at `REVISION = '132'`. This doc exists so future code doesn't accidentally adopt a **newer-API**
> pattern (most online examples target current Three.js) — and so we don't accidentally use a
> _pre-r132_ pattern either. When the live docs and this doc disagree, trust this doc.

## Why r132 specifically (don't bump casually)

r132 is the **last release shipping both** `StereoEffect` and `DeviceOrientationControls` in
`examples/jsm/`. Newer versions removed `DeviceOrientationControls` outright. Both are central to
this project (hand-rolled stereo + phone head-tracking), so **r132 is the boundary** — bumping
requires re-confirming both modules still exist (they don't, past r132).

- `three/examples/jsm/effects/StereoEffect.js` — present.
- `three/examples/jsm/controls/DeviceOrientationControls.js` — present (gone in later releases).

## Color management — see the dedicated doc

The biggest version trap. One-line summary: r132 uses `renderer.outputEncoding` /
`texture.encoding` / `THREE.sRGBEncoding` (3001) / `THREE.LinearEncoding` (3000), and
`renderer.physicallyCorrectLights`. The newer `colorSpace` / `SRGBColorSpace` / `outputColorSpace`
/ `useLegacyLights` **do not exist in r132**. Full detail in
`color-management-and-ibl.md`.

## Geometry: BufferGeometry only

- **The legacy `THREE.Geometry` class is GONE** (removed in r125; only `BufferGeometry` exists in
  `src/core` at r132). Any tutorial using `new THREE.Geometry()` with `.vertices` /
  `.faces` / `geometry.faces[i].color` is **pre-r125 and will throw** here. Build attributes
  instead: `setAttribute('position', new THREE.Float32BufferAttribute(arr, 3))`,
  `geometry.setIndex([...])`, `geometry.setFromPoints([...Vector3])`,
  `geometry.computeVertexNormals()`.
- `BoxBufferGeometry`, `PlaneBufferGeometry`, `SphereBufferGeometry`, … **still exist in r132** as
  deprecated aliases of the non-`Buffer` names (verified: `export { BoxGeometry as
BoxBufferGeometry }`). They were **removed in r144**, so prefer the modern `BoxGeometry` spelling
  now to stay forward-safe — but old `*BufferGeometry` snippets won't break on r132.
- Merge util is **`mergeBufferGeometries`** (in `examples/jsm/utils/BufferGeometryUtils.js`).
  Renamed `mergeGeometries` _after_ r132 — newer imports will fail here.

## Materials & vertex colors

- **`material.vertexColors` is a boolean** (`true` / `false`; default `false`). The old
  `THREE.VertexColors` / `THREE.FaceColors` enum constants are gone (removed r125). Don't write
  `vertexColors: THREE.VertexColors`.
- **RGBA vertex colors ARE supported in r132** (corrects a stray "RGB only" comment in the repo):
  a `color` attribute with `itemSize === 4` enables `USE_COLOR_ALPHA` (verified in
  `WebGLPrograms.js` → `vertexAlphas`). `itemSize === 3` is plain RGB. Both work in core
  materials. The codebase deliberately uses RGB + additive-black for fades anyway (see the
  effects doc) — that's a style choice, not an r132 limitation.
- **`InstancedMesh`** exists (`setMatrixAt`, `getMatrixAt`, `instanceMatrix.needsUpdate`) and
  supports per-instance color via **`setColorAt(i, color)` / `instanceColor`** — but **RGB only**
  (the `instanceColor` attribute is allocated `itemSize 3`). No per-instance alpha.
- Material flags used heavily here and stable in r132: `transparent`, `opacity`, `depthTest`,
  `depthWrite`, `blending` (`THREE.AdditiveBlending`), `side` (`FrontSide`/`BackSide`/`DoubleSide`),
  `fog`, `toneMapped`, `flatShading`, `wireframe`, `vertexColors`.

## Lights

- `renderer.physicallyCorrectLights = true` opts into real falloff (so `PointLight`/`SpotLight`
  `decay`/`distance` are physical). In r132 it **defaults to `false`** (verified). The later
  rename to `useLegacyLights` (inverted sense) **has not happened here**.
- `RectAreaLight` works only with Standard/Physical materials and needs `RectAreaLightUniformsLib`
  init from `examples/jsm/` — and casts **no shadows**.

## Misc naming

- **`THREE.MathUtils`** is the math helper namespace (`MathUtils.lerp`, `.clamp`, `.degToRad`,
  `.randFloat`, …). `THREE.Math` still exists in r132 as a **deprecated alias** (via
  `Three.Legacy.js`) but was removed later — **use `THREE.MathUtils`**.
- `PMREMGenerator` has both `fromScene(scene, sigma)` and `fromEquirectangular(texture)` in r132,
  plus `compileEquirectangularShader()` / `compileCubemapShader()`.

## Project-specific conventions that look unusual but are intentional

These aren't r132 quirks, but they'll trip up anyone porting "standard" Three.js patterns into
this repo:

- **`THREE` is passed in, not imported, by the shared `assets/*.js` modules**
  (`makeMoon(THREE, …)`). Reason: each experiment owns its copy of three; the asset library stays
  decoupled. Don't add `import * as THREE from 'three'` to an asset module.
- **Stereo is hand-rolled** in `karaoke/scene/stereo.js` (scissor + viewport per eye, plus a
  `lensShift = 38` px lens-centering offset). Plain `StereoEffect` can't do that offset — that's
  _why_ it's hand-rolled. Don't "simplify" it back to `StereoEffect`.
- **No WebXR, no `EffectComposer`.** Both are off the table for this hardware/stereo approach
  (platform notes + perf/effects docs).
- **Animated props expose `group.userData.update(t, intensity)`**; the render loop drives them.
  Match that contract when adding props.
