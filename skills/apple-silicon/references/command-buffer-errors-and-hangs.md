---
topic_id: "v2:MMOG"
topic_path: "metal-compute/failure-diagnosis"
semantic_id: "njftVwNlscKcPR10unu9T8PB7XKRwAAM"
related_ids:
  - "1nf9B0Put9rmL79tWhbwU0bkgVK40AAD"
  - "7RdpVwltrBr8Eyw2j-Xxj5KFXR17wAAN"
---
# Command-buffer errors & GPU hangs (failure diagnosis)

What a command buffer's lifecycle looks like, how the GPU reports runtime failures, and
— the repo-specific punchline — **this backend never checks any of it today**, so a
GPU-side fault currently surfaces as silent garbage output. This card is the
debugging-time bolt-on.

Sources (Apple DocC JSON, fetched 2026-06-11): `MTLCommandBuffer.status`, `.error`,
`addCompletedHandler(_:)`, `MTLCommandBufferStatus` (+ case pages),
`MTLCommandBufferError` (`mtlcommandbuffererror-swift.struct` + `/code`),
`MTLCommandBufferDescriptor.errorOptions`, `MTLCommandBufferErrorOption`,
`MTLCommandBufferEncoderInfo` — under
<https://developer.apple.com/tutorials/data/documentation/metal/...json>.

## The status lifecycle (`MTLCommandBufferStatus`)

`notEnqueued → enqueued → committed → scheduled → completed | error`

DocC: a buffer's state "can only change to a state below it in the table, and ends its
life cycle at either `completed` or `error`." The first two states are where encoding
happens; `committed` means the queue is resolving dependencies; `scheduled` means
resources are ready and it's waiting on the GPU; `error` is "the unsuccessful, final
state … the GPU stopped running the buffer's commands because of a runtime issue."

In this backend every buffer goes notEnqueued → committed in one breath
(`commit_command_buffer()`, no explicit `enqueue`), and only `flush()` ever observes a
final state — implicitly, via `waitUntilCompleted`, **which returns the same way for
`completed` and `error`.**

## `.error` and the real error codes

`MTLCommandBuffer.error` — "remains nil unless the GPU can't successfully run the
command buffer." The codes (`MTLCommandBufferError.Code`, DocC-verified list):

