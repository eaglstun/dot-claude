---
topic_id: "v2:OEHM"
topic_path: "rust-arkit/arkit-features"
semantic_id: "ZLj5sHrRtR_q2YH2jcD4E1g9Fgd8YAAJ"
related_ids:
  - "JKkJs_hYJq9qmYu82YrsWsoNXmd8wAAN"
  - "hKgts3H4Nk-qESvmmYLsavoNnmfcQAAA"
---
# ARKit

Source: <https://developer.apple.com/documentation/arkit>
(plus the per-symbol subpages linked below)
Fetched: 2026-06-27

## What it's for

ARKit integrates hardware sensing to produce augmented reality apps and games. It combines
device motion tracking, world tracking, scene understanding, and display conveniences to
simplify building an AR experience that places 2D/3D elements into the live camera view.

> Note for this project: ARKit is a **native iOS** framework. It has **no JavaScript/WebView
> API** — nothing in ARKit is callable from the web page directly. Our experiments today get
> head orientation from web `deviceorientation` events (`DeviceOrientationControls`), which the
> native shell already enables via the `WKUIDelegate` motion-permission grant (see the
> `headset` skill's `ios-webview-wrapper-notes.md`). ARKit would only enter the picture if we
> wanted tracking the web stack can't provide (positional/6-DoF world tracking, plane/image
> detection, face tracking), and even then it must be **bridged** Swift→JS via
> `WKWebView.evaluateJavaScript` / a `WKScriptMessageHandler` (see `wkwebview-bridging.md`).
> For plain head rotation, ARKit is overkill vs. the existing `deviceorientation` path or a
> `CMMotionManager` bridge (see `coremotion.md`).

## Landing-page structure

The ARKit landing page is split by platform:

- **visionOS** section: `ARKitSession`, `DataProvider`, `Anchor`, "ARKit in visionOS". This is
  the modern data-provider API used on Apple Vision Pro — a different surface from iOS ARKit.
- **iOS** section: `ARSession`, `ARAnchor`, and the "ARKit in iOS" collection (where the
  configuration classes live).

Apple Vision Pro / visionOS is the only Apple platform with WebXR; iOS Safari still has none
(see `CLAUDE.md`). The iOS symbols below are the relevant ones for an iPhone-in-headset.

## Core session & frame objects (iOS)

| Symbol      | Kind  | Availability | Notes                                                                                                                        |
| ----------- | ----- | ------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `ARSession` | class | iOS 11.0+    | `class ARSession`. Manages motion tracking, camera passthrough, image analysis. (visionOS: deprecated — use `ARKitSession`.) |
| `ARFrame`   | class | iOS 11.0+    | `class ARFrame`. A captured video image plus position-tracking info for one frame.                                           |
| `ARAnchor`  | class | iOS 11.0+    | `class ARAnchor`. Position + orientation of an item in the physical environment.                                             |
| `ARCamera`  | class | iOS 11.0+    | `class ARCamera`. Camera position and imaging characteristics for a given frame.                                             |

### ARSession key members

```swift
func run(_ configuration: ARConfiguration, options: ARSession.RunOptions = [])
func pause()
var configuration: ARConfiguration? { get }
var identifier: UUID { get }
struct ARSession.RunOptions
var delegate: (any ARSessionDelegate)?
var delegateQueue: dispatch_queue_t?
func add(anchor: ARAnchor)
func remove(anchor: ARAnchor)
```

## Configuration classes (the capability surface)

You pick a configuration subclass and pass it to `ARSession.run(_:options:)`. Each gates a
distinct hardware capability; check `<Class>.isSupported` before using.

| Symbol                               | Availability | What it tracks                                                                            |
| ------------------------------------ | ------------ | ----------------------------------------------------------------------------------------- |
| `ARConfiguration` (base)             | iOS 11.0+    | Base class. Key members below.                                                            |
| `ARWorldTrackingConfiguration`       | iOS 11.0+    | 6-DoF device position relative to the environment (full positional/world tracking).       |
| `AROrientationTrackingConfiguration` | iOS 11.0+    | **Orientation only** (3-DoF), rear camera. Closest analog to our `deviceorientation` use. |
| `ARFaceTrackingConfiguration`        | iOS 11.0+    | Facial movement/expressions via the front (TrueDepth) camera.                             |
| `ARImageTrackingConfiguration`       | iOS 12.0+    | Known 2D images via the rear camera.                                                      |
| `ARBodyTrackingConfiguration`        | iOS 13.0+    | Human body poses, planes, and images, rear camera.                                        |
| `ARGeoTrackingConfiguration`         | iOS 14.0+    | World locations via GPS + map data + compass.                                             |

(Also exist, not separately fetched: `ARObjectScanningConfiguration` iOS 12.0+,
`ARPositionalTrackingConfiguration` iOS 13.0+.)

### ARConfiguration key members

```swift
class var isSupported: Bool { get }
var worldAlignment: ARConfiguration.WorldAlignment      // enum: .gravity / .gravityAndHeading / .camera
var isLightEstimationEnabled: Bool
var frameSemantics: ARConfiguration.FrameSemantics      // OptionSet
class func supportsFrameSemantics(_:) -> Bool
var videoFormat: ARConfiguration.VideoFormat
class var supportedVideoFormats: [ARConfiguration.VideoFormat] { get }
```

`worldAlignment` matters if bridging to the web frame: `.gravityAndHeading` gives an
absolute compass-referenced frame (like web `deviceorientationabsolute`); `.gravity` is
gravity-aligned with an arbitrary heading.

## Delegate protocols

| Symbol              | Availability | Declaration                                                                                                                                  |
| ------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `ARSessionObserver` | iOS 11.0+    | `protocol ARSessionObserver : NSObjectProtocol` — respond to session state changes (interruptions, tracking-state changes).                  |
| `ARSessionDelegate` | iOS 11.0+    | `protocol ARSessionDelegate : ARSessionObserver` — receive captured frames (`session(_:didUpdate:)` delivers `ARFrame`s) and tracking state. |

`ARSessionDelegate.session(_:didUpdate frame:)` is the per-frame hook you'd use to pull a
pose out of ARKit and forward it into the WebView each frame.

## Deprecation notes

- No iOS deprecations on the symbols above as of this fetch.
- `ARSession`, `ARSessionDelegate`, `ARSessionObserver` carry **visionOS-only deprecation**
  (visionOS 1.0) — on visionOS use the newer `ARKitSession` / `DataProvider` API. They are
  **not** deprecated on iOS. Irrelevant to an iPhone-in-headset, but don't mistake the
  visionOS marker for an iOS one.

## iPhone 17 Pro (this project)

iOS 11+ everything here is trivially available. World/face/body/geo tracking all supported on
a current Pro device. The realistic question is never "is the API there" but "do we want a
native AR session running behind a WebView at all" — for head-look it is not needed.
