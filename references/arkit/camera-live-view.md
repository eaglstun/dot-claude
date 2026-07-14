---
topic_id: "v2:OEEA"
topic_path: "rust-arkit/arkit-features"
semantic_id: "FPSBtnRaRqOoORr8dYDeVP-LouJGIAAD"
related_ids:
  - "JHgGF37YMwO43R-95YLLxWmXCqNGYAAC"
  - "humpNHxTAzN7XRL99Qqu0W2XLjdnAAAC"
---
# Camera live view in the headset (passthrough / camera preview)

Source:

- AVFoundation capture: <https://developer.apple.com/documentation/avfoundation>
  - <https://developer.apple.com/documentation/avfoundation/avcapturesession>
  - <https://developer.apple.com/documentation/avfoundation/avcapturedevice>
  - <https://developer.apple.com/documentation/avfoundation/avcapturedevice/discoverysession>
  - <https://developer.apple.com/documentation/avfoundation/avcapturedeviceinput>
  - <https://developer.apple.com/documentation/avfoundation/avcapturevideopreviewlayer>
  - <https://developer.apple.com/documentation/avfoundation/avcapturevideodataoutput>
- ARKit camera frame: <https://developer.apple.com/documentation/arkit/arframe/capturedimage>
- WKWebView camera plumbing:
  - <https://developer.apple.com/documentation/webkit/wkuidelegate/webview(_:requestmediacapturepermissionfor:initiatedbyframe:type:decisionhandler:)>
  - <https://developer.apple.com/documentation/webkit/wkwebviewconfiguration/allowsinlinemediaplayback>
  - <https://developer.apple.com/documentation/webkit/wkwebviewconfiguration/mediatypesrequiringuseractionforplayback>
  - WWDC21 "Explore WKWebView additions" <https://developer.apple.com/videos/play/wwdc2021/10032/>
  - WebKit bug 208667 (getUserMedia in WKWebView) <https://bugs.webkit.org/show_bug.cgi?id=208667>

Fetched: 2026-06-27

## The question

Show a live iPhone camera feed inside the headset — a passthrough/AR-style background behind
the WebGL scene, or a camera preview. The hard part is not capturing pixels; it is getting
them into our **hand-rolled WebGL stereo render so the feed appears in BOTH eyes**, inside the
`WKWebView` shell. Three paths below, with the bottom line first.

## Bottom line (recommendation)

**Use the all-web path: `navigator.mediaDevices.getUserMedia` → a `<video>` element →
`THREE.VideoTexture` → draw that texture into the scene, which `StereoEffect`/our manual
stereo render already duplicates into both eyes.** It is the only option that lands the pixels
where our renderer can use them per-eye without an impossible per-frame native→WebGL bridge.

Requirements to make it work in our shell:

- iOS **14.3+** for `getUserMedia` to exist at all in a `WKWebView` (it does on iPhone 17 Pro).
- App must be able to capture natively → **`NSCameraUsageDescription`** in Info.plist (and
  `NSMicrophoneUsageDescription` if audio is requested). Without the usage string the API is
  not exposed / the app is rejected.
- A `WKUIDelegate` to grant the camera prompt (iOS 15+, see below) — same pattern as the
  motion-permission grant we already do.
- `WKWebViewConfiguration.allowsInlineMediaPlayback = true` and drop the user-gesture
  requirement via `mediaTypesRequiringUserActionForPlayback = []` so the `<video>` plays
  inline (not fullscreen) and starts without a tap — essential for a headset.

The two **native** paths (AVFoundation, ARKit) capture fine but then face the same wall:
there is no supported, performant way to push a live camera texture from native code into the
page's WebGL context every frame. They are viable only if you abandon the WebGL stereo render
for that layer (e.g. composite a native camera layer _behind_ a transparent web view), which
breaks our single-WebGL-canvas stereo model. Treat them as "do not use for this" unless we
re-architect.

---

## Path 1 — Web: getUserMedia / MediaStream (RECOMMENDED)

### The iOS WKWebView gotcha (the important part)

- `navigator.mediaDevices.getUserMedia()` did **not** work in `WKWebView` for third-party
  apps until **iOS 14.3**. Before 14.3 only Safari and `SFSafariViewController` had camera
  access for web content; a plain `WKWebView` returned no camera. (WebKit bug 208667; WWDC21
  "Explore WKWebView additions".)
- Since **iOS 14.3**, `getUserMedia` is **automatically exposed in a `WKWebView` if the host
  app is itself able to capture** — i.e. it has the camera/mic usage strings. Access is then
  gated by a user prompt like Safari's.
- Our deployment target is iOS 16 and the device is iPhone 17 Pro, so 14.3 is comfortably met.

### Required native config in the shell

| Item                                            | Where                                | Notes                                                                  |
| ----------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------- |
| `NSCameraUsageDescription`                      | Info.plist                           | Required string; gates whether `getUserMedia` is even exposed.         |
| `NSMicrophoneUsageDescription`                  | Info.plist                           | Only if you request audio.                                             |
| `allowsInlineMediaPlayback = true`              | `WKWebViewConfiguration` (iOS 8.0+)  | So the `<video>` renders inline, not in the fullscreen player.         |
| `mediaTypesRequiringUserActionForPlayback = []` | `WKWebViewConfiguration` (iOS 10.0+) | `WKAudiovisualMediaTypes` — `[]` lets the feed autoplay without a tap. |
| Camera permission grant                         | `WKUIDelegate` (iOS 15.0+)           | Method below; mirrors our existing motion-permission grant.            |

### WKUIDelegate camera/mic permission (iOS 15.0+)

