---
related_ids:
  - "JGziC21y2zWJnQoM4nCH3JF4G4umcAAM"
  - "ZG0w579Q2TWZLYoC9HqDQJlYMcmzAAAF"
semantic_id: "ZCynByxRxzcJnZqQ5DCi0jAYUt-6IAAB"
---

# Vector displays and pen-plotter linework in Three.js

The Sketchpad / robot-draftsman look: no fill anywhere, one ink, and a picture that is
**drawn in an order** rather than appearing all at once.

**Version note:** written against **r180**. The GLSL is plain and runs on r132 unchanged;
only import paths differ. Unlike most of the techniques here this one needs **no full-screen
post pass at all** — it is geometry and blend state — so it is one of the few desktop
techniques that ports to the phone-in-headset project intact. See
`visual-effects-without-postprocessing.md` for why that matters there.

## What the machine actually was

Ivan Sutherland, **Sketchpad**, 1963, on Lincoln Lab's **TX-2** (64K of 36-bit words).
A **vector CRT** — the beam was told to go from point to point, so there was no raster,
no pixels and no fill, only strokes. Input was a **light pen**. Drawings were stored as
masters with instances in a ring structure, and a **geometric constraint solver** held
lengths and angles fixed while you dragged.

Two different aesthetics get conflated under "Sketchpad", and they want different code:

|           | vector CRT                             | pen plotter / draftsman          |
| --------- | -------------------------------------- | -------------------------------- |
| ground    | black                                  | paper                            |
| ink       | one phosphor colour, glowing           | one dark ink                     |
| crossings | **brighter** (additive)                | **darker** (multiply)            |
| motion    | continuous refresh, everything at once | one stroke at a time, pen lifts  |
| flaws     | beam bloom, drift                      | overshoot, slop, corner rounding |

Most of the pipeline is shared. Pick the blend mode and the flaw model per look.

## The five tells

Judge an imitation against these before tuning anything:

1. **No fill, ever.** Tone comes only from line density. The moment a surface is shaded,
   the illusion is a wireframe overlay on a normal render.
2. **Crossings change value.** Additive glow where strokes overlap is the single strongest
   CRT tell and it costs one line of blend config — no bloom pass required.
3. **Uniform line weight with depth.** A beam does not get thinner far away. Perspective
   line thinning reads as "3D engine", not "display".
4. **It is drawn in an order.** For the draftsman reading this is the whole thing, and it
   is what the rest of this file is mostly about.
5. **Ends overshoot, corners round.** A pen has mass. Perfect corners read as vector art.

## Getting lines at all

```js
const edges = new THREE.EdgesGeometry(geometry, 20); // crease angle, degrees
const lines = new THREE.LineSegments(edges, mat);
```

`EdgesGeometry` is not cheap and is deterministic — **build it once per unique geometry and
cache it**, never per instance. Merge the results into one buffer where you can; linework
scenes die on draw calls, not on fragments.

**`linewidth` is ignored** on essentially every WebGL backend — you get 1px. Already covered
in `visual-effects-without-postprocessing.md`; the fix is `Line2` / `LineMaterial` from
`three/addons/lines/*`, which builds screen-space quads (4× the vertices, and a different
attribute layout than the code below assumes). For a CRT look 1px plus additive glow is
often closer to the reference anyway.

### The gotcha that decides the whole approach

**`EdgesGeometry` finds crease edges, not silhouettes.** A sphere has no creases, so it
draws _nothing_. A cylinder draws its two end circles and no sides. Real vector displays
drew whatever was in the display list, which for curved bodies meant hand-authored
generator lines.

This is the fork in the road:

- **Geometric edges** — can be ordered into strokes, so they can be _drawn over time_.
  Silhouettes missing on curved geometry.
- **Depth/normal edge detection in a post pass** — catches silhouettes correctly, but the
  edges only exist as fragments, with no identity and no order, so a pen cannot walk them.

**Progressive drawing requires geometric lines.** If the scene is mostly curved and you
want the plotter animation, add explicit generator lines to the models rather than trying
to make a post pass sequential.

`EdgesGeometry` is not the only source of segment soup. **Marching-squares contour
extraction** (`terrain-contour-lines.md`) emits exactly this format, so terrain contours feed
straight into the chainer below — a topographic map that draws itself one contour at a time,
which is about as close to a real plotter as this technique gets.

## Turning segment soup into strokes

`EdgesGeometry` emits an unordered, non-indexed segment soup: 2 verts per edge, arbitrary
winding, arbitrary order. A draftsman draws **trails** — pen down, follow a connected path,
pen up. So weld the endpoints into a graph and decompose it into trails.

