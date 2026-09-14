---
name: apple-arkit
description: Apple native-iOS sensing reference for the phone-in-headset VR project. Use for ARKit, Core Motion, camera and LiDAR depth, face or hand tracking, placement, and native-to-WKWebView bridging questions.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: AOzNN3g6Ek9uWQucXQKOwOinfmfkwAAM
  related_ids: '["JKkJs_hYJq9qmYu82YrsWsoNXmd8wAAN","humpNHxTAzN7XRL99Qqu0W2XLjdnAAAC"]'
---

# Apple ARKit and native sensing

Trimmed markdown digests of Apple `developer.apple.com` documentation, saved for
the phone-in-headset VR project. Each page starts with its source URL(s) and
fetch date and keeps symbol names, signatures, and iOS availability markers, with
the navigation boilerplate dropped.

**How this ties to the project:** the experiments run as WebGL in an iOS
`WKWebView` shell and get head tracking from web `deviceorientation` events, not
from native ARKit. These pages cover the **native** APIs and the **bridge** you
would use if native sensing ever needs to reach the web scene. See the
**`headset`** skill for the shell itself.

Written and consulted by the **`arkit-docs`** agent. Reuse what is here before
re-fetching; re-pull if Apple has likely changed the surface.

## References - load on demand

Detail lives in `references/`. One pointer per page:

- **[arkit.md](references/arkit.md)**
  - the ARKit framework: `ARSession`/`ARFrame`/`ARAnchor`/`ARCamera`, the
    configuration classes (world, orientation, face, image, body, geo),
    `ARSessionDelegate`, and the iOS vs visionOS split. _Read for the ARKit API
    surface._

- **[coremotion.md](references/coremotion.md)**
  - `CMMotionManager` device motion, `CMDeviceMotion`, `CMAttitude` (roll/pitch/
    yaw, quaternion, rotation matrix), reference frames. _Read for the fallback
    head-tracking path._

- **[wkwebview-bridging.md](references/wkwebview-bridging.md)**
  - `evaluateJavaScript` / `callAsyncJavaScript`, `WKScriptMessageHandler` +
    `WKUserContentController`. _Read when native sensor data has to reach the
    page._

- **[camera-live-view.md](references/camera-live-view.md)**
  - passthrough/preview three ways: web `getUserMedia`/`MediaStream`, native
    AVFoundation capture, and `ARFrame.capturedImage`, plus the Info.plist keys.
    _Read for anything camera-feed. Bottom line: getUserMedia to a
    `VideoTexture`._

- **[scene-depth.md](references/scene-depth.md)**
  - LiDAR depth: `FrameSemantics.sceneDepth`/`.smoothedSceneDepth`,
    `ARDepthData.depthMap` and `confidenceMap`, intrinsics scaling and
    unprojection, orientation conventions. _Read before any depth-reprojected
    stereo work. Native Metal only, not a WebGL drop-in._

- **[face-tracking.md](references/face-tracking.md)**
  - front-camera face sensing: `ARFaceTrackingConfiguration` (device support,
    multi-face, world+face), `ARFaceAnchor` (face coordinate system, eye
    transforms, `lookAtPoint`), `ARFaceGeometry` constant topology,
    `ARSCNFaceGeometry` + occlusion, video-texture mapping, and the 52 blend
    shapes. _Read for anything face-driven. Blocked in-headset — front camera is
    against the user's face._

- **[hand-tracking.md](references/hand-tracking.md)**
  - hands, two ways: visionOS `HandTrackingProvider`/`HandAnchor`/`HandSkeleton`
    (27 joints, 3D, `ARKitSession` + `.handTracking` auth) and the iOS-only-real
    path, Vision `VNDetectHumanHandPoseRequest` (21 joints, 2D, iOS 14+).
    _Read for gesture input. `HandTrackingProvider` is visionOS-only — on iPhone
    it's Vision, and Vision's origin is lower-left._

- **[room-scanning.md](references/room-scanning.md)**
  - RoomPlan: `RoomCaptureSession`/`RoomCaptureView`/`RoomBuilder`, the
    `CapturedRoom` parametric model, multi-room `CapturedStructure`, and USD
    export. _Read for room scanning. Output is bounding boxes, NOT a mesh — and
    units/axes are undocumented. LiDAR required, no visionOS._

- **[placement-correction.md](references/placement-correction.md)**
  - heuristic drop-to-floor and wall-clip nudging without physics:
    `ARPlaneAnchor`, `ARRaycastQuery`/`ARSession.raycast`, `ARMeshAnchor`, and
    direct depth sampling. _Read when placing objects against real geometry._

## Conventions for this shelf

- Each page starts with its Apple source URL(s) and fetch date, and keeps
  signatures plus iOS availability markers.
- Pulled via Apple's JSON doc endpoints
  (`developer.apple.com/tutorials/data/documentation/<path>.json`), which return
  structured signatures and availability when the rendered HTML comes back thin.
- Pull on demand and reuse before re-fetching.
