---
semantic_id: "2s_tM3taV50q3ZtYRYKH00p-agau8AAM"
related_ids:
  - "asn7M3zWcp3j7Zu0FYLXk0k3DiKscAAD"
  - "AOzNN3g6Ek9uWQucXQKOwOinfmfkwAAM"
---
# Hand tracking — visionOS `HandTrackingProvider` and the iOS Vision fallback

Source (API reference, fetched via Apple JSON doc endpoints):

visionOS ARKit:

- <https://developer.apple.com/documentation/arkit/handtrackingprovider>
- <https://developer.apple.com/documentation/arkit/handanchor>
- <https://developer.apple.com/documentation/arkit/handskeleton>
- <https://developer.apple.com/documentation/arkit/handskeleton/jointname>
- <https://developer.apple.com/documentation/arkit/arkitsession>
- <https://developer.apple.com/documentation/arkit/arkitsession/authorizationtype>
- <https://developer.apple.com/documentation/arkit/dataproviderstate>
- <https://developer.apple.com/documentation/bundleresources/information-property-list/nshandstrackingusagedescription>

iOS Vision:

- <https://developer.apple.com/documentation/vision/vndetecthumanhandposerequest>
- <https://developer.apple.com/documentation/vision/vndetecthumanhandposerequest/maximumhandcount>
- <https://developer.apple.com/documentation/vision/vnhumanhandposeobservation>
- <https://developer.apple.com/documentation/vision/vnhumanhandposeobservation/chirality>
- <https://developer.apple.com/documentation/vision/vndetectedpoint>
- <https://developer.apple.com/documentation/vision/detecting-hand-poses-with-vision>

Coordinate-origin convention confirmed against (the API pages do not state it):

- WWDC19 "Understanding Images in Vision Framework"
  <https://developer.apple.com/videos/play/wwdc2019/222/>
- WWDC24 "Discover Swift enhancements in the Vision framework"
  <https://developer.apple.com/videos/play/wwdc2024/10163/>
- WWDC20 "Detect Body and Hand Pose with Vision"
  <https://developer.apple.com/videos/play/wwdc2020/10653/>

Fetched: 2026-08-19

## Read this first — two different frameworks

> **`HandTrackingProvider` does not exist on iOS.** It is **visionOS 1.0+ only**, part of the
> newer `ARKitSession` / `DataProvider` ARKit surface that `arkit.md` describes as the
> visionOS-side split. There is no iPhone or iPad availability, no back-deploy, and no
> equivalent ARKit class on iOS. Building against it on this project's target does not compile.
>
> **On iOS the hand-tracking lane is the Vision framework** — `VNDetectHumanHandPoseRequest`,
> iOS 14.0+, 21 2D joints per hand with confidence. Different framework, different joint
> vocabulary, different coordinate space, no depth. §B is the one that runs on the phone.

| | visionOS (§A) | iOS (§B) |
| --- | --- | --- |
| Framework | ARKit (`HandTrackingProvider`) | Vision (`VNDetectHumanHandPoseRequest`) |
| Availability | visionOS 1.0+ *(also macOS 26.0+)* | iOS 14.0+ |
| Output | 27 joints, **3D** transforms in world space | 21 joints, **2D** normalized points |
| Depth | Yes, inherent | No — pair with LiDAR to lift to 3D |
| Chirality | `HandAnchor.chirality`, always present | `observation.chirality`, **iOS 15.0+** |
| Delivery | Async anchor stream, system-driven | You run it per frame, on your own budget |
| Permission | `.handTracking` + `NSHandsTrackingUsageDescription` | Camera permission only |

**Project relevance:** §B is a genuinely viable input channel for the phone-in-headset build —
the **rear** camera faces exactly where a user's hands gesture, which is the opposite of the
front-camera problem that kills face tracking in-headset (`face-tracking.md`). And unlike
`depthMap`, a hand frame is ~21 points × 2 hands × 3 floats ≈ a few hundred bytes of JSON,
so it bridges to the WebView at interactive rates. See `wkwebview-bridging.md`.

---

# §A — visionOS: `HandTrackingProvider`

## A1. Session, authorization, Info.plist

The newer ARKit is session-plus-providers rather than one configuration object:

```swift
let session = ARKitSession()
let handTracking = HandTrackingProvider()

guard HandTrackingProvider.isSupported else { return }

Task {
    // Optional but preferred: ask before running, so you can handle a denial.
    let result = await session.requestAuthorization(for: HandTrackingProvider.requiredAuthorizations)
    guard result[.handTracking] == .allowed else { return }

    do {
        try await session.run([handTracking])
    } catch {
        print("ARKitSession error:", error)
    }
}
```

