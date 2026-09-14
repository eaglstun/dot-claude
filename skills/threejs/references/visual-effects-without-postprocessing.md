---
topic_id: "v2:LGLN"
topic_path: "metal-renderer"
semantic_id: "J_2kLm9VQjcd_Asr4Sgr9qHpOsniUAAP"
related_ids:
  - "x_M0SG8UQreJxDok6QwK95WYS4xEcAAD"
  - "B_QgbjDv0zcp1Q8HYjii1LTZAMObQAAJ"
---
# Visual Effects in r132 (geometry/material only, phone-safe)

> **Pinned to Three.js r132 (0.132.2).** Constraint: **no post-processing** — hand-rolled stereo
> means full-frame passes break eye fusion (see the perf doc). Every effect here lives in the
> scene as geometry + material, so it renders correctly in both eyes for free. House examples:
> `assets/threejs/neon-sign.js`, `assets/threejs/moon.js`, `assets/threejs/disco-ball.js`,
> `karaoke/scene/truck-trails.js`, `karaoke/scene/squiggles.js`.

## The core glow idiom: unlit + additive + fog-immune

Every "light-emitting" thing in this project is the same recipe — an unlit material that _adds_
its color to whatever's behind it, ignores fog, and never writes depth (so it can't occlude the
solid world, but the solid world still hides it via `depthTest`).

```js
new THREE.MeshBasicMaterial({
  color,
  transparent: true,
  blending: THREE.AdditiveBlending,
  depthWrite: false, // don't occlude; allow halos to stack
  depthTest: true, // world geometry still hides it (default)
  fog: false, // punch through scene fog like a real light
  toneMapped: false, // keep the authored brightness; don't let ACES roll it off
});
```

`toneMapped: false` matters whenever `outputEncoding`/tone mapping is on (it is in lit-textures):
it keeps neon at the brightness you picked instead of letting the filmic curve dim it.

**Do** use this for: neon tubes, coronas, sparkle glints, trails, energy ribbons, stars.
**Do not** use additive for anything that should look _solid_ — additive over a bright background
washes out (it only ever adds light).

## Glowing lines & paths: CatmullRomCurve3 → TubeGeometry

The house way to draw any glowing line, bolt, squiggle, or comet trail. A smooth tube reads far
better than `THREE.Line` (which is 1px and ignores `linewidth` on most platforms).

```js
const curve = new THREE.CatmullRomCurve3(points /* Vector3[] */);
const geo = new THREE.TubeGeometry(
  curve,
  tubularSegments,
  radius,
  radialSegments,
  /*closed*/ false,
);
```

- A **core** tube + one or two fatter, dimmer **corona** tubes = a convincing glow (neon-sign.js
  uses radius ×2.4 and ×4.2 at low opacity).
- See `assets/threejs/neon-sign.js` (lightning-bolt path, per-segment flicker) and
  `karaoke/scene/squiggles.js` (wavy out-of-plane paths reusing the neon asset).

## Per-vertex fade without per-vertex alpha (the black-color trick)

Additive blending means **black adds nothing** → a vertex colored black is invisible. So you can
fade a trail along its length using only an RGB `color` attribute, scaling each vertex's color
toward black at the tail. This is the trick in `karaoke/scene/truck-trails.js` `buildTube()`:

```js
g.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3)); // itemSize 3 = RGB
// material: vertexColors: true, blending: AdditiveBlending
```

> **r132 accuracy note (corrects a comment in the source):** r132 **does** support RGBA vertex
> colors — a `color` attribute with `itemSize === 4` flips on `USE_COLOR_ALPHA` in the core
> materials (verified in `WebGLPrograms.js`: `vertexAlphas` requires `itemSize === 4`). So
> per-vertex _alpha_ is technically available. The black-color trick is still preferred here
> because it's simpler (one RGB attribute, no transparent-sort concerns) and, under additive
> blending, fading color→black and fading alpha→0 look identical. For **non-additive** fades
> (e.g. an alpha-blended ribbon), reach for the `itemSize:4` color attribute instead.

