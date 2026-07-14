---
topic_id: "v2:LPOA"
topic_path: "metal-renderer/passthrough-rendering"
semantic_id: "DvAqXixhozcdPHHsXrw4cdKEM9JecAAC"
related_ids:
  - "TvGynH8Kgie79TascJKIwWlIC6POYAAA"
  - "nvOnDK5IQrfJlB40VHmytfiIEotAsAAF"
---
# Real-world depth prepass occludes virtual content — now ON and consistent across all modes

Source (the bug this generalises, and its current resolution):

- `ios/KaraokeVR/StereoARRenderer.swift` — the occlusion prepass (`stampRealDepth(...)`) draws the
  reprojection grid through `depthPrepassPipeline` with `sceneDepth` (`lessEqual` + **write**),
  stamping real-world LiDAR depth into the z-buffer; the served props / roaming spots / mannequin
  then draw with that same `sceneDepth` state and fail the depth test wherever a real surface is
  nearer. Gated behind `occludePropsWithRealDepth` (now **true**) on branch `main`, 2026-06-28.
- Depth buffer clears to far (1.0) each frame: MTKView `depthStencilPixelFormat = .depth32Float`
  (`ios/KaraokeVR/ARLiveView.swift`), default `clearDepth`.
- Apple: a depth prepass writes occluding depth so later draws are clipped by it — that's its whole
  purpose. <https://developer.apple.com/documentation/metal/mtldepthstencilstate>

## Current behaviour (2026-06-28): occlusion ON, uniform across all 10 modes

The user WANTS the AR props to hide behind real-world geometry (walls/furniture/people) consistently
in EVERY render mode. So real-world occlusion is now ON everywhere, with no per-mode difference:

- **Flat modes (0/1/2/5/6/7/8)** — `drawBackground`'s default branch calls `stampRealDepth(...)` when
  `occludePropsWithRealDepth` is true (it is), stamping real depth before the props draw.
- **Mode 3 (DEPTH viz)** — its case also calls `stampRealDepth(...)` first; the viz quad below uses
  `backgroundDepth` (compare-always, **no write**), so the stamped real depth survives for the props.
- **Modes 4 (reproject mesh) / 9 (point cloud)** — already write their own real-surface depth in
  their `drawBackground` branch (`reprojectPipeline` / `pointCloudPipeline`, both `sceneDepth` =
  lessEqual+write), so the props occlude against the mesh/cloud there with no extra work.

Result: in all 10 modes the props are clipped by nearer real geometry, and still depth-sort among
themselves (their own `lessEqual`+write in drawMesh / drawMannequin; the buffer clears to far each
frame). No front/back popping as auto-cycle switches modes.

`stampRealDepth(encoder:proj:eyeView:camTransform:k:depthTex:clipOffset:)` is the single shared
prepass helper — the flat default branch and mode 3 both call it, so the prepass block isn't
duplicated. `clipOffset` (lensShift) must match the props' so the stamped depth registers with them.

`occludePropsWithRealDepth` is kept as the single switch (the user has gone back and forth): flip it
false to put props on top in the flat modes + mode 3. Note that flipping it false reintroduces the
asymmetry below (4/9 still occlude, the flat modes + mode 3 don't) — that's the documented trade-off
of the simple-flag approach, accepted because occlusion is wanted ON for now.

## The shape of the original bug (kept for the next time it regresses)

"My virtual props appear in some render modes but vanish in others." The tell is that the modes where
they vanish are exactly the ones that run a **real-world depth prepass** (or otherwise write real
geometry depth — e.g. mode 4's reproject mesh), and the modes where they show are the ones that DON'T.

It looks mode-specific but isn't: every prepass mode behaves identically. The user just notices it in
whichever mode makes the occluding surface obvious. Two structurally identical modes (mode 0 LIVE and
mode 1 HEAT share the exact prepass + prop path) hide the props the same way — so if one hides them,
suspect a cause UPSTREAM of the per-mode fragment, in the shared prepass/depth state, not the shader.

Why it reads as "missing" rather than "occluded": stage props sit ~2.2–2.5 m ahead of the anchor
(`showcaseDistance`, `mannequinZ`). In any normal room a wall/floor/furniture is nearer than that, so
the prepass stamps a closer depth across the whole prop footprint and the `lessEqual` test discards
every prop fragment. Total disappearance, not a clipped edge. A small room will hide props beyond its
walls — that's the intended behaviour (the user roams larger/outdoor spaces); no clamps are applied.

## Confirming it cheaply

- Check the depth state the props bind (`sceneDepth` = `lessEqual` + write) and what wrote depth
  before them. If a full-frame prepass wrote real-world depth with the same/closer compare, the props
  are being occluded, not failing to draw.
- Temporary proof: flip `occludePropsWithRealDepth = false` (or draw props with a compare-always depth
  state) for one build — props snap to always-on-top → confirmed occlusion, not a missing buffer /
  bad matrix / culled geometry.

## History: the per-mode-reset detour (removed 2026-06-28)

An earlier iteration had `occludePropsWithRealDepth = false` (props always on top in the flat modes)
plus a `resetDepthToFar(...)` far-plane wipe gated to modes 4/9 so they matched — props on top
everywhere. That whole approach (`depthResetPipeline`, `depthResetState`, `resetDepthToFar`, and the
`depthResetVertex` shader) was **deleted** when the user reversed the decision to want occlusion ON.
If you ever want props-on-top-everywhere again, the cleaner route is the flag plus a 4/9 depth reset —
recoverable from git history around this commit — not re-deriving it from scratch.

Source: `StereoARRenderer.swift` — `stampRealDepth(_:)`, `depthPrepassPipeline` (buildPipelines),
`sceneDepth` (buildDepthStates), call sites in `drawBackground` (default branch + case 3);
`Passthrough.metal` — `depthOnlyFragment` paired with `reprojectVertex`. Branch `main`, 2026-06-28.
