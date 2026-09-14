---
topic_id: "v2:LIKI"
topic_path: "metal-renderer"
semantic_id: "JHgGF37YMwO43R-95YLLxWmXCqNGYAAC"
related_ids:
  - "humpNHxTAzN7XRL99Qqu0W2XLjdnAAAC"
  - "FPSBtnRaRqOoORr8dYDeVP-LouJGIAAD"
---
# ARKit LiDAR scene depth (for depth-reprojected stereo passthrough)

Source (API reference, fetched via Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/arkit/ardepthdata>
- <https://developer.apple.com/documentation/arkit/ardepthdata/depthmap>
- <https://developer.apple.com/documentation/arkit/ardepthdata/confidencemap>
- <https://developer.apple.com/documentation/arkit/arconfidencelevel>
- <https://developer.apple.com/documentation/arkit/arframe/scenedepth>
- <https://developer.apple.com/documentation/arkit/arframe/smoothedscenedepth>
- <https://developer.apple.com/documentation/arkit/arframe/capturedimage>
- <https://developer.apple.com/documentation/arkit/arconfiguration/framesemantics-swift.property>
- <https://developer.apple.com/documentation/arkit/arconfiguration/framesemantics>
- <https://developer.apple.com/documentation/arkit/arconfiguration/supportsframesemantics(_:)>
- <https://developer.apple.com/documentation/arkit/arcamera/intrinsics>
- <https://developer.apple.com/documentation/arkit/arcamera/imageresolution>
- <https://developer.apple.com/documentation/arkit/arcamera/projectionmatrix(for:viewportsize:znear:zfar:)>
- <https://developer.apple.com/documentation/arkit/arcamera/viewmatrix(for:)>
- <https://developer.apple.com/documentation/arkit/arframe/displaytransform(for:viewportsize:)>

Empirical specifics (resolution, intrinsics scaling) confirmed against:

- Apple sample "Displaying a point cloud using scene depth"
  <https://developer.apple.com/documentation/ARKit/displaying-a-point-cloud-using-scene-depth>
- WWDC20 "Explore ARKit 4" <https://developer.apple.com/videos/play/wwdc2020/10611/>
- Apple Developer Forums thread 663995 (LiDAR intrinsics/extrinsics)
  <https://developer.apple.com/forums/thread/663995>

Fetched: 2026-06-27

## What this is for

Build a depth-grid mesh that unprojects each LiDAR depth texel to a 3D camera-space point and
reprojects it per eye (±IPD/2) for stereo passthrough. The three things that must be exactly
right — depth **units/axis**, intrinsics **resolution mapping**, and depthMap-vs-capturedImage
**orientation** — are nailed down below.

> Project caveat (same wall as `camera-live-view.md`): all of this is **native ARKit**, not web.
> ARKit has no JS API; `ARDepthData.depthMap`/`capturedImage` are native `CVPixelBuffer`s with
> no supported per-frame path into the WebView's WebGL context. A depth-reprojected passthrough
> therefore implies a **native Metal renderer** (ARKit + Metal/RealityKit), not our hand-rolled
> WebGL stereo. Treat this digest as the facts for a native render layer; it does **not** drop
> into the `main.js` WebGL pipeline. Bridging only a low-rate signal (e.g. a downsampled depth
> frame) over `evaluateJavaScript` is not viable at passthrough frame rates.

---

## 1. Enabling depth

Depth is a per-frame **frame semantic** on a world-tracking configuration. LiDAR required.

```swift
struct ARConfiguration.FrameSemantics          // iOS 13.0+ (OptionSet-style)
  static var sceneDepth: ARConfiguration.FrameSemantics          // distance device→objects (per frame)
  static var smoothedSceneDepth: ARConfiguration.FrameSemantics  // same, temporally averaged

var frameSemantics: ARConfiguration.FrameSemantics { get set }   // iOS 13.0+  (on ARConfiguration)
class func supportsFrameSemantics(_ frameSemantics: ARConfiguration.FrameSemantics) -> Bool  // iOS 13.0+
```

Enable both at once for a custom renderer that wants raw + smoothed:

```swift
let config = ARWorldTrackingConfiguration()
if ARWorldTrackingConfiguration.supportsFrameSemantics([.sceneDepth, .smoothedSceneDepth]) {
    config.frameSemantics = [.sceneDepth, .smoothedSceneDepth]
}
session.run(config)
```

- `frameSemantics` defaults to empty; `sceneDepth`/`smoothedSceneDepth` are **nil unless added**.
- `supportsFrameSemantics(.sceneDepth)` returns `true` only on **LiDAR** devices (Pro iPhones
  since iPhone 12 Pro, iPad Pro 2020+). iPhone 17 Pro has LiDAR — supported.
- Depth is vended at **60 Hz** on each `ARFrame` (WWDC20 / sample).
- `sceneDepth` vs `smoothedSceneDepth`: identical content, but the framework **temporally
  smooths** the smoothed variant to reduce frame-to-frame flicker ("lessen its frame-to-frame
  delta"). Smoothed = steadier visuals (good for passthrough); raw = lowest latency / most
  responsive to motion. Both come from the LiDAR scanner.

## 2. Reading depth — ARDepthData

```swift
class ARDepthData                                   // iOS 14.0+
  unowned(unsafe) var depthMap: CVPixelBuffer       // iOS 14.0+  (REQUIRED, non-optional)
  unowned(unsafe) var confidenceMap: CVPixelBuffer? // iOS 14.0+  (optional)

var ARFrame.sceneDepth: ARDepthData?                // iOS 14.0+
var ARFrame.smoothedSceneDepth: ARDepthData?        // iOS 14.0+
```

`ARDepthData` "describes the distance to regions of the real world **from the plane of the
camera**" — read it off the current `ARFrame` each update.

### depthMap (the key buffer)

- **Pixel format:** `kCVPixelFormatType_DepthFloat32` (32-bit float, OSType `fdep`). Apple's
  guidance: read it at runtime with `CVPixelBufferGetPixelFormatType(_:)` and, for the GPU,
  use Metal `MTLPixelFormat.r32Float`.
- **Units: METRES.** depthMap abstract: "The estimated distance from the device to its
  environment, **in meters**." Each texel is a float distance in metres.
- **Axis convention: distance along the optical axis (Z), perpendicular to the camera plane —
  NOT euclidean range.** Both `ARDepthData` ("from the **plane** of the camera") and `depthMap`
  ("from the device to its environment") describe a depth-along-Z value. So to unproject:
  `X = (u - ox)/fx * Z`, `Y = (v - oy)/fy * Z`, `Z = depth` — the standard pinhole back-project
  where `Z` is the stored depth directly. Do **not** treat the stored value as ray length; if
  you need euclidean range, compute `sqrt(X²+Y²+Z²)` after unprojecting.
- **Resolution: typically 256×192** (4:3), lower-res than `capturedImage` but **same aspect
  ratio and same FOV** — it is registered to the captured image. Apple does **not** formally
  document the 256×192 number in the API reference; **query it at runtime** with
  `CVPixelBufferGetWidth/Height` rather than hardcoding.

### confidenceMap

- **Pixel format:** `kCVPixelFormatType_OneComponent8` (8-bit, OSType `L008`) → Metal
  `MTLPixelFormat.r8Uint`. Query at runtime.
- One byte per `depthMap` texel, holding an `ARConfidenceLevel` raw value:

```swift
enum ARConfidenceLevel : Int    // iOS 14.0+ (Comparable)
  case low    = 0
  case medium = 1
  case high   = 2
```

- ARKit is **less confident on reflective / strongly light-absorbing surfaces**. For
  reprojection, mask or down-weight `low`-confidence texels (they produce flyaway points).

## 3. Camera intrinsics & unprojection — the resolution-mapping gotcha

```swift
var ARCamera.intrinsics: simd_float3x3              // iOS 11.0+
var ARCamera.imageResolution: CGSize               // iOS 11.0+
func projectionMatrix(for: UIInterfaceOrientation, viewportSize: CGSize,
                      zNear: CGFloat, zFar: CGFloat) -> simd_float4x4   // iOS 11.0+
func viewMatrix(for: UIInterfaceOrientation) -> simd_float4x4          // iOS 11.0+
func ARFrame.displayTransform(for: UIInterfaceOrientation,
                              viewportSize: CGSize) -> CGAffineTransform // iOS 11.0+
```

### Intrinsics K and the resolution they belong to (CRITICAL)

`intrinsics` (3×3 pinhole `K`): `fx, fy` = focal length in **pixels** (equal for square
pixels); `ox, oy` = principal-point offset from the **top-left** of the image, in pixels.

**`intrinsics` are expressed for `imageResolution`** — i.e. the full-res `capturedImage` in the
camera's **native sensor orientation** (e.g. 1920×1440, 4:3). They do **not** match the
256×192 depthMap. To unproject the depthMap you must **scale K by the resolution ratio**:

```
sx = depthWidth  / imageResolution.width    // e.g. 256/1920
sy = depthHeight / imageResolution.height    // e.g. 192/1440  (== sx since aspect matches)
fx' = fx*sx,  fy' = fy*sy,  ox' = ox*sx,  oy' = oy*sy
```

Then per depth texel `(u,v)` (in depthMap pixels) with depth `Z` metres:
`x = (u - ox')/fx' * Z`, `y = (v - oy')/fy' * Z`, `z = Z` → camera-space point. (Confirmed by
the Apple point-cloud sample and forums thread 663995, which scale `256/1920`, `192/1440`.)

### Orientation: depthMap and capturedImage are in the SAME (native sensor / landscape) frame

- `imageResolution` doc: `capturedImage` "contains image data in the camera device's **native
  sensor orientation**" — i.e. landscape-right, **not** rotated for the UI.
- `depthMap` is in that **same orientation** and registered to `capturedImage` (same FOV, same
  aspect, just downsampled). So a depth texel `(u,v)` and the captured-image pixel at the same
  normalized coordinate look at the same world ray — sample color from `capturedImage` at the
  scaled-up coordinate when colorizing the mesh. Neither buffer is pre-rotated for device
  orientation.
- Because both are unrotated, do orientation handling **once**, in your render matrices, not by
  rotating buffers: build the camera basis from `ARCamera.transform` (or `viewMatrix(for:)`)
  and place unprojected camera-space points into world space; the points already account for
  FOV via the (scaled) intrinsics.

### projectionMatrix / viewMatrix / displayTransform — helpers only

- `projectionMatrix(for:viewportSize:zNear:zFar:)` and `viewMatrix(for:)` both note: "**has no
  effect on ARKit**" — they just construct matrices from the camera state + a target
  `UIInterfaceOrientation`/viewport for **your** renderer. `zNear/zFar` are yours to choose.
  For stereo you typically ignore the provided projection and build your own per-eye projection
  with an x-shifted eye position (±IPD/2), reusing the camera's intrinsics-derived FOV.
- `displayTransform(for:viewportSize:)` returns a `CGAffineTransform` mapping **normalized**
  image coords `(0,0)`→top-left … `(1,1)`→bottom-right to coords that account for orientation +
  aspect-fit crop of the captured image to a viewport. It does **not** scale to viewport pixels.
  Use it if you draw the raw camera image to screen and need the rotate/crop; for a
  3D-unprojected depth mesh you generally don't need it (you handle orientation in the camera
  basis), but it's the documented tool if you also blit the 2D feed.

### capturedImage is YCbCr, not RGB (passthrough color gotcha)

`capturedImage` is **full-range biplanar YCbCr (YUV)**, ITU-R 601-4, full-range (not
video-range). To display/colorize you must convert luma+chroma planes to sRGB per ITU-T T.871
(Apple gives the Metal conversion matrix on the `capturedImage` page / the "Displaying an AR
experience with Metal" sample). Don't assume an RGB texture.

---

## Bottom-line facts

- Enable via `frameSemantics = [.sceneDepth]` (and/or `.smoothedSceneDepth`) on
  `ARWorldTrackingConfiguration`, gated by `supportsFrameSemantics(_:)`; **LiDAR-only**, present
  on iPhone 17 Pro. Depth at 60 Hz. (frame semantics iOS 13.0+, scene depth iOS 14.0+.)
- `depthMap`: `CVPixelBuffer`, `kCVPixelFormatType_DepthFloat32` → Metal `r32Float`, **metres**,
  **~256×192** (query at runtime), 4:3, registered to `capturedImage`.
- Depth is **distance along the optical axis (Z), from the camera plane — not ray length.**
  Unproject with the plain pinhole `Z`-back-project.
- `confidenceMap`: `kCVPixelFormatType_OneComponent8` → `r8Uint`, values `ARConfidenceLevel`
  `low=0/medium=1/high=2`; mask low for clean reprojection.
- **Intrinsics belong to `imageResolution` (full-res, native sensor orientation), not the
  depthMap.** Scale `fx,fy,ox,oy` by `depthRes/imageResolution` before unprojecting.
- `depthMap` and `capturedImage` share the **same unrotated native-sensor (landscape)
  orientation and FOV**; handle device orientation in your matrices, not by rotating buffers.

## Gotchas that bite a custom Metal unprojection

1. **Forgetting to scale K to depth resolution** → points off by ~7.5× (1920/256); the classic
   bug. Scale `fx,fy,ox,oy`, not just one.
2. **Treating depth as ray length** instead of optical-axis Z → barrel-distorted reconstruction
   toward frame edges. Use `Z` directly as the z-component.
3. **Hardcoding 256×192** → breaks on a format change; read `CVPixelBufferGetWidth/Height` and
   `CVPixelBufferGetPixelFormatType` at runtime.
4. **Assuming buffers are screen-oriented** → both are native-sensor (landscape) and unrotated;
   rotating pixels instead of using the camera basis double-applies orientation.
5. **Expecting RGB from `capturedImage`** → it's full-range YCbCr; convert per ITU-T T.871.
6. **`unowned(unsafe)` buffers** → `depthMap`/`confidenceMap` are not retained by ARKit beyond
   the frame; lock (`CVPixelBufferLockBaseAddress`) and copy/upload within the frame callback,
   don't stash the `ARFrame`.
7. **Low-confidence flyaways** on reflective/dark surfaces → mask by `confidenceMap`.
8. **Project context:** none of this reaches our WebGL stereo without a native Metal renderer;
   it is not a drop-in for the WebView pipeline (see top note).
