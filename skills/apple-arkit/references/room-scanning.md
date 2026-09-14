---
semantic_id: "YKjJ0VzcNz-qjZq1m0LP8f4XPjPPcAAP"
related_ids:
  - "asn7M3zWcp3j7Zu0FYLXk0k3DiKscAAD"
  - "JKkJs_hYJq9qmYu82YrsWsoNXmd8wAAN"
---

# RoomPlan — parametric room scanning

Source (API reference + articles, fetched via Apple JSON doc endpoints; the HTML pages are a JS
SPA and return only a `<title>` to a plain fetch):

- <https://developer.apple.com/documentation/roomplan>
- <https://developer.apple.com/documentation/roomplan/roomcapturesession> (+ `Configuration`, `Instruction`, `CaptureError`)
- <https://developer.apple.com/documentation/roomplan/roomcaptureview> (+ `RoomCaptureViewDelegate`)
- <https://developer.apple.com/documentation/roomplan/roombuilder> · `capturedroomdata` · `structurebuilder`
- <https://developer.apple.com/documentation/roomplan/capturedroom> (+ `Surface`, `Object`, `Section`, `Confidence`, `USDExportOptions`, `ModelProvider`)
- <https://developer.apple.com/documentation/roomplan/capturedstructure>
- <https://developer.apple.com/documentation/roomplan/capturedroomattribute> + all eight conformers
- <https://developer.apple.com/documentation/roomplan/scanning-the-rooms-of-a-single-structure>
- <https://developer.apple.com/augmented-reality/roomplan/> (marketing — contains **no** limits or best practices)

**Every numeric limit in this file comes from WWDC transcripts, not documentation:**

