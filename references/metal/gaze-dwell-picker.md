---
topic_id: "v2:LHPF"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "TvGynH8Kgie79TascJKIwWlIC6POYAAA"
related_ids:
  - "JHgGF37YMwO43R-95YLLxWmXCqNGYAAC"
  - "znmiBn-4GmUp3TuYdxgSddlYU6Mc8AAJ"
---
# Gaze-raycast + dwell select in this stereo renderer (head-pose → hit-test → ring)

Source (ground truth = this repo + ARKit docs):

- `ios/KaraokeVR/StereoARRenderer.swift` — `yawAnchor(from:)` (L1063-1076) already derives
  head heading/position from `frame.camera.transform`; `draw(in:)` exposes `frame.timestamp`
  (the frame clock, used by the scanner sweep L604-606) and the per-eye loop / `clipOffset`
  lensShift (L611-678); `updateHUD` (L953-967) is the idiom for CPU-built clip-space geometry
  drawn through `cubePipeline` with identity MVP.
- `ios/KaraokeVR/ModeLabel.swift` — bake one `MTLTexture` per label string (CGContext → rgba8
  premultiplied), draw through the lyric pipeline. The tile-title baker is a twin of this.
- ARKit `ARCamera.transform` — column-major 4x4, camera→world; **−Z (column 2 negated) is the
  optical axis** the rear camera (and thus the passthrough gaze) points down; column 3 is the
  world position. Confirmed in-repo by `yawAnchor` using `-columns.2` as forward.
  https://developer.apple.com/documentation/arkit/arcamera/transform
- MSL Spec (Apple), fragment derivatives / `fract` / `atan2` for an optional SDF ring fragment.

Fetched/derived: 2026-06-28

## Head-forward gaze ray (orientation-free)

The passthrough shows the rear camera, so the user's gaze == camera optical axis. No
interface-orientation math is needed for the ray itself (the reticle is screen-centre in both
eyes; the ray is in ARKit world):

```swift
let cam = frame.camera.transform
let headPos     = SIMD3<Float>(cam.columns.3.x, cam.columns.3.y, cam.columns.3.z)
let headForward = normalize(-SIMD3<Float>(cam.columns.2.x, cam.columns.2.y, cam.columns.2.z))
```

## Angle hit-test with hysteresis (resolution-independent)

For each target placed at a known world position `tileWorldPos`:

```swift
let dir   = normalize(tileWorldPos - headPos)
let angle = acos(clamp(dot(headForward, dir), -1, 1))     // radians off gaze centre
```

Pick `argmin(angle)`. Hysteresis kills boundary flicker — a tile only _becomes_ hovered under
`enterHalfAngle`, and only _releases_ once past a wider `leaveHalfAngle`:

```
if hovered == nil { hovered = best if best.angle < enterHalfAngle }
else              { keep hovered unless hoveredAngle > leaveHalfAngle (then re-acquire) }
```

Prefer angle-between-vectors over project-to-screen-and-measure-distance: it's independent of
the per-eye viewport/lensShift, and for a head that rotates roughly in place the small position
drift at ~2 m is negligible. Place targets on a cylinder of fixed yaw/pitch about a **latched,
yaw-only, gravity-aligned anchor** (reuse `yawAnchor`) so a tile's world position is constant:
`anchor * rotationY(colYaw) * rotationX(rowPitch) * translation(0,0,-R)`. That same matrix
orients each quad to face inward — no per-frame billboard math.

## Dwell clock + commit, off `frame.timestamp`

`frame.timestamp` is monotonic and frame-paced (already the clock for the scanner). Reset the
dwell start whenever the hovered target changes; commit at threshold; debounce + require
look-away after a commit so one stare can't double-fire:

```
on hover change      → hoverStart = frame.timestamp        (ring resets to 0)
progress             = (now - hoverStart) / dwellSeconds   (drives the ring 0→1)
commit when progress >= 1 AND (now - lastCommit) > debounce
on commit            → lastCommit = now; hovered = nil      (must re-acquire to re-arm)
```

The clicker (`UITapGestureRecognizer` → `handleTap`) is the accelerator: it commits the
_currently_ hovered target instantly. Because the clicker is unreliable (CLAUDE.md), dwell is
primary and tap is the shortcut — never the only path.

## Aspect-correct centre ring (the one gotcha)

The dwell ring is head-locked at screen centre, drawn in BOTH eye viewports at
`clipOffset = shift * eyeSign` (the lensShift), exactly like the HUD. A per-eye viewport is
half the drawable width but full height, so NDC x and y are NOT isotropic — a ring built in raw
NDC comes out as an ellipse. Scale the ring's x by `eyeAspect = eyeHeight / (drawableWidth/2)`
(or pass it as a uniform) so it stays circular. The sweep arc (0→progress·2π, clockwise from 12
o'clock) is cheapest as CPU-built triangle-strip geometry through `cubePipeline` (identity MVP,
vertex-coloured — the `updateHUD` idiom, zero new shader); a small SDF fragment on one quad
(`atan2` for the sweep mask, `smoothstep` for AA) is the prettier upgrade if the arc edge
aliases.

## Tinting a premultiplied tile on hover (don't break the blend)

The menu tiles are baked premultiplied-alpha plates drawn through the lyric blend (src `.one`,
dst `.oneMinusSourceAlpha`). To tint one toward an accent on hover **while keeping it
premultiplied**, lerp the colour toward `accent * coverage`, not toward bare `accent` — the
texel's rgb is already `colour·a`, so the tint target must be scaled by the same `c.a` or the
transparent rounded-corners leak colour:

```metal
float4 c = plate.sample(s, uv);          // premultiplied
c.rgb = mix(c.rgb, u.accent.rgb * c.a, u.highlight);   // accent tint, still premultiplied
c.rgb = mix(c.rgb, c.a,            u.flash);            // whiten on commit (white*coverage == c.a)
return c * u.alpha;                       // scaling a premultiplied texel stays valid
```

Keep the shared uniform struct all-scalar plus 16-byte-aligned vectors (`float4x4`, `float4`,
`float2`) — **no bare `float3`** — so the Swift mirror's stride matches and the hover/flash
floats don't read garbage (the classic float3-pads-to-16 desync). Confirmed building in
`StereoARRenderer.MenuUniforms` ↔ `Passthrough.metal MenuPanelUniforms` (2026-06-28).

Concrete aspect correction (the centre-ring gotcha, numbers): `eyeAspect = drawableHeight /
(drawableWidth/2)` and scale only the ring's **x** by it. For a 2556×1179 landscape drawable
that's `1179 / 1278 ≈ 0.92`.

## Relevance to this renderer

This is the recipe for any gaze+dwell UI here (the song picker, later any in-scene reticle
menu): derive the ray from `camera.transform`, hit-test by angle with enter/leave hysteresis,
clock the dwell off `frame.timestamp`, draw the ring with the HUD geometry idiom + aspect
correction + lensShift, and let the clicker commit the hovered target as an accelerator. Targets
ride a latched yaw-only anchor so they're body-anchored (you can look away to aim elsewhere) yet
constant in world space.
</content>
</invoke>
