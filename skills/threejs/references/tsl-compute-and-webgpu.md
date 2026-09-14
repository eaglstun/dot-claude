---
semantic_id: "4WngDnw9wSUJqQxsqhOS3pV4WLu2UAAP"
related_ids:
  - "JGziC21y2zWJnQoM4nCH3JF4G4umcAAM"
  - "9mihB2Qg1i0L2ZoJMDiHdJF9U4vWQAAD"
---
# TSL compute shaders — real GPU compute in Three.js, and the WebGL fallback surprise

TSL (Three.js Shading Language) is the node-based shader language behind `WebGPURenderer`,
and it brings something WebGL Three.js never had: **actual compute shaders with storage
buffers**, dispatched with `renderer.compute()`. Where `gpucomputationrenderer.md` fakes
computation by ping-ponging float textures through fragment shaders, this is the real
thing — arbitrary buffer reads and writes, workgroup semantics, no texture-as-memory
contortions. The surprise, verified in the source rather than assumed, is that
**`renderer.compute()` also works on the WebGL fallback backend**, implemented with
transform feedback.

**Version scope:** TSL as described here belongs to the **r16x+ / r180** era. It does **not
exist in any usable form in r132** — do not reach for any of this in the phone-in-headset
project, which is pinned and uses `WebGLRenderer`. For that project the answer is
`gpucomputationrenderer.md`, full stop.

**Caveat on volatility:** TSL churned harder than any other part of Three.js during its
introduction — `tslFn` became `Fn`, node imports moved, several helpers were renamed. The
API below is verified against current `dev` and the official TSL wiki. If you're on a
specific r180 build and something doesn't resolve, check that build's own exports before
concluding the doc is wrong. This is the one area where "the current docs" and "your
version" diverge most often.

## Declaring and dispatching

```js
import * as THREE from "three";
import { Fn, instanceIndex, storage } from "three/tsl";

const renderer = new THREE.WebGPURenderer();
await renderer.init();

const computeShader = Fn(() => {
  // body
})().compute(count);

renderer.compute(computeShader);
```

`Fn()` wraps a function body into a node; calling it produces the node; **`.compute(count)`**
turns that node into a dispatchable compute operation where `count` is the number of
invocations. Dispatch with `renderer.compute(node)`.

## Storage

Three ways to get a writable GPU buffer:

| helper                            | use                                                 |
| --------------------------------- | --------------------------------------------------- |
| `storage(attribute, type, count)` | a read/write storage buffer from a buffer attribute |
| `instancedArray(array, type)`     | instanced buffer attribute array                    |
| `attributeArray(array, type)`     | standard buffer attribute array                     |

Index into them with **`.element(index)`**, where the index is itself a node — that's what
makes indirect/dynamic addressing work:

```js
const positions = instancedArray(count, "vec3");

const update = Fn(() => {
  const p = positions.element(instanceIndex);
  p.addAssign(vec3(0, -0.01, 0));
})().compute(count);
```

## Built-in invocation IDs

| node            | type  | meaning                                        |
| --------------- | ----- | ---------------------------------------------- |
| `instanceIndex` | uint  | the invocation index — the one you'll use most |
| `globalId`      | uvec3 | global invocation ID                           |
| `workgroupId`   | uvec3 | workgroup ID                                   |
| `localId`       | uvec3 | local invocation ID within the workgroup       |

## The WebGL fallback — verified, and better than expected

`WebGPURenderer` falls back to a WebGL2 backend when WebGPU is unavailable, and the
reasonable assumption is that compute simply dies there. **It doesn't.**
`src/renderers/webgl-fallback/WebGLBackend.js` implements `compute()` using **transform
feedback**: it binds a compute program, calls `gl.beginTransformFeedback(gl.POINTS)`, draws
with `drawArrays`/`drawArraysInstanced`, and swaps the dual buffers afterwards. It enables
`gl.RASTERIZER_DISCARD` for the duration so nothing rasterizes.

What that means practically:

- A TSL compute pass that reads and writes storage buffers **can run without WebGPU**.
  That is a much stronger portability story than "WebGPU or nothing".
- The `count` parameter must be **a single number** on this path — the backend warns if
  handed an array or an `IndirectStorageBufferAttribute`.

**Where to be careful.** Transform feedback is a vertex-stage mechanism, not a compute
pipeline, and workgroup-level concepts (`localId`, `workgroupId`, shared memory, barriers)
have no direct equivalent in it. I have verified that the dispatch path exists and how it's
implemented; I have **not** verified which workgroup-dependent TSL features degrade or
throw there. If your shader relies on anything beyond per-invocation `instanceIndex` work,
test it on the fallback before shipping to browsers without WebGPU — don't take the
existence of `compute()` as proof your particular shader runs.

## When this beats GPUComputationRenderer

|                                       | GPUComputationRenderer                | TSL compute                                   |
| ------------------------------------- | ------------------------------------- | --------------------------------------------- |
| storage                               | float **textures**, fixed 2D grid     | **buffers**, any length                       |
| writes                                | one texel per invocation, gather only | arbitrary buffer writes, **scatter possible** |
| atomics / shared memory               | none                                  | available on a real WebGPU backend            |
| variable-length output                | no                                    | yes                                           |
| sorting, prefix sums, neighbour lists | painful to impossible                 | tractable                                     |
| r132                                  | **yes**                               | **no**                                        |
| renderer required                     | `WebGLRenderer`                       | `WebGPURenderer` (WebGPU or WebGL fallback)   |

The decision is usually made for you by the renderer the project already uses. Where you do
have the choice — CAPRICCIO on r180 — the question is whether your algorithm needs scatter,
atomics, or variable output. Height fields, boids, and reaction-diffusion don't; they map
onto textures perfectly and `GPUComputationRenderer` is less machinery. Particle systems
with neighbour queries, GPU sorting, or dynamic emission do, and that's where TSL earns the
migration.

## Related

- `gpucomputationrenderer.md` — the WebGL-era alternative, and the only option on r132.
- `fluid-simulation.md` — a solver that maps well onto either.
- `r180-api-surface.md` — import paths and what moved between the two pinned versions.