`none`, **`timeout`** (system interrupted/terminated the buffer before it finished — the
GPU-hang watchdog), **`pageFault`** ("the command buffer generated a page fault the GPU
can't service" — the classic kernel-OOB-pointer outcome), `notPermitted`,
`outOfMemory`, `invalidResource`, `memoryless`, `deviceRemoved`, `stackOverflow`,
`accessRevoked`, `internal`. Domain: `MTLCommandBufferErrorDomain`.

A hung/faulting kernel typically lands as `timeout` or `pageFault`, and macOS may also
log "GPU Restart"/discarded-work messages to the console; subsequent command buffers on
the queue can then error in cascade — so **the first error after a flush is the one
that matters**. (The cascade/console behavior is field knowledge, not DocC-verifiable;
the codes above are.)

## Extended fault info: `errorOptions` + encoder infos

By default "a GPU driver doesn't report additional error information." To get per-encoder
blame, build buffers from a descriptor:

```swift
let desc = MTLCommandBufferDescriptor()
desc.errorOptions = .encoderExecutionStatus
let cb = commandQueue.makeCommandBuffer(descriptor: desc)!

cb.addCompletedHandler { cb in
    guard let error = cb.error as NSError? else { return }
    if let infos = error.userInfo[MTLCommandBufferEncoderInfoErrorKey] as? [MTLCommandBufferEncoderInfo] {
        for info in infos where info.errorState == .faulted {
            print("\(info.label) faulted!", info.debugSignposts)
        }
    }
}
```

`MTLCommandEncoderErrorState` — **iOS 14 / macOS 11**; raw values from the SDK header, which the
doc page doesn't publish:

| Case | Raw | Meaning |
| --- | --- | --- |
| `.unknown` | 0 | *"the error information was likely not requested"* |
| `.completed` | 1 | ran to completion |
| `.affected` | 2 | hit by an error; may or may not have caused it; **did not execute in full** |
| `.pending` | 3 | never started |
| `.faulted` | 4 | **these commands caused the error** |

**`.faulted` is the culprit; `.affected` is collateral damage** — debugging the wrong encoder is
the easy mistake here.

**If you don't set the option, the `userInfo` key does not exist at all** (header). Its absence
means "you didn't ask," not "nothing faulted."

**Cost.** Docs: *"can slightly reduce your app's CPU runtime performance."* The header is
blunter: *"may increase CPU, GPU, and/or memory overhead on some platforms; testing for impact
is suggested."* WWDC20 frames it as low enough to consider **shipping**, per command buffer,
after measuring — unlike the validation layers, which are development-only.

**Xcode shortcut:** ticking **Shader Validation** in Edit Scheme ▸ Run ▸ Diagnostics also turns
on enhanced command buffer errors for *all* command buffers — no descriptor changes needed.

As noted below, this backend sets no labels on buffers or encoders today (`mtlbuffer-api.md` on
`label` being the free win), so encoder infos come back anonymous until labels are added. **This
feature is worth exactly as much as your naming discipline.**

## `.deviceRemoved` is dead on Apple silicon

Worth deleting rather than handling. `.deviceRemoved` has a **macOS-only** availability block,
now carrying this deprecation message:

> *"MTLCommandBufferErrorDeviceRemoved cannot occur on Apple Silicon"* — deprecated at macOS 27.0.

Device removal was an eGPU-era Intel-Mac failure mode. The `MTLDeviceWasRemovedNotification`
family (`MTLCopyAllDevicesWithObserver`) is likewise macOS-only and irrelevant to any
Apple-silicon-only or iOS target.

Two other per-case availability notes: `.stackOverflow` is iOS 15 / macOS 12 (check
`MTLComputePipelineDescriptor.maxCallStackDepth`); `.memoryless` is iOS 10 / macOS 11.

## Shader logging — `os_log` from inside a kernel

**Metal 3.2+, iOS 18 / macOS 15 / visionOS 2.** Print from GPU code with no capture and no
Xcode — the tool that did not exist when the rest of this card was written.

Compile with logging enabled (any one of these):

```bash
xcrun metal -std=metal3.2 -fmetal-enable-logging -o out.metallib in.metal
```
- Xcode build setting **Other Metal Compiler Flags** → `-fmetal-enable-logging`
- or `MTLCompileOptions.enableLogging = true`

```metal
constant os_log logger("com.metal.xyz", "abc");   // subsystem, category
[[kernel]] void myKernel(uint i [[thread_position_in_grid]]) {
    if (i == 7) { logger.log_info("Hello There!"); }
}
```

```swift
let d = MTLLogStateDescriptor()
d.bufferSize = 16 * 1024
d.level = .debug
let logState = try device.makeLogState(descriptor: d)
logState.addLogHandler { subsystem, category, level, message in print(message) }
commandBufferDescriptor.logState = logState        // or MTLCommandQueueDescriptor.logState
```

`MTLLogLevel`: `.undefined`, `.debug`, `.info`, `.notice`, `.error`, `.fault`.

Process-wide alternative, no code changes: `MTL_LOG_LEVEL` (default `MTLLogLevelDebug`),
`MTL_LOG_BUFFER_SIZE` (default **1024 bytes**, min 1 KB, max 1 GB), `MTL_LOG_TO_STDERR=1`.
*"If you define only one of the variables, the other assumes its default value."*

**Three constraints that bite:**

1. **The default buffer is 1 KB**, and *"when the log buffer reaches its capacity, the system
   discards any subsequent messages."* A chatty kernel truncates silently.
2. **Gate your logging** — it runs per thread. An ungated `log_info` across a million threads is
   a million messages.
3. **Ordering is not guaranteed.** Draining happens only after the command buffer finishes, so
   *"the system may not maintain the sequence of messages."* Log an index; don't infer order.

Keep subsystem + category + format under **1024 characters** per message or it truncates.

### Reading shader-validation faults programmatically

Separate and older — **iOS 14 / macOS 11**, not the 18/15 feature above:

```swift
var MTLCommandBuffer.logs: MTLLogContainer { get }   // valid only after execution finishes

protocol MTLFunctionLog
var type: MTLFunctionLogType { get }                 // only case: .validation
var debugLocation: (any MTLFunctionLogDebugLocation)? { get }
var encoderLabel: String? { get }
var function: (any MTLFunction)? { get }
```

This is how a **headless test rig** reads Shader Validation faults (see
`gpu-capture-and-shader-validation.md`) and fails loudly in CI instead of quietly logging: in
`addCompletedHandler`, print `log.encoderLabel` and `debugLocation.functionName:line:column`.

## `makeCommandQueue` has no error channel

```swift
func makeCommandQueue() -> (any MTLCommandQueue)?                    // documented as maxCommandBufferCount 64
func makeCommandQueue(maxCommandBufferCount: Int) -> (any MTLCommandQueue)?
func makeCommandQueue(descriptor: MTLCommandQueueDescriptor) -> (any MTLCommandQueue)?  // iOS 18 / macOS 15
```

Optional, never throwing, no published reason codes. `nil` is all you get.

Related and easy to misread as a slow GPU: `makeCommandBuffer(descriptor:)` *"blocks the calling
CPU thread when the queue doesn't have any free command buffers, and returns after the GPU
finishes executing one."* A mysterious stall at command-buffer creation is **queue backpressure**.

## What the repo does today (verified by grep, 2026-06-11)

`grep -n "status\|error\|addCompletedHandler" src/metal/*.mm`: the **only** waits are
`waitUntilCompleted` in `flush()` (`src/metal/device.mm`); `NSError**` checking exists
only for _pipeline/library creation_ in `MetalContext` — **no code reads
`commandBuffer.status` or `.error`, and no `addCompletedHandler` exists.** A pageFault
in `ct2_gemm_s8` would complete the flush normally and the CPU would read whatever is
in the output buffer.

The 5-line check worth adding to `flush()` when debugging (MRC, matches house style):

```objc
[to_wait waitUntilCompleted];
if (to_wait.status == MTLCommandBufferStatusError) {
  NSError* err = to_wait.error;
  throw std::runtime_error(std::string("Metal: command buffer failed: ")
      + (err ? [[err localizedDescription] UTF8String] : "(no error object)"));
}
```

Caveat: `g_last_committed` is only the _last_ buffer; an earlier buffer in the FIFO
could be the one that errored. For full coverage during a hunt, add an
`addCompletedHandler` in `commit_command_buffer()` instead — DocC explicitly calls the
completion handler "a good place to check the status property" — logging
`status == error` with the op's pipeline name. Handlers run on a driver CPU thread;
keep them to logging.

## Triage order for "output is garbage" on Metal

1. **Stale read** (most common here): a CPU read without `metal::flush()` — the value
   changes run-to-run or matches the _previous_ step. See
   `storage-and-synchronization.md`; also recall the project gotcha that mid-pipeline
   CPU reads of MPS-GEMM output are unreliable — read at layer boundaries.
2. **Error'd command buffer**: add the status check above. If it fires with
   `pageFault`/`invalidResource` → a binding or OOB bug; with `timeout` → a hang
   (infinite loop in a kernel, or a barrier not reached by all threads — see
   `threadgroup-and-simdgroup-synchronization.md`).
3. **Kernel OOB that doesn't fault** (scribbles inside a mapped buffer): the status
   check stays clean. Run with `MTL_SHADER_VALIDATION=1` and capture a `.gputrace` —
   `gpu-capture-and-shader-validation.md` is the recipe.
4. **Numeric, not memory** (NaN/overflow): none of the above will fire — use the
   CPU-ref bisection + layer-boundary tripwire approach that found the Gemma2 tanh NaN
   (`math-functions-and-numeric-parity.md`, `common-functions.md`).

### Worked example: the CTranslate2 Metal backend

- The only completion point is `metal::flush()` in `src/metal/device.mm`
  (`g_last_committed` + `waitUntilCompleted`); `commit_command_buffer()` is where a
  debugging `addCompletedHandler` belongs. Neither checks `status`/`error` today — by
  design kept minimal, this card is the opt-in.
- Buffers are created bare via `[get_command_queue() commandBuffer]`
  (`new_command_buffer()`, `src/metal/device.mm`) — switching to
  `commandBufferWithDescriptor:` with `errorOptions` is a 3-line debugging change at
  that single choke point.
- Cross-refs: stale-read mechanics in `storage-and-synchronization.md`; OOB tooling in
  `gpu-capture-and-shader-validation.md`; why per-op buffers exist at all in
  `dispatch-overlap-and-perf-model.md`.