| Symbol | Platform |
| --- | --- |
| `ARKitSession()` | visionOS 1.0+, macOS 26.0+ |
| `func run(_: [any DataProvider]) async throws` | visionOS 1.0+ |
| `func stop()` | visionOS 1.0+ |
| `func requestAuthorization(for:) async -> [AuthorizationType: AuthorizationStatus]` | visionOS 1.0+ |
| `func queryAuthorization(for:) async -> [AuthorizationType: AuthorizationStatus]` | visionOS 1.0+ |
| `var events: ARKitSession.Events` | visionOS 1.0+ |

`ARKitSession.AuthorizationType` cases: **`.handTracking`** (detailed hand-tracking data),
`.worldSensing` (plane detection, scene reconstruction, image tracking), `.cameraAccess`,
`.accessoryTracking`.

**`ARKit stops a session when it deinitializes.`** Hold a strong reference to the session for as
long as it must run — a session created inside a function body and dropped is a silent no-op.

**Info.plist:** `NSHandsTrackingUsageDescription` (String, visionOS 1.0+) — "Privacy - Hands
Tracking Usage Description". Covers hand skeleton, wrist, and forearm position. Missing key ⇒
no prompt, no data.

`queryAuthorization(for:)` checks without prompting — use it to branch UI before you commit to
asking.

## A2. `HandTrackingProvider`

| Member | Signature |
| --- | --- |
| `init()` | `init()` |
| `static var isSupported: Bool` | runtime-environment support check |
| `static var requiredAuthorizations: [ARKitSession.AuthorizationType]` | what to request |
| `var state: DataProviderState` | `.initialized` / `.running` / `.paused` / `.stopped` |
| `var anchorUpdates: AnchorUpdateSequence<HandAnchor>` | async stream of updates |
| `var latestAnchors: (leftHand: HandAnchor?, rightHand: HandAnchor?)` | most recent, polled |
| `func handAnchors(at: TimeInterval) -> (leftHand: HandAnchor?, rightHand: HandAnchor?)` | query at a timestamp |

`final class HandTrackingProvider`, conforming to `DataProvider`, `Sendable`,
`CustomStringConvertible`. All members visionOS 1.0+.

Two consumption styles, and the choice matters:

```swift
// Push: react to every update as it arrives.
for await update in handTracking.anchorUpdates {
    let hand = update.anchor
    guard hand.isTracked else { continue }
    // update.event is .added / .updated / .removed
}

// Pull: sample the freshest value inside your own render loop.
let (left, right) = handTracking.latestAnchors
```

`handAnchors(at:)` queries for a **specific timestamp** — the one to use when hand poses must
line up with a frame you are about to render rather than with wall-clock now. Feeding it the
render's target presentation time is what keeps hands from lagging the scene.

## A3. `HandAnchor`

```swift
struct HandAnchor        // visionOS 1.0+
```

| Property | Type | Meaning |
| --- | --- | --- |
| `chirality` | `HandAnchor.Chirality` | `.left` or `.right` |
| `handSkeleton` | `HandSkeleton?` | joints — **optional**, can be nil |
| `originFromAnchorTransform` | `simd_float4x4` | hand location/orientation in **world** space |
| `isTracked` | `Bool` | whether ARKit is currently tracking this hand |
| `id` | `UUID` | stable anchor identity |
| `fidelity` | `HandAnchor.Fidelity` | tracking fidelity of this hand |

Conforms to `Anchor`, `TrackableAnchor`, `Identifiable`, `Sendable`, `Equatable`.

The name `originFromAnchorTransform` is the convention, not decoration: it reads
**origin ← anchor**, a transform *from* anchor space *to* world-origin space. Every transform in
this API is named `<destination>From<source>`, which makes composition order legible.

## A4. `HandSkeleton` and joints

```swift
func joint(_ named: HandSkeleton.JointName) -> HandSkeleton.Joint   // visionOS 1.0+
var allJoints: [HandSkeleton.Joint]                                 // visionOS 1.0+
```

`HandSkeleton.Joint`:

| Property | Meaning |
| --- | --- |
| `name` | `HandSkeleton.JointName` |
| `anchorFromJointTransform` | joint space → **anchor** space |
| `parentFromJointTransform` | joint space → **parent joint** space |
| `isTracked` | per-joint tracking flag |

**Getting a joint into world space** — chain the two, right to left:

```swift
let joint = hand.handSkeleton?.joint(.indexFingerTip)
guard let joint, joint.isTracked else { return }
let worldTransform = hand.originFromAnchorTransform * joint.anchorFromJointTransform
let worldPosition  = worldTransform.columns.3.xyz
```

`parentFromJointTransform` is the one for driving a skinned rig or walking the hierarchy;
`anchorFromJointTransform` is the one for placing content. Mixing them up produces hands that
look folded into themselves.

### The 27 joint names — `HandSkeleton.JointName` (visionOS 1.0+, `CaseIterable`)

