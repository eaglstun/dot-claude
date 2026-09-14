---
semantic_id: "asn7M3zWcp3j7Zu0FYLXk0k3DiKscAAD"
related_ids:
  - "2s_tM3taV50q3ZtYRYKH00p-agau8AAM"
  - "YKjJ0VzcNz-qjZq1m0LP8f4XPjPPcAAP"
---

# ARKit face tracking (ARFaceTrackingConfiguration, ARFaceAnchor, blend shapes)

Source (article + API reference, fetched via Apple JSON doc endpoints):

- <https://developer.apple.com/documentation/arkit/tracking-and-visualizing-faces>
- <https://developer.apple.com/documentation/arkit/arfacetrackingconfiguration>
- <https://developer.apple.com/documentation/arkit/arfacetrackingconfiguration/issupported>
- <https://developer.apple.com/documentation/arkit/arfacetrackingconfiguration/maximumnumberoftrackedfaces>
- <https://developer.apple.com/documentation/arkit/arfacetrackingconfiguration/supportednumberoftrackedfaces>
- <https://developer.apple.com/documentation/arkit/arfacetrackingconfiguration/supportsworldtracking>
- <https://developer.apple.com/documentation/arkit/arfacetrackingconfiguration/isworldtrackingenabled>
- <https://developer.apple.com/documentation/arkit/arfaceanchor>
- <https://developer.apple.com/documentation/arkit/arfaceanchor/geometry>
- <https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapes>
- <https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation>
- <https://developer.apple.com/documentation/arkit/arfaceanchor/lefteyetransform>
- <https://developer.apple.com/documentation/arkit/arfaceanchor/lookatpoint>
- <https://developer.apple.com/documentation/arkit/arfacegeometry>
- <https://developer.apple.com/documentation/arkit/arscnfacegeometry>
- <https://developer.apple.com/documentation/arkit/arworldtrackingconfiguration/userfacetrackingenabled>

Fetched: 2026-08-19

## What this is for

The **front-camera** sensing lane: ARKit tracks the user's face and hands back a pose, a
deforming mesh, per-eye transforms, and 52 expression coefficients. Uses in reach: face-driven
avatars, expression as an input channel, gaze as a pointer, occlusion geometry, and
video-texture face distortion.

> **Project caveat — read before planning anything around this.** Face tracking uses the
> **front** camera, and ARKit's detection range is up to ~3 m. With the phone seated in a
> Cardboard-class headset the front camera sits a couple of centimetres from the user's face,
> mostly occluded by the shroud — **face tracking will not work in-headset**. This digest is
> the API surface for the phone-held-up cases (a companion/mirror mode, a calibration step
> before the phone goes in the headset, a non-headset build) and for
> `ARWorldTrackingConfiguration.userFaceTrackingEnabled` (§7), which is the one shape where
> face data coexists with rear-camera world tracking.
>
> **Unlike depth, face data bridges fine.** `scene-depth.md` rules out per-frame bridging
> because a `depthMap` is a CVPixelBuffer. A face frame is a 52-float dictionary plus two or
> three 4×4 matrices — a few hundred bytes of JSON. That goes over `evaluateJavaScript` or a
> `WKScriptMessageHandler` at 60 Hz without drama. See `wkwebview-bridging.md`. What does
> **not** bridge is `ARFaceGeometry.vertices` (~1200 `simd_float3`s per frame).

---

## 1. Enabling face tracking

```swift
guard ARFaceTrackingConfiguration.isSupported else { return }
let configuration = ARFaceTrackingConfiguration()
if #available(iOS 13.0, *) {
    configuration.maximumNumberOfTrackedFaces = ARFaceTrackingConfiguration.supportedNumberOfTrackedFaces
}
configuration.isLightEstimationEnabled = true
sceneView.session.run(configuration, options: [.resetTracking, .removeExistingAnchors])
```

