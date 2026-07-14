---
topic_id: "v2:LHOH"
topic_path: "metal-renderer/stereo-effects"
semantic_id: "nvOnDK5IQrfJlB40VHmytfiIEotAsAAF"
related_ids:
  - "v_-mL386UidNhTNMcngz7JppGoKEsAAB"
  - "5vWmDHeIAvVVgD3FZPhzrTsgE4gIIAAH"
---
# Aligning a 2D overlay (Vision points) to the hand-rolled passthrough quad

Sources:

- `ios/KaraokeVR/StereoARRenderer.swift` `updateQuad(...)` (the quad's image→screen mapping) and
  `posePointToNDC(...)` (the inverse used by the pose overlay).
- Apple: `ARFrame.displayTransform(for:viewportSize:)` maps **normalized image coords (origin
  TOP-LEFT, y-down, 0…1) → normalized view coords (top-left, y-down, 0…1)** for an interface
  orientation + viewport. (developer.apple.com/documentation/arkit/arframe/2923543-displaytransform)
- Apple Vision: `VNRecognizedPoint.location` is normalized **origin BOTTOM-LEFT, y-UP**, in the
  space of the image AS ORIENTED by the `CGImagePropertyOrientation` passed to the request handler.

## How the passthrough quad samples the camera image

`updateQuad` pairs each NDC corner with a **view coord** (UIKit, top-left y-down), runs it through
`viewToImage = displayTransform.inverted()` to get an image UV, then **expands about centre by
1/worldZoom** to de-zoom:

```
sampledUV = 0.5 + (viewToImage(viewCoord) - 0.5) / worldZoom      // worldZoom 0.7 ⇒ ×1.43 (wider FOV)
```

So a fixed _screen_ pixel samples a _more spread_ image coord. `worldZoom < 1` reveals more FOV and
the world looks smaller; it is applied to BOTH the flat passthrough sampling and the 3D projection
(`proj.columns *= worldZoom`).

## The inverse: where does an image feature land on screen?

To draw a dot ON a real feature, invert the above (`posePointToNDC`):

```
iuv  = (vx, 1 - vy)                       // Vision y-UP → image top-left y-down
iuv  = 0.5 + (iuv - 0.5) * worldZoom      // CONTRACT about centre (inverse of the quad's /worldZoom)
view = displayTransform(iuv)              // image→view  (forward transform, NOT inverted)
ndc  = (view.x*2 - 1, 1 - view.y*2)       // view top-left → NDC centre/y-up
```

Two traps that silently offset/rotate the overlay:

1. **worldZoom direction.** The overlay multiplies `(iuv-0.5)` by `worldZoom`; the quad divides. Get
   this backwards and the dots drift outward from centre as the scene de-zooms.
2. **Transform direction.** The quad uses `displayTransform.inverted()` (view→image); the overlay
   uses the **forward** `displayTransform` (image→view). Don't reuse the inverted one.

## Orientation / Vision coordinate space

Pass Vision a `CGImagePropertyOrientation` matching the interface orientation so it detects an
upright subject. The mapping above assumes the **landscapeRight ⇒ `.up`** rear-camera case, where the
oriented image == the native `capturedImage` buffer, so Vision's normalized space lines up with the
space `displayTransform` works in (after the y-flip). For landscapeLeft (`.down`, a 180° reorient)
you most likely need to flip BOTH final x and y — exposed as `poseFlipX/poseFlipY` constants for an
on-device nudge. Rear-camera convention used: portrait `.right`, portraitUpsideDown `.left`,
landscapeLeft `.down`, landscapeRight `.up`.

## Drawing it fusion-safe per eye

Build the overlay as CubeVertex `[x,y,z,1,r,g,b,a]` clip-space geometry (dots = small quads, bones =
thin quads), draw through `cubePipeline` with **identity MVP + the eye's `clipOffset` (lensShift) +
`backgroundDepth` (compare-always)** — identical to the HUD pips / reticle. Geometry is
eye-independent (lensShift is the only per-eye difference, applied as the uniform `offset`), so build
once per frame and draw twice. `displayTransform` uses `viewportSize = eyeSize` (half-width), so the
produced NDC is already per-eye-viewport NDC.
