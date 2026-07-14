---
topic_id: "v2:LHGC"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "z_cmaC6RULdRHuwjVZ2aIRR4G0DrcAAG"
related_ids:
  - "x_M0SG8UQreJxDok6QwK95WYS4xEcAAD"
  - "xfMyKG4UYqd1lnJjWlk5ZuGwIr6IcAAC"
---
# Distant backdrop occlusion + follow-me anchoring (mesa)

Learned 2026-06-28 making the always-on mesa backdrop actually render. Sources:

- In-repo: `StereoARRenderer.swift` (`drawMesaBackdrop`, `mesaModel`, `updateFloorY`, `resolvedFloorY`,
  `updateQuad` affine), `Passthrough.metal` (`mesaVertex`/`mesaFragment`), `Models/Mesa.swift`.
- `occludePropsWithRealDepth` prepass: `reprojectVertex` in `Passthrough.metal` (the `raw<=0 ? 8.0` sink).

## The depth-PREPASS caps the z-buffer at ~8 m → distant props are ALWAYS hidden

When `occludePropsWithRealDepth = true`, a full-screen LiDAR depth prepass (`depthPrepassPipeline` via
`reprojectVertex`) stamps real depth before the props — and it **sinks no-data / out-of-range texels to
8 m**. So the z-buffer is ≤8 m across the _entire_ screen, including open sky. Any prop farther than
that (a 30 m horizon mesa) is occluded everywhere with standard `sceneDepth`, even through open sky.
Symptom: the backdrop never appears in any frame/mode, indoors or out.

**Fix for a far backdrop:** don't use the z-buffer at all. Draw it with `backgroundDepth` (no z-test)
and do **per-pixel occlusion against the LiDAR depth TEXTURE** in its own fragment: discard where the
real reading is VALID (`d > 0`) and clearly in front (`d < dist − bias`); show it where depth is no-data
(sky/beyond range). That is genuinely depth-correct (near real walls/trees hide it; open sightlines show
it) without the 8 m cap. Draw it FIRST so nearer props (painter's order) cover it.

### Sampling real depth at a 3D fragment's screen point

The depth map is registered to the camera image, sampled by the passthrough quad's display-transformed
UV. To sample it for an arbitrary 3D fragment: pass the quad's **NDC→UV affine** (2 columns + offset,
reconstructed from the quad's 4 corners in `updateQuad`) as a uniform; in the fragment compute
`ndc = clipPos.xy/clipPos.w`, **back out the lensShift** (`ndc − offset`, since the quad's UV is keyed
to the un-shifted corner), then `uv = A·ndc' + b`. The quad UV already bakes the `1/worldZoom` de-zoom,
so it stays registered. Compare against `clipPos.w` (= optical-axis distance for the ARKit projection;
`worldZoom` scales x/y, not w) which matches LiDAR metres.

## Follow-me anchoring (camera-relative, grounded, upright)

`sceneAnchor` is latched at launch → world-pinned props fall behind a roaming user (they vanished from a
97 s ride). For props that must always be visible (dancer "buddy", mesa "horizon"), build a **per-frame
yaw-only frame at the CURRENT camera** (`yawAnchor(from: camera.transform)`) and place them a fixed
distance down its −Z. Yaw-only keeps them world-upright under head pitch/roll; the per-frame position
keeps them a fixed distance ahead (you can't scooter past). Grounding uses the _current_ camera Y:
`groundLift = (floorWorldY − camY) − modelFeetY·scale + nudge`.

## Floor-latch robustness (don't let a bad plane bury everything)

Grounding to ARKit horizontal planes outdoors can latch a spurious LOW plane → huge negative groundLift →
props sink underground (another way they "disappear"). Filter: only accept planes between ~0.4 m and
~3 m below the **current** camera; take the running min among those; and clamp the resolved floor to that
band, degrading to an assumed camera-height fallback. Never trust an unbounded running-min.
