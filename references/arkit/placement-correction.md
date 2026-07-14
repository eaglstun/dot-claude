---
topic_id: "v2:LJKH"
topic_path: "metal-renderer"
semantic_id: "humpNHxTAzN7XRL99Qqu0W2XLjdnAAAC"
related_ids:
  - "JHgGF37YMwO43R-95YLLxWmXCqNGYAAC"
  - "FPSBtnRaRqOoORr8dYDeVP-LouJGIAAD"
---
# ARKit placement correction — drop-to-floor + wall-clip nudge (heuristic, no physics)

For a hand-rolled Metal AR app already running `ARWorldTrackingConfiguration` with
`.smoothedSceneDepth` + horizontal `ARPlaneAnchor` floor detection. Goal: occasional (not
per-frame) per-prop corrections — snap a prop's world Y to the real floor, and detect/nudge a
prop out of a real wall. No physics engine.

Sources (Apple JSON doc endpoints `developer.apple.com/tutorials/data/documentation/<path>.json`):

- ARPlaneAnchor <https://developer.apple.com/documentation/arkit/arplaneanchor>
  (`center`, `extent`, `planeExtent`, `geometry`, `alignment`, `classification`)
- ARPlaneGeometry <https://developer.apple.com/documentation/arkit/arplanegeometry>
  (`boundaryVertices`)
- ARPlaneExtent <https://developer.apple.com/documentation/arkit/arplaneextent>
- ARRaycastQuery <https://developer.apple.com/documentation/arkit/arraycastquery>
  (+ `Target`, `TargetAlignment`)
- ARSession.raycast(_:) <https://developer.apple.com/documentation/arkit/arsession/raycast(_:)>
  (+ `trackedRaycast(_:updateHandler:)`)
- ARFrame.raycastQuery(from:allowing:alignment:)
  <https://developer.apple.com/documentation/arkit/arframe/raycastquery(from:allowing:alignment:)>
- ARRaycastResult <https://developer.apple.com/documentation/arkit/arraycastresult>
- ARConfiguration.SceneReconstruction
  <https://developer.apple.com/documentation/arkit/arconfiguration/scenereconstruction>
- ARWorldTrackingConfiguration.sceneReconstruction / supportsSceneReconstruction(\_:)
- ARMeshAnchor / ARMeshGeometry / ARGeometrySource / ARMeshClassification

Fetched: 2026-06-29.

---

## Symbol reference (verified signatures + iOS availability)

### Plane anchors (already in this app)

```swift
class ARPlaneAnchor                                   // iOS 11.0+
  var center: simd_float3 { get }                     // iOS 11.0+  anchor-LOCAL XZ; y is always 0
  var extent: simd_float3 { get }                     // iOS 11.0+  x=width, z=length, y unused
                                                       //  DEPRECATED iOS 16 -> use planeExtent
  var planeExtent: ARPlaneExtent { get }              // iOS 16.0+
  var geometry: ARPlaneGeometry { get }               // iOS 11.3+
  var alignment: ARPlaneAnchor.Alignment { get }      // iOS 11.0+  .horizontal | .vertical
  var classification: ARPlaneAnchor.Classification { get }  // iOS 12.0+
  // transform: simd_float4x4 inherited from ARAnchor (anchor->world). iOS 11.0+
// The plane spans the anchor's local XZ plane; the anchor's local +Y axis IS the plane normal.

class ARPlaneExtent                                   // iOS 16.0+
  var width: Float { get }                            // along local X
  var height: Float { get }                           // along local Z (note: "height" = length)
  var rotationOnYAxis: Float { get }                  // radians; see iOS-16 rotation gotcha

class ARPlaneGeometry                                 // iOS 11.3+
  var boundaryVertices: [simd_float3] { get }         // iOS 11.3+  CONVEX boundary polygon,
                                                       //  in the anchor's transform (local) space;
                                                       //  local y ~ 0. Use for point-in-plane.
  var vertices: [simd_float3]; var triangleIndices; var triangleCount; var textureCoordinates
// "The shape of a plane geometry is always convex (minimal convex hull)."
```

### Raycast (the robust floor/wall probe)

