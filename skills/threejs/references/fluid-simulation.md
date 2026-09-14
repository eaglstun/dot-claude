---
semantic_id: "xK0Cjx6wYXSNhI2OYjqXdsBJI_i3QAAH"
related_ids:
  - "Rr2iDRZQYSEdXM8OZ7qFetIZK4v3QAAB"
  - "xjWDhHA8EWQdYSlc4nqxUuH447uyAAAH"
---
# Real fluid simulation in Three.js — the Stam solver, and what it costs

Three.js has **no fluid dynamics of any kind**. No solver, no SPH, no Navier-Stokes,
nothing in core or in the addons. `Water.js` is a reflection shader
(`water-and-flow-map-shaders.md`) and the GPGPU water example is a height field, not a
fluid. If you want ink curling through water, smoke, or a velocity field that pushes
things around, you implement a solver yourself — almost always the **semi-Lagrangian
"Stable Fluids" method**, which is a fixed sequence of fullscreen shader passes over
velocity and dye textures. This file is the pass order, the cost, and the decision about
whether it belongs in a given project.

## Lineage

Jos Stam's _Stable Fluids_ (1999) made real-time fluid tractable by trading physical
accuracy for unconditional stability: advect backwards along the velocity field instead of
integrating forwards, and the simulation can never explode no matter the timestep. NVIDIA's
**GPU Gems chapter 38**, "Fast Fluid Dynamics Simulation on the GPU", is the canonical
GPU formulation. Pavel Dobryakov's **WebGL-Fluid-Simulation** is the well-known WebGL
implementation (**MIT licensed**, so it's usable rather than merely readable), itself
crediting the GPU Gems chapter and earlier ports by mharrys and haxiomic.

## The pass order

Verified against Dobryakov's `step()`. Each item is one fullscreen shader pass:

1. **Curl** — compute vorticity ∇×v from the velocity field
2. **Vorticity confinement** — push curl-derived force back into velocity
3. **Divergence** — measure ∇·v
4. **Pressure clear** — initialise pressure, scaled by the dissipation factor
5. **Pressure solve** — Jacobi iteration, **×`PRESSURE_ITERATIONS`**
6. **Gradient subtract** — remove ∇p from velocity, making it divergence-free
7. **Advect velocity** — transport velocity along itself
8. **Advect dye** — transport the visible colour field along velocity

Steps 3–6 are the incompressibility projection: measure how much the field is compressing,
solve for a pressure that cancels it, subtract. The Jacobi loop is the expensive part and
the quality knob — fewer iterations means a visibly compressible, mushier fluid.

**Why vorticity confinement exists:** semi-Lagrangian advection is unconditionally stable
but _dissipative_ — it smears out exactly the small swirls that make fluid look like fluid.
Step 2 detects the curl that's about to be lost and adds energy back at that scale. It is a
deliberate physical fudge, and without it the result looks like syrup. Turn `CURL` to 0
once to see what the advection is doing to you.

## Default parameters that actually work

Dobryakov's verified defaults, a good starting point for any port:

| parameter              | default  | notes                                         |
| ---------------------- | -------- | --------------------------------------------- |
| `SIM_RESOLUTION`       | **128**  | the velocity/pressure grid. Small on purpose. |
| `DYE_RESOLUTION`       | **1024** | the visible colour field, 8× the sim          |
| `DENSITY_DISSIPATION`  | 1        | how fast dye fades                            |
| `VELOCITY_DISSIPATION` | 0.2      | how fast motion dies                          |
| `PRESSURE`             | 0.8      | pressure retained between frames              |
| `PRESSURE_ITERATIONS`  | **20**   | the Jacobi loop count                         |
| `CURL`                 | 30       | vorticity confinement strength                |
| `SPLAT_RADIUS`         | 0.25     | injection size                                |

**The resolution split is the whole trick.** Velocity lives on a 128×128 grid; the dye you
actually look at lives at 1024×1024. Fluid motion is low-frequency and reads fine when
interpolated up, while the dye carries all the visible detail. Raising `SIM_RESOLUTION`
is the most expensive change you can make and usually the least visible one — if it looks
low-res, raise the dye instead.

## Cost model

Per frame, with the defaults: 1 curl + 1 vorticity + 1 divergence + 1 clear + 20 pressure

- 1 gradient + 1 velocity advect = **26 passes at 128×128**, plus **1 dye advection at
  1024×1024**.

That works out to about **426k fragment invocations for the entire sim** and **1.05M for
the single dye pass**. Read that twice: the 20-iteration pressure solve everyone worries
about is a rounding error next to one full-resolution dye advection. Optimise the dye pass
first — or lower `DYE_RESOLUTION`, which costs far less visually than it looks like it
should.

The real cost on tiled mobile GPUs isn't arithmetic, it's **27 render-target switches per
frame**, each flushing a tile buffer. That's the number to watch, and it's why this is a
desktop technique by default.

## Implementing it in Three.js

**On r132 / WebGLRenderer** — build it on `GPUComputationRenderer`
(`gpucomputationrenderer.md`). The mapping is direct: velocity, pressure, divergence and
curl become variables; every pass is a compute fragment shader; the Jacobi loop means
calling into the pressure variable repeatedly, which the helper doesn't do natively — you'll
drive those iterations yourself with `doRenderTarget()` against ping-ponged targets rather
than the one-pass-per-`compute()` model. The two-resolution split also fights the helper's
single-grid-size constructor, so expect two instances or hand-rolled targets.

**On r180 with WebGPURenderer** — TSL compute (`tsl-compute-and-webgpu.md`) is cleaner for
the solver, though note the passes are all gather operations on a regular grid, so the
storage-buffer advantages barely apply. This is one of the cases where the older
texture-based approach is genuinely well suited and migrating buys you little.

**Or port Dobryakov's directly.** It's MIT, self-contained GLSL, and the shaders drop onto
render targets you already know how to manage. For most needs this is the honest fastest
path — the value is in the tuned constants and the pass order, both of which are hard-won.

## Should you? A verdict per project

**CAPRICCIO (r180, desktop, post pass available):** yes, viable. 27 passes is real but
affordable on a desktop GPU, and it composes with the existing full-screen chain. Budget it
against everything else in `dithering-and-halftone.md` and the plotter passes, and consider
whether the fluid needs to run every frame — many uses look fine at 30 Hz sim with the dye
advected every frame.

**Phone-in-headset (r132, stereo, no post):** **no.** 27 render-target switches per frame
on a tiled mobile GPU, in a project whose entire visual-effects doctrine
(`visual-effects-without-postprocessing.md`) exists to avoid full-screen passes, while
already rendering everything twice.

If you want _something_ fluid-ish there, the ranked alternatives are: a height-field wave
sim on a small grid (cheap, interacts, genuinely good), a flow-map scroll
(`water-and-flow-map-shaders.md`, nearly free), or a GPU particle system on
`GPUComputationRenderer` with a curl-noise velocity field — which looks remarkably like
fluid, costs one pass, and simulates nothing at all.

**One thing to get right in either project:** the simulation is **view-independent**. Step
it **once per frame** and sample the result from both eyes. Stepping it per-eye doubles the
cost and advances the physics twice per displayed frame, which is a correctness bug, not
just a performance one.

## Related

- `gpucomputationrenderer.md` — the substrate on WebGL.
- `tsl-compute-and-webgpu.md` — the substrate on WebGPU.
- `water-and-flow-map-shaders.md` — the cheap alternatives when you want the look only.
- `phone-gpu-stereo-performance.md` — the budget this is being weighed against.
