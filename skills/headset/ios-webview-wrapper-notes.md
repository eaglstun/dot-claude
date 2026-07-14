# iOS WebView Wrapper App (`ios/`)

A thin native iOS shell that runs the experiments fullscreen in the phone-in-headset.
It does **not** reimplement any VR logic — it just hosts the existing web page in a
`WKWebView` and clears the iOS-specific obstacles that block a plain Safari tab from
working well in a headset.

## Why a native wrapper at all

Mobile Safari works, but a wrapper buys us things Safari can't:

- **True fullscreen** — no address bar, no status bar, no home indicator, no tab chrome
  eating the stereo viewport.
- **Stays awake** — `isIdleTimerDisabled = true` so the screen never dims mid-session.
- **Locked landscape** and no scroll/zoom/bounce, so the split-screen canvas can't drift.
- **A launcher** that lists every experiment from the dev server, so you pick one with
  the phone out and then drop it in the headset.

## Head tracking: the native CoreMotion bridge (the important part)

This is the thing that quietly breaks naive WebView wrappers, so read this before
touching the head-tracking path.

- In **Mobile Safari**, head tracking uses the normal web path:
  `DeviceOrientationEvent.requestPermission()` (called from a user gesture — the first tap),
  then `DeviceOrientationControls` consumes `deviceorientation` events. No native help needed.
- In a **`WKWebView`**, that path is **dead**: WKWebView does **not** deliver
  `deviceorientation` events to JS even when motion access is granted (verified on iOS 26).
  Granting the page's request via this `WKUIDelegate` method (iOS 15+) is necessary but **not
  sufficient** — the events simply never arrive, so `DeviceOrientationControls` gets no data:

  ```swift
  func webView(_ webView: WKWebView,
               requestDeviceOrientationAndMotionPermissionFor origin: WKSecurityOrigin,
               initiatedByFrame frame: WKFrameInfo,
               decisionHandler: @escaping (WKPermissionDecision) -> Void) {
      decisionHandler(.grant)
  }
  ```