```swift
class ARRaycastQuery                                  // iOS 13.0+
  init(origin: simd_float3, direction: simd_float3,
       allowing target: ARRaycastQuery.Target,
       alignment: ARRaycastQuery.TargetAlignment)     // iOS 13.0+  (arbitrary world-space ray)

  enum Target           { case existingPlaneGeometry   // iOS 13.0+  bounded to scanned shape
                          case existingPlaneInfinite    // iOS 13.0+  detected plane, extended infinitely
                          case estimatedPlane }         // iOS 13.0+  feature-points/depth, no anchor needed
  enum TargetAlignment  { case horizontal; case vertical; case any }   // iOS 13.0+

// ARFrame convenience builds SCREEN-point queries only:
func ARFrame.raycastQuery(from: CGPoint, allowing: Target, alignment: TargetAlignment)
     -> ARRaycastQuery                                 // iOS 13.0+
// For a prop world-space ray, construct ARRaycastQuery(origin:direction:...) directly.

func ARSession.raycast(_ query: ARRaycastQuery) -> [ARRaycastResult]   // iOS 13.0+
//   results sorted NEAREST -> furthest from the ray origin; empty on miss.
func ARSession.trackedRaycast(_:updateHandler:) -> ARTrackedRaycast?   // iOS 13.0+ (repeating)

class ARRaycastResult                                 // iOS 13.0+
  var worldTransform: simd_float4x4 { get }           // hit pose in WORLD space
  var anchor: ARAnchor? { get }                        // the plane anchor hit (nil for pure estimated)
  var target; var targetAlignment
```

### Scene reconstruction / mesh (NOT enabled today; smoothedSceneDepth only)

```swift
struct ARConfiguration.SceneReconstruction            // iOS 13.4+
  static var mesh; static var meshWithClassification
var ARWorldTrackingConfiguration.sceneReconstruction  // iOS 13.4+ (default empty)
class func supportsSceneReconstruction(_:) -> Bool    // iOS 13.4+  LiDAR-only (iPhone 17 Pro: yes)

class ARMeshAnchor                                    // iOS 13.4+  var geometry: ARMeshGeometry
class ARMeshGeometry                                  // iOS 13.4+
  var vertices: ARGeometrySource                       // ARGeometrySource wraps an MTLBuffer
  var normals: ARGeometrySource                        //  (componentsPerVector/format/offset/stride/count)
  var faces: ARGeometryElement                         //  triangle index buffer; indexCountPerPrimitive
  var classification: ARGeometrySource                 //  per-face ARMeshClassification (iOS 13.4+:
                                                        //  floor/wall/ceiling/table/seat/door/window/none)
// Vertices are anchor-local: world = anchor.transform * float4(v,1).
```

---

## NEED 1 — Drop-to-floor (world Y under an arbitrary XZ)

**Ranked**

1. **Downward `ARRaycastQuery` against `.existingPlaneGeometry`, alignment `.horizontal`**
   (iOS 13.0+) — most robust + cheap. Cast from well above the prop straight down; ARKit
   respects the plane's real convex footprint and returns results **sorted nearest-first** along
   the ray, so multiple stacked floors are handled for free. Take `worldTransform.columns.3.y`.

   ```swift
   func floorY(underX x: Float, z: Float, fromHeight y0: Float = 3) -> Float? {
     let origin = simd_float3(x, y0, z)
     let down   = simd_float3(0, -1, 0)
     for target in [.existingPlaneGeometry, .existingPlaneInfinite, .estimatedPlane]
                    as [ARRaycastQuery.Target] {
       let q = ARRaycastQuery(origin: origin, direction: down,
                              allowing: target, alignment: .horizontal)
       if let hit = session.raycast(q).first { return hit.worldTransform.columns.3.y }
     }
     return nil   // no floor seen under this XZ yet
   }
   ```

   Fallback chain widens tolerance: `.existingPlaneGeometry` (only within scanned shape) →
   `.existingPlaneInfinite` (prop is past the scanned edge but same floor) → `.estimatedPlane`
   (no detected plane; uses depth/feature points).

2. **Manual horizontal-plane + boundary test** — no-raycast fallback, or when you must bind to a
   specific _classified_ floor. Pick anchors with `alignment == .horizontal` (prefer
   `classification == .floor`). Transform the XZ into anchor-local space with `inverse(transform)`,
   run point-in-polygon against `geometry.boundaryVertices` (local XZ, convex). For a
   gravity-aligned horizontal plane the world floor Y at that XZ is just
   `anchor.transform.columns.3.y` (local y=0, rotation is yaw-only). Choose the candidate with the
   greatest Y still below the prop.

Use #1; keep #2 for floor-classification preference or when raycast returns empty.

---

## NEED 2 — Wall-clip detect + push-out direction

**Ranked for an occasional per-prop check**

