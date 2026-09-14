---
name: threejs
description: Version-specific Three.js reference for the phone VR project's pinned r132 renderer and desktop r180 visual techniques. Use when writing or debugging Three.js, choosing an effect implementation, or checking APIs and constraints for the correct project version.
metadata:
  public: 'true'
  topic_id: v2:LBAE
  topic_path: metal-renderer/threejs-api
  semantic_id: BODE5nU53h-bmQtYcEqiUtlY-qO2AAAC
  related_ids: '["VqWBJfUu8muHyBteNFiyUtH8eufYAAAB","cMSY9ylTB0cZ2QpIcEqvUikNfIe5IAAL"]'
---

# Three.js — local reference notes

Hand-written notes from real projects, not a mirror of the docs.

**Check the version scope before applying anything here.** Two projects feed this, and they
have opposite constraints:

| files                                                                        | project                | constraints                                                                   |
| ---------------------------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------- |
| `references/r132-*`, `phone-gpu-*`, `visual-effects-*`, `color-management-*` | phone-in-headset VR    | **pinned r132**, hand-rolled stereo, no WebXR, phone GPU, no full-screen post |
| `references/r180-*`, `dithering-*`, `material-injection-*`, `nes-*`          | CAPRICCIO city builder | **r180**, desktop, a full-screen post pass is fine                            |

Newer Three.js docs describe APIs that do not exist or behave differently in r132, which is
why the r132 files exist at all. Conversely, a desktop technique that assumes a post pass or
a generous draw-call budget must not be dropped into the VR project unexamined.