```swift
// iOS 15.0+, visionOS 1.0+
optional func webView(_ webView: WKWebView,
    requestMediaCapturePermissionFor origin: WKSecurityOrigin,
    initiatedByFrame frame: WKFrameInfo,
    type: WKMediaCaptureType,                 // .camera / .microphone / .cameraAndMicrophone
    decisionHandler: @escaping @MainActor @Sendable (WKPermissionDecision) -> Void)
// e.g. decisionHandler(.grant)

// async form, same availability:
optional func webView(_ webView: WKWebView,
    decideMediaCapturePermissionsFor origin: WKSecurityOrigin,
    initiatedBy frame: WKFrameInfo, type: WKMediaCaptureType) async -> WKPermissionDecision
```

Determines whether the web content can use the mic/camera. If you do **not** implement it on
iOS 15+, the user still gets the default system prompt (acceptable, but a headset can't easily
tap a prompt — granting in the delegate avoids that, exactly like our motion grant). Note this
is a different `WKUIDelegate` method from the motion one
(`requestDeviceOrientationAndMotionPermissionFor`, see `wkwebview-bridging.md` /
`ios-webview-wrapper-notes.md`) — a camera live view needs **both** granted.

### How pixels reach our WebGL stereo scene (all-web, simple)

`getUserMedia({video:{facingMode:'environment'}})` → assign the `MediaStream` to a `<video>`
element (muted, `playsinline`, autoplay) → `new THREE.VideoTexture(video)` → use it as a
material map (e.g. on a large background quad or a sphere). Because the feed is now an ordinary
Three.js texture in the scene graph, our existing per-eye stereo render draws it in **both
eyes** for free. This is the only path that is genuinely viable for the headset.

Caveats: it is **mono** — both eyes see the same single rear-camera image (no real stereo
depth; fine for a passthrough backdrop). Set `videoTexture` color space for r132
(`texture.encoding = THREE.sRGBEncoding`) to match our color management. Secure context is
required (we already serve HTTPS).

---

## Path 2 — Native AVFoundation capture (NOT viable for our WebGL stereo)

Real, full-control native capture. All classes available very early; current on iPhone 17 Pro.

| Symbol                             | Availability | Declaration / role                                                                                                                                                        |
| ---------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AVCaptureSession`                 | iOS 4.0+     | `class AVCaptureSession` — coordinates flow from inputs to outputs.                                                                                                       |
| `AVCaptureDevice`                  | iOS 4.0+     | `class AVCaptureDevice` — a camera/mic.                                                                                                                                   |
| `AVCaptureDevice.DiscoverySession` | iOS 10.0+    | `class DiscoverySession` — find devices by type/position (the modern replacement for `devices(for:)`).                                                                    |
| `AVCaptureDeviceInput`             | iOS 4.0+     | `class AVCaptureDeviceInput` — wraps a device as a session input.                                                                                                         |
| `AVCaptureVideoPreviewLayer`       | iOS 4.0+     | `class AVCaptureVideoPreviewLayer` — a `CALayer` that displays the live feed. Native UI only.                                                                             |
| `AVCaptureVideoDataOutput`         | iOS 4.0+     | `class AVCaptureVideoDataOutput` — delivers `CMSampleBuffer` frames (CPU/GPU access) via `AVCaptureVideoDataOutputSampleBufferDelegate.captureOutput(_:didOutput:from:)`. |

Info.plist: **`NSCameraUsageDescription`** (and `NSMicrophoneUsageDescription` for audio) —
mandatory; the app crashes on first capture without it.

Why it does not help us: `AVCaptureVideoPreviewLayer` paints into a **native layer**, not our
WebGL canvas — it can't appear inside the single web canvas we stereo-split. Going via
`AVCaptureVideoDataOutput` gives you `CMSampleBuffer`/`CVPixelBuffer` frames, but there is **no
supported API to upload those into the WebView's WebGL context** each frame; you'd be copying
pixels across the native↔JS boundary at video rate, which is not feasible. You would only use
AVFoundation if you composited a native camera layer _behind_ a transparent `WKWebView` — that
abandons our hand-rolled WebGL stereo (the camera layer wouldn't be split per-eye), so it does
not fit this project.

---

## Path 3 — ARKit camera frame (camera + tracking together; same bridge wall)

If you wanted the camera feed **and** ARKit tracking from the same stream:

```swift
// ARFrame.capturedImage — iOS 11.0+
var capturedImage: CVPixelBuffer { get }   // the raw camera pixel buffer behind ARKit
```

Delivered per frame via `ARSessionDelegate.session(_:didUpdate:)` (see `arkit.md`). It is the
pixel buffer ARKit is already analyzing, so you get image + pose for free.

Same wall as Path 2: `capturedImage` is a native `CVPixelBuffer`. Getting it into our page's
WebGL each frame requires a native→WebGL bridge that doesn't exist in a supported, performant
form. Only worth it if we move the whole render natively (RealityKit/SceneKit/Metal), which is
a different project than our WebGL/WebView stack — out of scope unless explicitly asked.

---

## One-line decision table

| Path                        | Pixels into our WebGL stereo (both eyes)?                    | Verdict                           |
| --------------------------- | ------------------------------------------------------------ | --------------------------------- |
| getUserMedia → VideoTexture | Yes — ordinary Three.js texture, stereo render duplicates it | **Use this**                      |
| AVFoundation capture        | No supported per-frame native→WebGL upload                   | Avoid (needs native render layer) |
| ARKit `capturedImage`       | Same as above; adds tracking                                 | Avoid unless going fully native   |
