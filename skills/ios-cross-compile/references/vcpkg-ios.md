---
semantic_id: "2cSJMtLTGVuY2ItqXnxyEeLnxMccAAAK"
related_ids:
  - "l0Q7NvD6G06wmpMOenx2OaA3wPccoAAM"
  - "icW7MvLeG0v8iLsqdhRmM5gX1VGYsAAD"
---
# vcpkg iOS gotchas

Provenance: all four traps verified empirically (root-caused, workarounds confirmed by
rebuild) during a real iOS port with ~64 ports building for `arm64-ios` (2026). The
port-file line references were checked against vcpkg at that time. These are upstream
bug _candidates_ — none have been filed.

## 0. Setup shape that works

- Separate `--x-install-root` per platform (`.../ios/vcpkg_installed`,
  `.../ios-sim/vcpkg_installed`, native). Device and simulator are **separate full
  dependency builds** — different triplets, no sharing.
- `VCPKG_TARGET_TRIPLET=arm64-ios` (or `arm64-ios-simulator`) with
  `VCPKG_HOST_TRIPLET=<your native triplet>` set explicitly.

## 1. `CMAKE_OSX_DEPLOYMENT_TARGET` leaks into the HOST triplet

Passing `-DCMAKE_OSX_DEPLOYMENT_TARGET=17.0` (an _iOS_ version) to the top-level
configure leaks into vcpkg's **host** triplet compiler detection, which then runs

```
clang -mmacosx-version-min=17.0
```

and dies hard — there is no macOS 17.

**Workaround:** pass `-DVCPKG_MANIFEST_INSTALL=OFF` to the project configure and run
the dependency install as a separate explicit step where no macOS-hostile variables are
in play:

```sh
vcpkg install --triplet=arm64-ios-simulator --host-triplet=arm64-osx-dynamic \
  --overlay-triplets=... --overlay-ports=... \
  --x-install-root=$PWD/build/ios-sim/vcpkg_installed --x-manifest-root=$PWD
```

## 2. Autotools ports: iOS and macOS map to the same triple

`ports/vcpkg-make/vcpkg_make.cmake` (`z_vcpkg_make_determine_target_triplet`) maps
**both** iOS and macOS to `${arch}-apple-darwin`. On an arm64 Mac targeting arm64 iOS,
`--host` and `--build` become the identical string, so autoconf concludes it is a
_native_ build and tries to **run** the freshly compiled iOS test binary:

```
checking whether we are cross compiling... configure: error: cannot run C compiled programs.
```

Every autotools port fails this way (first observed on `icu:arm64-ios`). The UWP branch
of the same function even carries the comment "Needs to be different from --build to
enable cross builds" — the iOS branch needs the same treatment.

**Workaround:** in the iOS triplet file:

```cmake
set(VCPKG_MAKE_BUILD_TRIPLET "--host=arm-apple-darwin")
```

The value **must stay `*-apple-darwin*`** — do _not_ use `aarch64-apple-ios`. Ports
pattern-match the string: ICU's `configure.ac` / `acinclude.m4` select `U_DARWIN` /
`mh-darwin` from it, and a non-darwin triple silently picks the wrong platform config.

## 3. `MACOSX_BUNDLE` breaks ports that install CLI tools

With `CMAKE_SYSTEM_NAME=iOS`, CMake defaults every `add_executable` to
`MACOSX_BUNDLE`. Any port that installs a command-line tool without a
`BUNDLE DESTINATION` in its `install()` rule then **hard-fails at configure**
(observed with libwebp's `img2webp` / `webpmux`).

**Workaround:** set it off triplet-wide:

```cmake
set(VCPKG_CMAKE_CONFIGURE_OPTIONS -DCMAKE_MACOSX_BUNDLE=OFF)
```

(Also worth passing on the main project configure — helper executables there hit the
same rule.) The pattern recurs in _any_ port building a CLI tool, so the systemic fix
would be vcpkg defaulting it off for iOS triplets.

## 4. `VCPKG_TARGET_IS_OSX` dispatch falls through — and fails DOWNSTREAM

Port files frequently dispatch as
`if(WINDOWS) elseif(OSX) elseif(LINUX) else() → Linux`. iOS is **not**
`VCPKG_TARGET_IS_OSX`, so it silently falls into a Linux or device branch. The
defining property: **the error always surfaces in a downstream port or link step, never
in the guilty port.** Two proven examples:

- **ANGLE selects its Linux port for iOS** (desktop-GL backend, `SystemInfo_macos.mm`,
  IOKit/Quartz links). Surfaces later as
  `Display.cpp: error: Unsupported OpenGL platform` — which names nothing resembling
  the cause. Fix shape: `elseif(VCPKG_TARGET_IS_OSX OR VCPKG_TARGET_IS_IOS)`, and use
  the iOS source lists ANGLE already ships.
- **libvpx builds _device_ objects under the _simulator_ triplet** — its iOS branch
  picks `arm64-darwin-gcc` with no simulator distinction (upstream libvpx has no
  `arm64-iphonesimulator` target at all). Nothing fails in libvpx. It surfaces when
  ffmpeg links:

  ```
  ld: building for 'iOS-simulator', but linking in object file (libvpx.a[3](vpx_encoder.c.o)) built for 'iOS'
  ```

  reported by ffmpeg's configure as the useless
  `libvpx enabled but no supported decoders found`. Proven at the object level:
  `libopus.a` members carried `platform IOSSIMULATOR` while `libvpx.a` members in the
  same install tree carried `LC_VERSION_MIN_IPHONEOS`.

**Debugging rule:** when a port fails mysteriously on iOS, suspect an _upstream_ port's
platform dispatch. Verify per-port with `vtool -show-build` on archive members (see
[rust-cross.md](rust-cross.md) §3 for the recipe and the load-command trap) rather than
reading the failing port's logs harder.

A related unverified case for flavor: harfbuzz gates its `coretext` feature
`"supports": "osx"` even though CoreText is public on iOS — _probably_ over-conservative,
but never actually built on iOS to confirm, so treat as suspicion, not fact.

## Gotchas

- All four traps are invisible on a macOS build of the same tree — they exist only
  under the iOS triplets.
- When a feature can't build cleanly for iOS, check whether the consumer actually needs
  it before fighting the port (e.g. dropping a codec feature that the project never
  references costs nothing).

## Spot-checking one object is not enough

Two ports have now been caught emitting **device** objects into a **simulator** tree — and in the
second case only *part* of the archive was wrong. Within one `libskia.a`, the Metal members were
`platform IOS` / `minos 26.5` while everything else was `IOSSIMULATOR` / `minos 17.0`: the port
honoured the simulator sysroot for its C++ sources and not for its `.mm` ones.

A spot check of the first member passes cleanly and tells you nothing. Tally the whole archive:

```sh
lipo -thin arm64 libfoo.a -output /tmp/thin.a 2>/dev/null || cp libfoo.a /tmp/thin.a
cd /tmp && mkdir -p x && cd x && ar x /tmp/thin.a
for f in *.o; do vtool -show-build "$f" 2>/dev/null \
  | grep -oE "platform +[A-Z-]+|LC_VERSION_MIN_[A-Z]+"; done | sort | uniq -c
```

More than one distinct line in that output is a bug, wherever it came from.

These failures are also **latent**: a wrong object that nothing references gets dead-stripped, so
the archive links fine until the day you enable the code path that needs it. "It linked
yesterday" is not evidence the archive is sound.