| Group | Count | Cases |
| --- | --- | --- |
| Forearm / wrist | 3 | `forearmArm`, `forearmWrist`, `wrist` |
| Thumb | 4 | `thumbKnuckle`, `thumbIntermediateBase`, `thumbIntermediateTip`, `thumbTip` |
| Index | 5 | `indexFingerMetacarpal`, `indexFingerKnuckle`, `indexFingerIntermediateBase`, `indexFingerIntermediateTip`, `indexFingerTip` |
| Middle | 5 | `middleFingerMetacarpal`, `middleFingerKnuckle`, `middleFingerIntermediateBase`, `middleFingerIntermediateTip`, `middleFingerTip` |
| Ring | 5 | `ringFingerMetacarpal`, `ringFingerKnuckle`, `ringFingerIntermediateBase`, `ringFingerIntermediateTip`, `ringFingerTip` |
| Little | 5 | `littleFingerMetacarpal`, `littleFingerKnuckle`, `littleFingerIntermediateBase`, `littleFingerIntermediateTip`, `littleFingerTip` |

The thumb has **four** joints, not five — no metacarpal. Code that assumes a uniform 5-per-digit
layout breaks on the thumb.

Because the enum is `CaseIterable`, `JointName.allCases` drives a debug skeleton visualiser in a
few lines.

### Pinch detection

There is no pinch event in this API — derive it from joint distance:

```swift
guard let skeleton = hand.handSkeleton else { return false }
let thumb = skeleton.joint(.thumbTip)
let index = skeleton.joint(.indexFingerTip)
guard thumb.isTracked, index.isTracked else { return false }

let t = (hand.originFromAnchorTransform * thumb.anchorFromJointTransform).columns.3.xyz
let i = (hand.originFromAnchorTransform * index.anchorFromJointTransform).columns.3.xyz
return distance(t, i) < 0.02        // ~2 cm; hysteresis in real use
```

Use two thresholds (enter ~2 cm, exit ~3 cm) or the pinch chatters on and off at the boundary.

---

# §B — iOS: Vision `VNDetectHumanHandPoseRequest`

The path that actually runs on the phone. **iOS 14.0+** (macOS 11.0+, tvOS 14.0+, visionOS 1.0+).
Vision is a per-image request you drive yourself, not a stream ARKit hands you.

## B1. Running the request

```swift
let request = VNDetectHumanHandPoseRequest()
request.maximumHandCount = 1        // default is 2 — lower it if one hand will do

let handler = VNImageRequestHandler(cvPixelBuffer: frame.capturedImage,
                                    orientation: .right,   // see gotcha 4
                                    options: [:])
try handler.perform([request])

guard let observation = request.results?.first else { return }
```

| Symbol | iOS |
| --- | --- |
| `VNDetectHumanHandPoseRequest` (subclass of `VNImageBasedRequest`) | 14.0+ |
| `var maximumHandCount: Int` — **default 2** | 14.0+ |
| `var results: [VNHumanHandPoseObservation]?` | 14.0+ |
| `class var supportedJointNames` / `supportedJointsGroupNames` | 14.0+ |
| `VNDetectHumanHandPoseRequestRevision1` | 14.0+ |

Hands are **ordered by relative size, and only the largest `maximumHandCount` get key points
determined.** So `maximumHandCount` is not a filter applied after the fact — it decides how much
work happens. Keep it at 1 unless two hands are genuinely needed.

## B2. `VNHumanHandPoseObservation`

```swift
func recognizedPoint(_ jointName: JointName) throws -> VNRecognizedPoint
func recognizedPoints(_ groupName: JointsGroupName) throws -> [JointName: VNRecognizedPoint]
var availableJointNames: [JointName]
var availableJointsGroupNames: [JointsGroupName]
var chirality: VNChirality            // iOS 15.0+ / macOS 12.0+ — NOT iOS 14
```

Both `recognizedPoint` accessors **throw**. A joint the model could not place is an error, not a
low-confidence point, so wrap in `try?` and treat nil as "not visible this frame."

`VNRecognizedPoint` (via `VNDetectedPoint`, iOS 14.0+) carries `x`, `y`, and a
`confidence: VNConfidence` in 0.0…1.0. **Filter on confidence** — Apple's own hand-pose sample
discards points below roughly 0.3, and unfiltered points snap around wildly.

### The 21 joints

| Group (`JointsGroupName`) | Cases (`JointName`) |
| --- | --- |
| — | `wrist` |
| `.thumb` | `thumbCMC`, `thumbMP`, `thumbIP`, `thumbTip` |
| `.indexFinger` | `indexMCP`, `indexPIP`, `indexDIP`, `indexTip` |
| `.middleFinger` | `middleMCP`, `middlePIP`, `middleDIP`, `middleTip` |
| `.ringFinger` | `ringMCP`, `ringPIP`, `ringDIP`, `ringTip` |
| `.littleFinger` | `littleMCP`, `littlePIP`, `littleDIP`, `littleTip` |
| `.all` | everything above |

