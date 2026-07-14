---
topic_id: "v2:LPOM"
topic_path: "metal-renderer/passthrough-rendering"
semantic_id: "3vc2au8qe7-q5zKtwpVQttjKAQGKMAAP"
related_ids:
  - "2tX8QsIoeZ7GIjF4y5eQlhLkUgGtsAAD"
  - "y_ckZw6mcieLdTtXZj5R9MhIE-mqoAAL"
---
# Per-eye temporal accumulation (trails / persistence) without breaking stereo fusion

Sources (verified in-repo + Apple docs):

- `ios/KaraokeVR/StereoARRenderer.swift:149-153` (trail texture decl), `:546-565` (per-eye
  array + pre-pass trigger), `:694-770` (`ensureTrailTexture` / `runTrailPass` /
  `drawTrailComposite`) — the working mode-4 trail this note generalises.
- `ios/KaraokeVR/Passthrough.metal:255-272` (`fadeFragment`, `trailCompositeFragment`) and
  `:224-253` (`outlineOnlyFragment`, the per-frame contribution).
- Blend-pipeline descriptors: `StereoARRenderer.swift:248-307` (fade = `.blendColor`
  destination multiply; outline = `.max`; composite = additive `.one/.one`).
- Apple: MTLBlendOperation (min/max ignore source/destination blend factors) —
  <https://developer.apple.com/documentation/metal/mtlblendoperation>
- Depth facts this builds on: `.claude/references/arkit/scene-depth.md` (r32Float, metres,
  ~256x192, registered, optical-axis Z, 60 Hz).

## The fusion problem, stated

Temporal effects need frame history. A naive full-drawable feedback buffer blended back over
both eyes smears content across the left/right split and **destroys stereo fusion** — the same
reason the web path avoids framebuffer feedback. The rule for this renderer: **history must be
accumulated per eye, and no fragment may sample across the eye seam (x = 0.5 of the drawable).**

## Three plumbing schemes (pick by what the update reads)

1. **Single shared drawable-sized buffer, isolated by viewport (mode-4's scheme).** One
   `rgba16Float` private texture the size of the whole drawable (both eyes side by side). The
   contribution pass calls `enc.setViewport(eye.viewport)` for the left/right half and draws
   only inside it; the composite samples each eye's own half via `uvScaleBias = (0.5, eye*0.5)`
   (`Passthrough.metal:266-272`). Eyes stay independent **iff every fragment reads only its own
   texel or texels on its own side of the seam.** A point-wise fade (`fadeFragment` returns a
   constant, decay carried entirely by the blend) is seam-safe; a neighbour-tap blur in the
   accumulation/composite is NOT unless u is clamped to the eye half. Memory: W*H*8 bytes
   (~25 MB at a ~2600x1200 drawable).
2. **Two per-eye textures (`...L`, `...R`), each eye-viewport-sized.** Physical isolation: a
   neighbour-tap blur/bloom can't cross eyes because the texture ends at the boundary
   (clamp-to-edge sampler). **Same total memory** as scheme 1 (2 x (W/2 x H)), just two
   allocations and two render-pass setups. Use whenever the effect spatially filters.
3. **Ping-pong pair (read A, write B, swap).** Needed ONLY when the update reads a _displaced_
   texel — advection, slit-scan, optical-flow warp, or reprojecting the history buffer by the
   camera's inter-frame delta. Doubles memory and adds a resample pass. NOT needed for
   decay+accumulate (scheme 1 proves in-place load+blend is enough).

## The decay-without-ping-pong trick (why mode 4 needs no second buffer)

`.max` and `.add` are order-independent and a scalar fade is a per-texel multiply, so the buffer
can be updated in place: load it, fade it, blend the fresh frame in. The fade can't ride on a
`.max` blend because **Metal ignores blend factors for min/max ops**
(`StereoARRenderer.swift:249-251`). So the decay is a separate fullscreen pass:
`fadeFragment` returns 0 and the pipeline uses `sourceFactor = .zero`,
`destinationRGBBlendFactor = .blendColor` with `setBlendColor(decay,decay,decay,decay)` →
`texel = texel * decay` (`:259-266`, `:721-722`). Then the contribution pass `.max`-blends (or
switch to `.add` for additive light-painting). One buffer, two small passes, per eye.

Tuning lives as named constants in house style (`StereoARRenderer.swift:84-87`): e.g.
`trailDecay: Double = 0.86` ≈ a ~0.3 s tail at 60 fps. Clear-on-(re)entry is handled by a
`trailCleared` flag flipping `loadAction` between `.clear` and `.load` (`:715`, `:559`).

## Head-motion smear (the world-lock gotcha)

The accumulation buffer is **screen/drawable space, not world-locked.** A static world point
projects to a different pixel each frame as the head turns, so its faded history is left at
stale pixels → a full-frame smear on every head turn, which is nauseating in a headset.
Mitigations, cheapest first:

- **Short decay** (≤0.3 s) keeps the smear subtle — mode 4's choice, and why it ships.
- **Gate accumulation to scene motion** (prev-frame diff or depth-velocity) AND suppress it when
  head angular velocity is high (frame-to-frame `ARCamera.transform` rotation delta, or
  CoreMotion): when the head is turning fast, freeze or fast-fade instead of accumulating.
- **Reproject the history buffer** by the inter-frame camera rotation before compositing (a 2D
  homography resample of the buffer ≈ pure-rotation reprojection for distant content). This is
  the real world-lock fix but needs scheme 3 (ping-pong) + one warp pass.
- **Confine the trail to in-scene geometry** (per-vertex world-space accumulation on the
  reprojected depth mesh) so head motion is handled by the existing per-eye mesh reprojection
  rather than a screen-space buffer.

## Relevance to this renderer

This is the reusable backbone for any new motion-trail / persistence mode (light-painting,
beat-synced echo, depth-banded comet trails, moving-region ghosting). Reach for scheme 1 +
the decay trick first (mode 4 already proves it at 60 fps); upgrade to scheme 2 only when the
effect filters spatially, and to scheme 3 only when it warps/advects. Always state how the two
eyes stay isolated and how head-turn smear is bounded.