| Symbol                                         | iOS   | Notes                                                                  |
| ---------------------------------------------- | ----- | ---------------------------------------------------------------------- |
| `ARFaceTrackingConfiguration()`                | 11.0+ | Inherits `ARConfiguration`. Front camera. Detects faces within ~3 m.   |
| `class var isSupported: Bool`                  | 11.0+ | **Always gate on this.** Not a device-model check — ask the framework. |
| `class var supportedNumberOfTrackedFaces: Int` | 13.0+ | Framework ceiling. Don't hardcode a number; read it.                   |
| `var maximumNumberOfTrackedFaces: Int`         | 13.0+ | **Default is 1.** Must opt in to multi-face.                           |
| `class var supportsWorldTracking: Bool`        | 13.0+ | Gate for `isWorldTrackingEnabled`.                                     |
| `var isWorldTrackingEnabled: Bool`             | 13.0+ | Adds device 6-DoF pose to a _face_-tracking session.                   |
| `var isLightEstimationEnabled: Bool`           | 11.0+ | Uses the face as a light probe → `ARDirectionalLightEstimate`.         |

**Device support** — the split matters and is easy to get backwards:

- **iOS/iPadOS 14+**: any device with an **Apple Neural Engine** (TrueDepth _not_ required).
- **iOS/iPadOS 13 and earlier**: requires a **TrueDepth camera**.
- **ARKit is unavailable in the iOS Simulator**, full stop. Guard with
  `#if targetEnvironment(simulator)` or the build will surprise you at runtime.

**Privacy:** Apple's Developer Program License Agreement requires apps using face tracking to
publish a privacy policy describing the face-tracking data and its use. This is a
review-blocking requirement, not a suggestion.

---

## 2. `ARFaceAnchor` — pose, eyes, gaze

ARKit adds/updates `ARFaceAnchor` objects automatically once the session runs. In SceneKit,
hang content off the node ARKit manages for the anchor and it follows the face for free:

```swift
func renderer(_ renderer: SCNSceneRenderer, nodeFor anchor: ARAnchor) -> SCNNode? {
    guard anchor is ARFaceAnchor else { return nil }
    contentNode = SCNReferenceNode(named: "coordinateOrigin")
    return contentNode          // ARKit keeps its transform in sync per frame
}
```

| Property                                          | iOS   | Meaning                                                      |
| ------------------------------------------------- | ----- | ------------------------------------------------------------ |
| `var transform: simd_float4x4` (from `ARAnchor`)  | 11.0+ | Face position/orientation in **world** space.                |
| `var geometry: ARFaceGeometry`                    | 11.0+ | Coarse deforming triangle mesh (§3).                         |
| `var blendShapes: [BlendShapeLocation: NSNumber]` | 11.0+ | Expression coefficients (§6).                                |
| `var leftEyeTransform: simd_float4x4`             | 12.0+ | Eyeball centre + orientation, **relative to the anchor**.    |
| `var rightEyeTransform: simd_float4x4`            | 12.0+ | Same, right eye.                                             |
| `var lookAtPoint: simd_float3`                    | 12.0+ | Gaze target in face space, derived from both eye transforms. |
| `var isTracked: Bool` (from `ARTrackable`)        | 11.0+ | **Check it.** A stale anchor keeps its last transform.       |

**Face coordinate system** — right-handed, metres, origin **centred behind the face**:

- **+X** → the viewer's right (i.e. the face's own _left_)
- **+Y** → up relative to the face itself, _not_ to the world
- **+Z** → out of the face, toward the viewer

**Eye transforms:** translation is the centre of the eyeball relative to the anchor; **+Z
points from the eyeball centre out through the pupil**, so gaze direction is the transform's
third column. Rotation about X aims the pupil up/down. **The eye never rotates about Z** —
don't try to read roll off it.

