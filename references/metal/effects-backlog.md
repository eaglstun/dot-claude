---
topic_id: "v2:LHFL"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "y_ckZw6mcieLdTtXZj5R9MhIE-mqoAAL"
related_ids:
  - "3vc2au8qe7-q5zKtwpVQttjKAQGKMAAP"
  - "3bc0CV4uOCSJbFnw9hsg98FcVOoocAAK"
---
# Renderer effects backlog — depth / outline / trails

Synthesized 2026-06-28 from three `metal-fx-researcher` plans (depth-map, outline, motion-trail
lanes). All effects stay in the **fusion-safe lane** (per-eye, in-pass; passthrough is monoscopic
so per-eye fragment math can't break fusion) and are costed against the shipping mode-2 blur
(~17 taps/eye ×2 = the "this holds framerate" anchor). Detailed technique + sources live in the
sibling notes: `fragment-effect-fusion-and-cost.md`, `depth-stylization.md`,
`per-eye-temporal-accumulation.md`. Existing modes: 0 passthrough · 1 heatmap tint · 2 blur+edge ·
3 raw depth · 4 reprojected stereo + depth-coloured trail · **5 topographic contours (SHIPPED)** ·
**6 scanner sweep (SHIPPED)** · **7 cel/toon + depth ink (SHIPPED)** · **8 volumetric fog +
spotlight (SHIPPED)** · **9 holographic point-cloud (SHIPPED)**. The render mode now also
auto-cycles on a ~12 s timer while a song plays (`autoCycleModes`); the clicker still cycles
manually. Hand a chosen effect to `metal-renderer`.

## Recommended build order (cheap → wow, each tees up the next)

1. ~~**Depth Scanner Sweep**~~ ✅ **SHIPPED (mode 6).** Neon plane glides near→far lighting real
   surfaces as it passes. Sawtooth loop off the frame clock today; beat-sync still TODO (see below).
2. ~~**Cel/toon + depth ink**~~ ✅ **SHIPPED (mode 7).** Live world flattened to cartoon luminance
   bands + a luma-Sobel interior ink + a bold depth-silhouette outline. Validated the **luma-Sobel
   block** that comic/blueprint/hologram reuse. ~1 colour fetch + 8 luma + 5 depth taps/px/eye.
3. ~~**Topographic depth contours**~~ ✅ **SHIPPED (mode 5).** Glowing iso-distance rings every N cm,
   `fwidth`-AA'd, depth-coloured, with an additive glow halo + a distance-scaled between-ring tint.
4. **Beat/line-synced silhouette echo** _(S, high)_ — mode-4 outline pulses + throws a decaying
   echo on the downbeat. **Zero new render targets** (reuses mode-4's per-eye trail buffer); can't
   break fusion. _Needs a timing source_ — see below.

Then the M-tier "wow" tier:

- **Comic-book ink + halftone** _(M, very high)_ — ink lines + CMYK dot-screen fill; the
  "pop-art karaoke" mode. Outline lane's favorite; #2 is its stepping-stone.
- **Depth Portal / Stage backdrop** _(M→L, very high)_ — keep the singer (near), replace the far
  room with a synthwave stage. The karaoke wow. Ship screen-locked, then world-lock via per-pixel
  view ray to kill vection.
- ~~**Holographic point-cloud**~~ ✅ **SHIPPED (mode 9).** Room as glowing depth-coloured dots in
  true 3D on black; reuses mode-4's unprojection grid drawn as `.point` primitives (perspective dot
  size, no-data clip-culled). Vertex/raster-bound (192×144 points ×2 eyes), cheap fragment.
- **Light-painting persistence** _(M, high)_ — bright/neon pixels smear into comet streaks; gate
  with depth-band + head-velocity to control smear.

## Full slate (per lane)

**Depth:** ~~Scanner Sweep~~ ✅ · ~~Topographic Contours~~ ✅ · ~~Volumetric Fog + Spotlight~~ ✅
**(mode 8)** · Depth Portal/Stage · ~~Holographic Point-Cloud~~ ✅ **(mode 9)** · Depth
Posterize/Duotone · (micro: x-ray near-highlight, depth ripple).

**Outline:** Comic-book ink+halftone ⭐ · ~~Cel/toon + depth ink~~ ✅ **(mode 7)** ·
Normals-from-depth rim light · ~~Topographic Contours~~ ✅ · Hologram scanline · Blueprint/wireframe ·
Animated marching outline · (micro: chromatic-aberration edges, orientation-coloured ink).

**Trails:** Beat/line-synced silhouette echo ⭐ · Depth-banded comet trails (also the head-motion
safety valve for the others) · Light-painting persistence · Hue-cycling · Moving-region echo ·
Full-RGB echo _(nausea-flagged)_ · Slit-scan _(ambitious, memory-flagged)_.

## Cross-cutting constraints (from the notes)

- **Fusion:** never blend across the eye seam (drawable x=0.5). Point-wise fades on the shared
  mode-4 buffer are safe; spatial filters need per-eye textures; advection needs ping-pong. See
  `per-eye-temporal-accumulation.md`.
- **Head-motion smear:** any screen-space history buffer smears on head-turn (nauseating). Bound
  with short decay, depth-band gating, head-angular-velocity gating, or world-locked reprojection.
- **Sobel/normals shimmer** on low-res noisy LiDAR depth at distance → prefer `smoothedSceneDepth`,
  `fwidth`-based AA, fade out past ~3–4 m. Guard fast-math `normalize(0)` (NaN sparkle).

## Timing source for beat-reactive effects

The song API now carries **`bpm` + `meter`** (per song, partially populated) plus per-line lyric
cues (`lines[].t`). Plan: a small clock that uses `bpm` when present (`beatPeriod=60/bpm`,
downbeat every `meter`-numerator beats, anchored to song start / a lyric cue), and falls back to
**line-sync** off `lines[].t` when `bpm` is null. Don't derive BPM from cue spacing. A true
onset/beat track would need an API schema add or offline precompute. See
`../karaoke-api/contract.md`.