- So in the app we **hand-roll a native CoreMotion bridge** — `MotionBridge.swift`. It reads
  `CMMotionManager.deviceMotion` (reference frame `.xArbitraryZVertical`) and pushes the
  attitude **quaternion** into the page each frame via `evaluateJavaScript`, calling
  `window.__nativeOrientation(w, x, y, z)`. The page is loaded with **`?native=1`** so it
  skips `requestPermission`/`DeviceOrientationControls` and drives the camera from that
  callback. (CoreMotion device-motion needs no usage-description prompt — only
  motion-activity/pedometer do — so there's no `NSMotionUsageDescription`.)

- **The web side must convert CoreMotion's coordinate frame to three.js's**, and this is
  fiddly enough that it ate a whole debugging session. CoreMotion reports a **Z-up** world;
  three.js is **Y-up**. `DeviceOrientationControls` normally hides this inside its Euler
  reordering, but feeding the raw quaternion we have to do it by hand. The transform — in
  each experiment's native block (`hello-world/main.js`, `karaoke/scene/session.js`,
  `lit-textures/main.js`) — is:

  ```
  camera.quaternion = worldFix(−90°X) · natQ · worldFixInv(+90°X) · backCam(−90°X) · landscapeRoll(−90°Z)
  ```

  - **worldFix conjugation (−90°X)** — Z-up → Y-up basis change. Without it the axes scramble
    (rolling the phone "like a steering wheel" looks up/down).
  - **backCam (−90°X)** — aims the camera out the _back_ of the phone (three's own `_q1`).
  - **landscapeRoll (−90°Z)** — the headset always holds the phone in landscape, but
    `window.orientation` reports **0** inside the native WebView, so the usual _dynamic_
    screen-orientation compensation never fires and the horizon sits rolled 90°. So it's a
    fixed bake-in; flip its sign for the opposite landscape mounting.

  Add **`?debug`** to any experiment for an on-screen HUD (taps / native gyro calls / live
  yaw·pitch·roll / `window.orientation`) — there's no console inside the headset.

Sources:

- Apple: `requestDeviceOrientationAndMotionPermissionFor(_:...)`
  <https://developer.apple.com/documentation/webkit/wkuidelegate/webview(_:requestdeviceorientationandmotionpermissionfor:initiatedbyframe:decisionhandler:)>
- Apple Developer Forums — Device Motion in WKWebView
  <https://developer.apple.com/forums/thread/125490>

## Self-signed dev cert

The dev server uses `@vitejs/plugin-basic-ssl` (self-signed). Both the `WKWebView`
(`WKNavigationDelegate`) and the `URLSession` that fetches `/api`
(`TrustingSessionDelegate`) implement the auth-challenge callback and trust any server
cert. **This is a DEV convenience** — it disables certificate validation, which is fine
for a LAN dev box (and harmless against prod's real cert). `Info.plist` also sets
`NSAllowsArbitraryLoads` to cover the `NO_SSL=1` (plain-HTTP-behind-tunnel) path.

## Dev caching — don't let it eat your edits

WKWebView caches JS hard, and a `URLRequest` cache policy only governs the **main document**,
not the subresources WebKit fetches itself (the experiment's `main.js`). So edits can fail to
reach the phone even on a fresh navigation. Two defenses are in place:

- **`WebVRView.swift` uses `config.websiteDataStore = .nonPersistent()`** — a memory-only
  store, so each experiment entry starts with an empty cache (a fresh `WKWebView` is created
  per launch). No on-disk cache to go stale.
- **`vite.config.js` sends `Cache-Control: no-cache`** on dev responses (a `devNoCache`
  plugin; Vite also sets it on transformed modules), forcing revalidation so subresources
  can't serve stale.

If a change still won't appear: confirm the in-app **host** points at a _reachable, running_
dev server (the Debug default in `ios/Config/Debug.xcconfig` is a hardcoded LAN IP that goes
stale when the machine's address changes — check `ipconfig getifaddr en0`). A dead/wrong host
silently falls back to whatever's cached or to prod.

## How content is served — the launcher + `/api`

The app defaults to **prod** (`https://vr.pinecone.website`), where the build emits a
static `/api`. Point the host at a `yarn dev` box instead to load the **live dev server**,
so edits to `main.js` hot-reload in the headset.

- `vite.config.js` (the `projects-api` plugin) serves `GET /api` — every top-level
  directory that contains an `index.html`, as `{ projects: [{ name, path, title }] }`
  (title comes from the page's `<title>`). In dev it's middleware; in a build the same
  plugin emits it as a static `dist/api` file, so prod serves the identical endpoint.
- Because the launcher needs to reach _all_ experiments, run Vite from the **repo root**
  (`yarn dev`, no directory argument) so projects are served at `/<dir>/` and the
  endpoint can scan the root. Running `yarn dev hello-world` still works for plain
  browser dev of a single experiment.
- Experiment `index.html` files must reference their script with a **relative** path
  (`./main.js`, not `/main.js`) so they load correctly when served at `/<dir>/`.

The launcher (`LauncherView.swift`) fetches `/api`, lists the experiments, and opens the
chosen one in a fullscreen `WebVRView`. The server host is editable in the UI and
persisted with `@AppStorage("serverHost")` (default `https://vr.pinecone.website`), so
retargeting to a LAN dev box doesn't require a rebuild.

## Project layout & building

```
ios/
  KaraokeVR.xcodeproj/        # hand-authored, objectVersion 77 (synchronized folder)
  Info.plist                  # landscape, status bar hidden, ATS dev exception
  Config/                     # Debug.xcconfig (LAN dev host) / Release.xcconfig (prod host)
  KaraokeVR/                  # synchronized source group — new files auto-included
    KaraokeVRApp.swift        # @main App
    LauncherView.swift        # experiment list + editable host; also opens the native AR view
    WebVRView.swift           # fullscreen WKWebView host (nonPersistent store, motion grant, cert trust)
    MotionBridge.swift        # CoreMotion → window.__nativeOrientation quaternion push (the web head-tracking)
    ServerClient.swift        # /api fetch over a cert-trusting URLSession
    ARLiveView.swift          # native path: ARKit session + MTKView host (no web page)
    StereoARRenderer.swift    # native path: Metal side-by-side stereo (camera passthrough + test cube)
    Passthrough.metal         # native path: YCbCr→RGB passthrough + cube shaders
    Models/                   # native procedural Metal model factories (see ios-model-maker)
    Assets.xcassets/
```

Two render paths share the launcher: the **web experiments** (`WebVRView`, the three.js
stereo) and a **native "AR Live View"** (`ARLiveView`/`StereoARRenderer`, ARKit camera
passthrough). The native path drives its camera from `frame.camera.viewMatrix(for:)` /
`projectionMatrix(for:)`, so it does **not** share the web path's CoreMotion→three frame
math above.

The `.xcodeproj` uses a **`PBXFileSystemSynchronizedRootGroup`** (Xcode 16+), so any file
dropped into `KaraokeVR/` is picked up automatically — no need to edit `project.pbxproj`
when adding sources.

- Open in Xcode: `open ios/KaraokeVR.xcodeproj`, pick your device, Run.
- Headless compile check (no signing):
  ```sh
  xcodebuild -project ios/KaraokeVR.xcodeproj -target KaraokeVR \
    -sdk iphonesimulator -configuration Debug CODE_SIGNING_ALLOWED=NO build
  ```
- **Deploy to the paired phone from the CLI** (no Xcode GUI needed):
  ```sh
  # 1. build signed — team is EKNXJ2NR3G ("the user Eaglstun"), NOT the cert's parenthetical
  xcodebuild -project ios/KaraokeVR.xcodeproj -scheme KaraokeVR -configuration Debug \
    -destination 'generic/platform=iOS' -derivedDataPath /tmp/dd \
    -allowProvisioningUpdates DEVELOPMENT_TEAM=EKNXJ2NR3G build
  # 2. install + launch (device id from `xcrun devicectl list devices`)
  xcrun devicectl device install app --device <id> /tmp/dd/Build/Products/Debug-iphoneos/KaraokeVR.app
  xcrun devicectl device process launch --device <id> com.rackandpinecone.KaraokeVR
  ```
- Deployment target: iOS 16.0 (the motion-permission delegate is iOS 15+).

## In-headset flow

1. Start the server at the repo root: `yarn dev` (HTTPS on `:8443`).
2. Launch the app, confirm/edit the host, tap an experiment.
3. The experiment loads fullscreen and head tracking starts **immediately** — the app
   appends `?autostart=1&native=1`, so there's no tap-to-start gate, and `MotionBridge`
   feeds the gyro in via `window.__nativeOrientation`.
