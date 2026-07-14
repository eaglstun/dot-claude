---
name: headset
version: 1.0.0
description: >-
  Reference for this phone-in-headset (Google Cardboard / Daydream-class) VR project — why
  WebXR is off the table, the hardware specs driving lens/IPD tuning, the iOS WebView
  wrapper, and the pinned Three.js r132 API surface. Use when building or debugging any
  experiment here: stereo rendering, head tracking, lensShift/IPD, the clicker input, the
  iOS motion-permission entry flow, the native iOS shell, or looking up a Three.js r132
  API.
public: true
semantic_id: "VqWBJfUu8muHyBteNFiyUtH8eufYAAAB"
related_ids:
  - "BODE5nU53h-bmQtYcEqiUtlY-qO2AAAC"
  - "9mihB2Qg1i0L2ZoJMDiHdJF9U4vWQAAD"
topic_id: "v2:LBKK"
topic_path: "metal-renderer/threejs-api"
---

# Headset — phone-in-headset VR reference

Background and reference material for this project's **slide-your-phone-in headset** (the
phone is screen + sensors + compute; the headset is lenses + strap). The fast-moving rules
of the road — stack, `lensShift`, the clicker, iOS gotchas — live in the repo root
**`CLAUDE.md`**; this skill holds the deeper background that doesn't need to be in context
every turn.

## When to use this skill

Working on anything in this repo. Before reaching for the "obvious" VR advice, remember the
hard constraint: **no WebXR, no A-Frame VR button** — we hand-roll WebGL stereo. If a request
sounds like it wants WebXR / Cardboard mode, read `phone-vr-platform-notes.md` first.

## Which doc answers which question

Read the **one** file that matches the task — don't load all four.

| You're working on…                                                                                                                               | Read                           |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------ |
| Why no WebXR? what's the working approach? the iOS motion-permission gesture? dev-over-HTTPS-on-LAN?                                             | `phone-vr-platform-notes.md`   |
| Phone screen size / IPD / per-eye width feeding `lensShift`; the physical headset (lenses, strap, clicker)                                       | `hardware.md`                  |
| The native iOS shell that hosts the web pages in a `WKWebView` (the `ios/` app)                                                                  | `ios-webview-wrapper-notes.md` |
| A specific Three.js API — `StereoEffect`, `DeviceOrientationControls`, materials, lights, IBL, r132 color management (`encoding`/`sRGBEncoding`) | `threejs-docs.md`              |

All four are version-pinned to this project's reality (Three.js **r132**, iPhone 17 Pro,
June 2026 platform landscape). When a doc and the live web disagree on a Three.js API, trust
the doc's r132 source links — threejs.org reflects the current release, not our pin.