- [WWDC22 s10127 "Create parametric 3D room scans with RoomPlan"](https://developer.apple.com/videos/play/wwdc2022/10127/)
- [WWDC23 s10192 "Explore enhancements to RoomPlan"](https://developer.apple.com/videos/play/wwdc2023/10192/)

There is no WWDC24 or WWDC25 RoomPlan session; those two are the complete video record.

Fetched: 2026-08-19

---

## 1. It is parametric, not a mesh

This is the thing people get wrong.

> _"The framework outputs a scan as **parametric data**, which makes it easy for your app to modify
> the scanned room's individual components."_

A `CapturedRoom` is a list of **oriented bounding boxes with semantic labels**. Every wall, door,
window, opening, floor, and object is a `transform` (`simd_float4x4`) + `dimensions`
(`simd_float3`) + a `category` + a `confidence`. **There is no vertex buffer, no triangle list, and
no texture anywhere in the API.**

A mesh appears only at **export**, when RoomPlan tessellates that parametric description into USD —
and even then furniture stays boxes:

> _"If you export a scan result to USDZ … objects output as bounding boxes."_

**You cannot get the raw LiDAR mesh out of RoomPlan.** If you want the actual reconstructed
surface, you need ARKit scene reconstruction (`ARMeshAnchor`) — see `scene-depth.md` and
`placement-correction.md`. Running both on a shared `ARSession` is exactly why the iOS 17
bring-your-own-session initializers matter.

The one escape from box-shaped geometry is `polygonCorners` (iOS 17+), which gives real polygon
outlines for slanted walls, walls with a beam, and L-shaped floors.

### Relationship to ARKit

RoomPlan **wraps an `ARSession`** and exposes it as `RoomCaptureSession.arSession`. It is one
session, shared — you do not get a second camera stream, but you keep your own rendering and can
read `arSession.currentFrame` to draw alongside.

```swift
init(arSession: ARSession? = nil)                      // iOS 17.0+
init(frame: CGRect, arSession: ARSession)              // RoomCaptureView, iOS 17.0+
```

> _"By providing your own `ARSession` object, you can continue your app's existing AR experience by
> seamlessly transitioning into a room-scanning session with RoomPlan."_

Two constraints: the configuration must be world-tracking, and **`arSession` is effectively
get-only** — assigning to it throws `CaptureError.invalidARConfiguration`.

---

## 2. Three tiers

### `RoomCaptureView` — drop-in UI (iOS 16.0+)

Gives you the camera feed, real-time overlays, coaching text, and an approve-the-scan review
screen with a miniature "dollhouse" (`isModelEnabled`). **There is no `run()` on the view** — you
drive it through `view.captureSession.run(configuration:)`.

```swift
func captureView(shouldPresent roomDataForProcessing: CapturedRoomData,
                 error: (any Error)?) -> Bool          // default true
func captureView(didPresent processedResult: CapturedRoom, error: (any Error)?)
```

`shouldPresent` is the real control point: `true` processes immediately **and shows Apple's
interactive review UI**; `false` hands you the raw `CapturedRoomData` with no review screen.

Costs: you cannot restyle overlays, coaching, or the dollhouse; you don't choose `RoomBuilder`
options on this path; and `RoomCaptureViewDelegate` inherits **`NSCoding`**, an odd conformance to
force on your delegate.

### `RoomCaptureSession` — bring your own UI (iOS 16.0+)

```swift
static var isSupported: Bool { get }
func run(configuration: RoomCaptureSession.Configuration)
func stop()                                   // iOS 16 — pauses the ARSession
func stop(pauseARSession: Bool = true)        // iOS 17
```

**`Configuration` has exactly one knob**, `isCoachingEnabled` (default `true`). No room-size hint,
no quality/speed tradeoff, no category filter. Do not expect to tune the scanner.

**The four update callbacks are not interchangeable** — three are deltas, one is a snapshot:

| Callback        | Payload                                                                         |
| --------------- | ------------------------------------------------------------------------------- |
| `didAdd`        | **delta** — newest surfaces/objects only                                        |
| `didRemove`     | **delta** — what was removed                                                    |
| `didChange`     | **delta** — only what recently changed                                          |
| **`didUpdate`** | **full snapshot** — _"all surfaces/objects … regardless of the recent changes"_ |

**Render from `didUpdate`.** All six methods have blank default implementations, so the protocol is
effectively all-optional.

```swift
enum Instruction { case normal, moveCloseToWall, moveAwayFromWall,
                        turnOnLight, slowDown, lowTexture }

enum CaptureError { case deviceNotSupported, deviceTooHot, exceedSceneSizeLimit,
                         invalidARConfiguration, worldTrackingFailure, internalError }
```

`.lowTexture` fires on a solid-color wall or a view with no defining edges.

### `RoomBuilder` / `CapturedRoomData` — deferred processing

```swift
struct CapturedRoomData          // Codable, Sendable — "an opaque object that holds the raw results"
class RoomBuilder
    init(options: RoomBuilder.ConfigurationOptions)
    func capturedRoom(from: CapturedRoomData) async throws -> CapturedRoom
    static let beautifyObjects: ConfigurationOptions
```

The point of `CapturedRoomData` being `Codable` is that the expensive ML post-process can move off
the phone and off the moment — _"defer processing to a later date or … to another device."_ Mac
Catalyst availability exists precisely so a Mac can do it.

**`beautifyObjects` mutates your data.** It is not a rendering flag:

> _"If a capture contains a group of chairs around a table, this option **realigns the chairs
> neatly around the table**. If a chair has object attributes, this option **unifies the
> attributes** such that each chair in the group contains the same attributes."_

For measurement work, pass `[]`.

---

## 3. The data model

```swift
struct CapturedRoom            // iOS 16.0+, Codable, Sendable
    var walls, doors, windows, openings: [Surface]   // 16.0
    var floors: [Surface]                            // 17.0
    var objects: [Object]                            // 16.0
    var sections: [Section]                          // 17.0
    var story: Int, version: Int                     // 17.0
    var identifier: UUID
```

**`floors` is iOS 17.** A `CapturedRoom` on iOS 16 has no floor surface at all.

```swift
struct Surface
    var category: Surface.Category      // .wall .door(isOpen:) .window .opening  |  .floor (17.0)
    var confidence: Confidence          // .high .medium .low
    var transform: simd_float4x4
    var dimensions: simd_float3
    var completedEdges: Set<Edge>       // .top .bottom .left .right
    var curve: Curve?                   // startAngle/endAngle/radius, + center (17.0)
    var polygonCorners: [simd_float3]   // 17.0
    var parentIdentifier: UUID?         // 17.0 — e.g. a window's host wall
```

Two underused signals:

- **`completedEdges`** tells you which edges the scanner actually resolved. A wall missing `.top`
  means the ceiling junction was never seen — a per-edge quality signal.
- **`Category.door` carries `isOpen: Bool`**, so `Category` isn't trivially switchable without
  handling the payload.

```swift
struct Object
    var category: Object.Category       // 16 cases, all iOS 16.0, CaseIterable
    var attributes: [any CapturedRoomAttribute]              // 17.0
    func attribute<T: CapturedRoomAttribute>(of: T.Type) -> T?   // 17.0
```

The complete furniture list, fixed and not extensible: `bathtub, bed, chair, dishwasher, fireplace,
oven, refrigerator, sink, sofa, stairs, storage, stove, table, television, toilet, washerDryer`.

**No lamp, rug, plant, artwork, desk, bookshelf** (that's `storage`), **or person.**

Attributes (iOS 17) cover **only chairs, sofas, storage, and tables** — beds, appliances, toilets,
and TVs have none: `ChairType`, `ChairArmType`, `ChairLegType`, `ChairBackType`, `SofaType`,
`StorageType`, `TableType`, `TableShapeType`.

**`Confidence` is about classification, not geometry.** _"The confidence in a `category` that the
captured room assigns…"_ — a `.high` wall means "this is definitely a wall", **not** "these
dimensions are accurate." Apple gives no numeric thresholds and no guidance for `.low`.

`Section` (iOS 17) is **functional-area labelling within one scan** — an open-plan space yields
`.kitchen` and `.diningRoom` sections in a single `CapturedRoom`, distinguished by `center`. It is
not the multi-room mechanism.

### ⚠️ Units and coordinates are never documented

**This is the significant gap.** Across every RoomPlan documentation page, both WWDC transcripts,
and the SDK's doc comments, the words "meter"/"metre" **never appear**. The complete published text
for the geometry is:

> `dimensions` — _"A bounding box that contains the surface."_ / _"…sized to the object's
> extremities."_
> `transform` — _"A matrix that defines the surface's position and orientation in the scene."_

**Never stated:** the units · which component of `dimensions` is width/height/length · the origin of
a `CapturedRoom` · whether +Y is up · what the columns of `transform` mean · the local frame of a
Surface or Object.

Two incidental hints: `Curve.center` _"Corresponds to **xz** center coordinates"_ and
`polygonCorners` is _"in **local plane coordinates**"_. The "xz" phrasing implies Y is vertical —
but Apple never says so.

**Sound inference, labelled as such:** RoomPlan runs on an `ARSession`, and Apple does say the two
share a coordinate space (_"each `RoomCaptureSession` needs to share the same common coordinate
space as the `ARSession`"_). So the origin is the **ARKit world origin** — _the device's pose when
the session first ran_, not the room's centre or a corner — and ARKit's documented conventions
apply: right-handed, **+Y up along gravity**, origin at initial device position, **metres**.

**Folklore, flag it if anyone repeats it:** the widely-cited convention that `transform` column 0 =
right, 1 = up, 3 = position, and `dimensions` = `[width, height, length]` traces to Apple developer
forums thread 707998, where **no reply is marked Apple staff**. It's almost certainly right (it's
the standard simd/ARKit layout) but it is **not documented**. Verify empirically before depending
on it.

---

## 4. Multi-room (iOS 17)

```swift
class StructureBuilder
    init(options: StructureBuilder.ConfigurationOptions)     // typealias to RoomBuilder's
    func capturedStructure(from rooms: [CapturedRoom]) async throws -> CapturedStructure

struct CapturedStructure                 // iOS 17.0+
    var rooms: [CapturedRoom]
    var walls, doors, windows, openings, floors: [Surface]   // de-duplicated union
    var objects: [Object] ; var sections: [Section]
```

Every nested name is a **typealias back to the `CapturedRoom` types** — no new data model. A
`CapturedStructure` is a de-duplicated union (shared walls merged) that also retains the original
`rooms`.

**The hard precondition:** all rooms must share compatible world space. Two documented routes —
keep one continuous `ARSession` across scans, or reload a saved `ARWorldMap`. Failure mode is
`StructureBuilder.BuildError.invalidRoomLocation` (_"one or more rooms reside in a different
vicinity"_).

> **The footgun Apple states twice:** `stop()` pauses the `ARSession`. Call it between rooms and you
> lose the shared coordinate space, and the merge fails. **Use `stop(pauseARSession: false)`.**

After reloading an `ARWorldMap`, _"wait for `TrackingState` to change from `relocalizing` to
`normal`"_ — which needs the camera to observe part of a previously scanned area, i.e. a
"walk back to the last room" UI.

**Backgrounding kills multi-room.** Send the app to the background, restart it, or hit an ARKit
tracking error, and you must restart the session and relocalize. This is the single biggest
implementation cost in multi-room.

_(Note a real tension in Apple's own material: WWDC23 says MultiRoom "works best for **single-floor**
residential houses", while the docs say structures "support rooms … on **different floors**" and
ship `story: Int` on four types. Both are Apple statements.)_

---

## 5. Export

```swift
func export(to url: URL, exportOptions: USDExportOptions = .mesh) throws          // iOS 16
func export(to url: URL, metadataURL: URL? = nil,
            modelProvider: ModelProvider? = nil,
            exportOptions: USDExportOptions = .mesh) throws                       // iOS 17
```

> **Tip, and it's a real bug:** _"Before iOS 17.4, the first letter of the USD file name needs to be
> a character other than a number."_ A filename starting with a digit silently breaks export on
> iOS 16.0–17.3.

**Apple's own feature table — the decisive comparison, and it surprises people:**

| Feature                                           | `.parametric` | `.mesh` | `.model` |
| ------------------------------------------------- | :-----------: | :-----: | :------: |
| Changing size/position of objects, windows, doors |       ✔       |         |          |
| Boolean operations                                |       ✔       |         |          |
| Section positions and labels                      |       ✔       |    ✔    |    ✔     |
| Polygonal walls                                   |               |    ✔    |    ✔     |
| **Windows/doors cut out of wall geometry**        |               |    ✔    |    ✔     |
| Recessed areas of a sink or fireplace             |               |    ✔    |    ✔     |
| ModelProvider models                              |               |         |    ✔     |

So `.parametric` is the **editable/CAD** output — unit cubes you can rescale and boolean — but it
does **not cut window and door holes in the walls**. `.mesh` (the default) is the **visually
correct** output but baked. Anyone assuming `.parametric` is strictly richer gets a surprise.

**File formats:** the docs say "USD" in method docs and "USDZ" in the overview; marketing says "USD
or USDZ". `CapturedRoom.Error` includes `urlMissingFileExtension` / `urlInvalidFileExtension`, so
**the extension selects the format — but Apple never enumerates the accepted ones.** Only `.usdz` is
demonstrated.

**`ModelProvider` (iOS 17)** swaps real 3D models in for the boxes, keyed by category _or attribute
combination_ (e.g. all `.stool` objects with a `.star` base). Accepted model formats, from Apple's
sample: **`.usdc` (preferred), `.abc`, `.obj`, `.ply`, `.stl`**.

**The route to any non-USD format:** `CapturedRoom`, `CapturedStructure`, and `CapturedRoomData` are
all `Codable`. `JSONEncoder` gives you the full parametric model as JSON — which is what Apple's own
custom-model tooling consumes.

---

## 6. Requirements

**LiDAR, unambiguously:**

> `RoomCaptureSession.isSupported` — _"This property is `true` if the device contains a LiDAR
> Scanner; otherwise, `false`."_

WWDC22: _"supported on all LiDAR-enabled iPhone and iPad Pro models."_ Practically: iPhone 12 Pro
and later Pro-tier iPhones, iPad Pro from 2020 on. **No LiDAR = no RoomPlan.** There is no
documented `UIRequiredDeviceCapabilities` key for LiDAR (the `arkit` key gates on ARKit, not
LiDAR), so **`isSupported` at runtime is your only real gate.** No Simulator support.

**Platforms: iOS, iPadOS, Mac Catalyst only.** Across all 273 symbols — **no visionOS**, no native
macOS, no tvOS. For a framework this AR-adjacent the visionOS absence is worth stating. Nothing in
RoomPlan is beta or deprecated.

**Mac Catalyst is processing-only, and fails silently:**

> _"RoomPlan **ignores all capture-session-related calls** on macOS apps built with Mac Catalyst."_

`run(configuration:)` doesn't error there — it does nothing.

**iOS 17 added:** bring-your-own-`ARSession`, all of multi-room, stories and sections, `floors` +
`polygonCorners` + `Curve.center`, `parentIdentifier`, the whole attribute system, `ModelProvider`,
and `version`.

### Limits — all from WWDC, none from documentation

| Limit            | Apple's words                                                                                        | Source |
| ---------------- | ---------------------------------------------------------------------------------------------------- | ------ |
| Single room      | _"maximum room size of 30 feet by 30 feet or around 9 by 9 meters"_                                  | WWDC22 |
| Multi-room total | _"a maximal total area of 2,000 square feet or around 186 square meters"_                            | WWDC23 |
| Scan duration    | _"avoid repeated scans or single long scans over 5 minutes"_                                         | WWDC22 |
| Lighting         | _"A minimum 50 lux or higher is recommended"_                                                        | WWDC22 |
| Ceiling          | _"Even high ceilings could exceed the limit of the scanning range of the LiDAR sensor."_ — no figure | WWDC22 |

**`exceedSceneSizeLimit`'s actual threshold is never stated** — one sentence of docs, no Discussion,
and the WWDC numbers are phrased as recommendations and never tied to this error.

**Known-hard cases** (WWDC22): _"full-height mirrors and glass pose a challenge for the LiDAR
sensor"_, high ceilings, _"very dark surfaces."_ Mitigations Apple suggests: open curtains, close
doors to avoid scanning outside the room.

**Fixed in iOS 17:** slanted and curved walls, recessed kitchen elements (dishwashers, ovens,
sinks), and curved walls now render in `RoomCaptureView`.

**Never addressed anywhere:** sloped/vaulted _ceilings_ (only slanted _walls_), outdoor spaces,
large open-plan or commercial spaces, clutter tolerance. Apple's scoping language is consistently
"a single residential room."

**Privacy:** no RoomPlan page mentions `Info.plist` or any usage-description key. The only Apple
artifact is a build setting in the sample project —
`INFOPLIST_KEY_NSCameraUsageDescription` — and the requirement is inherited from ARKit, which does
document it. No location or motion key.

**There is no RoomPlan page in the Human Interface Guidelines.**

---

## 7. Gotchas

1. **Parametric, not mesh.** No vertices in the API. For real geometry, run ARKit scene
   reconstruction on the shared `ARSession`.
2. **Units and axes are undocumented.** Metres/+Y-up is inference from ARKit, and the `transform`
   column convention is _forum folklore_. Verify empirically.
3. **`didUpdate` is the snapshot; the other three are deltas.**
4. **Results are explicitly unstable mid-scan** — objects appear, get reclassified, get resized,
   get removed. Identifiers persist; geometry does not. Don't cache dimensions from a live callback.
5. **`beautifyObjects` physically moves furniture** and homogenises attributes. Pass `[]` for
   measurement.
6. **`stop()` vs `stop(pauseARSession: false)`** decides whether multi-room merging can work at all.
7. **Delegate threading is undocumented** — no queue is stated, and `RoomCaptureSessionDelegate`
   carries no `@MainActor` (though `RoomCaptureView` does). Neither Apple sample implements the
   session delegate directly. **Marshal to the main actor explicitly.**
8. **`.parametric` does not cut door/window holes.** Default `.mesh` does.
9. **Pre-iOS-17.4: a USD filename starting with a digit breaks export.**
10. **Mac Catalyst silently no-ops capture calls.**
11. **`deviceTooHot` is a realistic outcome**, not theoretical, on a long structure walk-through.
12. **Confidence is about the label, not the measurement.**
13. **`version` exists with no documented semantics.** Persist it anyway — the schema already
    changed once between iOS 16 and 17, and Apple gives no migration guidance.
14. **Unverified: whether live `didUpdate` snapshots populate `sections`, `attributes`, or
    `polygonCorners`.** Test before relying on it.
