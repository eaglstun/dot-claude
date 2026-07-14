# Phone-in-Headset VR — Platform Notes (June 2026)

Reference notes for building VR for a **slide-your-phone-in headset** (Google Cardboard /
Daydream class device). The phone provides the screen, sensors, and compute; the headset is
just lenses + strap.

## TL;DR

- **WebXR is NOT a viable path for this hardware in 2026.** iOS Safari has no WebXR at all,
  and the Cardboard stereoscopic mode is deprecated across the ecosystem.
- **Use plain WebGL stereo rendering instead:** Three.js `StereoEffect` + device-orientation
  camera control. No WebXR dependency → works in both iOS Safari and Android Chrome.
- Truly platform-agnostic, no build step, no app store, iterate by refreshing a browser.

## Why not WebXR / A-Frame's VR button

- **iOS Safari does not implement WebXR** on iPhone/iPad (only visionOS / Apple Vision Pro
  supports it). Since the target user is in the Apple world, this alone rules WebXR out.
- **Cardboard / slide-in stereoscopic mode is deprecated.** A-Frame has *disabled Cardboard
  mode by default* as a step toward removal. Modern WebXR targets standalone headsets
  (Quest, Galaxy XR, Android XR), not phones-in-cardboard.
- A-Frame's mobile fallback is now **"magic window"** — single-view (look around by moving
  the phone, like a porthole). This is **NOT** the split-screen two-lens view the headset
  needs.

## The working approach: WebGL stereo (no WebXR)

The classic Cardboard render predates WebXR and still works: render the scene twice
side-by-side (one camera per eye) with lens distortion, and rotate the camera from the
phone's motion sensors.

Stack:
- **Three.js** (via CDN, no build step)
- **`StereoEffect`** — splits the canvas into two eye views
- **`DeviceOrientationControls`** (or raw `deviceorientation` events) — head tracking
- It's just a `<canvas>`, so it runs anywhere WebGL does.

### Critical caveat: iOS motion permission
On iOS, access to `deviceorientation` / `devicemotion` requires:
1. A served page over **HTTPS** (localhost is exempt for dev, but phone-on-LAN is not — see below).
2. An explicit **permission request triggered by a user gesture**, e.g.:
   ```js
   button.addEventListener('click', async () => {
     if (typeof DeviceOrientationEvent.requestPermission === 'function') {
       const state = await DeviceOrientationEvent.requestPermission();
       if (state === 'granted') startVR();
     } else {
       startVR(); // Android / older iOS: no permission gate
     }
   });
   ```
   So the entry flow must be: load page → tap "Enter VR" button → (iOS prompts) → stereo view.

### Serving to the phone for dev
- The phone needs to reach the dev machine over the LAN, and **iOS motion APIs require a
  secure context (HTTPS)** — plain `http://<lan-ip>` will silently block motion on iOS.
- Options: a quick self-signed HTTPS dev server, or a tunneling service that gives an HTTPS
  URL (e.g. an ngrok-style tunnel) pointing at the local server.

## Roadmap idea

1. Stereo "hello world" — split-screen scene (floor + floating objects), look around by
   turning head. Validates the edit→refresh→headset loop.
2. 360° photo/video viewer — map an equirectangular image onto an inside-out sphere.
3. Gaze-based interaction — reticle in center; dwell-to-select (the main viable input on a
   controller-less slide-in headset).

## Libraries to be aware of

- `StereoEffect.js` and `DeviceOrientationControls.js` live in Three.js `examples/jsm/` but
  have been deprecated/removed from some builds over the years — may need to vendor a copy or
  pin a Three.js version that still ships them. Verify availability when scaffolding.

## Sources

- [The state of WebXR on iOS, and beyond — Variant Launch](https://launch.variant3d.com/blog/23-06-state-webxr-on-ios-beyond)
- [VR Headsets & WebXR Browsers — A-Frame docs](https://aframe.io/docs/1.7.0/introduction/vr-headsets-and-webxr-browsers.html)
- [WebXR: Browser Support and Known Issues (2026) — TestMu/LambdaTest](https://www.testmuai.com/learning-hub/webxr-compatible-browsers/)
- [WebXR — Immersive Web](https://immersiveweb.dev/)
