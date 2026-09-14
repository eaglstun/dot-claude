---
semantic_id: "C4SLc_J7E1q2mIluPnNyKwQPy1ewAAAD"
related_ids:
  - "q4aLc_JrE1qUmBsocjomM4gnynPFoAAI"
  - "2cSJMtLTGVuY2ItqXnxyEeLnxMccAAAK"
---

# Simulator workflow

Provenance: the loop below was used daily during a real port (2026); every command
listed was actually run.

## 1. The core loop

All scriptable, no Xcode GUI needed:

```sh
xcrun simctl boot "iPhone 16 Pro"          # boots the device...
open -a Simulator                          # ...but does NOT open the GUI — this does
xcrun simctl install booted "$PWD/build/ios-sim/bin/MyApp.app"
xcrun simctl launch booted com.example.MyApp
xcrun simctl io booted screenshot out.png  # verify visually, headlessly
```

Two rules baked into that snippet:

- **`simctl boot` does not show you anything.** The device is running headless until
  `open -a Simulator` attaches the GUI. Screenshots work either way.
- **Always pass `simctl install` an absolute path.** It resolves relative paths against
  something other than the shell's cwd and invents a doubled path.

## 2. Getting output back

```sh
# stdout/stderr of the app, attached:
xcrun simctl launch --console booted com.example.MyApp

# system log after the fact:
xcrun simctl spawn booted log show --predicate 'process == "MyApp"'
```

Install failures log to `~/Library/Logs/CoreSimulator/CoreSimulator.log` (sometimes
uselessly — the "Missing bundle ID" failure adds nothing there; see
[bundles-and-signing.md](bundles-and-signing.md) §3).

## 3. Signing: none

Simulator installs need **no code signature at all** — verified with a clean unsigned
build. No ad-hoc signing, no identity, no provisioning profile, no Apple account. This
makes the simulator the right first target for a port: the entire
build → install → launch → screenshot loop runs unattended in CI-style scripts.

## 4. The simulator is a separate platform

Not a flag on the device build:

- vcpkg triplet `arm64-ios-simulator` vs `arm64-ios` — a **full second dependency
  build**, nothing shared.
- Rust triple `aarch64-apple-ios-sim` vs `aarch64-apple-ios`.
- `CMAKE_OSX_SYSROOT=iphonesimulator` vs `iphoneos` — this sysroot is the _only_ thing
  distinguishing the two at the CMake level (`CMAKE_SYSTEM_NAME` is `iOS` for both).
- Device objects linked under a simulator triplet fail with
  `ld: building for 'iOS-simulator', but linking in object file ... built for 'iOS'` —
  and ports can produce exactly that silently
  (see [vcpkg-ios.md](vcpkg-ios.md) §4).

## 5. Reinstalling over a running app photographs the wrong build

`simctl install` will happily replace the bundle of an app that is **currently running**,
and `simctl launch` then returns the _existing_ pid rather than starting anything. The
screenshot you take is the previous build's state — often mid-session, with whatever the
user had on screen — and the old instance dies a few seconds later when the OS notices its
bundle has moved. The result reads exactly like "my new code did something bizarre and then
crashed".

Always:

```sh
xcrun simctl terminate booted <bundle-id> 2>/dev/null
xcrun simctl install booted "$PWD/Build/ios-sim/bin/App.app"
xcrun simctl launch booted <bundle-id>
```

and confirm the app really restarted before believing a screenshot — the surest tell is
whether it is showing its launch state. To separate a crash from a bundle swap, compare
`ls -lt ~/Library/Logs/DiagnosticReports/ | grep <AppName>` against the current time; a
swap leaves no crash report.

Related: give the app time to finish its launch animation before screenshotting. A shot
taken during the zoom-in shows a half-composited window that looks like a rendering bug.

## Driving touch input from a script

There is no `simctl` verb for taps or drags. The options, in order of how much they cost:

- **Ask the human.** If someone is at the machine, this beats everything.
- `cliclick` (Homebrew) or a few lines of Python with `Quartz.CGEventCreateMouseEvent`,
  posting synthetic clicks and drags to the Simulator window's screen coordinates
  (`osascript -e 'tell application "System Events" to tell process "Simulator" to get
{position, size} of window 1'`). Neither is installed by default. This seizes the real
  cursor, so do not do it while someone is using the machine.
- The Simulator maps a host mouse drag to a single-finger pan, so a drag is enough to test
  scrolling. Pinch needs Option-drag and is much harder to synthesise convincingly.

## Gotchas

- An arm64 Mac's simulator runs arm64 iOS binaries natively — same CPU arch as the
  device, different platform marking in every object file. Architecture checks
  (`lipo -info`) cannot tell them apart; platform load commands
  (`vtool -show-build`) can.
- `simctl launch` needs the `CFBundleIdentifier` from the _installed_ Info.plist — if
  install "succeeded" but launch can't find the ID, re-check bundle layout.