**`lookAtPoint`:** an abstraction over both eye transforms. Positive X component ⇒ looking
left (viewer's right); **vector length encodes focus distance** — short for a near object,
long for a far one. Handy: one `simd_float3` is a complete cheap gaze signal to bridge.

---

## 3. `ARFaceGeometry` — the mesh

| Member                                                            | iOS   |
| ----------------------------------------------------------------- | ----- |
| `var vertices: [simd_float3]`                                     | 11.0+ |
| `var vertexCount: Int`                                            | 11.0+ |
| `var textureCoordinates: [vector_float2]`                         | 11.0+ |
| `var textureCoordinateCount: Int`                                 | 11.0+ |
| `var triangleIndices: [Int16]`                                    | 11.0+ |
| `var triangleCount: Int`                                          | 11.0+ |
| `init?(blendShapes: [ARFaceAnchor.BlendShapeLocation: NSNumber])` | 11.0+ |

**Topology is constant for the lifetime of the app.** `vertexCount`, `triangleCount`,
`textureCoordinateCount`, the `triangleIndices` buffer, and the `textureCoordinates` buffer
**never change**. Only `vertices` changes frame to frame as the mesh adapts to shape and
expression.

Practical consequences:

- Upload indices + UVs **once**; per frame stream only the vertex buffer.
- A UV-space texture (makeup, tattoos, a wireframe) is authored once and stays registered to
  the same anatomy on every face and every frame.
- Apple does **not** document the actual vertex/triangle counts. Read `vertexCount` at
  runtime rather than baking in a number you found in a blog post.

`init(blendShapes:)` synthesizes a mesh from coefficients with **no live session** — useful
for previewing an expression, or for rebuilding a mesh on the far side of a bridge from the
52 floats instead of shipping vertices.

Apple ships `ARFaceGeometry.obj` (neutral pose) with the sample project as a modelling
template for face-attached art.

---

## 4. `ARSCNFaceGeometry` — SceneKit rendering and occlusion

**Metal-backed SceneKit only.** Not supported under OpenGL-based SceneKit rendering.

| Member                                                 | iOS   |
| ------------------------------------------------------ | ----- |
| `convenience init?(device: MTLDevice)`                 | 11.0+ |
| `convenience init?(device: MTLDevice, fillMesh: Bool)` | 11.0+ |
| `func update(from: ARFaceGeometry)`                    | 11.0+ |

`fillMesh: true` fills the eye and mouth **holes**, giving a solid surface — which is what you
want for occlusion, and what you want for video texturing.

Visible mesh, driven per frame:

```swift
let faceGeometry = ARSCNFaceGeometry(device: sceneView.device!)!
faceGeometry.firstMaterial!.diffuse.contents = wireframeTexture   // transparent PNG
faceGeometry.firstMaterial!.lightingModel = .physicallyBased
contentNode = SCNNode(geometry: faceGeometry)

func renderer(_ r: SCNSceneRenderer, didUpdate node: SCNNode, for anchor: ARAnchor) {
    guard let g = node.geometry as? ARSCNFaceGeometry,
          let faceAnchor = anchor as? ARFaceAnchor else { return }
    g.update(from: faceAnchor.geometry)
}
```

**Occlusion geometry** — the real face hides virtual objects behind it. Write depth, not
colour:

```swift
let faceGeometry = ARSCNFaceGeometry(device: sceneView.device!)!
faceGeometry.firstMaterial!.colorBufferWriteMask = []   // depth only
occlusionNode = SCNNode(geometry: faceGeometry)
occlusionNode.renderingOrder = -1                       // draw before the content it hides
```

Depth writes make SceneKit sort other objects correctly around it; the empty colour mask lets
the camera image show through. That's how virtual glasses get realistically occluded by a nose.
Both halves are required — drop `renderingOrder = -1` and the trick fails silently.

Face-anchored content under `ARFaceTrackingConfiguration` with `isLightEstimationEnabled`
picks up real directional lighting automatically if its materials are physically based.

---

## 5. Mapping live camera video onto the face mesh

Texture the camera feed onto the mesh, then deform the mesh — the basis of face-distortion
effects.

```swift
let faceGeometry = ARSCNFaceGeometry(device: sceneView.device!, fillMesh: true)!
let material = faceGeometry.firstMaterial!
material.diffuse.contents = sceneView.scene.background.contents  // the live feed
material.lightingModel = .constant                               // no relighting
```

The mesh's own UVs are wrong for this — you need each vertex's **screen** position as its UV.
A SceneKit shader modifier at the `geometry` entry point (`SCNShadable`):

```metal
// Vertex → camera space → clip space → normalized viewport coords.
float4 vertexCamera     = scn_node.modelViewTransform * _geometry.position;
float4 vertexClipSpace  = scn_frame.projectionTransform * vertexCamera;
vertexClipSpace /= vertexClipSpace.w;

// Clip XY is [-1,1]; texture UV is [0,1], Y-flipped (upper-left origin).
float4 vertexImageSpace = float4(vertexClipSpace.xy * 0.5 + 0.5, 0.0, 1.0);
vertexImageSpace.y = 1.0 - vertexImageSpace.y;

// ARKit's display transform: device orientation * front-facing camera flip.
float4 transformedVertex = displayTransform * vertexImageSpace;

_geometry.texcoords[0] = transformedVertex.xy;
```

Feed the shader the **inverse** of ARKit's display transform each frame:

```swift
let affineTransform = frame.displayTransform(for: .portrait, viewportSize: sceneView.bounds.size)
let transform = SCNMatrix4(affineTransform)
faceGeometry.setValue(SCNMatrix4Invert(transform), forKey: "displayTransform")
```

`displayTransform(for:viewportSize:)` is the same helper `scene-depth.md` covers — here it also
carries the **front-camera mirror flip**. Skip it and the texture is mirrored and rotated, in a
way that looks almost right at rest and obviously wrong the moment the head turns.

---

## 6. Blend shapes — 52 expression coefficients

`ARFaceAnchor.blendShapes` is `[BlendShapeLocation: NSNumber]`, each value **0.0 (neutral) →
1.0 (maximum)**. Read it in `renderer(_:didUpdate:for:)`:

```swift
let blendShapes = faceAnchor.blendShapes
guard let eyeBlinkLeft  = blendShapes[.eyeBlinkLeft]  as? Float,
      let eyeBlinkRight = blendShapes[.eyeBlinkRight] as? Float,
      let jawOpen       = blendShapes[.jawOpen]       as? Float
else { return }
eyeLeftNode.scale.z  = 1 - eyeBlinkLeft
eyeRightNode.scale.z = 1 - eyeBlinkRight
jawNode.position.y   = originalJawY - jawHeight * jawOpen
```

Use as few as the effect needs. All are iOS 11.0+ **except `tongueOut`, which is iOS 12.0+**.

| Region    | Count | Constants                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Left eye  | 7     | `eyeBlinkLeft`, `eyeLookDownLeft`, `eyeLookInLeft`, `eyeLookOutLeft`, `eyeLookUpLeft`, `eyeSquintLeft`, `eyeWideLeft`                                                                                                                                                                                                                                                                                                                |
| Right eye | 7     | `eyeBlinkRight`, `eyeLookDownRight`, `eyeLookInRight`, `eyeLookOutRight`, `eyeLookUpRight`, `eyeSquintRight`, `eyeWideRight`                                                                                                                                                                                                                                                                                                         |
| Jaw       | 4     | `jawForward`, `jawLeft`, `jawRight`, `jawOpen`                                                                                                                                                                                                                                                                                                                                                                                       |
| Mouth     | 23    | `mouthClose`, `mouthFunnel`, `mouthPucker`, `mouthLeft`, `mouthRight`, `mouthSmileLeft`, `mouthSmileRight`, `mouthFrownLeft`, `mouthFrownRight`, `mouthDimpleLeft`, `mouthDimpleRight`, `mouthStretchLeft`, `mouthStretchRight`, `mouthRollLower`, `mouthRollUpper`, `mouthShrugLower`, `mouthShrugUpper`, `mouthPressLeft`, `mouthPressRight`, `mouthLowerDownLeft`, `mouthLowerDownRight`, `mouthUpperUpLeft`, `mouthUpperUpRight` |
| Eyebrows  | 5     | `browDownLeft`, `browDownRight`, `browInnerUp`, `browOuterUpLeft`, `browOuterUpRight`                                                                                                                                                                                                                                                                                                                                                |
| Cheeks    | 3     | `cheekPuff`, `cheekSquintLeft`, `cheekSquintRight`                                                                                                                                                                                                                                                                                                                                                                                   |
| Nose      | 2     | `noseSneerLeft`, `noseSneerRight`                                                                                                                                                                                                                                                                                                                                                                                                    |
| Tongue    | 1     | `tongueOut` _(iOS 12.0+)_                                                                                                                                                                                                                                                                                                                                                                                                            |

Left/Right in these names is the **face's own** left/right, matching the face coordinate system
— which is mirrored relative to what you see on screen. `eyeBlinkLeft` fires when the eye on
the _right_ side of the preview closes.

The `eyeLook*` coefficients and the eye transforms of §2 are two views of the same thing:
coefficients are cheap and animation-ready; `lookAtPoint` is the one to bridge if gaze is meant
to be a pointer.

---

## 7. Simultaneous world + face tracking (iOS 13+)

Two directions, two configurations — pick by which camera drives the scene:

**Rear camera drives, face rides along** — `ARWorldTrackingConfiguration`:

```swift
let configuration = ARWorldTrackingConfiguration()
if ARWorldTrackingConfiguration.supportsUserFaceTracking {
    configuration.userFaceTrackingEnabled = true      // iOS 13.0+
}
```

Yields an `ARFaceAnchor` for the user's face during a world-tracking session — the multiplayer
avatar-expression case, or facial expression as a control channel over a world-anchored scene.

**Front camera drives, device pose rides along** — `ARFaceTrackingConfiguration`:

```swift
if ARFaceTrackingConfiguration.supportsWorldTracking {
    configuration.isWorldTrackingEnabled = true       // iOS 13.0+
}
```

Adds the device's 6-DoF pose to a face-tracking session.

| Symbol                                                  | iOS   |
| ------------------------------------------------------- | ----- |
| `ARWorldTrackingConfiguration.supportsUserFaceTracking` | 13.0+ |
| `ARWorldTrackingConfiguration.userFaceTrackingEnabled`  | 13.0+ |
| `ARFaceTrackingConfiguration.supportsWorldTracking`     | 13.0+ |
| `ARFaceTrackingConfiguration.isWorldTrackingEnabled`    | 13.0+ |

Both are separately gated — `isSupported` on the face config says nothing about whether the
device can run both cameras at once.

---

## 8. Gotchas

1. **The front camera is blocked in-headset.** Anything face-tracked has to live in a
   phone-held-up mode, or come in through `userFaceTrackingEnabled` on a world-tracking
   session. See the caveat at the top.
2. **Availability trips people up.** Everything is iOS 11 _except_: eye transforms,
   `lookAtPoint`, and `tongueOut` are **iOS 12**; everything multi-face or dual-tracking is
   **iOS 13**. Apple's own sample wraps `maximumNumberOfTrackedFaces` in `#available(iOS 13.0, *)`.
3. **`maximumNumberOfTrackedFaces` defaults to 1.** Multi-face is opt-in, and the ceiling is
   `supportedNumberOfTrackedFaces`, not a constant you remember.
4. **Apple's article text says "only one face at a time."** That predates iOS 13 multi-face;
   the code sample in the same article is the current truth. Trust the API.
5. **Occlusion needs both halves**: `colorBufferWriteMask = []` _and_ a negative
   `renderingOrder`. Half of it renders nothing and hides nothing, with no error.
6. **Video-texture mapping needs the inverted `displayTransform`**, and it is what supplies the
   front-camera mirror flip.
7. **`ARSCNFaceGeometry` is Metal-only** under SceneKit. OpenGL-backed SceneKit gets nothing.
8. **`isTracked` before use.** An untracked anchor still has a `transform`; it's just stale, and
   face-attached content will hang in space.
9. **No Simulator.** `#if targetEnvironment(simulator)` guard, or plan on a device-only path.
10. **Ship a privacy policy** covering face data — a License Agreement requirement.
11. **Don't stream `vertices` over the WebView bridge.** ~1200 `simd_float3`s per frame. Send
    the 52 coefficients and rebuild with `ARFaceGeometry(blendShapes:)` if a mesh is needed.
