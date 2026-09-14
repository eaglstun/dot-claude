---
name: ios-cross-compile
description: Field guide for cross-compiling C++/CMake/vcpkg projects to iOS devices and simulators. Use for host-tool, target-triple, mixed-archive, vcpkg, bundle, simctl, platform-macro, build/link/install, and iOS runtime-constraint problems.
metadata:
  version: 1.0.0
  semantic_id: l0Q7NvD6G06wmpMOenx2OaA3wPccoAAM
  related_ids: '["2cSJMtLTGVuY2ItqXnxyEeLnxMccAAAK","icW7MvLeG0v8iLsqdhRmM5gX1VGYsAAD"]'
---

# Cross-compiling large C++ to iOS

Field notes from taking a multi-million-line C++23 / CMake / vcpkg browser engine from
zero to a UIKit app running on the iOS simulator: 64 vcpkg dependencies, ~2700
translation units, mixed C++/Rust static libraries. Everything here was verified by
actually building — error strings are verbatim so symptoms are searchable. This is
general-purpose knowledge, not tied to one repo.

Nothing here was filed upstream; where a note says a bug "belongs upstream", treat it as
a candidate, not a filed issue.

## The prime directive: measure by building, not by grepping

An early grep of the codebase counted **244 platform-conditional sites across 82 files**
that "would need fixing" for iOS. Compiling every library end to end needed **six**
source fixes. Grep counts conditions; only the compiler counts defects. Don't scope an
iOS port from a grep — configure, build, and fix what actually breaks, in order.

## What iOS forbids (and how it reshapes a codebase)

These are hard platform rules, not build settings. They decide architecture before any
code is written:

- **No `fork`/`exec`.** Multi-process designs must collapse to threads in one process
  (or platform service mechanisms). A workable shape: each former helper process becomes
  a `service_main(int ipc_socket)` entry point handed one end of a `socketpair()`, run on
  a thread; site isolation is disabled.
- **No Mach bootstrap.** `bootstrap.h` is simply absent from the iOS SDK (no
  `usr/include/servers/`). Mach-port IPC registration paths must fall back to sockets.
- **No JIT.** A normal app cannot `mmap` with `MAP_JIT|PROT_EXEC`. Disable JIT
  compilers at configure time and use interpreters.
- **`UIApplicationMain` never returns**, which breaks any `exec()`-style or "run main
  loop to completion, then continue" abstraction.

## The build order that works

1. **vcpkg dependencies first**, into a per-platform install root. See
   [vcpkg-ios.md](references/vcpkg-ios.md) for the four traps that will hit you.
2. **A native host-tools build** for any compiled code generators. See
   [host-tools.md](references/host-tools.md).
3. **The cross configure** — `-DCMAKE_SYSTEM_NAME=iOS -DCMAKE_OSX_SYSROOT=iphoneos`
   (or `iphonesimulator`), `-DCMAKE_OSX_ARCHITECTURES=arm64`,
   `-DCMAKE_OSX_DEPLOYMENT_TARGET=<ver>`, `-DCMAKE_MACOSX_BUNDLE=OFF`.
4. **Libraries, then the app target.** Verify archives are really iOS objects
   ([rust-cross.md](references/rust-cross.md) has the `vtool` recipe — `ar` will happily
   splice macOS and iOS objects into one archive with no error).
5. **Bundle and run on the simulator.** See
   [bundles-and-signing.md](references/bundles-and-signing.md) and
   [simulator-workflow.md](references/simulator-workflow.md).

**Always configure into a fresh build directory after a failed cross configure.**
CMake caches `CMAKE_SYSTEM_PROCESSOR ""` into `CMakeSystem.cmake` from a first failed
run and re-includes it forever — adding `-DCMAKE_SYSTEM_PROCESSOR=arm64` to a dirty
build dir silently does nothing.

## References — load on demand

- **[host-tools.md](references/host-tools.md)** — build-time code generators
  (`add_executable`) get cross-compiled and then executed on the build machine, which
  iOS answers with SIGKILL (exit 137). The two fix patterns, a worked
  `add_host_executable()` wrapper, why `target_*()` can't touch IMPORTED targets, and
  the struct-layout matching rule. _Read when a custom command dies with exit 137 or
  "exec format error", or before adding any compiled generator to a cross-compiled
  project._

- **[rust-cross.md](references/rust-cross.md)** — one host-derived `rustc -vV` triple
  shared by host tools and target static libs produces mixed-platform archives that
  link "successfully". Triple mapping (`aarch64-apple-ios` vs `-sim`), splitting host
  from target, and how to actually verify per-object platform with `vtool`. _Read when
  Rust is anywhere in the build, or when a link error mentions "built for macOS"._

- **[vcpkg-ios.md](references/vcpkg-ios.md)** — the trap catalogue: deployment-target
  leakage into the host triplet, autotools `--host`/`--build` collapsing to the same
  triple, `MACOSX_BUNDLE` configure failures, and ports whose `VCPKG_TARGET_IS_OSX`
  dispatch silently falls through to Linux or device branches — with the verbatim
  downstream errors each one produces. _Read before the first `vcpkg install` for an
  iOS triplet, and whenever a port fails with an error that names a different port._

- **[bundles-and-signing.md](references/bundles-and-signing.md)** — iOS bundles are
  flat (no `Contents/`), and the two traps that only exist on iOS: a resource directory
  colliding with the executable name on a case-insensitive filesystem, and the
  reserved-name `Resources/` directory that makes CFBundle ignore your Info.plist —
  surfacing as the wholly misleading "Missing bundle ID". _Read when assembling the
  .app, or when `simctl install` rejects a bundle._

- **[simulator-workflow.md](references/simulator-workflow.md)** — the
  boot/install/launch/screenshot/log loop with `simctl`, the absolute-path requirement,
  and the fact that simulator installs need no code signature at all. _Read when it's
  time to run the thing._

- **[event-loops.md](references/event-loops.md)** — `UIApplicationMain` never returns, so a
  framework that owns its own `exec()` has to be bridged onto a run loop somebody else is
  already running. What ports unchanged (all of CoreFoundation), the four methods that
  don't, the install-before-anything ordering rule, why `pump()` must work with no `exec()`
  on the stack, why timers belong on `kCFRunLoopCommonModes`, and why waking the run loop is
  not the same as draining the event queue. _Read when porting an event loop, or when
  events arrive late, in bursts, or stop during a scroll._

- **[platform-macros.md](references/platform-macros.md)** — "does this `__APPLE__` mean
  macOS or Apple?" — the sorted table (IOKit power management, seatbelt, Cocoa, Mach
  bootstrap vs CoreText, Metal, IOSurface, libobjc, `pthread_setname_np`), and why
  getting it wrong compiles clean on macOS and breaks only on iOS. _Read when adding or
  auditing any Apple platform conditional._

## Working rules

1. **Silent is the default failure mode.** `ar` doesn't check platform, vcpkg port
   dispatch falls through without warning, autoconf misdetects native builds, CMake
   caches bad values. When something finally errors, the guilty party is usually
   upstream of the message. Verify artifacts (with `vtool`, `lipo`, `otool`) instead of
   trusting exit codes.
2. **Device and simulator are different platforms**, not one platform with a flag:
   different vcpkg triplets, different Rust triples, separate dependency builds,
   different signing requirements. Budget for two full dependency builds.
3. **Prefer the simulator first** — no signing identity, no provisioning profile, no
   device, and the whole install/launch loop is scriptable.
4. **Hard-error over silent fallback** in your own build code: an unknown target triple
   or a missing host tool should stop configure with instructions, because every silent
   fallback in this domain produces a broken artifact that fails much later.
