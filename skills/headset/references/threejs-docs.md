# Three.js — docs for the APIs we use

Curated links into the Three.js docs, scoped to what these experiments actually touch.

**Version:** we pin **`three@0.132.2` (tag `r132`)** — see `../../../CLAUDE.md` → "Stack" for why
(it's the last release shipping both `StereoEffect` and `DeviceOrientationControls` in
`examples/jsm/`). The live docs at threejs.org reflect the **current** release, so for anything
version-sensitive prefer the pinned `r132` source links below; the API pages are close enough
for everyday lookups.

## The two fragile example modules (pin to r132)

These live in `examples/jsm/`, are not in the main API docs, and have drifted/been removed in
later versions. Always read the copy at our tag:

- **StereoEffect** — splits the canvas into two side-by-side eye views.
  [source @ r132](https://github.com/mrdoob/three.js/blob/r132/examples/jsm/effects/StereoEffect.js)
  (we currently render stereo by hand for the `lensShift` offset, but this is the reference impl.)
- **DeviceOrientationControls** — phone motion → camera rotation. **Removed in later releases**,
  so r132 is the boundary.
  [source @ r132](https://github.com/mrdoob/three.js/blob/r132/examples/jsm/controls/DeviceOrientationControls.js)
- Browse all bundled modules at the tag:
  [examples/jsm @ r132](https://github.com/mrdoob/three.js/tree/r132/examples/jsm)

## Core

- [Manual: Creating a scene](https://threejs.org/docs/#manual/en/introduction/Creating-a-scene)
- [WebGLRenderer](https://threejs.org/docs/#api/en/renderers/WebGLRenderer) — `setSize`,
  `setPixelRatio`, and the stereo split: `setScissor`, `setViewport`, `setScissorTest`, `clear`.
- [Scene](https://threejs.org/docs/#api/en/scenes/Scene) ·
  [Fog](https://threejs.org/docs/#api/en/scenes/Fog) ·
  [Color](https://threejs.org/docs/#api/en/math/Color) (`setHSL`)
- [Object3D](https://threejs.org/docs/#api/en/core/Object3D) — `position`, `rotation`,
  `add`, `traverse`, `lookAt`, `updateMatrixWorld`, `getWorldDirection`, `getWorldPosition`.
- [Group](https://threejs.org/docs/#api/en/objects/Group) ·
  [Mesh](https://threejs.org/docs/#api/en/objects/Mesh)

## Cameras

- [PerspectiveCamera](https://threejs.org/docs/#api/en/cameras/PerspectiveCamera)
- [StereoCamera](https://threejs.org/docs/#api/en/cameras/StereoCamera) — `cameraL` / `cameraR`,
  `update(camera)`; the basis for the hand-rolled stereo render in `hello-world/main.js`.

## Geometry (what the assets are built from)

- [BoxGeometry](https://threejs.org/docs/#api/en/geometries/BoxGeometry) ·
  [CylinderGeometry](https://threejs.org/docs/#api/en/geometries/CylinderGeometry) ·
  [PlaneGeometry](https://threejs.org/docs/#api/en/geometries/PlaneGeometry) ·
  [RingGeometry](https://threejs.org/docs/#api/en/geometries/RingGeometry)

## Materials

- [MeshStandardMaterial](https://threejs.org/docs/#api/en/materials/MeshStandardMaterial) —
  PBR, **lit** (needs a light in the scene, or it's black). The workhorse for textured surfaces.
  [MeshPhysicalMaterial](https://threejs.org/docs/#api/en/materials/MeshPhysicalMaterial) extends
  it with `clearcoat`, `transmission`, `sheen` — heavier; reach for it only when Standard can't do it.
- [MeshBasicMaterial](https://threejs.org/docs/#api/en/materials/MeshBasicMaterial) — unlit,
  ignores lights entirely. Used for reticle/labels with `depthTest:false`, `fog:false`.
  [MeshLambertMaterial](https://threejs.org/docs/#api/en/materials/MeshLambertMaterial) /
  [MeshPhongMaterial](https://threejs.org/docs/#api/en/materials/MeshPhongMaterial) — cheaper lit
  models (Gouraud / Blinn-Phong) if Standard is too costly on the phone GPU.
- [Material](https://threejs.org/docs/#api/en/materials/Material) — shared flags:
  `transparent`, `opacity`, `depthTest`, `side` (`THREE.FrontSide` / `BackSide` / `DoubleSide` —
  `BackSide` on a big sphere = cheap skybox), `wireframe`.

### MeshStandardMaterial map slots (the texture channels)

All take a `Texture`. Set `material.needsUpdate = true` if you swap one after first render.

| Slot              | What it drives          | Color or data?                        | Notes                                          |
| ----------------- | ----------------------- | ------------------------------------- | ---------------------------------------------- |
| `map`             | base/albedo color       | **color** → `encoding = sRGBEncoding` | multiplied by `.color`                         |
| `roughnessMap`    | per-pixel roughness     | data (linear)                         | uses green channel; multiplied by `.roughness` |
| `metalnessMap`    | per-pixel metalness     | data (linear)                         | uses blue channel; multiplied by `.metalness`  |
| `normalMap`       | surface normal detail   | data (linear)                         | strength via `normalScale` (Vector2)           |
| `bumpMap`         | grayscale height fake   | data (linear)                         | cheaper than normal map, lower quality         |
| `displacementMap` | actual vertex push      | data (linear)                         | needs geometry with enough segments to push    |
| `aoMap`           | baked ambient occlusion | data (linear)                         | **requires a 2nd UV set** — see uv2 note       |
| `emissiveMap`     | glow areas              | **color** → `encoding = sRGBEncoding` | paired with `.emissive` + `.emissiveIntensity` |
| `envMap`          | reflections / IBL       | special (see env maps)                | strength via `.envMapIntensity`                |

**uv2 gotcha:** `aoMap` (and `lightMap`) read `geometry.attributes.uv2`, not `uv`. Built-in
geometries only ship `uv`. Copy it once: `geo.setAttribute('uv2', new THREE.BufferAttribute(geo.attributes.uv.array, 2))`.
Forget this and the AO map silently does nothing.

## Textures

- [Texture](https://threejs.org/docs/#api/en/textures/Texture) — the config knobs:
  - **Tiling:** `wrapS` / `wrapT` (`THREE.RepeatWrapping` to tile, `ClampToEdgeWrapping`,
    `MirroredRepeatWrapping`) + `repeat` (Vector2). Repeat only tiles if wrap is set to Repeat.
  - **Sharpness at grazing angles:** `anisotropy` — big readability win in VR where you look
    across floors/walls. Cap it: `renderer.capabilities.getMaxAnisotropy()`.
  - **Filtering:** `magFilter` / `minFilter` (`LinearFilter`, `NearestFilter` for pixel-art,
    the `*MipmapLinearFilter` family for distance). `generateMipmaps` (default true).
  - `offset` (Vector2), `flipY` (default true), `needsUpdate`.
- [TextureLoader](https://threejs.org/docs/#api/en/loaders/TextureLoader) —
  `load(url, onLoad, onProgress, onError)`. Returns the `Texture` synchronously (image fills in
  later). Share a [LoadingManager](https://threejs.org/docs/#api/en/loaders/managers/LoadingManager)
  across loaders to know when _everything_ is ready (good for a "tap to enter" gate).
- [CubeTextureLoader](https://threejs.org/docs/#api/en/loaders/CubeTextureLoader) — 6 images for
  a skybox / reflection cube; `load([px,nx,py,ny,pz,nz])`.
- [CanvasTexture](https://threejs.org/docs/#api/en/textures/CanvasTexture) — text/number labels
  drawn to a 2D canvas (the in-world panel).

## Color management (r132 — VERSION-CRITICAL, read this)

Color was reworked **after** r132. Today's tutorials use `texture.colorSpace = THREE.SRGBColorSpace`
and `renderer.outputColorSpace`. **Those do not exist in r132.** Our version uses `encoding`:

- `renderer.outputEncoding = THREE.sRGBEncoding` — set once. Without it everything looks washed out.
- **Color textures** (`map`, `emissiveMap`): `texture.encoding = THREE.sRGBEncoding`.
- **Data textures** (`normalMap`, `roughnessMap`, `metalnessMap`, `aoMap`, `displacementMap`):
  leave at the default `THREE.LinearEncoding`. Tagging these sRGB is the classic "why is my
  normal map subtly wrong" bug.
- `renderer.physicallyCorrectLights = true` — opt into real falloff so `PointLight`/`SpotLight`
  `decay`/`distance` behave physically. (Renamed `useLegacyLights` in later releases — not here.)
- Tone mapping: `renderer.toneMapping = THREE.ACESFilmicToneMapping` + `toneMappingExposure`
  for a filmic roll-off instead of clipped highlights.
- [r132 migration guide](https://github.com/mrdoob/three.js/wiki/Migration-Guide#r131--r132) ·
  [Color management discussion (later, for contrast)](https://threejs.org/docs/#manual/en/introduction/Color-management)

## Lights

- [AmbientLight](https://threejs.org/docs/#api/en/lights/AmbientLight) — flat fill from all
  directions, no shadows, no direction. Cheap base so shadowed sides aren't pure black.
- [HemisphereLight](https://threejs.org/docs/#api/en/lights/HemisphereLight) —
  `(skyColor, groundColor, intensity)`. Sky-from-above / ground-bounce-from-below; nicer ambient
  than flat `AmbientLight` for outdoor-ish scenes. No shadows.
- [DirectionalLight](https://threejs.org/docs/#api/en/lights/DirectionalLight) — `(color, intensity)`,
  parallel rays (sun). Aim via `.position` → `.target`. **Can cast shadows** (ortho shadow camera).
- [PointLight](https://threejs.org/docs/#api/en/lights/PointLight) —
  `(color, intensity, distance, decay)`, omni from a point. Can cast shadows (6-face cube — pricey).
- [SpotLight](https://threejs.org/docs/#api/en/lights/SpotLight) —
  `(color, intensity, distance, angle, penumbra, decay)`, cone. `penumbra` (0–1) softens the edge.
  Can cast shadows.
- [RectAreaLight](https://threejs.org/docs/#api/en/lights/RectAreaLight) —
  `(color, intensity, width, height)`, soft panel light. **No shadows.** Only works with
  Standard/Physical, and needs `RectAreaLightUniformsLib` init from `examples/jsm/`.
- [LightProbe](https://threejs.org/docs/#api/en/lights/LightProbe) /
  [shadow setup](https://threejs.org/docs/#api/en/lights/shadows/LightShadow) — `light.castShadow`,
  `mesh.castShadow` / `.receiveShadow`, `renderer.shadowMap.enabled`, `light.shadow.mapSize`.

## Environment maps & image-based lighting (IBL)

The biggest single jump in "looks real" for a PBR material — it gives metals something to reflect
and fills shadows with believable ambient color.

- [PMREMGenerator](https://threejs.org/docs/#api/en/extras/PMREMGenerator) — pre-filters an
  equirect/HDR image into the mip-chain Standard/Physical materials expect:
  `pmrem.fromEquirectangular(tex).texture`.
- Set `scene.environment = envTex` to light **every** Standard material at once (cleaner than
  per-material `envMap`). Optionally `scene.background = envTex` to show it.
- [RGBELoader @ r132](https://github.com/mrdoob/three.js/blob/r132/examples/jsm/loaders/RGBELoader.js)
  — loads `.hdr` equirect environments (the usual IBL source).

## Interaction & math (gaze + clicker)

- [Raycaster](https://threejs.org/docs/#api/en/core/Raycaster) — `set(origin, dir)`,
  `intersectObjects`; cast from camera center each frame to find the gazed object.
- [Vector3](https://threejs.org/docs/#api/en/math/Vector3) ·
  [Vector2](https://threejs.org/docs/#api/en/math/Vector2) ·
  [Box3](https://threejs.org/docs/#api/en/math/Box3) (`setFromObject` — used to sit assets on the floor)

## VR / mobile perf (textures & lighting cost double here)

We render the scene **twice per frame** (one viewport per eye), on a phone GPU, with no active
cooling. Budget accordingly:

- **Shadows are the first thing to cut.** Real-time shadow maps are expensive and you pay per eye.
  Prefer a **baked `aoMap`** + a good `scene.environment` over `castShadow`. If you must, keep
  one `DirectionalLight` shadow at a small `shadow.mapSize` (512).
- **IBL beats more lights.** One pre-filtered `scene.environment` usually looks better _and_ runs
  faster than stacking several real lights — and it's the cheap path to convincing metal/roughness.
- **Texture sizes:** keep maps ≤ 1024² (2048² only when truly needed); mipmaps on. Big textures
  blow the mobile memory/bandwidth budget fast.
- **Anisotropy** is a cheap, high-value win for floors/walls you look across — but read the cap
  from `renderer.capabilities.getMaxAnisotropy()`, don't hardcode 16.
- Watch `renderer.setPixelRatio` — capping at ~2 keeps fill-rate sane on high-DPI phones.
