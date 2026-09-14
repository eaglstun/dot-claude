---
semantic_id: "_Uy_c_JpmdvQ-rNFd_XuE5g_jFf4EAAI"
related_ids:
  - "icW7MvLeG0v8iLsqdhRmM5gX1VGYsAAD"
  - "l0Q7NvD6G06wmpMOenx2OaA3wPccoAAM"
---

# Platform macros: "macOS" vs "Apple"

Provenance: the sort table below comes from compile failures and SDK inspection during a
real port (2026), not from documentation.

## 1. The question to ask at every conditional

On Apple platforms, `#ifdef __APPLE__` / CMake `if (APPLE)` is true on **both** macOS
and iOS. The correct split comes from `<TargetConditionals.h>`:

```c
#include <TargetConditionals.h>
#if defined(__APPLE__) && TARGET_OS_IPHONE
// iOS (device and simulator)
#elif defined(__APPLE__)
// macOS
#endif
```

(`TARGET_OS_IOS` also exists; do not guess at macro names — several plausible-sounding
ones don't exist, and `#ifdef` on a nonexistent macro is silently false.)

**When adding or auditing a platform conditional, ask: does this condition mean "macOS"
or "Apple"?** Getting it wrong compiles fine on macOS and breaks only on iOS — which is
why large codebases accumulate wrong ones invisibly.

## 2. The sort table (each entry verified the hard way)

**macOS-only** — must be `macOS`, not `Apple`:

| Thing                              | Evidence                                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------------- |
| IOKit power management             | `IOKit/pwr_mgt/IOPMLib.h` is macOS-only, _even though IOKit.framework itself exists on iOS_ |
| The seatbelt sandbox (`sandbox.h`) | macOS-only sandboxing API                                                                   |
| Cocoa / AppKit                     | `Cocoa/Cocoa.h` absent on iOS (UIKit instead)                                               |
| Mach bootstrap                     | `bootstrap.h` absent from the iOS SDK entirely (no `usr/include/servers/`)                  |

**Apple-wide** — genuinely means `__APPLE__`, works on both:

| Thing                             | Note                                                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| CoreText                          | public framework on iOS too                                                                                              |
| Metal                             | shared                                                                                                                   |
| IOSurface                         | exists on iOS — but the umbrella header `IOSurface/IOSurface.h` is macOS-only; import `IOSurface/IOSurfaceRef.h` instead |
| libobjc                           | shared                                                                                                                   |
| One-argument `pthread_setname_np` | the Apple signature on both platforms                                                                                    |

The IOKit and IOSurface rows show the fractal nature of this: a framework can exist on
both platforms while specific _headers_ within it are macOS-only. "The framework exists
on iOS" is not the same claim as "this include compiles on iOS".

## 3. The measurement lesson

Grepping for platform conditionals wildly overestimates a port. A real data point: an
early estimate of **"244 `__APPLE__`-family sites across 82 files"** needing review
turned into **six actual source fixes** to compile every library end to end. Most
existing `AK_OS_MACOS`-style sites were already correct for iOS, because macOS-only was
what they meant.

**Measure by building, not by grepping.** Configure the cross build, compile, and fix
the errors the compiler actually reports — in a well-factored codebase there are far
fewer than the grep suggests. Grep counts conditions; only the compiler counts defects.

## 4. Platform constraints that no macro can fix

These aren't conditional-compilation issues; they force design changes:

- **No `fork`/`exec`** — helper-process architectures must run services as threads
  handed a `socketpair()` FD (`service_main(int ipc_socket)`-style entry points), with
  per-process isolation features disabled.
- **No Mach bootstrap** — Mach-port IPC rendezvous has no registration mechanism;
  socket transports replace it.
- **No JIT** — a normal app cannot `mmap(MAP_JIT|PROT_EXEC)`; JIT tiers must be
  compile-time disabled in favor of interpreters. (A JIT that also spawns a separate
  compiler process trips _both_ prohibitions.)
- **`UIApplicationMain` never returns** — main-loop abstractions that expect to regain
  control after "run the app" don't map.

## The worst shape: a platform `#else` that returns a sentinel

Worse than a conditional that fails to compile is one that **succeeds and returns a wrong
value**. Watch for this pattern:

```c
#if   defined(OS_LINUX)   return gettid();
#elif defined(OS_WINDOWS) return GetCurrentThreadId();
#elif defined(OS_MACOS)   pthread_threadid_np(nullptr, &id); return id;   // not iOS!
#else                     return 0;                                       // <-- disaster
#endif
```

A real case cost an hour: on iOS the `#else` gave **every thread the ID 0**. Zero was also the
"invalid / no thread" sentinel, so a `is_current_thread()` helper returned false _on the very
thread that owned the object_. Every IPC connection then died on its first message with an
owner-thread assertion, in a stack that pointed at the messaging layer and gave no hint that a
platform macro was to blame. (`pthread_threadid_np` is Apple-wide and works fine on iOS.)

When auditing a codebase for a new platform, grep for platform chains whose fallback returns
`0`, `nullptr`, `false`, or an empty value rather than `#error`-ing. Those are the ones that
will greet you as a bizarre runtime failure a long way from the cause. Adding the `#error` is
usually a good upstream contribution in its own right.

## Gotchas

- CMake's `if (APPLE)` has the same ambiguity as `__APPLE__`; the iOS test is
  `if (IOS)` (true when `CMAKE_SYSTEM_NAME` is `iOS`), and order matters — an
  `elseif (APPLE)` above an iOS branch swallows iOS.
- Assembly with newer ISA extensions may need explicit `-mcpu` when the deployment
  target's default is older than the instructions used (observed: hand-written aarch64
  assembly using an ARMv8.3 instruction needed `-mcpu=apple-a12` to assemble for iOS).