## Particles: a fixed Points pool (not spawn/destroy)

For sparks, embers, drifting motes. The pattern in `truck-trails.js` (style `'particles'`):
allocate a fixed-size `BufferGeometry` once, recycle slots, and **park dead particles invisible
by zeroing their vertex color** (black = additive-invisible) instead of resizing buffers.

```js
const pmat = new THREE.PointsMaterial({
  size: 0.55,
  map: softSprite,
  vertexColors: true,
  transparent: true,
  blending: THREE.AdditiveBlending,
  depthWrite: false,
  sizeAttenuation: true,
  fog: false,
  toneMapped: false,
});
// each frame: write ppos[]/pcol[], then
pgeo.attributes.position.needsUpdate = true;
pgeo.attributes.color.needsUpdate = true;
```

- `sizeAttenuation: true` shrinks distant points (perspective). The soft round look comes from a
  64² radial-gradient `CanvasTexture` as `map` (generated once, no asset file).
- **Perf:** points are billboarded fragments — big `size` = overdraw, ×2 eyes. Keep the pool
  bounded (the trail caps at 70). **iOS caveat:** GLSL `gl_PointSize` is clamped by the driver, so
  very large `size` won't grow past the cap and can pop; if you need big soft blobs, use Sprites
  or quads instead of Points.

## Sprites: camera-facing glints

For point-glints that should always face you (mirror-ball sparkle in `assets/threejs/disco-ball.js`):

```js
const m = new THREE.SpriteMaterial({
  map: softSprite,
  color,
  blending: THREE.AdditiveBlending,
  depthWrite: false,
  fog: false,
  toneMapped: false,
});
const s = new THREE.Sprite(m.clone()); // clone so each can flicker independently
```

`Sprite` auto-billboards (no manual lookAt). Cheap individually; same overdraw caution as Points.

## Camera-facing ribbons (manual billboard)

When a flat strip must face the camera but follow a path (the literal "rainbow" trail), build the
quad strip yourself: width axis = `tangent × (camera.position − point)`, normalized. See
`buildRainbow()` in `truck-trails.js`. Use `side: THREE.DoubleSide` so it's visible from both
faces, and the same black-color fade along its length.

## Animation conventions (reuse these, the render loop expects them)

- **`group.userData.update(t, intensity)`** — attach an updater to any animated prop; the render
  loop calls it each frame. `intensity` (0..1) ramps the whole effect on at reveal. Pattern in
  `assets/threejs/moon.js`, `assets/threejs/neon-sign.js`, `karaoke/scene/squiggles.js`.
- **Free-running clock** for motion that must stay smooth when song time resets to 0: keep a
  local `clock += dt` accumulator, separate from song time (`squiggles.js` `squiggleClock`).
- **Cheap "live" flicker without allocation:** pre-build a few geometry **variants** and cycle
  `.visible` + opacity per frame (electric arcs in `moon.js`) — fakes crackling electricity with
  zero per-frame geometry work. Far cheaper than rebuilding a jagged line each frame.
- **Flicker math:** product of two out-of-phase sines (`Math.sin(t*33)*Math.sin(t*7.3)`) gives
  organic, non-periodic buzz/dropout — used for the neon "burnt-out segment" and the arcs.

## What to avoid

- **No `EffectComposer` / post passes** — breaks stereo (see perf doc). All "glow" is additive
  geometry, not a bloom pass.
- **No `THREE.Line` for thick glowing lines** — `linewidth` is ignored on most GL backends; use a
  `TubeGeometry`. (`Line`/`LineBasicMaterial` is fine for the hair-thin electric arcs in moon.js,
  where 1px _is_ the look.)
- **Don't forget `geometry.dispose()`** when rebuilding geometry each frame, or you leak GPU
  buffers.
