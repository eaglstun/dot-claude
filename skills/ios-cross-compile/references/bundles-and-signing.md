---
semantic_id: "mcWpM1Db01u9rRpgUjfkI4RXzleFkAAJ"
related_ids:
  - "q4aLc_JrE1qUmBsocjomM4gnynPFoAAI"
  - "icW7MvLeG0v8iLsqdhRmM5gX1VGYsAAD"
---

# iOS app bundles and signing

Provenance: both traps hit and root-caused for real during a port (2026); the signing
claim was verified with a clean unsigned simulator build.

## 1. iOS bundles are FLAT

macOS:

```
MyApp.app/Contents/Info.plist
MyApp.app/Contents/MacOS/MyApp
MyApp.app/Contents/Resources/...
```

iOS:

```
MyApp.app/Info.plist
MyApp.app/MyApp
MyApp.app/<resources, right at the root>
```

No `Contents/`, no `MacOS/`, no `Resources/`. Any bundle-assembly CMake that hardcodes
`Contents/Resources` paths, `Contents/lib` symlinks, or `iconutil`-generated `.icns`
files is macOS-only and must branch. iOS icons go through `CFBundleIconName` + an asset
catalog; the Info.plist needs iOS keys (`LSRequiresIPhoneOS`, `UILaunchScreen`) and
must not carry `NSPrincipalClass = NSApplication`.

Also: CMake's `MACOSX_PACKAGE_LOCATION "Resources/foo"` source-file property **drops the
`Resources/` prefix** on iOS — the file lands at the bundle root. If you need resources in
a subdirectory, bypass that property and copy them yourself with an explicit custom
command. Note that `$<TARGET_BUNDLE_DIR:...>` cannot be used in an
`add_custom_command(OUTPUT ...)` path, so spell the destination out.

Both of the following traps exist _because_ the bundle is flat. macOS never hits either
— `Contents/MacOS` and `Contents/Resources` keep executables and resources apart.

## 2. Trap: resource name collides with the executable name

Apple filesystems are case-insensitive by default. A resource directory placed at the
bundle root whose name equals the executable's name (say, a `myapp/` resource tree next
to the `MyApp` binary) collides — and the failure is a _link_ error:

```
ld: open() failed, errno=21 (Is a directory)
```

The linker is trying to write the executable where a directory already sits. Rename the
resource directory.

## 3. Trap: never name a bundle subdirectory `Resources`

On iOS, CFBundle treats a root-level directory literally named `Resources` as a
**layout marker** — it decides the bundle uses the directory-per-role shape and looks
for `Info.plist` _inside_ it. Your perfectly good root `Info.plist` goes unread, and
`simctl install` fails with:

```
Missing bundle ID
```

This message has **nothing to do with the bundle ID** and is **not a codesigning
problem** — both are the natural (wrong) debugging paths, and the CoreSimulator log
adds nothing. The fix is purely the directory name: call the resource tree anything
else (`res`, `assets`, ...).

## 4. Signing

- **Simulator: no code signature is required at all.** Not even ad-hoc. Verified by
  installing and launching a completely unsigned build. If a simulator install fails,
  signing is a red herring — look at bundle layout first (see trap 3).
- **Device:** needs a real signing identity, a provisioning profile, and a physical
  phone. Ad-hoc `codesign -s -` is not sufficient for a device.

This asymmetry is a strong reason to bring the port up on the simulator first.

## Gotchas

- `simctl install` failure logs land in `~/Library/Logs/CoreSimulator/CoreSimulator.log`
  — worth checking, though for the "Missing bundle ID" case it says nothing useful.
- A cross build with `CMAKE_SYSTEM_NAME=iOS` already generates flat-bundle paths (e.g.
  ninja targets under `bin/MyApp.app/` with no `Contents/`) — if your install rules
  still write `Contents/...`, the two layouts fight.
