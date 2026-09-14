# Hardware — the actual phone + headset

The physical devices these experiments run on. Specs here feed the stereo / lens-centering
math (`lensShift`, IPD); see `../../../CLAUDE.md` → "Tuning: eye distance" for how they're used.

## Phones

The screen, sensors, and compute. Used in **landscape** in the headset, so the screen's long
edge is horizontal and is split into two eye halves. Per-eye width and `lensShift` differ by
phone, so anything tuned on one phone needs a re-check on the other.

### iPhone 17 Pro (primary)

Known specs (Apple / GSMArena):

- **Display:** 6.3″ LTPO Super Retina XDR OLED, 120 Hz ProMotion
- **Resolution:** 2622 × 1206 px, **460 ppi**
- **CSS viewport:** ~402 × 874 pt at **devicePixelRatio 3** (so 1206 × 2622 device px)
- **Body:** 150.0 × 71.9 × ~8.75 mm

Derived numbers for the stereo math (landscape orientation):

- **Physical screen size:** long edge 2622 px ÷ 460 ppi ≈ **144.8 mm** wide; short edge
  1206 px ÷ 460 ppi ≈ **66.6 mm** tall.
- **Per eye:** each half is 1311 px ≈ **72.4 mm** wide.
- **`lensShift` scale:** `lensShift` is in CSS px. At DPR 3, the saved default `30` ≈ 90 device
  px ≈ **5.0 mm** of inward shift per eye. (Average human IPD ≈ 63 mm → ~31.5 mm half-IPD,
  which is what the shift is pulling each eye's image toward.)

### iPhone 12 mini

Smaller alternative phone. At 5.4″ it sits comfortably **inside** the BASHKAN 4.7–6.2″ range
(unlike the 17 Pro), but the narrower screen means a different per-eye width and `lensShift`.

Known specs (Apple / GSMArena):

- **Display:** 5.4″ Super Retina XDR OLED
- **Resolution:** 2340 × 1080 px, **476 ppi**
- **CSS viewport:** 360 × 780 pt at **devicePixelRatio 3** (so 1080 × 2340 device px)
- **Body:** 131.5 × 64.2 × 7.4 mm

Derived numbers (landscape):

- **Physical screen size:** long edge 2340 px ÷ 476 ppi ≈ **124.9 mm** wide; short edge
  1080 px ÷ 476 ppi ≈ **57.6 mm** tall.
- **Per eye:** each half is 1170 px ≈ **62.4 mm** wide — about 10 mm narrower per eye than the
  17 Pro, so expect to re-tune `lensShift` rather than reuse the 30 default.

## Headset: BASHKAN 3D VR Headset

A plastic slide-in viewer (lenses + strap), not literal cardboard. The phone is the whole
system; this is optics + a head mount.

Known specs (Amazon listing, model B06XBYCQ2M):

- **Phone size support:** smartphones **4.7″–6.2″**. Note: the iPhone 17 Pro is **6.3″**, a hair
  over the stated max — the body (71.9 mm wide) still seats in the clamp, but it's at/over the
  upper limit, so expect the lenses to sit near the edge of their usable range.
- **Phone retention:** spring-loaded front cover / clamp; drop the phone into the front tray and
  a buckle holds it.
- **Audio:** built-in stereo headphones.
- **Fit:** adjustable head strap (over-the-top + around), foam face cushioning.
- **Input:** has a clicker lever that taps the screen at a fixed point (see `../../../CLAUDE.md` →
  "Input model — the clicker").

To measure (not published; measure on the physical unit if the tuning needs them):

- Lens diameter and lens-to-lens center spacing (drives the real target for `lensShift`).
- Lens-to-screen distance / focal length.
- Field of view.
- Whether the lens spacing is adjustable on this unit.

## Headset: Samsung Gear VR

Also a slide-in viewer — you drop the phone in the front — but unlike the BASHKAN it is **not a
passive optics-and-strap shell**. It has its own electronics, and that's exactly why it does
**not** fit this project as-is. Read the caveats before assuming it's a drop-in.

Built by Samsung with Oculus. Models: SM-R322 (2015, micro-USB), SM-R323 (2016, USB-C),
SM-R324 (2017), SM-R325 (2017, USB-C, ships with a 3DOF motion controller). Released
Aug 21 2015; the line was effectively done by 2017 and Oculus ended Gear VR software support
around 2020.

Known specs (Samsung / Wikipedia):

- **Field of view:** ~96° on the first three models, ~101° on the R323 and later.
- **Phone retention:** spring clamp in the front cradle — genuine slide-in, like the BASHKAN.
- **On-board IMU (unused by us):** the headset carries its **own** inertial measurement unit
  (gyro + accelerometer + proximity sensor) for rotational tracking, targeting **<20 ms**
  motion-to-photon latency. It only powers on when a compatible Samsung phone is plugged into the
  USB connector and the Oculus runtime handshakes with it. We don't use any of that — see below.
- **Input (mostly dead for us):** side **touchpad + back button + volume keys** on the headset
  (and on the R325, a separate handheld 3DOF controller). These are electronic — they need the
  headset powered via the USB handshake, so with an unconnected iPhone they do **nothing**.
- **Adjustment:** focus wheel on top. **No IPD adjustment** (focus only).

### How we'd actually use it: as a passive shell

The "Samsung phone + Oculus native app" path is a different platform and not ours. But you don't
have to use it that way. **Just don't plug the iPhone into the USB connector.** With nothing on
the connector, the headset's IMU, touchpad, proximity sensor, and Oculus handshake never power
on — and a Gear VR collapses into exactly what the BASHKAN is: **lenses + focus wheel + strap.**

In that mode it runs **basically fine with an iPhone**, in either delivery form this project
uses:

- **Safari / WebGL** — our hand-rolled stereo split on screen, the **phone's own** sensors doing
  head tracking via `DeviceOrientationControls`, viewed through the Gear VR lenses. Same model as
  the BASHKAN.
- **The native iOS WebView shell** (`ios-webview-wrapper-notes.md`) — identical from the
  headset's point of view; it's still just optics in front of the iPhone screen.

The headset's superior IMU and touchpad sit there inert; we lean on the phone exactly like we
already do. Two things to actually check before relying on it:

- **Physical fit.** The Gear VR cradle is built around a Samsung-sized phone and a USB plug boss.
  An iPhone 17 Pro may not seat or clamp cleanly — **measure / test the real unit.** If it seats,
  re-tune `lensShift` for these lenses (FOV ~96–101°, different optics than the BASHKAN).
- **Input.** With the touchpad dead and no mechanical screen-tap lever (unlike the BASHKAN's
  clicker), there's **no built-in clicker path**. Plan on gaze-dwell selection or a separate
  Bluetooth clicker/gamepad (see next section).

## Input: Bluetooth clicker

The mechanical clicker (lever that taps the screen) is unreliable, and a passive Gear-VR shell
doesn't have one at all. A **Bluetooth clicker** is the better in-headset input — phone stays
sealed, no screen contact needed. But on iOS most "VR remotes" silently fail, so read this first.

### The one rule that kills most cheap "VR remotes"

A web page in iOS Safari (or our WebView) can read external input only two ways:

1. **`keydown` events** — the device must pair as an **HID keyboard** sending a _real_ key
   (`Enter`, `Space`, an arrow, a letter). This is the simple path: `window.addEventListener('keydown', …)`.
2. **Gamepad API** (`navigator.getGamepads()`) — reliable on iOS Safari **only for MFi-certified**
   controllers; generic HID gamepads are hit-or-miss.

The trap: most $8 "VR Box" remotes and AB-Shutter camera clickers send **volume or media
keycodes**, which iOS Safari **cannot** intercept from JS. They pair fine and do nothing. Avoid
the bargain bin unless tested.

### Picks

- **8BitDo Micro, in Keyboard Mode (~$25) — recommended.** Pairs as a real HID keyboard, so each
  button sends an actual keystroke we read via `keydown`. 24.8 g, keychain-sized, 16 buttons,
  rechargeable. The button count fixes the "clicker shouldn't be the only path" constraint
  (`../../../CLAUDE.md` → Input model) — map two buttons to the same key for redundancy, or split
  select/back/menu for real gaze-UI. **iOS caveat:** set the keyboard profile **once on a
  Mac/PC/Android** with 8BitDo Ultimate Software (iOS can't configure it), then it persists.
- **AirTurn handheld, e.g. TAP (~$70) — zero-fuss alternative.** Purpose-built to fire
  customizable keystrokes that iOS apps read; doesn't disable iOS input. Bombproof, long battery.
  Pricier and more music-gear, but no config dance.
- **MFi gamepad (Backbone / GameSir / Nimbus+) — overkill but bulletproof** if you'd rather poll
  the Gamepad API than listen for keydown.

### Gotchas

- **It can't bootstrap the iOS motion gesture.** `DeviceOrientationEvent.requestPermission()`
  needs a real **touchscreen** tap; a Bluetooth keypress doesn't count. Flow stays: tap "Enter VR"
  on screen → grant motion → seal phone in → drive everything after with the clicker.
- **Verify any candidate in 30 seconds:** pair it, open a page logging
  `window.addEventListener('keydown', e => console.log(e.key))` in iOS Safari, press the button.
  If a normal `e.key` prints, it works. If nothing prints, it's sending media codes — return it.

## Sources

- [iPhone 17 Pro — Technical Specifications (Apple)](https://www.apple.com/iphone-17-pro/specs/)
- [Apple iPhone 17 Pro — Full specifications (GSMArena)](https://www.gsmarena.com/apple_iphone_17_pro-14049.php)
- [BASHKAN 3D VR Headset (Amazon, B06XBYCQ2M)](https://www.amazon.com/BASHKAN-Headset-Headphones-Adjustable-Smartphones/dp/B06XBYCQ2M)
- [Samsung Gear VR (Wikipedia)](https://en.wikipedia.org/wiki/Samsung_Gear_VR)
- [Gear VR with Controller, SM-R325 — Samsung Support](https://www.samsung.com/us/business/support/owners/product/gear-vr-with-controller-sm-r325/)
- [8BitDo Micro Bluetooth Gamepad (Keyboard Mode)](https://www.8bitdo.com/micro/)
- [AirTurn TAP — Bluetooth keystroke controller](https://www.airturn.com/products/airturn-tap-adjustable)
- [Gamepad API browser support (caniuse)](https://caniuse.com/gamepad)
