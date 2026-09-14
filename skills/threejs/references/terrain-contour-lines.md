---
related_ids:
  - "JGziC21y2zWJnQoM4nCH3JF4G4umcAAM"
  - "JZQkJVAhZxGIrLwC4kqk1Bl5MZ12cAAK"
semantic_id: "hGznKXSR0bGZDF5epWuH1BlYm5FGMAAG"
---

# Contour lines on terrain in Three.js

Topographic contours — level sets of height — either as a shader band on the terrain
material, or as real polylines extracted with marching squares.

**Version note:** written against **r180**. Both paths are plain GLSL / plain JS and run on
r132 unchanged; only import paths differ. Neither needs a full-screen post pass, so both
port to the phone-in-headset project (the shader path costs a handful of fragment
instructions on a material that is already being drawn).

## Pick the path first, they are not interchangeable

|                             | shader bands                       | marching-squares polylines             |
| --------------------------- | ---------------------------------- | -------------------------------------- |
| cost                        | ~20 fragment instructions, 0 draws | CPU extraction + 1 draw call           |
| follows deformed terrain    | automatically, per pixel           | must re-extract when the field changes |
| antialiasing                | free and correct via `fwidth`      | you own it (1px lines, or `Line2`)     |
| distance LOD                | free, continuous                   | you rebuild, or hide levels            |
| labels / elevation numbers  | no                                 | yes                                    |
| per-contour styling         | index contours only                | anything                               |
| draw progressively, plotter | no                                 | **yes** — see below                    |
| export to SVG               | no                                 | yes                                    |

Default to the shader. Reach for marching squares when you need labels, per-line styling,
or the pen-plotter drawing animation.

## Where the height comes from

Contours are level sets of **world** height. Not object space, not view space.

```js
mat.onBeforeCompile = (s) => {
  s.vertexShader = s.vertexShader
    .replace("#include <common>", "#include <common>\nvarying vec3 vWorldPos;")
    .replace(
      "#include <worldpos_vertex>",
      "#include <worldpos_vertex>\nvWorldPos = worldPosition.xyz;",
    );
  // ...matching declaration + the contour code in the fragment shader
};
```

`#include <worldpos_vertex>` only emits `worldPosition` when the material needs it, so if
that chunk turns out to be empty, compute it yourself with
`modelMatrix * vec4(transformed, 1.0)` **after** the displacement chunks. See
`material-injection-and-triplanar.md` for the general shape of this and the chunk-order
traps.

If the terrain is displaced in the vertex shader, the contour must read the **displaced**
height — otherwise contours sit on the undisplaced base surface and slide around as the
terrain moves, which looks like a projection bug and is very hard to read as one.

## The shader path

Built up in the order the problems appear.

**Naive.** `fract(h / interval) < 0.02` gives you contours that are the wrong thickness
everywhere: fat where the ground is flat, invisible where it is steep, and a moiré mess in
the distance. Thickness has to be defined in **pixels**, which means asking the GPU how fast
height is changing per pixel.

```glsl
float f = h / uInterval;      // height, in units of contour interval
float w = fwidth(f);          // ...and how many intervals a pixel spans
float d = abs(fract(f - 0.5) - 0.5);         // distance to nearest contour
float px = d / max(w, 1e-6);                 // that distance, in pixels
float line = 1.0 - smoothstep(width - 0.5, width + 0.5, px);
```

`fwidth` here folds slope _and_ distance into one number, which is exactly right: a contour
band is thin in world units on a steep slope and wide on a flat one, and this gets both
without a single extra uniform.

**Then Nyquist.** Below two pixels per interval the pattern cannot be represented at all,
and pushing on regardless is what produces the shimmering moiré on distant hills. Fade to
the pattern's own average ink instead:

```glsl
float duty = clamp(2.0 * width * w, 0.0, 1.0);
return mix(line, duty, smoothstep(0.34, 0.5, w));
```

Same failure and same fix as the ground-hatch in CAPRICCIO and as dither cell sizing —
see `dithering-and-halftone.md`.

**Then LOD**, which is better than fading to grey where you can afford two evaluations.
Double the interval as density rises. The nice property: each coarser level keeps _every
second contour_ of the finer one, so the crossfade reads as alternate lines fading out,
not as the whole map dissolving.

### The whole thing, validated

Compiled with `glslangValidator` as `#version 300 es`. For a `ShaderMaterial` use three's
default dialect (`varying` / `gl_FragColor`) or set `glslVersion: THREE.GLSL3`.

