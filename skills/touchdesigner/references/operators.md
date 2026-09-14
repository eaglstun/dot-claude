# Operator families and crossing between them

## The families in practice

### TOP — textures (GPU, 2D images)

Every pixel operation. Wires carry a texture with a resolution and pixel format.

- **Generators:** Constant, Noise, Ramp, Text, Circle, Rectangle, Movie File In,
  Video Device In, NDI In, Syphon Spout In (Syphon on macOS), Render.
- **Filters:** Level, Blur, Transform, Composite, Over/Add/Multiply, Feedback,
  Displace, Lookup, Threshold, Edge, Cache, Resolution, Fit, Crop, Flip.
- **Outputs:** Null, Out, Movie File Out, Video Device Out, Syphon Spout Out, Window COMP.
- **Compute:** GLSL TOP for arbitrary fragment/compute shaders. This is the escape
  hatch when no built-in does what you want.

Key parameters that cause most confusion: **Resolution** (Use Input / Custom /
Eighth…), **Pixel Format** (8-bit fixed by default — switch to 16-bit or 32-bit
float when accumulating, doing feedback, or storing data instead of color), and
**Fill/Extend** modes on Transform-ish TOPs.

**Feedback TOP** is the one non-obvious node: it holds the _previous frame_ of a
target TOP, which is how you build trails, accumulators, and reaction-diffusion.
It reads from a TOP you name, and you composite it back in — a deliberate cycle
the cook engine allows.

### CHOP — channels (numbers over time)

A CHOP holds one or more named **channels**, each with **samples**. Audio is just a
CHOP at 44100 samples/sec; a mouse position is a CHOP at 1 sample/frame; a
timeline animation is a CHOP with many samples.

- **Sources:** Constant, Noise, LFO, Pattern, Audio Device In, Audio File In,
  Mouse In, Keyboard In, MIDI In, OSC In, DMX/Art-Net, Serial, Timer, Beat, Count.
- **Filters:** Math, Filter, Lag, Limit, Logic, Select, Rename, Merge, Shuffle,
  Resample, Trim, Speed, Delay, Trigger, Analyze, Envelope.
- **Sinks:** Null, Out, Audio Device Out, OSC Out, MIDI Out, DMX Out.

**Filter vs Lag** is the classic smoothing choice: `Lag CHOP` gives separate
attack/release slew (good for envelopes, VU-style behavior); `Filter CHOP` is a
symmetric low-pass over a window (good for de-jittering sensor data).

Sample rate mismatches are a frequent bug source — merging a 44100 Hz audio CHOP
with a 60 Hz control CHOP will resample one of them. Check the CHOP's info bar.

### SOP — geometry (CPU 3D)

Points, vertices, primitives. SOPs are CPU-bound; a SOP chain that rebuilds
100k points every frame will eat your frame budget.

- **Primitives:** Grid, Box, Sphere, Torus, Tube, Circle, Line, Text.
- **Modifiers:** Transform, Noise, Copy, Merge, Facet, Subdivide, Sort, Delete,
  Group, Point, Primitive, Carve, Sweep, Skin, Particle, Metaball.
- **I/O:** File In (obj/fbx/usd), Alembic In.

**When geometry is heavy, move it to the GPU:** instead of `Copy SOP` making
10,000 copies on CPU, use **instancing** on the Geometry COMP (feed it a CHOP or
TOP of transforms) or write positions into a 32-bit float TOP and read them in a
GLSL MAT. This is the single biggest realtime-performance decision in TD.

### MAT — materials

Phong, PBR, Constant, Wireframe, Point Sprite, Depth, and **GLSL MAT** for custom
vertex/pixel shaders. Assigned via the Geometry COMP's `Material` parameter (or
per-primitive via a `Material SOP`).

### DAT — text and tables

Two shapes: **table** (rows/cols) and **text** (a script or blob).

- **Data:** Table, Text, File In, Web, JSON (via Python), Folder, OP Find, Info.
- **Network:** OSC In/Out DAT, TCP/IP, UDP, WebSocket, Serial, MQTT.
- **Scripting:** Execute, CHOP Execute, DAT Execute, Parameter Execute, Panel
  Execute, Script (SOP/CHOP/DAT/TOP variants), Text DAT holding a module.

A DAT that holds Python is only _code_ — it runs when something calls it (a
callback hook, `run()`, or `mod()` import). See `callbacks.md`.

### COMP — components

Three flavors worth distinguishing:

- **Object COMPs** (3D transform hierarchy): Geometry, Camera, Light, Null, Bone.
- **Panel COMPs** (2D UI): Container, Button, Slider, Field, Table, List, Parameter.
- **Other**: Base COMP (a plain subnetwork — the workhorse for organizing and for
  building reusable `.tox` modules), Window COMP (an output window), Replicator,
  Time, Engine, Actor/Bullet.

The **Base COMP** is where your own tools live: give it custom parameters and a
Python extension and it becomes an object with an API. See `python-api.md`.

## Crossing between families

Wires stay in-family. To convert, use a dedicated operator:

| From → To             | Operator                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------- |
| CHOP → TOP            | `CHOP to TOP` (channels become pixel rows — the standard way to push data to the GPU)                   |
| TOP → CHOP            | `TOP to CHOP` (pixels become channels — GPU readback, **causes a stall**, use sparingly and at low res) |
| CHOP → SOP            | `CHOP to SOP` (channels become point attributes/positions)                                              |
| SOP → CHOP            | `SOP to CHOP` (point positions/attributes become channels)                                              |
| DAT → CHOP            | `DAT to CHOP` (table columns become channels)                                                           |
| CHOP → DAT            | `CHOP to DAT` (channels become a table)                                                                 |
| DAT → SOP             | `DAT to SOP` (table of points/prims becomes geometry)                                                   |
| SOP → DAT             | `SOP to DAT` (geometry becomes an inspectable table)                                                    |
| 3D scene → TOP        | `Render TOP` (a Camera + Geometry + Light → a texture)                                                  |
| COMP transform → CHOP | `Object CHOP` (world/local transform of object COMPs as channels)                                       |