Anatomical abbreviations, not visionOS names — CMC/MCP (base), PIP/MP (middle), DIP/IP (upper),
Tip. **Nothing maps one-to-one onto `HandSkeleton.JointName`**; there is no shared vocabulary and
no forearm joints at all. Any abstraction over both needs a hand-written mapping table.

### Coordinate space — the gotcha that costs an afternoon

**Vision's normalized coordinate space is 0.0…1.0 with the origin in the LOWER-LEFT corner.**
UIKit, SwiftUI, Core Graphics image space, and texture UVs all put it upper-left. Apple's API
reference pages do not say this anywhere; it is stated in the WWDC sessions cited above, and
WWDC24 calls it out explicitly as differing from SwiftUI.

```swift
let p = try observation.recognizedPoint(.indexTip)
// Vision (lower-left) → UIKit / image space (upper-left):
let uiPoint = CGPoint(x: p.location.x, y: 1 - p.location.y)
// or: VNImagePointForNormalizedPoint(p.location, width, height)   // iOS 11.0+
```

Skip the flip and everything is mirrored vertically — which looks *plausible* on a symmetric
open palm and obviously wrong the moment a finger points.

## B3. Lifting Vision's 2D points into 3D

Vision returns no depth. On a LiDAR device, sample `ARFrame.sceneDepth` at the joint's pixel and
unproject with the camera intrinsics — the exact machinery in **`scene-depth.md`** (§ intrinsics
scaling and unprojection). Sequence:

1. Vision point (normalized, lower-left) → flip Y → capture-image pixel coordinates.
2. Scale from `ARCamera.imageResolution` to the depth map's ~256×192, as `scene-depth.md`
   requires — intrinsics belong to the *image* resolution, not the depth resolution.
3. Sample `depthMap`, reject via `confidenceMap`.
4. Unproject to a camera-space 3D point.

Without LiDAR, a ray from the camera through the joint plus a plane or a fixed assumed distance
is the fallback. It is good enough for pointing, not for grabbing.

## B4. Cost and cadence

Vision hand pose is a neural-network inference. Running it on every 60 Hz ARFrame will eat the
frame budget the renderer needs.

- Run it on a **background queue**, not the ARSession delegate queue.
- **Throttle** — 15–30 Hz is plenty for gesture input; interpolate between results.
- Drop frames rather than queue them; a backlog turns into latency, and stale hands are worse
  than fewer hands.
- `maximumHandCount = 1` roughly halves the key-point work.

---

## Gotchas

1. **`HandTrackingProvider` is visionOS-only.** Not iOS, not iPadOS, no back-deployment. The
   whole `ARKitSession`/`DataProvider` surface is visionOS (+ macOS 26). On iPhone, §B or
   nothing.
2. **Two frameworks, two joint vocabularies, two counts** — 27 named ARKit joints vs 21 Vision
   joints, with no name in common. Don't write code that pretends they're the same skeleton.
3. **Vision's origin is lower-left.** Undocumented on the API pages, stated in WWDC. Flip Y, or
   call `VNImagePointForNormalizedPoint`.
4. **Pass the right `orientation` to `VNImageRequestHandler`.** `ARFrame.capturedImage` is in
   native-sensor (landscape) orientation regardless of how the device is held — the same
   convention `scene-depth.md` documents. Wrong orientation ⇒ the model quietly detects nothing,
   with no error to tell you why.
5. **`chirality` is iOS 15.0+**, though the request class is iOS 14.0+. Gate it.
6. **Vision's `recognizedPoint` throws**, and a missing joint is an error rather than a
   zero-confidence point. `try?` plus a confidence floor (~0.3).
7. **`maximumHandCount` defaults to 2** and decides how much inference runs, not just what gets
   returned. Hands are ranked by size, so the "wrong" hand wins if it's closer to the lens.
8. **The thumb has 4 joints in visionOS, not 5** — no metacarpal. Loops assuming 5 per digit
   crash or misindex.
9. **`HandAnchor.handSkeleton` is Optional** and `isTracked` exists on both the anchor and every
   individual joint. Check all three levels before trusting a position.
10. **Keep a strong reference to `ARKitSession`.** It stops on deinit, silently.
11. **`NSHandsTrackingUsageDescription`** is required on visionOS or the prompt never appears and
    no data arrives.
12. **Compose transforms in `<destination>From<source>` order**:
    `originFromAnchorTransform * anchorFromJointTransform`. Reversed, the hand renders in a
    plausible-but-wrong place.