Consulted by the `threejs-researcher` agent (alongside the `headset` skill's `threejs-docs.md`).

## Index

- **references/r132-api-gotchas.md** — r132 API surface & migration gotchas (what's different from modern Three.js).
- **references/visual-effects-without-postprocessing.md** — visual effects in r132 done geometry/material-only,
  the phone-safe way (no full-screen post that smears both eyes).
- **references/phone-gpu-stereo-performance.md** — performance on a phone GPU rendering stereo (cost budgets).
- **references/color-management-and-ibl.md** — r132 color management & image-based lighting.

### Techniques (desktop r180, mostly version-independent)

- **references/r180-api-surface.md** — the r180 API surface for CAPRICCIO's actual import set
  (`src/vendor-imports.json`), diffed against r132: what was removed, what is new, the
  `outputEncoding` → `outputColorSpace` breakage, and which names are safe to move between
  the two projects.
- **references/glitch-and-rgb-shift.md** — the built-in `RGBShiftShader` / `GlitchPass` /
  `AfterimagePass` / `FilmPass` / `DotScreenPass` (present in **both** r132 and r180): uniforms and
  real defaults, `GlitchPass`'s frame-counted fire/aftershock/bypass cycle, the
  `three/addons/*` vs `three/examples/jsm/*` import trap, and why full-screen post is
  fine in CAPRICCIO but breaks stereo in the headset project.
- **references/material-injection-and-triplanar.md** — `onBeforeCompile` to patch Three.js's own shader
  instead of replacing it (keeping lights, shadows and fog), custom per-vertex attributes, and
  triplanar world-space projection with distance-adaptive frequency.
- **references/dithering-and-halftone.md** — 1-bit rendering: the Atkinson error-diffusion algorithm and
  why it cannot be a fragment shader, ordered/Bayer vs blue noise for the realtime path,
  void-and-cluster generation, gradient-biased thresholds, and dither cell sizing.
- **references/nes-palette-and-sprite-limits.md** — rendering under NES PPU constraints, the
  Three.js half: the toon-ramp pre-pass, the 16×15 attribute pass that scores all four
  palettes per **16×16 block** (the source of attribute clash), palette-choice hysteresis so
  blocks don't strobe, resolve/composite, the sRGB-vs-linear matching trap, and integer +
  8:7 presentation. **The hardware itself** — the verified 64-entry 2C02 palette, the 25-color
  ceiling, tile/nametable/OAM structure, sprite limits, the grayscale and colour-emphasis
  bits, and which limits honestly transfer to 3D — moved to the `game-consoles` skill
  (`skills/game-consoles/references/nes.md`). The palette array lives there, not here.
- **references/vector-display-and-plotter-linework.md** — the Sketchpad / robot-draftsman look:
  vector-CRT vs pen-plotter tells, why `EdgesGeometry` misses silhouettes and what that forces,
  chaining segment soup into Eulerian pen strokes (with the greedy-vs-Hierholzer measurement),
  reusing one decomposition across a whole cityscape because chaining is topology-only,
  baking a single cumulative `aPen` attribute so the whole draw animation is one uniform,
  validated wobble/beam-tip shaders, additive-vs-multiply crossings, and hidden lines in two
  draw passes with no render targets. **Needs no post pass**, so unlike the rest of this
  section it ports to the phone-in-headset project intact. **In use in CAPRICCIO** —
  `src/25-plotter.ts` plots the megastructure horizon, swept by azimuth, drawing in over
  ~17s at load.
- **references/terrain-contour-lines.md** — topographic contours on terrain, both ways: the
  `fwidth`-based shader band (pixel-constant width, the Nyquist fade with its **measured**
  duty-cycle formula and the one case where it runs 5% dark, interval LOD that fades alternate
  lines rather than dissolving, index contours pinned to base heights across LOD, cliff
  dropout), and marching-squares extraction to real polylines (verified case table,
  centre-average saddle disambiguation, exact-hit levels). The polyline path emits segment
  soup, so it feeds `vector-display-and-plotter-linework.md`'s chainer directly — a topo map
  that draws itself contour by contour. Includes the bilinear-vs-triangulated draping error
  (measured) and why a constant Y lift is the wrong fix. **Needs no post pass.** **In use in
  CAPRICCIO** — the shader path, in `masonry()` in `src/00-shaders.ts`, at an interval pinned
  to the terrace step. Note what the terrain measurement there found: on a terraced world 90%
  of the ground is dead flat, so contours only ever describe the risers, and no interval
  serves both regimes.

### Core API notes (manual-sourced, version-independent, not yet used by either project)

- **references/animation-system.md** — `AnimationMixer`/`AnimationClip`/`KeyframeTrack`/
  `AnimationAction` for driving clips off an imported rigged/morph-target model, which loaders
  support it, and why it's a different thing from the phone-in-headset project's actual
  `userData.update(t, intensity)` prop-animation convention.
- **references/fog.md** — `THREE.Fog` (linear near/far) vs `THREE.FogExp2` (exponential),
  why `scene.background` must match the fog color, and the per-material `fog` opt-out for
  interiors/cockpits.

### Simulation & GPGPU — Three.js has no physics or fluids, so these are the substrates

Start at `fluid-simulation.md` if the question is "can Three.js do fluids" (no, and here's
what to build instead); start at `gpucomputationrenderer.md` if you need GPU state on r132.

- **references/water-and-flow-map-shaders.md** — the two water addons, verified options and
  defaults for both. `Water.js` is planar reflection and **re-renders the entire scene every
  frame** — which in the hand-rolled stereo project means four scene renders, with a
  reflection that's view-dependent and therefore wrong for the second eye. `Water2.js` is
  flow-map scrolling with no re-render, and its **half-cycle crossfade trick** for
  seamless scrolling UVs is worth stealing for lava, fog, or anything else that scrolls
  forever. Neither simulates anything.
- **references/gpucomputationrenderer.md** — the ping-pong float-texture GPGPU helper, the
  only real option on **r132**. Verified API (note `init()` returns **`null` on success** and
  a string on failure), the variable/dependency model, the auto-injected `resolution` and
  per-dependency samplers, half-float precision traps for accumulating positions, the
  gather-only restriction that shapes every algorithm, and the rule that a view-independent
  sim is stepped **once per frame, not once per eye**.
- **references/tsl-compute-and-webgpu.md** — real compute shaders on **r180 + WebGPURenderer**:
  `Fn()().compute(count)`, `storage`/`instancedArray`/`attributeArray` with `.element()`,
  `instanceIndex` and the workgroup IDs. Includes a verified surprise — `renderer.compute()`
  **also runs on the WebGL fallback backend**, via transform feedback with
  `RASTERIZER_DISCARD` — plus an honest boundary on what that path has and hasn't been
  confirmed to support. **Does not exist on r132.**
- **references/fluid-simulation.md** — the Stable Fluids / GPU Gems 38 solver: the verified
  8-stage pass order, Dobryakov's working default constants (MIT licensed), why vorticity
  confinement is a deliberate fudge that puts back what semi-Lagrangian advection smears
  out, and the cost analysis that matters — **the single 1024² dye advection outweighs the
  entire 20-iteration pressure solve**, and 27 render-target switches per frame is the real
  mobile cost. Verdict per project: viable in CAPRICCIO, **no** on the phone, with ranked
  cheaper alternatives.