**`TOP to CHOP` is the one to be careful with.** It pulls data off the GPU back to
the CPU, which synchronizes the pipeline. One small readback per frame is fine;
reading a 1920×1080 texture every frame is a frame-rate cliff. Downsample first
(`Resolution TOP` or an `Analyze TOP`) and read the smallest thing that answers
your question.

## Resolution propagates, and one small node collapses the chain

A TOP with `outputresolution` set to `useinput` inherits from upstream. Where a
node reconciles two inputs of different sizes, the whole downstream chain can drop
to the smaller one — so a single stale node silently throttles everything after
it. All verified in practice on 2026-08-09:

- **`feedbackTOP` finds its source through the `top` parameter, not a wire**, so
  its input connector looks optional. It isn't — the input is what sets the
  feedback buffer's resolution. Left unwired it sits at its default 128x128, and a
  Composite TOP reconciling that against a 1280x1280 input collapsed the entire
  chain to 128x128. Wire the chain's source TOP into the feedback's input as well
  as naming it in `top`.
- **An operator with no TOP input cannot use `useinput`.** `pointfileinTOP`
  defaults to it, silently falls back to 256x256, and discards points.
- **Mixing aspect ratios inside a feedback loop leaves artefacts** — a square
  buffer rotating inside a 4:3 frame cuts a dark arc across the image. When
  changing a loop's resolution, pin every node in the loop, not just the
  composite; inheritance did not propagate through the feedback branch on its own.

Diagnose with `[op.width, op.height]` node by node along the chain. The number
that matters is the operator's actual size, not what the resolution parameter
says — those disagree routinely.

## Transforms: rotate happens before translate

Object COMPs apply scale, then rotate, then translate. So a Geometry COMP that
uses its translate to move content to the world origin will **swing that content
through a huge arc** when rotated, rather than turning in place.

Set the COMP's **pivot** (`px`, `py`, `pz`) to the point you actually want to
rotate around, expressed in the geometry's own coordinates. To spin content in
place, pivot at its centroid; to hinge a scene around a wall, pivot in the wall
plane.

Related: a Camera COMP's `lookat` aims at the target COMP's **origin**, which is
not where its contents are if that COMP carries a translate. Aiming at empty
space this way is easy to miss — clear `lookat` and drive rotation explicitly when
the framing seems inexplicably off.

## Null operators — use them

Put a `Null` at the end of every chain you reference from elsewhere (Python,
exports, other networks). Nulls cost effectively nothing and give you a stable
name to point at, so you can insert or reorder operators upstream without
rewriting every reference. This is the single most useful habit in TD.

## Flags on the node tile

Small toggles on each operator's tile, easy to miss and responsible for a lot of
"why is nothing happening":

- **Bypass** (yellow) — pass input straight through, skipping this op.
- **Display** (blue-ish, on TOP/SOP/COMP) — whether it draws in the viewer.
- **Render** (SOP/COMP) — whether it's included in a Render TOP pass.
- **Clone** — this op mirrors the contents of a master op.
- **Cook Always** (in the Common page, not a tile flag) — force a cook every frame
  even when nothing changed. Sometimes necessary, often a performance mistake.
- **Lock** (on DATs/TOPs) — freeze the current contents, ignore inputs.

## Viewer-active

Clicking a COMP's viewer normally selects the node. Toggle **viewer active** (the
small crosshair on the tile, or `Alt`-click into it) to actually interact with the
panel/3D view inside. Countless "my button doesn't click" reports are this.

## Common hotkeys

`Tab` opens the OP Create dialog in a network editor. `P` toggles the parameter
dialog for the selected op. `H` homes/frames the network view. `U` goes up a
level, `I` goes into the selected component. `Esc` exits Perform mode. The full
list is in the app under **Help → Keyboard Shortcuts** — check there rather than
trusting a remembered binding.

## "All my nodes disappeared"

Two causes, both routine, neither destructive:

1. **You navigated up a level.** The root `/` holds only `project1`, `local` and
   `perform`, so it reads as an empty canvas. The **path bar in the pane's
   top-left corner** is the address — check it first. From Python:
   `ui.panes[0].owner.path`, and `ui.panes[0].owner = op('/project1')` puts a
   lost user back.
2. **The view is panned into empty space.** `H` frames everything at the current
   level.

## Nothing is on screen unless something points at it

TouchDesigner has no single "the output". Three ways to actually see a TOP:

- **Node tile thumbnails** — every TOP previews itself. Drag a node's
  bottom-right corner to enlarge the tile and its preview; oversized nodes parked
  in the network make good always-on monitors.
- **Window COMP** — a real OS window. Its `winop` parameter names **exactly one**
  operator; `winopen.pulse()` opens it. Note the Window COMP's own tile previews
  nothing at all — it is a black box labelled "Win", which reads as broken when it
  is working fine. If a window does not appear, set `justifyh`/`justifyv` to
  `center` and `alwaysontop` on rather than assuming failure. `monitors` lists the
  displays.
- **Perform mode** — full screen, editor hidden, and the only honest place to
  measure frame rate.

`project.cookRate` is the **target** fps, not the achieved one — it returns 60 on
a project running at 12. Real performance comes from the Performance Monitor or
the readout in the main window's bottom-right corner.