```glsl
uniform float uInterval;   // world units between contours at LOD 0
uniform float uWidthPx;    // half-width of a normal contour, in pixels
uniform float uIndexMul;   // how much fatter every 5th contour is
uniform float uTargetW;    // max intervals-per-pixel before dropping a level
uniform vec3  uInk, uPaper;

// One contour band. `f` is height in units of THIS level's interval, `w` is how
// many of those intervals a pixel spans, `k` is this level's interval multiplier
// relative to the base (1, 2, 4, ...).
float band(float f, float w, float k) {
  float n = floor(f + 0.5);                 // nearest contour
  // Index contours: every 5th BASE contour stays heavy at every LOD, because a
  // level-k contour n sits at base height n*k.
  float width = uWidthPx * (mod(n * k, 5.0) < 0.5 ? uIndexMul : 1.0);

  float d  = abs(fract(f - 0.5) - 0.5);
  float px = d / max(w, 1e-6);
  float line = 1.0 - smoothstep(width - 0.5, width + 0.5, px);

  float duty = clamp(2.0 * width * w, 0.0, 1.0);
  return mix(line, duty, smoothstep(0.34, 0.5, w));
}

void main() {
  float h    = vWorldPos.y;
  float base = h / uInterval;
  float w0   = fwidth(h) / uInterval;

  float lod = max(0.0, log2(max(w0, 1e-6) / uTargetW));
  float k0  = exp2(floor(lod));

  float c = mix(
    band(base / k0,       w0 / k0,       k0),
    band(base / (k0*2.0), w0 / (k0*2.0), k0*2.0),
    fract(lod)
  );

  // Cliffs: where the surface is near vertical, contours genuinely converge.
  // Let them go rather than resolving them into mush.
  c *= smoothstep(0.12, 0.45, abs(normalize(vWorldNormal).y));

  gl_FragColor = vec4(mix(uPaper, uInk, c), 1.0);
}
```

`mod(n * k, 5.0)` is exact, not an approximation: at `k = 2` the drawn contours are the even
base heights, and the ones passing the test are base 0, 10, 20 — precisely the multiples of
5 that survive at that level. Index contours never drift or double up across a LOD change.

### The duty formula is exact, with one measured exception

Integrating the band's coverage numerically against `duty = 2·width·w`: exact to four
decimals across `width ∈ {0.5, 1, 1.5, 2}` px and `w ∈ {0.02 … 0.34}` — **except**
`width = 1.5, w = 0.34`, where the clamp reports 1.0 but the true mean is **0.9458**, so the
fade runs about 5% too dark right at the transition. The cause is the smoothstep's soft
edges overlapping before the hard cores do.

**Keep `uWidthPx ≤ 1.0`** and the formula was exact in every case measured. Fatter contours
want a hand-fitted curve near saturation, or `uTargetW` lowered so LOD takes over before the
fade ever engages.

### Cliffs

`fwidth` explodes on near-vertical faces and every contour in the neighbourhood merges.
Real topographic maps have the same problem and solve it socially (hachures, rock drawing).
The `smoothstep` on `abs(normal.y)` above just drops contours on steep faces, which reads
correctly — cliffs become blank rock rather than a smear.

## The marching-squares path

Emits a **segment soup** — which is exactly the input format
`vector-display-and-plotter-linework.md`'s `chainSegments` wants. That is the payoff of
doing it geometrically: extract contours, chain them into strokes, and the pen-plotter
animation draws your topo map one contour at a time.

```js
// corners c00,c10,c11,c01 -> bits 0,1,2,3
// edges: 0 = bottom (c00-c10), 1 = right (c10-c11), 2 = top (c11-c01), 3 = left (c01-c00)
const CASES = [
  [],
  [3, 0],
  [0, 1],
  [3, 1],
  [1, 2],
  null /*saddle*/,
  [0, 2],
  [3, 2],
  [2, 3],
  [2, 0],
  null /*saddle*/,
  [2, 1],
  [1, 3],
  [1, 0],
  [0, 3],
  [],
];

export function marchingSquares(hf, w, h, level, opt = {}) {
  const { x0 = 0, z0 = 0, dx = 1, dz = 1 } = opt;
  const out = [];
  const H = (i, j) => hf[j * w + i];
  const lerpEdge = (ax, az, av, bx, bz, bv) => {
    const d = bv - av;
    const t = Math.abs(d) < 1e-12 ? 0.5 : (level - av) / d;
    return [ax + (bx - ax) * t, az + (bz - az) * t];
  };

  for (let j = 0; j + 1 < h; j++)
    for (let i = 0; i + 1 < w; i++) {
      const v00 = H(i, j),
        v10 = H(i + 1, j),
        v11 = H(i + 1, j + 1),
        v01 = H(i, j + 1);
      const m =
        (v00 > level ? 1 : 0) |
        (v10 > level ? 2 : 0) |
        (v11 > level ? 4 : 0) |
        (v01 > level ? 8 : 0);
      if (m === 0 || m === 15) continue;

      const X = x0 + i * dx,
        Z = z0 + j * dz;
      const pt = (e) => {
        switch (e) {
          case 0:
            return lerpEdge(X, Z, v00, X + dx, Z, v10);
          case 1:
            return lerpEdge(X + dx, Z, v10, X + dx, Z + dz, v11);
          case 2:
            return lerpEdge(X + dx, Z + dz, v11, X, Z + dz, v01);
          default:
            return lerpEdge(X, Z + dz, v01, X, Z, v00);
        }
      };

      let pairs = CASES[m];
      if (pairs === null) {
        // Saddle: all four edges cross and both ways of joining them are
        // topologically valid. Break the tie with the cell-centre value —
        // what the surface actually does between the samples.
        const centreAbove = (v00 + v10 + v11 + v01) * 0.25 > level;
        const cornersAbove = m === 5; // m===5 => c00 & c11 above
        pairs =
          centreAbove === cornersAbove
            ? m === 5
              ? [3, 2, 1, 0]
              : [0, 3, 2, 1]
            : m === 5
              ? [3, 0, 1, 2]
              : [0, 1, 2, 3];
      }

      for (let k = 0; k < pairs.length; k += 2) {
        const a = pt(pairs[k]),
          b = pt(pairs[k + 1]);
        out.push(a[0], level, a[1], b[0], level, b[1]);
      }
    }
  return new Float32Array(out);
}
```

