---
semantic_id: "xjWDhHA8EWQdYSlc4nqxUuH447uyAAAH"
related_ids:
  - "xK0Cjx6wYXSNhI2OYjqXdsBJI_i3QAAH"
  - "VqWBJfUu8muHyBteNFiyUtH8eufYAAAB"
---

# GPUComputationRenderer — GPGPU by ping-ponging float textures

`examples/jsm/misc/GPUComputationRenderer.js` is the classic way to run simulation state on
the GPU in a WebGL Three.js project: you store state in **float textures**, write fragment
shaders that read last frame's texture and write this frame's, and the helper manages the
double-buffered render targets, the fullscreen quad, and the uniform wiring. It is how the
official height-field water and boids examples work. It is **not** a compute shader and
**not** a physics engine — there are no atomics, no shared memory, no scatter writes. Every
invocation writes exactly one texel of one output, and that restriction shapes every
algorithm you can put on it.

**Version scope:** present in **r132 and r180 alike**, API unchanged in the parts that
matter; the signatures below are verified against current `dev`. This is the right tool for
the pinned r132 phone project, where TSL compute (`tsl-compute-and-webgpu.md`) does not
exist. In r180 with a WebGPU backend you have a real alternative.

## The API, verified

```
new GPUComputationRenderer(sizeX, sizeY, renderer)
```

| method                       | parameters                                               | returns                                           |
| ---------------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| `setDataType()`              | `FloatType \| HalfFloatType`                             | `this`                                            |
| `addVariable()`              | `name, computeFragmentShader, initialValueTexture`       | the **variable object**                           |
| `setVariableDependencies()`  | `variable, [variables]`                                  | —                                                 |
| `init()`                     | —                                                        | **`null` on success, an error string on failure** |
| `compute()`                  | —                                                        | —                                                 |
| `getCurrentRenderTarget()`   | `variable`                                               | `WebGLRenderTarget`                               |
| `getAlternateRenderTarget()` | `variable`                                               | `WebGLRenderTarget`                               |
| `createTexture()`            | —                                                        | `DataTexture`                                     |
| `createShaderMaterial()`     | `computeFragmentShader, uniforms?`                       | `ShaderMaterial`                                  |
| `createRenderTarget()`       | `sizeX?, sizeY?, wrapS?, wrapT?, minFilter?, magFilter?` | `WebGLRenderTarget`                               |
| `renderTexture()`            | `input, output`                                          | —                                                 |
| `doRenderTarget()`           | `material, output`                                       | —                                                 |
| `addResolutionDefine()`      | `materialShader`                                         | —                                                 |
| `dispose()`                  | —                                                        | —                                                 |

A **variable object** is the handle for everything you'll touch afterwards:

```text
name                 string
initialValueTexture  Texture
material             ShaderMaterial      <- where you add your own uniforms
dependencies         Array | null
renderTargets        Array<WebGLRenderTarget>   (the ping-pong pair)
wrapS, wrapT         number | null       <- set these BEFORE init()
minFilter, magFilter number
```

`variable.material.uniforms` is where you add your own uniforms — that's the material the
helper built for your compute shader.

**`init()` returns `null` when it succeeds.** It returns a _string_ when it fails. This
trips people up constantly, because the truthy-looking return is the error case:

```js
const error = gpuCompute.init();
if (error !== null) console.error(error); // NOT `if (error)` inverted
```

## The mental model

Each variable is a texture holding one `vec4` per simulated element. Each frame,
`compute()` runs every variable's fragment shader over a fullscreen quad, reading the
_previous_ targets and writing the _current_ ones, then swaps. Two rules follow:

- **You read neighbours, you write only yourself.** `gl_FragCoord.xy` is your element. You
  can sample any texel of any dependency, but you write one output. Diffusion, advection,
  and stencil operations map perfectly. Anything needing "add my contribution to someone
  else" (scatter) does not, and has to be inverted into a gather.
- **Dependencies are declared, not implied.** `setVariableDependencies(velocity, [velocity,
position])` makes both textures available _inside_ the velocity shader as `sampler2D`
  uniforms named after the variables.

Two uniforms are injected for you: **`resolution`** (a `vec2` of the grid size) and one
`sampler2D` per declared dependency. So a minimal compute shader has no uniform
declarations of its own at all:

