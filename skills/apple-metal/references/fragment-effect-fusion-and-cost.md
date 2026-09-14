---
topic_id: "v2:LHJK"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "3bc0CV4uOCSJbFnw9hsg98FcVOoocAAK"
related_ids:
  - "y_ckZw6mcieLdTtXZj5R9MhIE-mqoAAL"
  - "znmiBn-4GmUp3TuYdxgSddlYU6Mc8AAJ"
---
# Fragment-effect fusion safety + cost budget (stereo renderers)

Sources:

- Metal Shading Language Specification (Apple), "Fragment Functions — derivatives"
  (`dfdx`/`dfdy`/`fwidth`) and `[[point_size]]` / `point_coord` for point primitives.
- `apple-arkit/references/scene-depth.md` — LiDAR depth is r32Float, METRES, optical-axis Z,
  ~256x192, registered to `capturedImage`; no-data texels read 0.

**Provenance:** the cost anchors below were measured on a phone-class GPU (A17-generation)
running a per-eye stereo passthrough pass — a fullscreen quad rebuilt once per frame, drawn twice,
with a 17-tap disc blur as the "this holds framerate" reference point. Treat the tap counts as
calibrated for that class of device and re-measure on anything else.

Fetched/derived: 2026-06-28

## The fusion fact that governs every new fragment effect

**Flat passthrough is MONOSCOPIC.** `updateQuad` builds one quad (one set of texCoords) per
frame, and both eyes draw it with only a clip-space x nudge (`clipOffset = shift * eyeSign`,
the lensShift). So in modes 0-3 **both eyes sample the same camera pixels** — there is no real
binocular disparity in the camera image. The ONLY real-parallax camera path is mode 4
(`reprojectVertex` unprojects depth per eye).

Consequence for new effects:

- A **per-eye in-pass fragment effect** (fragment math on each eye's own viewport quad —
  fog, contours, scanner, posterize, duotone, portal) is **automatically fusion-safe**: each
  eye is computed identically from the same camera+depth, so it inherits passthrough's existing
  (already-comfortable) fusion. You do NOT need to do anything special per eye. This is the
  cheap, safe lane — prefer it.
- A **screen-space UV warp** (ripple/displacement) applied identically to both eyes does NOT
  break fusion here, because there's no stereo in the source to break — it only risks
  readability/vection/nausea, not retinal rivalry. (It WOULD be dangerous on a truly stereo
  source like mode 4.)
- **Full-drawable feedback** (motion blur, full-screen bloom, afterimage) still smears across
  the eye split — avoid, same as the web side. The existing trail (mode 4) stays safe only
  because it is accumulated **per eye** into split halves of the trail texture and composited
  back per eye (`runTrailPass` sets each eye's viewport; `trailCompositeFragment` picks the
  eye's half via `uvScaleBias`). Any new temporal effect must copy that per-eye-half discipline.

## Cost budget anchor (phone GPU, drawing twice)

Everything runs **twice** (two eye viewports on one drawable). Empirical ceiling already in
the codebase: **mode 2 (`passthroughBlurFragment`) does ~17 camera taps + 5 depth taps per
pixel, per eye, and ships.** That is the working budget anchor on the target device
(iPhone 17 Pro). So:

- A 1-5 tap depth fragment effect (fog, scanner, contour, posterize, duotone, spotlight,
  portal) is **far under budget** — these are effectively free relative to mode 2.
- A new full-disc blur/bloom-style fragment is at the mode-2 ceiling — fine alone, watch it if
  stacked.
- A depth-grid **point cloud** reuses the mode-4 grid (192x144 = 27,648 verts x2 eyes); it's
  vertex/raster-bound, not tap-bound — cheap fragment, watch point overdraw if point_size large.

## Idioms a new mode plugs into (no architecture change needed)

- **New mode = new fragment function + a new pipeline state**
  (clone `blurPassthroughPipeline` for an opaque background-replacing effect, or the
  `depthOverlayPipeline` premultiplied-alpha block for a translucent tint), + a `case` in
  `drawBackground` OR a `drawX()` overlay call in the per-eye loop (mirror `drawDepthOverlay`).
- Bump `modeCount`, append to `modeNames`, add the `ModeLabel` chip; HUD pips auto-size from
  `modeCount`. The `effectiveMode` guard (L542) already falls ANY `mode != 0` back to
  passthrough until depth is flowing — new depth modes inherit that for free.
- New tuning constants go as named `private let` constants on the renderer, with a units+range doc comment
  (house style: see `maxBlurRadius`, `edgeThreshold`, `trailDecay`).
- **Uniform struct layout must match Swift<->MSL.** Keep them scalar `Float`/`float4` like the
  existing `BlurUniforms`/`EdgeUniforms`; avoid `float3` members (pads to 16 B and desyncs).
- Depth: always route no-data through the `depthOrFar` convention (0 -> far), and remember
  depth is **optical-axis Z in metres** — band/contour/scanner thresholds are real metres.

## Relevance to this renderer

This is the checklist for adding any depth-driven effect: stay in the per-eye in-pass
fragment lane (free fusion), keep taps well under the mode-2 anchor, reuse the depthOrFar /
cosine-palette helpers and the overlay-pipeline idiom, and only reach for the per-eye-split
trail buffer if the effect must persist across frames.