This is an Eulerian path problem, and the theory gives a target to check against: a
connected component with `k` odd-degree nodes needs exactly `max(1, k/2)` trails. That
number is the minimum possible number of pen-lifts.

```js
// Segment soup -> array of node-index polylines, each edge used exactly once.
function chainSegments(pos, weld = 1e-4) {
  const q = (v) => Math.round(v / weld);
  const nodeOf = new Map(),
    nodePos = [];
  const idOf = (i) => {
    const k = `${q(pos[i])},${q(pos[i + 1])},${q(pos[i + 2])}`;
    let n = nodeOf.get(k);
    if (n === undefined) {
      n = nodePos.length;
      nodeOf.set(k, n);
      nodePos.push([pos[i], pos[i + 1], pos[i + 2]]);
    }
    return n;
  };

  const edges = [],
    adj = [];
  for (let s = 0; s < pos.length / 6; s++) {
    const a = idOf(s * 6),
      b = idOf(s * 6 + 3);
    if (a === b) continue; // degenerate
    const e = edges.length;
    edges.push([a, b]);
    (adj[a] || (adj[a] = [])).push(e);
    (adj[b] || (adj[b] = [])).push(e);
  }

  const used = new Uint8Array(edges.length);
  const deg = new Int32Array(nodePos.length);
  for (const [a, b] of edges) {
    deg[a]++;
    deg[b]++;
  }
  let remaining = edges.length;
  const nextEdge = (n) => (adj[n] || []).find((e) => !used[e]);

  // Greedy walk. From an odd node it gets stuck at another odd node;
  // from an even node it gets stuck back where it started (a circuit).
  const walk = (start) => {
    const path = [start];
    let cur = start;
    for (;;) {
      const e = nextEdge(cur);
      if (e === undefined) break;
      used[e] = 1;
      remaining--;
      const [a, b] = edges[e];
      deg[a]--;
      deg[b]--;
      cur = a === cur ? b : a;
      path.push(cur);
    }
    return path;
  };

  const strokes = [];

  // Phase 1 — open trails. Each one drops the odd count by exactly 2, so this
  // emits odd/2 strokes: the minimum number of pen-lifts. It strands loops.
  for (let n = 0; n < nodePos.length; n++)
    while (deg[n] % 2 === 1) {
      const t = walk(n);
      if (t.length > 1) strokes.push(t);
    }

  // Phase 2 — what's left is even everywhere, so every walk is a closed circuit.
  // Hierholzer: splice each one into a stroke it touches instead of emitting it.
  while (remaining > 0) {
    let host = -1,
      at = -1;
    outer: for (let s = 0; s < strokes.length; s++)
      for (let i = 0; i < strokes[s].length; i++)
        if (nextEdge(strokes[s][i]) !== undefined) {
          host = s;
          at = i;
          break outer;
        }
    if (host >= 0) {
      strokes[host].splice(at, 1, ...walk(strokes[host][at]));
    } else {
      const e = edges.findIndex((_, i) => !used[i]); // island with no contact
      const t = walk(edges[e][0]);
      if (t.length > 1) strokes.push(t);
    }
  }

  return { strokes, nodePos };
}
```

### Why the two phases, measured

Plain greedy — walk from odd nodes, emit whatever you get — covers every edge exactly once
and looks fine on paper. On a cube (12 edges, all 8 corners degree 3, so the minimum is 4)
it produces **5 strokes: 6 + 3 + 1 + 1 + 1**. Those three one-segment strokes are loops the
long walk cut itself off from, and they do not read as drawing — they read as lines
twitching on. With the phase split above the same cube gives **4 strokes — the theoretical
minimum**.

**Check the count, not the partition.** Re-measured on r180 (0.180.0) the same cube chains
to `6 + 3 + 1 + 2`, not the `6 + 4 + 1 + 1` recorded earlier. Both are 4 strokes and both
cover all 12 edges exactly once, so both are optimal; how the 12 edges _divide_ between
strokes falls out of the order `EdgesGeometry` happens to emit segments in, which is a
three-version implementation detail and not something to assert. The invariant worth
asserting in a test is `strokes.length === max(1, oddNodes / 2)` and total segments ===
edge count.

Also worth knowing: splicing a phase-1 trail is wrong and the bug is quiet. A walk from an
odd node returns an **open** path, and splicing an open path into the middle of another one
silently welds separate strokes together and leaves a discontinuity where the pen teleports.
Only phase-2 circuits are safe to splice. Assert that a spliced sub-walk ends where it
started.

### Repeating one primitive: skylines, cityscapes, greebles

