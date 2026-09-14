# Cooking, performance, and why nothing is happening

## The cook model

Each frame, TouchDesigner walks the dependency graph and cooks only the operators
whose inputs, parameters, or referenced values changed — plus everything
downstream of those. An operator with nothing new to say does not cook, and that
is the whole performance strategy.

Consequences worth internalizing:

- **An operator nobody looks at may not cook at all.** If a chain feeds nothing —
  no viewer, no Null anyone references, no output — it can go cold. This is the
  usual reason a script chain "stopped working" after you closed a viewer.
- **Referencing an operator in an expression creates a dependency.** `op('noise1')['x']`
  in a parameter makes `noise1` cook whenever that parameter is evaluated.
- **Cook Always** (Common parameter page) forces a cook every frame. Sometimes
  required (a Script DAT that polls something external); usually a smell.
- **Feedback and Cache** operators deliberately hold a previous frame, which is a
  controlled cycle. Anything else circular is an error.

## Diagnosing

1. **Performance Monitor** (`Dialogs → Performance Monitor`) — capture a frame and
   read the tree of what cooked and how long each took. This answers "what is
   eating my frame" definitively. Start here, not with guesses.
2. **Info CHOP** — point it at any operator to get `cook_time`, `cook_frame`,
   `total_cooks` as live channels. Wire one at a Text TOP for an always-on readout.
3. **Right-click an operator → Info** (or `op('x').cookTime`) for a one-off number.
4. **The frame-rate readout** in the bottom-right of the main window; also
   `me.time.rate` vs actual. `project.cookRate` is the target.
5. **Probe / OP Snippets** in the Palette — the Probe component gives a live
   inspector for any node.

Read `cook_time` as a fraction of your frame budget: at 60 fps you have **16.6 ms
total** for everything, GPU and CPU. A single operator at 4 ms is using a quarter
of the frame.

## The usual culprits, roughly in order

**GPU readback.** `TOP to CHOP`, `TOP.numpyArray()`, `TOP.save()`, and Script TOPs
that touch pixels on the CPU all force a sync between GPU and CPU. Downsample to
the smallest useful resolution first — reading a 1×1 or 8×8 TOP is cheap, reading
1920×1080 every frame is not.

**Resolution you didn't ask for.** A TOP chain inherits resolution from its input.
One 4K source at the top makes every downstream blur, composite, and feedback 4K.
Insert a `Resolution TOP` early and work at the size you actually output. Blur
radius cost in particular scales badly with resolution.

**32-bit float everywhere.** Use 8-bit fixed unless you need the range or
precision (feedback accumulators, data-in-texture, HDR). A 32-bit RGBA texture is
4× the memory bandwidth of 8-bit.

**CPU geometry.** `Copy SOP`, high-res `Grid`/`Sphere`, `Particle SOP`, and
`Subdivide` all run on the CPU and rebuild whole point arrays. If the geometry is
static, cook it once and put a `Null SOP` (or bake to a file) after it. If you need
thousands of copies, use **instancing** on the Geometry COMP instead — one draw
call, transforms supplied by a CHOP or TOP.

**Per-frame Python.** An `onFrameStart` that walks operators, does `findChildren`,
or builds strings runs 60×/sec. Move logic to edge-triggered callbacks, cache
lookups in extension attributes rather than re-resolving `op()` paths every frame.

**Uncached file/network I/O in a cook.** Reading a file or making an HTTP request
inside `onCook` or `onFrameStart` blocks the frame. Use the Web Client DAT's async
callback, or do the work in a `run()` on a later frame.

**Movie File In.** Codec matters enormously. **HAP** and **NotchLC** are designed
for realtime multi-stream playback and decode cheaply; H.264/H.265 decode is
expensive and seeks badly. For any installation playing more than one or two
videos, transcode to HAP. Also set the movie's **Pre-Read Frames** / cache
parameters rather than fighting stutter downstream.

## Sizing for the GPU

- Watch GPU memory in the Performance Monitor / Window menu. Every TOP holds its
  texture; a deep chain at high resolution and 32-bit float adds up fast.
- Prefer one `GLSL TOP` doing five operations over five separate TOPs when a chain
  is hot — each TOP is a full-screen pass with its own bandwidth cost.
- `Cache TOP` / `Cache Select TOP` hold N frames in GPU memory. Useful, expensive;
  budget the memory deliberately (frames × width × height × bytes-per-pixel).

## macOS / Apple Silicon notes

This install renders through **Vulkan on MoltenVK**, translating to Metal. Practical
effects:

- Shader compile and pipeline setup can be slower than on Windows/NVIDIA; the first
  frame using a new GLSL op may hitch.
- Unified memory means CPU↔GPU transfers are cheaper than on a discrete card, but
  readbacks still synchronize the pipeline — the advice above still holds.
- Anything CUDA-based is absent entirely. See `project-workflow.md`.
- Use **Syphon** for frame sharing with other Mac apps (Resolume, VDMX, Max).
  Spout is the Windows equivalent and is not available here.

## Perform mode

`Perform` mode runs the project without the network editor UI, which recovers real
frame time — the editor itself costs several ms per frame. Configure the output
via a Window COMP, then switch to Perform mode for anything you're actually
measuring or showing. `Esc` returns to the editor.

**Always benchmark in Perform mode.** Numbers taken with the network editor open,
viewers active, and a parameter dialog cooking are not the numbers your
installation will run at.

## Realtime flag

`project.realTime = True` (the default) drops frames to keep wall-clock pace. Set
it `False` when rendering out to a file — then every frame is computed regardless
of how long it takes.