```glsl
void main() {
  vec2 uv = gl_FragCoord.xy / resolution.xy;
  vec4 self = texture2D(textureVelocity, uv);   // dependency, auto-declared
  gl_FragColor = self * 0.99;
}
```

## The shape of a real setup

```js
const W = 128,
  H = 128;
const gpuCompute = new GPUComputationRenderer(W, H, renderer);

const pos = gpuCompute.createTexture();
const vel = gpuCompute.createTexture();
fillPositions(pos);
fillVelocities(vel); // write into .image.data

const posVar = gpuCompute.addVariable("texturePosition", posFrag, pos);
const velVar = gpuCompute.addVariable("textureVelocity", velFrag, vel);

gpuCompute.setVariableDependencies(posVar, [posVar, velVar]);
gpuCompute.setVariableDependencies(velVar, [posVar, velVar]);

velVar.material.uniforms.uTime = { value: 0 };
posVar.wrapS = posVar.wrapT = THREE.RepeatWrapping; // set BEFORE init()

const error = gpuCompute.init();
if (error !== null) console.error(error);

// per frame
velVar.material.uniforms.uTime.value = t;
gpuCompute.compute();
renderMaterial.uniforms.tPosition.value =
  gpuCompute.getCurrentRenderTarget(posVar).texture;
```

Set `wrapS`/`wrapT`/filters on the _variable_ before `init()` — after that the render
targets already exist and changing the variable's fields does nothing.

## What it's actually good at

- **Height-field waves.** The official `webgl_gpgpu_water` example: one variable holding
  height and velocity, a discrete wave equation reading four neighbours. Cheap, stable,
  and it interacts — drop something in and rings spread. This is the honest answer for
  "water that responds", and it is far cheaper than a real fluid solver.
- **Particles and boids.** `webgl_gpgpu_birds` — position and velocity textures, flocking
  rules gathered per bird. Scales to hundreds of thousands of particles because the CPU
  never touches them.
- **Cellular automata, reaction-diffusion, erosion, heat diffusion** — anything that's a
  stencil over a grid.
- **Anything you'd otherwise do per-particle on the CPU** and then upload, which is almost
  always the actual bottleneck being solved here.

## Cost model, and the phone

One `compute()` = one fullscreen quad per variable, at grid resolution. A 128×128 grid with
two variables is 32k fragment invocations — nothing. The costs that bite are elsewhere:

- **Render target switches.** Each variable is a separate pass with its own bind. Ten
  variables is ten passes, and on a tiled mobile GPU each one flushes a tile buffer. Prefer
  packing more state into fewer `vec4`s over adding variables.
- **Float texture support.** `FloatType` render targets need `EXT_color_buffer_float`.
  Mobile support is far better than it was, but `setDataType(THREE.HalfFloatType)` is the
  safer default on a phone — with the caveat that half floats have ~3 decimal digits of
  precision, which is fine for velocity and disastrous for a position that accumulates over
  minutes. Store position as an offset from a periodically-reset origin, or keep position
  in full float and velocity in half.
- **Reading back to the CPU.** `renderer.readRenderTargetPixels()` stalls the pipeline
  hard. If gameplay needs to know where a GPU particle is, restructure so it doesn't.

**For the phone-in-headset project specifically:** the simulation is **view-independent**,
so run `compute()` **once per frame**, not once per eye. Both eyes sample the same result
textures. This is the single most important thing to get right — a naive per-eye update
doubles the sim cost and, worse, steps the simulation twice per displayed frame, which
changes the physics.

## What it cannot do

- No compute shaders, no workgroups, no shared memory, no atomics.
- No scatter writes — every algorithm must be expressible as a gather.
- No variable-length output. The grid is fixed at construction.
- Sorting, prefix sums, and neighbour lists are all painful-to-impossible; this is why
  particle systems built on it use uniform grids or just accept O(n²) over a small n.

If you need any of those, that's the argument for `tsl-compute-and-webgpu.md`.

## Related

- `fluid-simulation.md` — a real Navier-Stokes solver, which is exactly this technique
  applied about 27 times per frame.
- `phone-gpu-stereo-performance.md` — the pass budget you're spending against.
- `visual-effects-without-postprocessing.md` — why extra fullscreen passes are politically
  sensitive in the r132 project.
