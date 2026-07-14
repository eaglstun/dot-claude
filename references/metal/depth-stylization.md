---
topic_id: "v2:LHJO"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "5vWmDHeIAvVVgD3FZPhzrTsgE4gIIAAH"
related_ids:
  - "v_-mL386UidNhTNMcngz7JppGoKEsAAB"
  - "nvOnDK5IQrfJlB40VHmytfiIEotAsAAF"
---
# Edge / normal / stylization recipes for the depth-passthrough renderer

Sources:

- MSL screen-space derivatives (`dfdx`/`dfdy`/`fwidth`) — Metal Shading Language Specification
  (Apple), §"Derivatives" (the `metal::dfdx`, `metal::dfdy`, `metal::fwidth` free functions);
  semantics summary: <http://www.aclockworkberry.com/shader-derivative-functions/> and Ben Golus,
  <https://bgolus.medium.com/distinctive-derivative-differences-cce38d36797b>.
  `fwidth(p) == abs(dfdx(p)) + abs(dfdy(p))`; derivatives are exact only across the 2×2
  rasterizer quad, so they're coarse but free.
- Normals-from-depth: Turánszki / Wicked Engine,
  <https://wickedengine.net/2019/09/improved-normal-reconstruction-from-depth/>; accurate
  (Humus-style 5-tap) variant, Yuwen Wu, <https://atyuwen.github.io/posts/normal-reconstruction/>;
  method roundup, Ben Golus, <https://gist.github.com/bgolus/a07ed65602c009d5e2f753826e8078a0>.
- In-repo precedents this builds on:
  - `ios/KaraokeVR/Passthrough.metal:83` `depthOrFar` — depth in metres, `<=0` (no LiDAR
    reading) sunk to 8 m so foreground silhouettes against sky/windows still register.
  - `ios/KaraokeVR/Passthrough.metal:114` 4-tap N/S/E/W depth-gradient silhouette (mode 2).
  - `ios/KaraokeVR/Passthrough.metal:224` `outlineOnlyFragment` — 24-tap (DIRS 8 × RINGS 3)
    feathered depth-edge disc, anti-aliasing the low-res LiDAR boundary into a glow (mode 4).
  - `ios/KaraokeVR/Passthrough.metal:53` `sampleCameraRGB` — YCbCr→RGB at one UV (reusable).
  - `ios/KaraokeVR/Passthrough.metal:205` `depthPalette` — near→far cosine ramp.

Fetched / verified: 2026-06-28.

## Depth facts that constrain every edge effect here

(Full detail in `.claude/references/arkit/scene-depth.md`.) `smoothedSceneDepth.depthMap` is
`r32Float`, **metres**, optical-axis Z (not ray length), **~256×192**, registered to the camera
image. Implications:

- A depth edge is a discontinuity **in metres** — already what the existing modes detect. It is
  geometry-true (real silhouettes) but **low-res and noisy at distance**: past ~3–4 m the 256×192
  grid + sensor noise makes raw single-tap gradients shimmer and stair-step. Feather (mode 4) or
  fade the effect out with distance.
- The **luma plane** (`textureY`, plane 0) is full camera resolution and free to sample
  (`textureY.sample(s,uv).r`). Luma edges (Sobel) catch **interior detail** depth can't —
  faces, text, texture — but also catch shadows/noise and have no metric meaning.
- All flat-passthrough fragment effects (modes 0/1/2 style) are **inherently per-eye-safe**: each
  eye redraws the same fragment math over the same camera+depth textures on its own viewport
  (only `lensShift` differs). No framebuffer feedback, no eye-to-eye blend → fusion is identical
  to plain passthrough. Keep new edge effects in this lane; avoid full-drawable post/feedback
  (that's the trap mode 4's trail avoids by splitting per-eye viewport halves).

## Sobel (luma edges)

3×3 separable gradient, 8 neighbour taps + reuse centre:

```
Gx = [-1 0 +1; -2 0 +2; -1 0 +1],  Gy = transpose(Gx)
edge = sqrt(Gx^2 + Gy^2)   // or |Gx|+|Gy| to skip the sqrt (fast-math-safe, cheaper)
```

Tap on luma (`r8`), not converted RGB — 8 taps not 8 full YCbCr conversions. Cost: **9 luma
taps/pixel × 2 eyes**. The mode-2 blur already does ~17 RGB taps/pixel/eye and holds 60 fps, so
9 luma taps is comfortably in budget. Threshold with `smoothstep(t0,t1,edge)` to suppress camera
noise; raise t0 if it crawls.

## Roberts cross (cheaper edges)

2×2 diagonal differences — 4 taps, blunter than Sobel, fine for a chunky comic ink. Use when tap
budget is tight (stacked with depth edges).

## Normals from depth (orientation-based shading: rim light, crease ink)

Two cost tiers:

1. **Derivative (cheapest, ~free):** unproject the centre depth texel to a camera-space position
   `p` (same pinhole math as `reprojectVertex`, `Passthrough.metal:182`), then
   `n = normalize(cross(dfdx(p), dfdy(p)))`. One depth tap. **Blocky** (quad-granular) and
   **wrong at silhouettes** (derivative straddles a depth jump → garbage normal); acceptable for
   a stylized rim, not for smooth shading.
2. **Central-difference 4-tap:** sample depth at ±dx, ±dy, unproject each, build tangents from
   the _smaller_ one-sided difference on each axis (Turánszki) to avoid silhouettes; cross them.
   4–5 depth taps. Cleaner; the Yuwen Wu 5-tap picks the best of the two one-sided diffs per axis
   for near-perfect normals at corners. Worth it for crease lines.

Uses: **rim light** `rim = pow(1 - saturate(dot(n, viewDir)), k)` glows grazing surfaces → gives
volume to a person; **crease ink** = ink where `dot(n_center, n_neighbour)` drops below a cosine
threshold, catching folds that are NOT depth silhouettes.

**Fast-math caveat (default ON in this project's pipelines):** `normalize` of a near-zero vector
is undefined/NaN under fast-math. Guard: `float l = length(v); n = l > 1e-5 ? v/l : float3(0,0,1);`
Don't rely on `isnan`-style checks — fast-math may assume operands are finite.

## Anti-aliasing procedural lines (contours, halftone, scanlines)

For an iso-line at constant value `c` of a smooth field `f` (e.g. depth contours every 0.25 m):
`w = fwidth(f); line = 1 - smoothstep(0, w, abs(fract(f/interval) - 0.5))` keeps the line ~1 px
wide regardless of distance — the right way to stop contour shimmer where depth steepens. Same
`fwidth` trick anti-aliases halftone dot edges and scanline bands.

## Relevance to this renderer

Every recipe here slots in as a **new flat-passthrough fragment function + pipeline + a `case` in
`drawBackground`** (mirroring mode 2's `passthroughBlurFragment` wiring), reusing `depthOrFar`,
`sampleCameraRGB`, `depthPalette`, and the depth texture already bound at `texture(2)`. They stay
in the fusion-safe in-pass lane; none needs the mode-4 trail/offscreen machinery unless you
deliberately want ghosting.
