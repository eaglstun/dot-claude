---
topic_path: "metal-renderer/threejs-api"
related_ids:
  - "J_2kLm9VQjcd_Asr4Sgr9qHpOsniUAAP"
  - "3_SU5xJ60Aeh6RtLdnKw1uHIMO6w0AAC"
semantic_id: "B_QgbjDv0zcp1Q8HYjii1LTZAMObQAAJ"
---

# RGB Shift, Glitch & the Built-in Post Passes

> Verified by reading `examples/jsm/` in **both** project installs — versions `0.132.2`
> and `0.180.0`.
> **The four passes and three shaders below exist, byte-for-byte equivalent in API terms, in both
> versions.** What differs is the import path and whether you're allowed to use them at all.

Three.js ships the chromatic-aberration / VHS-glitch look in the box. You do not need a library.

| file (under `examples/jsm/`)       | r132 | r180 |
| ---------------------------------- | ---- | ---- |
| `shaders/RGBShiftShader.js`        | ✅   | ✅   |
| `shaders/DigitalGlitch.js`         | ✅   | ✅   |
| `shaders/AfterimageShader.js`      | ✅   | ✅   |
| `postprocessing/GlitchPass.js`     | ✅   | ✅   |
| `postprocessing/AfterimagePass.js` | ✅   | ✅   |
| `postprocessing/FilmPass.js`       | ✅   | ✅   |
| `postprocessing/DotScreenPass.js`  | ✅   | ✅   |

## `RGBShiftShader` — the plain channel separation

The whole effect is four lines of GLSL. Red samples at `+offset`, blue at `-offset`, green stays
put, alpha follows green:

```glsl
vec2 offset = amount * vec2( cos(angle), sin(angle) );
gl_FragColor = vec4(
  texture2D(tDiffuse, vUv + offset).r,
  texture2D(tDiffuse, vUv         ).g,
  texture2D(tDiffuse, vUv - offset).b,
  texture2D(tDiffuse, vUv         ).a );
```

Uniforms — only two you'd ever touch:

- **`amount`** (default `0.005`) — shift distance where **`1` is the full width of the input**, so
  useful values are tiny. `0.002` is a subtle CRT fringe; `0.02` is already aggressive.
- **`angle`** (default `0.0`) — shift direction in **radians**. Animate this for the wobble; pulse
  `amount` for an impact hit.

Note the offset is a flat screen-space vector: the shift is uniform across the frame, not radial.
Real lens chromatic aberration grows toward the edges — if that's the goal, scale `amount` by
`distance(vUv, vec2(0.5))` in a patched copy of the shader.

## `GlitchPass` — a state machine, not a constant effect

`new GlitchPass( dt_size = 64 )` builds a `dt_size²` displacement heightmap and drives
`DigitalGlitch`. It does **not** glitch continuously. Each frame it picks one of three branches:

- **Fire** — when `_curF % _randX === 0`, or always if `goWild = true`. Randomizes `amount`
  (`Math.random()/30`), `angle` over ±π, `seed_x`/`seed_y` over ±1, both `distortion_*` over 0–1,
  then reseeds the trigger.
- **Aftershock** — for the first fifth of the interval after a fire, a milder version
  (`amount` = `Math.random()/90`, seeds over ±0.3).
- **Bypass** — otherwise sets `byp = 1`, which short-circuits the shader to a straight copy.

The trigger interval is `MathUtils.randInt(120, 240)` **frames**, not seconds — so at 60 fps it
fires roughly every 2–4 s, and on a machine running at 120 fps it fires **twice as often**. That
frame-rate coupling is in the stock source; if you need deterministic pacing, drive the uniforms
yourself instead of using the pass.

`goWild = true` forces the fire branch every frame — that's your "screen is dying" mode.

Companion default worth knowing: `new AfterimagePass( damp = 0.96 )` — higher `damp` means longer
trails, adjustable live via `pass.uniforms.damp.value`.

## The import-path trap between the two projects

**r132's `package.json` has no `exports` field at all.** The `three/addons/*` alias does not
resolve there — it was introduced later. r180 defines both:

```json
"./examples/jsm/*": "./examples/jsm/*",
"./addons/*":       "./examples/jsm/*"
```

So:

- `three/examples/jsm/shaders/RGBShiftShader.js` — **works in both.** Use this spelling for
  anything that might move between the repos.
- `three/addons/shaders/RGBShiftShader.js` — **r180 only.** Modern examples and the r180 source's
  own `@three_import` comments all use this form, so it's what you'll copy off the internet, and
  it will fail on the headset project with a bare module-resolution error.

## Using it in CAPRICCIO (r180, desktop) — fine, drop it in

```js
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { RGBShiftShader } from "three/addons/shaders/RGBShiftShader.js";

const rgb = new ShaderPass(RGBShiftShader);
rgb.uniforms.amount.value = 0.0025;
composer.addPass(rgb);
```

## Why this is banned in the headset project (r132)

Not a perf objection — a correctness one. **A full-screen pass runs over the entire framebuffer,
and that framebuffer holds both eye viewports side by side.** An RGB shift therefore smears colour
horizontally _across the seam between the two eyes_: pixels near the right edge of the left eye get
channel data from the left edge of the right eye. Each eye receives a different, wrong image at the
boundary, which is a stereo-fusion failure, not a style. Same argument kills `GlitchPass`,
`FilmPass`, and every other `EffectComposer` pass here — see
`visual-effects-without-postprocessing.md` for the standing rule and the geometry/material-only
alternatives.

The correct-but-expensive fix is to render **each eye into its own `WebGLRenderTarget`** and run
the shift per eye, so no sample ever crosses the seam. Budget for it honestly: two extra
render-target allocations plus two extra full-screen passes per frame on a phone GPU, on top of
already drawing the scene twice. Cost model in `phone-gpu-stereo-performance.md`.

**Untested here:** a post-free approximation is to draw the object three times with
`AdditiveBlending`, each copy tinted pure red / green / blue and offset slightly in screen space.
It stays inside the per-eye viewport so it can't smear the seam, but it triples draw calls for
that object and has not been implemented or measured in this project — treat it as a direction to
prototype, not a recommendation.