### What was verified

- **Cone**, `h = R − r`, contour at 15: every emitted point lands on the circle of radius
  `R − 15` to within **0.0035** on a unit grid, and it chains to **one closed stroke** with
  every node at degree 2.
- **Two peaks** → exactly two closed strokes.
- **Smooth noise field, 7 levels**: every non-closed contour terminates on the grid
  boundary — i.e. nothing dead-ends in the interior, which is the topological invariant that
  catches a wrong case table.
- **Pure saddle** `h = (i−c)(j−c)` at level 0, the worst case: resolves into disjoint arcs,
  no crossing, no degenerate segments.
- **Level exactly on sample values**: finite coordinates, contour lands on the right row.
  This is the case that produces `NaN` if you divide by `bv − av` unguarded.

### The saddle rule matters more than it looks

Cases 5 and 10 are genuinely ambiguous — the samples do not say whether two high corners are
connected or pinched apart. Picking arbitrarily (as many implementations do) makes contours
join and separate incoherently between adjacent levels, and on a moving field they pop.
Averaging the four corners and asking which side the centre is on is one extra add and
makes the whole family of contours mutually consistent.

## Draping: contours and the mesh disagree slightly

Marching squares interpolates **bilinearly** inside a cell. `PlaneGeometry` renders each
cell as **two triangles**, which is a different surface. At the cell centre the gap is
exactly `|v00 + v11 − v10 − v01| / 4` — the saddle term — so it is zero on any locally
planar cell and largest exactly where the terrain twists.

Measured on a smooth test field spanning 30.76 world units of height: **max gap 0.046, mean
0.016**, about **0.15%** of the height range. Small, but not zero, and it grows directly with
per-cell roughness — on noisy terrain it will be visible.

So the extracted polyline will dip below the rendered triangles in places and float above in
others. **Use `polygonOffset` on the line material, not a constant Y lift** — lifting by a
fixed Y shifts a contour _horizontally_ on any slope, by `lift / slope`, which on gentle
ground is a large and very visible error.

```js
lineMat.polygonOffset = true;
lineMat.polygonOffsetFactor = -1;
lineMat.polygonOffsetUnits = -1;
```

## Labels

The reason to extract polylines at all, usually. Because you have ordered points you can:
place the label where the contour is straightest (minimum turning over a window of points),
rotate the text to the local tangent, and **cut the gap out of the polyline itself** rather
than drawing an opaque box over it. Trimming a run of points out of a stroke is a splice;
the map convention is that the line breaks for the number, and faking it with a background
quad reads wrong immediately.

Keep labels upright: if the tangent points left, flip the text 180° and reverse it, or every
other label reads upside down.

## Cost

**Shader:** one `fwidth`, one `log2`, one `exp2`, two `band` evaluations. Roughly 20 ALU on a
material you were drawing anyway, zero extra draw calls, zero memory. Drop to one `band` and
the Nyquist fade if the budget is tight — that path is fine on a phone GPU.

**Marching squares:** linear in cells, per level. A 512² heightfield at 20 levels is ~5M cell
tests; that is a load-time or worker cost, not a per-frame one. Extraction only needs redoing
when the _field_ changes — camera movement changes nothing. If the terrain deforms every
frame, use the shader path; that is what it is for.

## Cartographic notes worth honouring

- **Contour interval is constant across a map.** Varying it by region is the single fastest
  way to make something read as decoration rather than as a map. The LOD in the shader is a
  _display_ concession, not a change of interval, which is why the index contours are pinned
  to base heights.
- **Every 5th contour is heavy and labelled.** Strongest single tell that this is a topo map.
- **Contours never cross and never branch.** If yours do, the case table is wrong — that is
  what the boundary-termination test above is for.
- **Closed loop = summit or depression**, and they are indistinguishable without hachures
  (inward ticks) or a spot height. If depressions matter in your terrain, the ticks are a
  per-stroke decoration on the polyline path, and impossible on the shader path.
