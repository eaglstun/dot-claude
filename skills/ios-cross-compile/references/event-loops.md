---
semantic_id: "q4aLc_JrE1qUmBsocjomM4gnynPFoAAI"
related_ids:
  - "C4SLc_J7E1q2mIluPnNyKwQPy1ewAAAD"
  - "icW7MvLeG0v8iLsqdhRmM5gX1VGYsAAD"
---
# Bridging a portable event loop onto the iOS run loop

Provenance: done for real (2026) porting a C++ engine's `EventLoop` abstraction to iOS, and
verified on the simulator with a timer/deferred-invoke smoke test.

Most cross-platform C++ frameworks own their main loop: some `exec()` runs until told to
stop. **iOS does not let you have that.** `UIApplicationMain()` takes over the main thread's
`CFRunLoop` and never returns. So the loop abstraction has to be bridged onto a run loop that
somebody else is already running, rather than driving one itself.

## The good news: CoreFoundation is fully present on iOS

If the macOS backend is written in CoreFoundation rather than AppKit — `CFRunLoopTimer`,
`CFSocket`, `CFRunLoopSource`, `CFFileDescriptor`, kqueue signal handling — then nearly all of
it ports **unchanged**. In the case measured, a 496-line macOS backend had exactly one
Cocoa-only function in it. Read the macOS backend before assuming a rewrite; you are probably
looking at a rename plus four methods.

What genuinely differs is only the loop-control surface:

| Method                 | macOS (AppKit)                      | iOS                                           |
| ---------------------- | ----------------------------------- | --------------------------------------------- |
| `exec()`               | `[NSApp run]`                       | `while (!exit_requested) pump(WaitForEvents)` |
| `pump()`               | `[NSApp nextEventMatchingMask:...]` | `CFRunLoopRunInMode(mode, interval, true)`    |
| `quit()`               | `[NSApp stop:nil]`                  | own flag + `CFRunLoopStop()`                  |
| `was_exit_requested()` | `![NSApp isRunning]`                | own flag                                      |
| "wake the loop" poke   | post a dummy `NSEvent` to `NSApp`   | `CFRunLoopWakeUp()`                           |

## Ordering rules that bite

- **Install the loop manager first, before anything else.** These frameworks typically lazily
  construct a default (Unix/`select`) manager the first time anything asks for the current one,
  and then the real `install()` asserts because something already exists. It must be the first
  statement in `main`, before any timer, socket, or loop object is touched.
- **A loop object usually must still exist on the main thread, even though nothing calls
  `exec()` on it.** Framework code reaches for "the current event loop" constantly — nested
  spin-until helpers, deferred invocation, timer registration — and dereferences it. Construct
  it and let it live forever; just never run it.
- Check what the application-level `execute()`/`run()` entry point does besides calling
  `exec()`. If it does real setup, that setup has to move somewhere that still happens.

## `pump()` must work standalone

Do not implement `pump()` as "a step of `exec()`". Nested/reentrant waiting helpers (spin
until a promise resolves, run a nested modal loop) call `pump()` directly with no `exec()`
anywhere on the stack. The shape that works:

```cpp
size_t pump(PumpMode mode)
{
    auto processed = queue.process();
    auto interval = mode == PumpMode::WaitForEvents ? 1.0e10 : 0.0;
    CFRunLoopRunInMode(kCFRunLoopDefaultMode, interval, /* returnAfterSourceHandled */ true);
    return processed + queue.process();
}
```

Drain the framework's own event queue on **both** sides of the run-loop turn — the run loop
turn is what generates the new events. A huge interval stands in for "wait indefinitely";
`returnAfterSourceHandled = true` makes it come back as soon as it has something.

`exec()` is then just the reference loop, and stays worth implementing: secondary threads that
run their own loop need it even though the main thread never will.

## Register timers on `kCFRunLoopCommonModes`, not the default mode

UIKit switches the main run loop into **tracking mode** while the user is scrolling or
dragging. A timer added only to `kCFRunLoopDefaultMode` silently stops firing for the whole
duration of the gesture and resumes when the finger lifts. This is a classic iOS bug that no
amount of desktop testing will surface — the app just appears to freeze mid-scroll.

