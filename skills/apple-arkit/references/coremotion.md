---
topic_id: "v2:OECP"
topic_path: "rust-arkit/arkit-features"
semantic_id: "9oBb16paY4J6HSm0_YLOUksfTmZvgAAC"
related_ids:
  - "JKkJs_hYJq9qmYu82YrsWsoNXmd8wAAN"
  - "humpNHxTAzN7XRL99Qqu0W2XLjdnAAAC"
---
# Core Motion

Source: <https://developer.apple.com/documentation/coremotion>

- <https://developer.apple.com/documentation/coremotion/cmmotionmanager>
- <https://developer.apple.com/documentation/coremotion/cmdevicemotion>
- <https://developer.apple.com/documentation/coremotion/cmattitude>
- <https://developer.apple.com/documentation/coremotion/cmquaternion>
- <https://developer.apple.com/documentation/coremotion/cmattitudereferenceframe>

Fetched: 2026-06-27

## What it's for

Core Motion reports motion and environment data from a device's accelerometers, gyroscopes,
magnetometer, and barometer. For head tracking the relevant product is **device motion**:
a fused, processed orientation/attitude estimate (gyro + accel + optionally magnetometer),
delivered as `CMDeviceMotion` objects via `CMMotionManager`.

> This is the most relevant native path for feeding head tracking into the web scene. Today
> the project does **not** use it: the iOS shell lets the OS deliver web `deviceorientation`
> events (which keep Safari's exact coordinate frame, the one `DeviceOrientationControls`
> expects) and grants motion permission via `WKUIDelegate`. The documented **fallback** (see
> `headset` skill `ios-webview-wrapper-notes.md`) is a CoreMotion bridge: run
> `CMMotionManager.startDeviceMotionUpdates`, convert `CMDeviceMotion.attitude` to
> `alpha/beta/gamma`, and `evaluateJavaScript` a synthetic `DeviceOrientationEvent` into the
> page each frame. The angle conversion needs on-device tuning, which is why it's a fallback,
> not the default. Requires `NSMotionUsageDescription` in Info.plist.

## CMMotionManager — iOS 4.0+

`class CMMotionManager` — the object for starting and managing motion services. Create **one
shared instance** per app (Apple's guidance); multiple instances degrade sensor performance.

### Device-motion members

```swift
var isDeviceMotionAvailable: Bool { get }            // iOS 4.0+
var isDeviceMotionActive: Bool { get }               // iOS 4.0+
var deviceMotion: CMDeviceMotion? { get }            // iOS 4.0+  (latest sample, pull-style)
var deviceMotionUpdateInterval: TimeInterval         // iOS 4.0+  (seconds; e.g. 1/60 for 60 Hz)
var showsDeviceMovementDisplay: Bool                 // iOS 5.0+

typealias CMDeviceMotionHandler = (CMDeviceMotion?, Error?) -> Void

func startDeviceMotionUpdates()                                                    // iOS 4.0+ (pull via .deviceMotion)
func startDeviceMotionUpdates(to: OperationQueue, withHandler: CMDeviceMotionHandler)             // iOS 4.0+ (push)
func startDeviceMotionUpdates(using: CMAttitudeReferenceFrame)                     // iOS 5.0+ (pull, chosen frame)
func startDeviceMotionUpdates(using: CMAttitudeReferenceFrame,
                              to: OperationQueue,
                              withHandler: CMDeviceMotionHandler)                  // iOS 5.0+ (push, chosen frame)
func stopDeviceMotionUpdates()                                                     // iOS 4.0+
```

For a per-frame head-tracking bridge you'd typically use the push form with a chosen
reference frame, set `deviceMotionUpdateInterval` to your render rate, and forward each
`CMDeviceMotion` into the WebView.

## CMDeviceMotion — iOS 4.0+

`class CMDeviceMotion` — encapsulated attitude, rotation rate, and acceleration.

```swift
var attitude: CMAttitude { get }            // orientation — the field you convert for head-look
var rotationRate: CMRotationRate { get }    // gyro, bias-removed (rad/s)
var gravity: CMAcceleration { get }         // gravity vector (g)
var userAcceleration: CMAcceleration { get }// user-induced accel, gravity removed (g)
// also: magneticField, heading (iOS 11.0+), sensorLocation (iOS 14.0+)
```

## CMAttitude — iOS 4.0+

`class CMAttitude` — device orientation relative to a reference frame at a point in time.
Same orientation, three interchangeable representations:

```swift
var roll: Double  { get }   // radians (rotation about longitudinal axis)
var pitch: Double { get }   // radians (rotation about lateral axis)
var yaw: Double   { get }   // radians (rotation about vertical axis)
var rotationMatrix: CMRotationMatrix { get }   // iOS 5.0+
var quaternion: CMQuaternion { get }           // iOS 5.0+
func multiply(byInverseOf attitude: CMAttitude) // relative attitude between two samples
```

For a Three.js bridge, the **quaternion** is the cleanest hand-off (no Euler-order ambiguity);
roll/pitch/yaw map conceptually to the web `gamma/beta/alpha` but axis conventions and signs
differ between Core Motion and the W3C `deviceorientation` frame, hence the "needs on-device
tuning" caveat.

## CMQuaternion — iOS 4.0+

`struct CMQuaternion` — a quaternion `(x, y, z, w)` representing an attitude measurement.

## CMAttitudeReferenceFrame — iOS 4.0+

`struct CMAttitudeReferenceFrame` (an `OptionSet`-style constant set; **not** a plain enum in
current docs). Members:

- `xArbitraryZVertical` — Z is vertical (gravity); X is arbitrary. Cheapest; no magnetometer.
- `xArbitraryCorrectedZVertical` — same, but magnetometer-corrected to reduce yaw drift.
- `xMagneticNorthZVertical` — X points to magnetic north.
- `xTrueNorthZVertical` — X points to true north (needs location + calibration).

Query supported frames with `CMMotionManager.availableAttitudeReferenceFrames` (class method).
For a drift-resistant absolute heading (matching web `deviceorientationabsolute`), use a
corrected/north frame; for relative head-look, `xArbitraryZVertical` is fine and cheapest.

## Deprecation notes

No deprecations on any of the symbols above as of this fetch — all current. (An earlier
small-model summary speculated a deprecation on the reference-frame constants; that is **not**
borne out by the docs.) These symbols are also available on visionOS 1.0+.