"Cache per unique geometry" reads like a non-answer when the scene is 200 boxes and every
box is a different size — that is 200 unique geometries, so it sounds like 200 chains.

It isn't, because **`chainSegments` depends only on topology, not on positions.** A
`BoxGeometry` at default segment counts always yields the same 12 crease edges in the same
emission order however you scale it, so the stroke decomposition is identical for every box
in the scene. Measured on r180 — `1×1×1`, `37×4.2×0.9` and `16×260×26` produce byte-identical
stroke arrays, 4 strokes each:

```js
// once, ever — for the whole city
const unit = chainSegments(
  new THREE.EdgesGeometry(new THREE.BoxGeometry(1, 1, 1), 20).getAttribute(
    "position",
  ).array,
);

// per building: reuse `unit.strokes`, substitute scaled+placed corner positions
const nodePos = unit.nodePos.map(([x, y, z]) =>
  new THREE.Vector3(x * w, y * h, z * d).applyMatrix4(placement).toArray(),
);
```

The same holds for any primitive used repeatedly at varying scale, and it collapses the
one genuinely expensive load-time step to a constant. It does **not** hold across different
segment counts, across mixed primitives, or after a merge — merging welds coincident corners
between neighbouring bodies and changes the graph, which changes the decomposition. Chain
first, merge the baked buffers after.

**Ordering across instances is a separate decision, and it is the whole performance.** Bake
each building's strokes into one continuous `aPen` run and the pen finishes a tower before
starting the next, which reads as a machine working across the skyline. Interleave them and
every building grows at once, which reads as a loading bar. Sort the instances before baking
— by azimuth for a sweep around the horizon, by distance for a plot that walks toward the
viewer — because after `bakePlot` the order is frozen into the attribute and the only way to
change it is to rebake.

Budget the gap accordingly: `gap` is in world units and accumulates once per stroke, so a
city of 200 boxes at 4 strokes each pays 800 gaps. At `gap = 2.0` that is 1600 world units
of pen-up travel, which can easily exceed the total inked length and leave the plot looking
stalled. Scale `gap` down as instance count rises, or make inter-building gaps large and
intra-building gaps small so the pauses land where the eye expects them.

## Baking the pen attributes

One float per vertex carries everything the animation needs: distance along the whole plot,
accumulated across strokes, with a gap inserted at each pen-up.

```js
function bakePlot(strokes, nodePos, { gap = 2.0 } = {}) {
  const position = [],
    tangent = [],
    pen = [];
  let d = 0;
  const V = (i) => nodePos[i];
  for (const s of strokes) {
    d += gap; // pen-up travel time
    for (let i = 0; i + 1 < s.length; i++) {
      const a = V(s[i]),
        b = V(s[i + 1]);
      const t = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
      const len = Math.hypot(t[0], t[1], t[2]) || 1;
      position.push(...a, ...b);
      tangent.push(...t, ...t); // un-normalised is fine
      pen.push(d, d + len);
      d += len;
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(position, 3));
  g.setAttribute("aTangent", new THREE.Float32BufferAttribute(tangent, 3));
  g.setAttribute("aPen", new THREE.Float32BufferAttribute(pen, 1));
  g.userData.penTotal = d;
  return g;
}
```

The whole animation is then **one uniform** sweeping `0 → penTotal` over a static buffer.
No geometry updates, no per-frame CPU work, no `needsUpdate`. `gap` in world units doubles
as the pause between strokes, which is most of what makes it read as a machine rather than
a wipe.

## The shaders

Both stages below were compiled with `glslangValidator` as `#version 300 es`. In a
`ShaderMaterial` drop the version/`in`/`out` and use three's default dialect (`attribute` /
`varying` / `gl_FragColor`), or set `glslVersion: THREE.GLSL3`.

```glsl
// vertex
in vec3  aTangent;   // stroke direction, object space
in float aPen;       // cumulative pen distance
uniform float uWobble;    // pen slop, in pixels
uniform vec2  uViewport;  // drawingBufferWidth/Height
out float vPen;

void main() {
  vec4 clip  = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  vec4 tclip = projectionMatrix * modelViewMatrix * vec4(position + aTangent, 1.0);

  // stroke direction in SCREEN space, so slop stays in the plane of the paper
  // however the line is oriented in the world
  vec2 d = (tclip.xy / tclip.w - clip.xy / clip.w) * uViewport;
  vec2 dir = length(d) > 1e-6 ? normalize(d) : vec2(1.0, 0.0);
  vec2 perp = vec2(-dir.y, dir.x);

  // two octaves of slop, deterministic in arc length: no texture, no rand
  float w = sin(aPen * 0.70) * 0.6 + sin(aPen * 0.23 + 1.7) * 0.4;

  // pixels -> NDC is 2/viewport, and clip.xy = ndc * clip.w
  clip.xy += perp * (w * uWobble) * 2.0 / uViewport * clip.w;

  vPen = aPen;
  gl_Position = clip;
}
```