## Waking the loop is not the same as draining the queue

The subtlest thing in this port. A "an event was posted" hook that only calls
`CFRunLoopWakeUp()` is **not** sufficient on iOS.

On macOS it can appear to work, because `[NSApp run]`'s loop drains the framework's event
queue as a side effect of running. With no NSApp, nothing does, so posted events sit in the
queue until something unrelated happens to process them — producing hangs and "events arrive
late, in bursts, when I touch the screen" symptoms.

The correct shape, which Qt-style backends also use: keep a per-thread `CFRunLoopSource` whose
perform callback drains the queue, then

```cpp
CFRunLoopSourceSignal(source);
CFRunLoopWakeUp(run_loop);
```

Signal _and_ wake. Signalling alone marks the source ready but a sleeping loop will not notice
until something else wakes it.

## CFSocket identity is per descriptor, not per watcher

If you back a framework's "watch this fd" abstraction with `CFSocket`, know that
`CFSocketCreateWithNative` **returns any CFSocket that already exists for that descriptor and
ignores the callback types and context you passed**. A second watcher on the same fd silently
gets the first one's socket and never fires.

This is easy to miss because most fds only ever get one watcher. It surfaces the first time
something wants read *and* write on one socket — a curl multi-handle integration is the classic
case. The symptom is maximally unhelpful: the connection succeeds (the write watcher was
registered first and works), then the transfer hangs forever with no error and no timeout,
because the read watcher was never really registered.

Worse, if disabling a watcher maps to unregistering, invalidating "the" CFSocket for the fd kills
notification for the other direction too.

Key the state **by descriptor**: one CFSocket per fd created with both callback types, a record of
which watcher owns each direction, `CFSocketEnableCallBacks`/`CFSocketDisableCallBacks` per
direction, and `CFSocketInvalidate` only when the last one goes. (Per-thread kqueue plus
`CFFileDescriptor` is the other way out, with no per-fd uniqueness rule.)

## A watcher's callback may destroy the watcher

Dispatch through a **strong** reference, not a weak one. Event callbacks legitimately tear down
the thing being called back — curl reports `CURL_POLL_REMOVE` from inside the very callback whose
socket it is removing. If the callable is owned by the object being destroyed, it gets freed
mid-execution. A `std::function` would be undefined behaviour here; a checked implementation traps
instead, which is how this one announced itself:

```
VERIFICATION FAILED: may_defer || !called_from_inside_function
```

Hold the reference for the whole dispatch and let it drop afterwards.

## Verifying it

You cannot eyeball an event loop. Use a temporary smoke test before wiring anything real to
it, and delete it afterwards:

1. A repeating timer that logs a counter — proves `CFRunLoopTimer` bridging and that the
   framework's timer registration reaches the run loop.
2. One deferred/queued invocation that logs — proves the source-signal path and the queue
   drain.

Run it with `xcrun simctl launch --console-pty booted <bundle-id>` to see `stdout`. If the
timer ticks but the deferred invoke never runs, the wake-vs-drain bug above is what you have.

## When the engine runs but nothing appears on screen

Porting a browser-engine-shaped codebase to a new UI, expect the platform layer to owe the engine
some state that has a **safe-looking default which silently disables rendering**. Two real cases,
both of which produced no error at all:

- **Visibility.** The document's visibility state defaulted to *hidden*, and the rendering step of
  the event loop skips hidden documents. The page loaded, parsed, and reported its title, while
  the render pass ran forever over an empty list. Desktop UIs send this from their window
  show/hide events; a new UI has to find the equivalent moment (on UIKit, `didMoveToWindow`).
- **Display refresh rate.** The compositor's frame scheduler was never started because nobody told
  it the display's refresh rate, so frames could be recorded and never presented.

The general shape: **grep the existing UI implementations for every call they make to the engine
that your new one does not.** A missing "tell the engine about the platform" call is invisible —
no error, no warning, just a component quietly deciding it has no work to do.

When you do have to debug it, instrument the pipeline **in order, from the engine outward**, and
find the first stage that never runs. Guessing at the visible end (the blit) wastes time when the
break is six stages upstream.