1. **Vertical `ARPlaneAnchor`s (cheapest, world-space, already available).** World normal
   `n = normalize(transform.columns.1.xyz)` (the anchor's local +Y is the plane normal). World
   plane center `c = (transform * float4(center,1)).xyz`. Signed distance of prop point `p`:
   `d = dot(n, p - c)`. Clip if `|d| < propRadius` **and** `p` projects inside the plane (test
   against `boundaryVertices` polygon, or the `planeExtent` rectangle). Push along the plane
   normal: `p += n * (propRadius - d) * sign(d)`.
   Trade-off: only walls ARKit detected as planes; vertical detection is flakier than
   horizontal; bounded to the detected extent.

2. **Horizontal `ARRaycastQuery` probes (`alignment: .vertical`).** From the prop, cast a few
   rays outward (cardinal dirs and/or the candidate push dir) allowing `.existingPlaneInfinite`
   or `.existingPlaneGeometry`. Nearest hit within `propRadius` ⇒ wall; push back along `-dir`
   (or the hit anchor's normal). Trade-off: directional sampling — needs several rays; still
   limited to anchored planes.

3. **`ARMeshAnchor` / scene reconstruction (`.mesh`) — NOT enabled today.** True world-space
   surface model; catches non-planar / undetected / cluttered walls that plane detection misses.
   Best fidelity for clearance, but: requires `config.sceneReconstruction = .mesh` (LiDAR-only,
   `supportsSceneReconstruction(_:)`; iPhone 17 Pro qualifies), adds continuous CPU/GPU + memory
   cost, and the nearest-surface test means iterating `ARMeshGeometry.faces`, transforming
   vertices by `anchor.transform`, and computing point-to-triangle distance (bound it to nearby
   anchors / `classification == .wall` faces). **Verdict: enable only if plane-based walls prove
   insufficient.** Bonus: enabling plane detection alongside the mesh makes ARKit _smooth_ the
   mesh where it detects planes, so the two cooperate.

4. **Sample the existing `sceneDepth.depthMap` directly (free; already on).** Project the prop's
   world point into the current camera/depth image, compare stored depth (metres, optical-axis Z)
   against the prop's camera-space Z. `realDepth < propZ - margin` ⇒ prop is behind a real surface
   _from this view right now_. Cheap supplementary live check, but **view-dependent** (only what's
   in frame), camera- not gravity-aligned, and yields no stable world-space push direction. Use
   only as an instantaneous "is it poking into something" sanity check, never as the wall model.

**Use:** vertical planes (1) as the primary world-space test + horizontal raycast (2) to confirm
/ measure clearance; reach for scene reconstruction (3) only when non-planar walls matter and you
accept the cost; depth-sampling (4) as a free live supplement.

---

## Gotchas

- **`extent` vs infinite plane.** `extent`/`planeExtent`/`boundaryVertices`/`.existingPlaneGeometry`
  are bounded to the _scanned_ area; a prop just past the scanned edge misses. Use
  `.existingPlaneInfinite` (or pad the extent test) when you trust surface continuity.
- **iOS-16 plane rotation change.** With deployment target ≥ iOS 16 the anchor's `transform` is
  **no longer auto-rotated** to `planeExtent.rotationOnYAxis` — you must apply that yaw yourself if
  you test against the axis-aligned `width`×`height` rectangle. **`boundaryVertices` sidesteps this**
  (always in the anchor's `transform` space) — prefer the polygon test.
- **`center` is anchor-local XZ with y≡0;** world center = `transform * float4(center,1)`.
- **Plane normal = `transform.columns.1` (local +Y)** for both horizontal (points up) and vertical
  (points out of the wall) planes; for a wall the sign can face either way — derive push direction
  from `sign(d)`.
- **World alignment must be `.gravity`** (the world-tracking default) for "down = −Y" to hold;
  don't use `.camera` alignment.
- **Depth registration.** If you sample `depthMap`, its intrinsics belong to `imageResolution`
  (full-res, native-sensor/landscape) — scale K to depth res before projecting, and treat depth as
  optical-axis Z, not range. (See `scene-depth.md`.)
- **`sceneReconstruction` availability:** iOS 13.4+, LiDAR-only; enabling adds `ARMeshAnchor`s to
  the delegate stream and an ongoing meshing cost — it's an opt-in, not free.
- **Raycast results are sorted nearest→furthest from the ray origin**; for a downward floor cast,
  element `[0]` is the topmost surface under the start point — start the ray clearly above the prop.

## Project tie-in

Native Metal/ARKit only — none of this reaches the WebGL/WebView track. It belongs to the
`ios/KaraokeVR` renderer (`StereoARRenderer`), which already holds the `ARSession`/`ARFrame` and
floor `ARPlaneAnchor`s. The web experiments still get head pose from `deviceorientation`.
