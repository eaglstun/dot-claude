# Point clouds, depth capture, and POPs

Verified against TD 2025.33070 on 2026-08-09 by loading real data through the
live session, not from documentation.

## Start with `pointfileinPOP`, not `pointfileinTOP`

**`pointfileinTOP` failed to load anything on this machine** — including TD's own
`Samples/PointClouds/banana.ply` — and reported no error while doing it.
`errors()` empty, `warnings()` empty, output a black texture. Its resolution
stayed at the 256x256 fallback, which reads exactly like a successful load of a
65,536-point cloud. That false positive cost four diagnostic rounds.

`pointfileinPOP`, given the identical file, returned the real problem instantly:

```
Error: Failed to open PLY file. Unsupported property type.
```

**Diagnose point-cloud loading with the POP.** Whether the TOP path is broken
generally or only in this build was not established; either way it cannot be
trusted to report failure. Check `numPoints()` on a POP rather than believing a
TOP's resolution.

Related operators: `pointfileinPOP`, `pointfileinTOP`, `pointfileselectTOP`,
`pointtransformTOP`, `pointspriteMAT`, `pointMAT`, `depthTOP`, `depthMAT`,
plus the `poptoTOP` / `poptoSOP` / `soptoPOP` / `toptoPOP` converters.

## TD's PLY reader rejects integer properties

Proven by elimination against a real Record3D frame (307,200 points):

| Variant                           | Points loaded | Result                    |
| --------------------------------- | ------------- | ------------------------- |
| `uchar` red/green/blue (as shot)  | 0             | Unsupported property type |
| same, header renamed to `uint8`   | 0             | Unsupported property type |
| float x/y/z only, colour stripped | 307,200       | clean                     |
| float x/y/z **and** float colour  | 307,200       | clean                     |

It is not the spelling — the reader wants floats. Rescale colour to 0..1 float
and rewrite the file. `uchar` colour is completely standard in PLY, so expect
this with any capture tool, not just Record3D.

## Playing a sequence: drive `file` with an expression

`pointfileinPOP` has **no transport controls** — its pages are Point File In,
Thin, ReRange, Common. There is no play/speed/cue/index. Animate it yourself:

```python
node.par.file.expr = "'/path/frames/%07d.ply' % (int(absTime.frame/2) % 920)"
```

`int(absTime.frame/2)` converts a 60 fps timeline to 30 fps source; `% 920` loops.
Use `absTime` so playback is independent of the timeline.

## Gotchas that cost real time

- **`thinrangelength` defaults to 100.** Turning the Thin page on without setting
  it silently reduces the cloud to 100 points. Set it to the full point count and
  use `thinstep` to decimate (`thinstep=8` on 307,200 -> 38,400).
- **`outputresolution` on `pointfileinTOP` defaults to `useinput`**, but the
  operator has no TOP input, so it falls back to 256x256 and throws away points.
- **Geometry COMPs rotate before translating.** A cloud offset to the world
  origin by a COMP translate will swing in a huge arc when rotated. Set the
  COMP's pivot (`px/py/pz`) to the cloud's own centroid to spin it in place.
- **Find planes with a histogram, don't eyeball them.** Binning point positions
  per axis makes walls obvious — a real wall showed as 11% of all points in a
  single bin, giving an exact pivot plane.

## POPs — the 2025 point/particle family

The 2025 builds added a seventh operator family. Verified count on this install:

```python
len([n for n in dir(td) if n.endswith('POP')])   # -> 103
```

POPs are GPU-resident point/particle geometry — what SOPs could never be, since
SOPs are CPU-bound and rebuild whole point arrays per cook. Present include
`pointfileinPOP`, `pointgeneratorPOP`, `copyPOP`, `attributePOP`,
`accumulatePOP`, `alembicinPOP`, `choptoPOP`, `dattoPOP`, `cachePOP`,
`connectivityPOP`, `cplusplusPOP`.

**Check POPs first** for anything involving large point counts or particles.
Reaching for `Copy SOP` out of habit is the CPU-bound mistake the performance
notes warn about.

## Record3D (iPhone LiDAR / TrueDepth)

Confirmed from record3d.app: exports **PLY** and **glTF**, streams RGBD over
**USB** (C++ and Python libraries provided), and offers Wi-Fi streaming to a
browser behind a paid Extension Pack. The site does not confirm `.r3d`, OBJ,
USDZ, or EXR export — do not assume those without checking.

Routes into TD, easiest first:

1. **PLY sequence -> `pointfileinTOP`.** No conversion, native, plays as video.
2. **USB live stream** via Record3D's Python lib. The phone becomes a live depth
   camera. Requires installing the lib against TD's bundled Python (3.11, arm64 —
   see `project-workflow.md`) and pumping frames through a Script TOP.
3. **glTF** for a static reconstructed mesh rather than points.

**Sensor choice matters more than people expect.** Rear LiDAR is room-scale but
sparse and noisy at distance — good for spaces and bodies in a room. Front
TrueDepth is far denser and more accurate but only works at arm's length — the
right choice for faces and hands, and the one that produces the recognisable
volumetric-portrait look.

