---
semantic_id: "Rr2iDRZQYSEdXM8OZ7qFetIZK4v3QAAB"
related_ids:
  - "xK0Cjx6wYXSNhI2OYjqXdsBJI_i3QAAH"
  - "ZG0w579Q2TWZLYoC9HqDQJlYMcmzAAAF"
---
# Water.js and Water2.js — reflective water surfaces, and why they are not a simulation

The two water addons that ship with Three.js (`examples/jsm/objects/Water.js` and
`Water2.js`) produce a convincing lake or river surface using **planar reflection plus
scrolling normal maps**. Neither one simulates anything: there is no velocity field, no
pressure, no mass, and nothing in either shader knows what a fluid is. They are a _look_.
If you need actual fluid behaviour, see `fluid-simulation.md`; if you need a wave
_surface_ driven by a real height field, see `gpucomputationrenderer.md`. This file covers
what the two addons actually do, what they cost, and the one that matters here — **Water.js
renders your whole scene a second time**, which in the hand-rolled stereo project means
four scene renders per frame.

**Version scope:** both addons exist in **r132 and r180** alike, and the API below is
verified against current `dev`. The option sets have been stable for years, but if you're
on r132 and something is missing, check the pinned copy before assuming the doc is wrong.
Import path differs: `three/examples/jsm/objects/Water.js` (r132) vs
`three/addons/objects/Water.js` (r180) — see `r180-api-surface.md`.

## Water.js — planar reflection

```js
import { Water } from "three/addons/objects/Water.js";

const water = new Water(new THREE.PlaneGeometry(1000, 1000), {
  textureWidth: 512,
  textureHeight: 512,
  waterNormals: normalTexture, // needs wrapS/wrapT = RepeatWrapping
  sunDirection: new THREE.Vector3(),
  sunColor: 0xffffff,
  waterColor: 0x001e0f,
  distortionScale: 3.7,
  fog: scene.fog !== undefined,
});
water.rotation.x = -Math.PI / 2;
scene.add(water);

// in the loop — nothing animates unless you drive this yourself
water.material.uniforms.time.value += delta;
```

Verified options and defaults:

| option            | default                          |
| ----------------- | -------------------------------- |
| `textureWidth`    | `512`                            |
| `textureHeight`   | `512`                            |
| `clipBias`        | `0.0`                            |
| `alpha`           | `1.0`                            |
| `time`            | `0.0`                            |
| `waterNormals`    | `null`                           |
| `sunDirection`    | `Vector3(0.70707, 0.70707, 0.0)` |
| `sunColor`        | `0xffffff`                       |
| `waterColor`      | `0x7F7F7F`                       |
| `eye`             | `Vector3(0, 0, 0)`               |
| `distortionScale` | `20.0`                           |
| `side`            | `FrontSide`                      |
| `fog`             | `false`                          |

Uniforms it builds: `normalSampler`, `mirrorSampler`, `alpha`, `time`, `size`,
`distortionScale`, `textureMatrix`, `sunColor`, `sunDirection`, `eye`, `waterColor`,
merged with the standard fog and lights uniform blocks.

### How it works, and the cost

Water.js keeps a `WebGLRenderTarget` (512×512, `HalfFloatType` by default) and, **every
frame it is drawn**, renders the scene from a mirrored camera into that target. It then
samples the reflection with an offset derived from the animated normal map.

That is a **full extra scene render per frame**, with all the draw calls, all the shadow
work, everything. It is the dominant cost of using this addon, and it scales with your
scene, not with the water's size on screen.

**In the phone-in-headset project this is a trap.** You are already rendering the scene
twice for hand-rolled stereo. Add Water.js and each eye triggers its own mirrored render:
**four scene renders per frame** on a phone GPU. On top of that, a planar reflection
computed from one eye's camera is _wrong_ for the other eye — reflections are
view-dependent, so a shared reflection breaks stereo disparity exactly where the eye is
most sensitive to it, on a specular surface.

If you want water in that project, use Water2 (no scene re-render) or a normal-mapped
`MeshStandardMaterial` with an env map. See `phone-gpu-stereo-performance.md`.

Cheap mitigations if you must keep it on desktop:

- Drop `textureWidth`/`textureHeight` to 256 — reflections are distorted anyway, and the
  normal-map perturbation hides the resolution loss almost entirely.
- Put reflected-but-irrelevant objects on a layer the mirror camera skips.

## Water2.js — flow maps, no reflection cost

Water2 is the better-behaved sibling: a **flow map** drives directional scrolling of two
normal maps, and it uses a `Reflector`/`Refractor` pair only if you wire them up. The
motion is what sells it — flowing rivers, currents that bend around rocks.

Verified options and defaults:

| option          | default                        |
| --------------- | ------------------------------ |
| `color`         | `0xFFFFFF`                     |
| `textureWidth`  | `512`                          |
| `textureHeight` | `512`                          |
| `clipBias`      | `0`                            |
| `flowDirection` | `Vector2(1, 0)`                |
| `flowSpeed`     | `0.03`                         |
| `reflectivity`  | `0.02`                         |
| `scale`         | `1`                            |
| `shader`        | the module's own `WaterShader` |
| `flowMap`       | `undefined`                    |
| `normalMap0`    | `Water_1_M_Normal.jpg`         |
| `normalMap1`    | `Water_2_M_Normal.jpg`         |

### The half-cycle trick, which is worth stealing

The interesting part of Water2 is how it hides the seam in scrolling UVs. A single
scrolling normal map has to reset eventually, and the reset pops. Water2 runs **two
offsets half a cycle apart** (cycle length 0.15), samples the normal maps at both, and
crossfades between them based on where each offset sits in its cycle. When one is about to
wrap, its weight is zero.

This is a general technique, not a water technique. Any time you need endlessly scrolling
UVs without a visible reset — flowing lava, drifting fog, a conveyor, sliding cloud
shadows — two half-cycle-offset samples with a triangular crossfade will do it, and it's
about four lines of GLSL. It composes cleanly with the `onBeforeCompile` patching in
`material-injection-and-triplanar.md`.

A `flowMap` (an RG texture encoding a 2D direction per texel) makes the scroll direction
vary across the surface, which is what turns a flat scroll into something that reads as a
current.

## Choosing between them, and against them

| you want                                        | use                                                           |
| ----------------------------------------------- | ------------------------------------------------------------- |
| a still, mirror-like lake on desktop            | **Water.js**, and accept the extra scene render               |
| a river, current, or any directional flow       | **Water2.js**                                                 |
| water in the stereo/phone project               | **neither as-is** — normal-mapped standard material + env map |
| waves that respond to something dropped in them | `gpucomputationrenderer.md` (height field)                    |
| smoke, ink, actual fluid motion                 | `fluid-simulation.md`                                         |

The honest summary: these two addons are excellent at looking like water sitting there, and
incapable of looking like water _doing_ anything. The moment the requirement includes the
word "interacts", they are the wrong tool and no amount of parameter tuning changes that.