```glsl
// fragment
uniform float uPen;    // how far the pen has travelled
uniform float uHot;    // length of the bright beam tip
uniform vec3  uInk;
uniform float uGhost;  // brightness of not-yet-drawn line; 0 = invisible
in float vPen;
out vec4 fragColor;

void main() {
  if (vPen > uPen) {
    if (uGhost <= 0.0) discard;
    fragColor = vec4(uInk * uGhost, 1.0);
    return;
  }
  float hot = 1.0 - clamp((uPen - vPen) / uHot, 0.0, 1.0);
  fragColor = vec4(uInk * (1.0 + hot * 3.0), 1.0);
}
```

Three things worth naming:

- **The cut lands mid-segment for free.** `vPen` interpolates along the line, so a long edge
  is drawn partially and correctly without subdividing it. Perspective-correct interpolation
  of an arc-length varying is exactly the right behaviour here, not an approximation.
- **`uHot` is the beam.** A short bright head on the drawn end is what sells "something is
  making this line" — it is the difference between a reveal and a plot.
- **`uGhost` is the construction-line mode.** Faint un-drawn geometry that the pen then
  inks over is very Sketchpad, and it is one branch, not a second pass.

The wobble is deliberately two sine octaves rather than noise: it is smooth in arc length,
so a stroke bends rather than jitters, and it is stable frame to frame because it depends
only on the attribute. Hash noise here vibrates and looks like a bug.

## Blend state, which is most of the look

```js
// vector CRT
new THREE.ShaderMaterial({
  blending: THREE.AdditiveBlending,
  depthWrite: false,
  transparent: true,
});
scene.background = new THREE.Color(0x000000);
```

Additive plus a black ground gives brighter crossings and a natural beam bloom at dense
areas **without a bloom pass**. Overlapping strokes blow out exactly where a real CRT did.

```js
// ink on paper
new THREE.ShaderMaterial({
  blending: THREE.MultiplyBlending,
  depthWrite: false,
});
```

Multiply darkens at crossings, which is what layered ink does. Note `uInk` then wants to be
a _near-white_ value that multiplies down, not a dark colour — the intuition inverts.

## Hidden lines without a post pass

Two draw passes, no render targets:

```js
// 1. depth-only prepass: the solid bodies, writing depth, no colour
mesh.material.colorWrite = false;
// 2. the linework, depth-tested against it
lineMat.depthTest = true;
lineMat.polygonOffset = true; // stop coincident edges z-fighting
lineMat.polygonOffsetFactor = -1;
lineMat.polygonOffsetUnits = -1;
```

Better still, and the actual drafting convention: draw the linework **twice**, once with
`depthFunc: THREE.LessEqualDepth` at full strength and once with
`depthFunc: THREE.GreaterDepth` at low opacity. Hidden edges show through faintly, the way
a drafter's construction lines do. Two draw calls, no targets, and it looks more like the
reference than correct hidden-line removal does.

## Cost

Per vertex: `position` (12B) + `aTangent` (12B) + `aPen` (4B) = **28 bytes**, versus 24 for
a plain lit vertex with normals. Vertex count is 2 per edge and edges are far fewer than
triangles.

The expensive part is `EdgesGeometry` + `chainSegments`, both **load-time and cacheable per
unique geometry**. Chaining is roughly linear in edge count; the phase-2 host search is a
scan over emitted strokes, which is fine at scene scale but is the first thing to index if
you ever feed it a hundred thousand edges.

At runtime it is one draw call per merged buffer and one uniform write per frame. This is
one of the cheapest stylised looks available — cheaper than the depth/normal edge post pass
it superficially resembles — as long as you accept the silhouette limitation above.

## Honest labelling

Sketchpad was a **2D drafting program with a constraint solver**. It did not render shaded
3D scenes, and it had no notion of hidden-line removal. A 3D wireframe in one glowing colour
is an homage to _the display it ran on_, not to the program.

If a project wants to claim Sketchpad specifically, the thing to actually implement is the
part nobody imitates: **constraints as first-class objects** — grab a corner, drag it, and
watch the lengths and angles that were declared fixed hold while everything else
reorganises. That is what was new in 1963. The glowing lines were just the CRT.
