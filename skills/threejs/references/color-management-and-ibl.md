---
topic_id: "v2:LAMC"
topic_path: "metal-renderer"
semantic_id: "IE2i8TWxQxcJiStuYDgz6lncOsGzEAAN"
related_ids:
  - "ZG0w579Q2TWZLYoC9HqDQJlYMcmzAAAF"
  - "BODE5nU53h-bmQtYcEqiUtlY-qO2AAAC"
---
# r132 Color Management & IBL

> **Pinned to Three.js r132 (0.132.2).** Verified against `node_modules/three` at
> `REVISION = '132'`. Color was reworked **after** r132: modern tutorials using
> `colorSpace` / `SRGBColorSpace` / `outputColorSpace` describe APIs that **do not exist
> here**. This project uses the older `encoding` system. Reference scene:
> `lit-textures/main.js`.

## The one-time renderer setup

```js
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.outputEncoding = THREE.sRGBEncoding; // r132: constant 3001
renderer.physicallyCorrectLights = true; // real light falloff (decay/distance)
renderer.toneMapping = THREE.ACESFilmicToneMapping; // filmic roll-off, no clipped highlights
renderer.toneMappingExposure = 1.0;
```

Without `outputEncoding = sRGBEncoding` the whole scene looks washed-out / flat. This is the
single most common r132 mistake when copying modern sample code.

## Color vs. data textures — the rule that bites

`sRGBEncoding` (3001) and `LinearEncoding` (3000, the default) are the only two encodings you
need. Tag **color** textures sRGB; leave **data** textures linear.

- **Do** (color maps): `texture.encoding = THREE.sRGBEncoding` on `map`, `emissiveMap`, and any
  `CanvasTexture` you draw UI/labels into. See `lit-textures/main.js` `makeTex()`.
- **Do not** tag data maps sRGB: `normalMap`, `roughnessMap`, `metalnessMap`, `aoMap`,
  `displacementMap`, `bumpMap` stay at the default `LinearEncoding`. Tagging a normal map sRGB
  is the classic "why is my lighting subtly wrong" bug.

```js
const t = new THREE.CanvasTexture(canvas);
t.encoding = THREE.sRGBEncoding; // it's a color map
```

## `Color` is NOT auto-converted in r132

There is no "working color space" in r132. A `new THREE.Color(0xff2d95)` or `setHSL(...)` value
is fed to the shader as-authored; only the **output** is sRGB-encoded by `outputEncoding`. The
`Color` class _has_ `convertSRGBToLinear()` / `copySRGBToLinear()` (verified in
`src/math/Color.js`) but nothing calls it for you. Practical consequences:

- Material `.color` / `.emissive` you pick by eye against the rendered result are already "right"
  — don't go hunting for a conversion call.
- This differs from r152+, where assigning a hex auto-converts from sRGB. **Do not** port
  color-space "fixes" from newer docs back into this project; they'll double-correct.

## IBL: RoomEnvironment + PMREMGenerator (no asset files)

The biggest single "looks real" win for `MeshStandardMaterial` / `MeshPhysicalMaterial`, and it
ships entirely in `examples/jsm/` — works offline in the headset, no HDR download.

```js
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

const pmrem = new THREE.PMREMGenerator(renderer);
pmrem.compileEquirectangularShader();
scene.environment = pmrem.fromScene(
  new RoomEnvironment(renderer),
  0.04,
).texture;
```

- `scene.environment` lights **every** Standard/Physical material at once — cleaner and cheaper
  than a per-material `envMap`. Per-material strength via `material.envMapIntensity`.
- `scene.background = envTex` optionally shows it; leave it unset to keep a dark scene (the
  karaoke scene wants black, so it sets `scene.background` to a flat color instead).
- For a real HDR instead of RoomEnvironment: `RGBELoader` (`examples/jsm/loaders/RGBELoader.js`)
  → `pmrem.fromEquirectangular(hdrTex).texture`. Both `fromScene` and `fromEquirectangular`
  exist in r132.

### IBL is the cheap path — prefer it to more lights

On a phone rendering stereo, one pre-filtered `scene.environment` usually looks better **and**
runs faster than stacking `PointLight`/`SpotLight`s, and it's what makes metalness/roughness
read at all. Add at most one `DirectionalLight` on top for a moving highlight. See the perf doc
for why shadows are the first thing to cut.

## What changed after r132 (so you recognize wrong advice)

| Newer API (NOT in r132)                | r132 equivalent (use this)                    |
| -------------------------------------- | --------------------------------------------- |
| `renderer.outputColorSpace`            | `renderer.outputEncoding`                     |
| `texture.colorSpace = SRGBColorSpace`  | `texture.encoding = THREE.sRGBEncoding`       |
| `THREE.SRGBColorSpace` / `LinearSRGB…` | `THREE.sRGBEncoding` / `THREE.LinearEncoding` |
| `renderer.useLegacyLights = false`     | `renderer.physicallyCorrectLights = true`     |
| auto sRGB→linear on `Color` assignment | none — values are used as authored            |

If you see `colorSpace` anywhere in a snippet, it's post-r132; translate it before using it.