**PLY sequences are large.** Uncompressed positions per frame at capture rate.
Add `*.ply` and `media/` to `.gitignore` before recording anything, not after.

## What to do with the points once loaded

- **Draw them** — `pointspriteMAT` renders points as sprites with per-point size
  and colour.
- **Instance on them** — put a SOP at every point via a Geometry COMP's
  instancing, positions supplied by the point texture. One draw call.
- **Deform them** — the positions are just pixel values. Multiply by noise,
  displace, transform with `pointtransformTOP`. The scan melts.
- **Composite it** — it all ends at a Render TOP, so a point cloud joins the
  ordinary 2D chain and can feed a feedback loop like any other texture.

## Occlusion holes — the defining problem, and two fixes

A depth capture only contains surfaces the sensor could see. Everything behind
anything is missing, so the render is full of holes that show whatever is behind
it. Both fixes below were verified working together on a handheld room scan.

**1. Accumulate with a feedback loop.** Set the feedback transform to no rotation
and no scale (pure temporal stacking) with a high decay (`levelTOP` opacity
~0.92) and composite with **`maximum`**. Because a handheld scan moves, later
frames supply geometry that earlier frames occluded, and the loop keeps the
brightest sample per pixel. Holes fill in with _real_ data within a second or
two. This is the good fix.

**2. Put something behind the remaining holes.** A Render TOP carries **real
alpha** — verified 0.0 in holes, 1.0 on geometry — so the black is genuine
emptiness, not paint. Anything composited underneath shows through. Deriving the
backdrop from the scene itself reads better than a flat colour:

```
render -> blur(140) -> level(brightness ~0.85, opacity ~0.45) -> transform(scale 1.8)
                    -> over a constantTOP floor colour   (never pure black)
render (sharp) ---------------------------------------> over that
```

Brightness above ~1.0 on the blur blows the backdrop to white — keep it under 1.

## How far you can rotate a single-viewpoint capture

About **33 degrees** off the original camera axis. Measured, not estimated: at
25-33 degrees depth reads well and the holes look intentional; by 45 degrees the
scan stretches into long occlusion shadows; near 90 degrees it is a flat card
seen edge-on.

A constant 360-degree rotation therefore spends most of its cycle unusable. Bound
it instead:

```python
33 * sin(absTime.seconds * 0.25)
```

This rocks through the good range continuously and always starts centred —
unlike `absTime.seconds * n`, which starts at whatever angle the app's uptime
happens to produce (observed: 229,231 degrees on a session hours old).

Getting a genuinely wider viewing angle is a **capture** problem, not a rendering
one: walk around the subject while recording so the scan accumulates surfaces
from several sides.

## Multi-camera capture — DESIGN NOTES, NOT YET TESTED

Everything above this heading was verified on real data. This section is reasoned
guidance only — no two-camera shoot has been attempted, and the workflow below
has not been run. Treat it as a starting plan to validate, not as established
fact.

**Accumulation only fills holes on static geometry.** The feedback trick works
because later frames supply what earlier frames occluded — which requires the
subject to hold still. A moving performer carries their occlusion shadow with
them, so it never fills, no matter how long the loop runs. Observed clearly on a
handheld room scan: the room filled in; the person did not.

Two cameras at the same instant is the structural fix — a surface hidden from A is
visible to B. Expect roughly **60-90 degrees** of separation to be useful: less
and both see the same surfaces, much more and the two shells stop overlapping.

Two problems to solve:

**Spatial registration.** Each device's coordinates originate where that ARKit
session started, so the clouds land in unrelated spaces and need one rigid
transform to combine. **Static rigs make this a single constant for the whole
take** — solve once, paste into the second Geometry COMP's translate/rotate.
Handheld, both origins drift independently and the alignment becomes per-frame.
Suggested route: solve offline with ICP (`open3d`) on one frame pair, decompose
the 4x4 into TD transform values. No need to install anything into TD's Python
for this.

**Temporal sync.** Devices don't start together. A clap or light flash visible to
both gives a common frame; bake the difference into the file expression:

```python
'…/camB/%07d.ply' % ((int(absTime.frame/2) + OFFSET) % NFRAMES)
```

Frame-rate drift is likely negligible over ~30s and may not be over several
minutes — unverified.

**Tripod vs handheld is a trade, not an upgrade:**

|                 | Handheld                         | Tripod                  |
| --------------- | -------------------------------- | ----------------------- |
| Static geometry | accumulates over time, very good | fixed to that viewpoint |
| Moving subjects | poor — holes track the subject   | clean, given two angles |
| Registration    | drifts, hard                     | one constant, easy      |

Empty room: handheld walking around is better, accumulation does the work free.
A performer: two tripods.

**Storage.** A 31-second single-camera LiDAR take measured 4.2 GB raw and 6.3 GB
converted. Two cameras doubles both, and the originals are worth keeping for
re-solving alignment. Budget ~25-30 GB per take and check disk before shooting.
