---
topic_id: "v2:OGLE"
topic_path: "rust-arkit"
semantic_id: "hKgts3H4Nk-qESvmmYLsavoNnmfcQAAA"
related_ids:
  - "JKkJs_hYJq9qmYu82YrsWsoNXmd8wAAN"
  - "ZLj5sHrRtR_q2YH2jcD4E1g9Fgd8YAAJ"
---
# Apple developer docs — local digests

Trimmed markdown digests of Apple `developer.apple.com` documentation, saved for this
phone-in-headset VR project. Each file starts with its source URL(s) and fetch date, and keeps
symbol names, signatures, and iOS availability markers (nav boilerplate dropped). Reuse these
before re-fetching; re-pull if Apple has likely changed the surface.

How these tie to the project: the experiments run as WebGL in an iOS `WKWebView` shell and get
head tracking from web `deviceorientation` events (`DeviceOrientationControls`), not native
ARKit. See `CLAUDE.md` and the `headset` skill (`ios-webview-wrapper-notes.md`). These docs
cover the **native** APIs and the **bridge** you'd use if native sensing ever needs to reach
the web scene.

## Index

| File                    | Topic              | Covers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ----------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `arkit.md`              | ARKit framework    | Overview; iOS vs visionOS split; `ARSession`/`ARFrame`/`ARAnchor`/`ARCamera`; configuration classes (`ARWorldTracking`, `AROrientationTracking`, `ARFaceTracking`, `ARImageTracking`, `ARBodyTracking`, `ARGeoTracking`); `ARSessionDelegate`/`ARSessionObserver`; availability + visionOS-only deprecations.                                                                                                                                                                                                                                                                                                                |
| `coremotion.md`         | Core Motion        | `CMMotionManager` device-motion API (start/stop, update interval, handlers); `CMDeviceMotion`; `CMAttitude` (roll/pitch/yaw, quaternion, rotationMatrix); `CMQuaternion`; `CMAttitudeReferenceFrame`. The fallback head-tracking bridge path.                                                                                                                                                                                                                                                                                                                                                                                |
| `wkwebview-bridging.md` | WebKit / WKWebView | Native↔JS bridging: `evaluateJavaScript` / `callAsyncJavaScript` (iOS 8/14/15 forms); `WKScriptMessageHandler` + `WKUserContentController` (`add`/`remove`, reply variant); `WKScriptMessage`. How native sensor data reaches the page.                                                                                                                                                                                                                                                                                                                                                                                      |
| `camera-live-view.md`   | Camera live view   | Showing a live iPhone camera feed in the headset (passthrough/preview). Web `getUserMedia`/`MediaStream` (WKWebView gained it iOS 14.3; `WKUIDelegate` media-permission iOS 15; `allowsInlineMediaPlayback`); native AVFoundation capture (`AVCaptureSession`/`Device`/`DiscoverySession`/`VideoPreviewLayer`/`VideoDataOutput`); ARKit `ARFrame.capturedImage`. Info.plist keys + how pixels reach our WebGL stereo. Bottom line: getUserMedia → `VideoTexture`.                                                                                                                                                            |
| `scene-depth.md`        | LiDAR scene depth  | Depth-reprojected stereo passthrough. Enabling: `FrameSemantics.sceneDepth`/`.smoothedSceneDepth`, `supportsFrameSemantics(_:)` (LiDAR-only). Reading: `ARFrame.sceneDepth`→`ARDepthData.depthMap` (`DepthFloat32`/`r32Float`, metres, ~256×192, depth=optical-axis Z) + `confidenceMap` (`ARConfidenceLevel` low/medium/high). Intrinsics/unprojection: `ARCamera.intrinsics` belong to `imageResolution` — must scale to depth res; depthMap & `capturedImage` share native-sensor (landscape) orientation; `projectionMatrix`/`viewMatrix`/`displayTransform` are render helpers. Native-Metal-only; not a WebGL drop-in. |

| `placement-correction.md` | Placement correction | Heuristic drop-to-floor + wall-clip nudge for the native renderer (no physics). `ARPlaneAnchor` (`center`/`extent`/`planeExtent`/`geometry.boundaryVertices`/`alignment`/`classification`) point-in-plane + plane-normal push; `ARRaycastQuery`/`ARSession.raycast` (`.existingPlaneGeometry`/`.existingPlaneInfinite`/`.estimatedPlane`, `.horizontal`/`.vertical`) for downward floor-Y and horizontal wall probes; `ARMeshAnchor`/`sceneReconstruction = .mesh` (NOT enabled today — cost/value note) for non-planar clearance; direct `sceneDepth.depthMap` sampling as a view-dependent live check. Ranked recos, Swift sketches, iOS-mins, and the iOS-16 plane-rotation + extent-vs-infinite gotchas. |

Fetched: 2026-06-27 (arkit/coremotion/wkwebview-bridging; camera-live-view + scene-depth added same day; placement-correction added 2026-06-29).
Pulled via Apple's JSON doc endpoints
(`developer.apple.com/tutorials/data/documentation/<path>.json`), which return structured
signatures/availability when the rendered HTML pages come back thin.

## Cross-references in the headset skill

- `ios-webview-wrapper-notes.md` — the actual `WKWebView` shell, the `WKUIDelegate`
  motion-permission grant, and the documented Core Motion → `deviceorientation` fallback.
- `phone-vr-platform-notes.md` — why no WebXR on iOS Safari (only visionOS has it).
