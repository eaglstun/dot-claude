---
semantic_id: "7T36nSu2sMoPrzBu2py4aebB2Su4oAAA"
related_ids:
  - "1nf9B0Put9rmL79tWhbwU0bkgVK40AAD"
  - "Zn7ezDKtmagPr1H2CxeKDLdD0bEXEAAC"
---
# The Xcode Metal debugger — and what of it survives a compute-only workload

Companion to `gpu-capture-and-shader-validation.md` (how to *take* a `.gputrace`) and
`command-buffer-errors-and-hangs.md` (what to do after a fault). This file is how to *read* a
trace.

Sources — Apple DocC JSON at `https://developer.apple.com/tutorials/data/documentation/<path>.json`:

- `xcode/metal-debugger` (the hub) · `xcode/analyzing-resource-dependencies` (the centerpiece)
- `xcode/analyzing-your-metal-workload` · `xcode/analyzing-memory-usage` · `xcode/optimizing-gpu-performance`
- `xcode/analyzing-apple-gpu-performance-using-{a-visual-timeline,counter-statistics}`
- `xcode/analyzing-apple-gpu-performance-using-{performance-heatmaps,shader-cost-graph}-a17-m3`
- `xcode/analyzing-draw-command-and-compute-dispatch-performance-with-{pipeline-statistics,gpu-counters}`
- `xcode/{inspecting-shaders,inspecting-the-bound-resources-for-a-command,inspecting-pipeline-states}`
- `xcode/debugging-the-shaders-within-a-draw-command-or-compute-dispatch`
- `xcode/{debugging-with-interactive-command-line-tools,investigating-gpu-issues-with-ai-agents}`
- `xcode/{building-your-project-with-embedded-shader-sources,naming-resources-and-commands}`
- `metal/{mtlhazardtrackingmode,mtlfence,mtlevent}` · <https://developer.apple.com/metal/tools/>

Video: [WWDC20/10605](https://developer.apple.com/videos/play/wwdc2020/10605/) (introduced the
Dependencies viewer) · [WWDC26/357](https://developer.apple.com/videos/play/wwdc2026/357/) ·
[WWDC26/388](https://developer.apple.com/videos/play/wwdc2026/388/)

**Part of the graph vocabulary below exists only in Apple's doc screenshots** (served from
`developer.apple.com/tutorials/images/com.apple.Xcode/…@2x.png`) and their callout labels, never in
prose. Those items are marked *screenshot-only*.

Fetched: 2026-08-19

---

## 0. Availability, and why there's none to quote

**These are UI-workflow articles: their DocC JSON carries `"role": "article"` and no platform block
at all (`variants: null`).** Every version or hardware gate in this file comes from prose in an
article body, from `developer.apple.com/metal/tools/`, or from a WWDC transcript — attributed each
time. Don't expect symbol-style availability metadata here; there is none.

---

## 1. The debugger as a system

> *"Unlike pausing at breakpoints during runtime, you can capture your Metal workload for multiple
> frames and then jump back and forth in time to explore the captured work. The Metal debugger
> enables you to explore the dependencies between passes, and offers insights for improving the
> performance of your app."*

The unit of work is **the trace**, not the breakpoint. Everything is post-hoc analysis of a
recorded `.gputrace`. Note that *"explore the dependencies between passes"* is one of only two
headline capabilities Apple names — a fair signal of how central the Dependencies viewer is meant
to be.

The hub organizes the toolset as a zoom ladder: **trace → pass → command → resource/shader → line
of MSL**. The Dependencies viewer sits on the "trace" rung and is the only viewer whose subject is
the **relationships between** passes rather than the contents of one.

The marketing page names a node vocabulary the DocC articles never do:

> *"The dependencies viewer … allows you to view relationships between **resources, passes,
> synchronization primitives, and individual encoder stages like vertex and fragment**."*

So fences and events are graph *citizens*, not edge decorations.

---

## 2. The Dependencies viewer

### 2.1 Getting there

Three routes: the **Show Dependencies** button on the Summary viewer, clicking any command buffer
or encoder in the Debug navigator, or a **Show in Dependencies** deep-link from an insight
elsewhere in the debugger.

### 2.2 The three detail levels are unnamed

**They are continuous zoom thresholds, not selectable modes, and Apple gives them no names.** The
article says only *"At the highest level…"*, *"As you zoom in to the next level…"*, *"As you zoom in
more…"*. The screenshots show **25% / 50% / 150%**. Don't invent labels like "Overview/Detail" —
there is no such control.

| Zoom | What appears |
| --- | --- |
| ~25% | Overall frame structure: command-buffer containers holding pass thumbnails, each with a **resource-count badge**, and whether data flows or synchronization exists between passes. |
| ~50% | Resources expand under each pass, each with a **consuming icon above** and **producing icon below** *(those two phrases are the official names, and appear only as screenshot callouts)*. |
| ~150% | Icons gain text labels ("Don't Care", "Clear", "Store", "Load"); large thumbnails; a **resource metadata** block (label, Attachment, Pixel Format, Dimensions, Allocated Size). Pass headers gain **GPU Time** and **Draws**. |

### 2.3 Two edge kinds — this is the core idea

> - *"**Solid lines** depict data flow. A previous pass produced data and a later pass consumes it."*
> - *"**Dashed lines** depict synchronization. There's no data flow, but there's a relationship
>   between the two passes."*

Apple's own example of the second: *"a render pass that clears an attachment on load has no data
dependency on any pass that previously modified the texture. However, that render pass needs to
wait until the previous passes finish modifying the texture — a synchronization."*

### 2.4 The three modes, and the asymmetry hiding in them

> - **All**: *"Shows all edges from synchronization primitives, and tracked and untracked resources."*
> - **Synchronzation** *(sic — Apple's live typo)*: *"Shows dashed synchronization edges from
>   synchronization primitives and tracked resources."*
> - **Data Flow**: *"Shows solid data-flow edges from tracked or untracked resources."*

Those three sentences are the densest thing on the page. Read carefully, they establish that edges
have **three provenances** — synchronization primitives, **tracked** resources, **untracked**
resources — distributed asymmetrically:

| Provenance | Synchronization edges | Data-flow edges |
| --- | --- | --- |
| Synchronization primitives (`MTLFence`, `MTLEvent`) | ✅ | ✖ |
| **Tracked** resources | ✅ | ✅ |
| **Untracked** resources | ✖ | ✅ |

**Why that matters for a hand-synchronized backend:** if your buffers are
`MTLHazardTrackingMode.untracked` (typical for a big scratch arena or heap suballocation), they
contribute **data-flow edges only**. So in **All** mode, any *dashed* line near an untracked
resource must come from **your own** fence or event. That's a genuinely useful invariant for
auditing manual synchronization, and it falls straight out of Apple's mode definitions.

Also worth carrying, from `MTLHazardTrackingMode`:

> *"**Metal doesn't apply hazard tracking to commands you submit to an `MTL4CommandQueue`, even when
> those commands use tracked resources.**"*

Under Metal 4, *all* synchronization is explicit — so every dashed edge should be yours.

### 2.5 Consuming and producing actions

> *"For textures in a render pass, the actions refer to the load and store actions for each
> attachment. … **Otherwise, the Dependencies viewer annotates the actions with generic
> read-and-write operations.**"*

That "otherwise" is what makes the viewer usable at all for compute (§3).

Glyph vocabulary, legible only in the screenshots:

| Glyph | Meaning |
| --- | --- |
| `//` diagonal hatch | **Don't Care** (`.dontCare` load or store) |
| `⌄⌄` double chevron | **Load** / **Store** |
| `✕` | **Clear** |

The hatch is deliberately the "empty" glyph and load/store the solid one, so a bandwidth-wasteful
pass reads as a wall of chevrons at a glance. Multisample: with
`.storeAndMultisampleResolve` both textures show a store; with `.multisampleResolve` the
multisample texture shows don't-care and the resolve texture shows store — expressed as *two nodes*,
not a distinct glyph.

### 2.6 Navigation

- **Resource pile** *(screenshot-only term)* — the viewer keeps "a few interesting resources"
  visible and hides the rest in a stacked-cards node with a count badge. Click it for a popover
  with a **Filter** field and a per-row **pin** toggle. **Apple documents no rule for what counts
  as "interesting"** — treat the heuristic as opaque.
- **Select a pass** → the sidebar *"suggests the pass that most recently modified"* each consumed
  resource, and *"the passes that later consume"* each produced one. This is the workhorse query
  for chasing an unexpected edge.
- **Select a resource** → related resources highlight: *"when you select a texture view, it
  highlights the parent textures. When you select a heap, it highlights the resources from the
  heap."* Heap highlighting is directly useful for suballocated compute backends.
- **Filter** collapses the graph to matching passes; *"when filtering by a resource, you can find
  passes that consume or produce the resource."* **Search** (Find ▸ Find) steps through matches
  with prev/next arrows and include/exclude per term.
- The sidebar's per-resource card carries a **Dependency** field with values *"Adds
  synchronization"* and *"Has data flow"* **on separate lines** — the direct per-edge answer to
  "why does this edge exist", and the only place the two properties are stated independently. It
  appears in no prose. *(screenshot-only)*

### 2.7 Insights — four categories, no published rule list

The article says only: *"Click the Insights button in the bottom right corner."* The substance is
in `analyzing-your-metal-workload`, which defines four categories: **Memory**, **Bandwidth**,
**Performance**, **API Usage**.

**There is no enumerated catalogue of individual insight rules anywhere in Apple's docs.** Say so
rather than implying a fixed list. The concrete diagnostics that can be attested:

| Diagnostic | Category | Source |
| --- | --- | --- |
| Stored-but-never-used attachment → *"consider changing the store action to 'Don't Care'"* (~11 MB saved in Apple's demo) | Bandwidth | WWDC20 |
| Unnecessary depth pre-pass — TBDR already does hidden-surface removal | Performance | WWDC20 |
| **"Encoder '<name>' has N redundant Buffer bindings"** | API Usage | screenshot |
| Wrong storage mode → switch to memoryless, 10.2 MB saved | Memory | article |
| Unused resources | Memory | article |

**"Unused" is rendered as the absence of an outgoing edge, not as a badge.** WWDC20, verbatim:
*"the depth and stencil textures are both set to 'Store,' but **there's no line coming out of
them**, so they're not actually being used by any other render command encoder in this frame."*
The badge is the separate insight marker — a small purple triangle on the pass, gaining a count at
high zoom.

---

## 3. The compute verdict

**Yes, the Dependencies viewer works for a pure `MTLComputeCommandEncoder` + `MTLBuffer` workload,
and yes it shows buffer-to-buffer dependencies between dispatches — but Apple never says so
directly, and roughly a third of the article is inert for you.**

### What is supported

**Compute passes are first-class nodes.** The article's units are "passes" and "command encoders",
never narrowed to render, and its one compute sentence confirms a compute pass can be an edge
endpoint: *"a compute pass reading from a texture that a previous render encoder wrote has data
flow between the two passes."*

**Buffers are first-class resources.** Two independent supports: the *"Otherwise… generic
read-and-write operations"* branch, and direct screenshot evidence — the resource-pile popover
lists `LightPositions0` and `LightData`, two `MTLBuffer`s with their own glyph, in the same
pinnable list as the textures.

**Buffer→buffer edges between dispatches follow from the edge definitions.** *"A previous pass
produced data and a later pass consumes it"* restricts neither resource type nor encoder type.

> **Evidentiary status, stated plainly:** Apple publishes **no** compute→compute worked example,
> **no** compute-only screenshot, and never writes the sentence "the Dependencies viewer shows
> buffer dependencies between compute dispatches." The above is a sound reading of the general
> definitions plus screenshot evidence — not a quotation. Don't present it as one.

**Fence/event edges apply directly** — `MTLComputeCommandEncoder` has `updateFence`/`waitForFence`,
`MTLCommandBuffer` has `encodeSignalEvent`/`encodeWaitForEvent`. For an over-synchronized compute
chain, **Synchronzation** mode is the right lens: ordering constraints stripped of data flow.

### What is render-only furniture

- **The entire load/store apparatus.** Load/store actions belong to `MTLRenderPassDescriptor`
  attachments. In a trace with no render passes, the `//` / `⌄⌄` / `✕` glyphs never appear, the
  MSAA paragraph is moot, and the sidebar's Load Action / Store Action rows have no analogue.
- **The Bandwidth category's marquee diagnostic** — the store-action fix that saves 11 MB in
  Apple's demo — **has no compute equivalent.** That is the single biggest chunk of the tool's
  advertised value that simply doesn't apply.
- **Pass thumbnails.** *"Each pass includes a thumbnail preview of its work."* There is nothing to
  preview for a kernel writing fp16 activations. Apple never describes what a compute pass renders
  as, so the lowest zoom level is probably much less useful for you — *expected, unverified.*
- **Generic read/write icons are never illustrated anywhere.** Every published screenshot is a
  render trace. What the compute annotations actually look like is genuinely undocumented.
- Vertex statistics, "Draws N", Draw ID heat maps, the depth-prepass insight, and
  "Synchronization (wait pixel)" in pipeline statistics.

### Does it flag redundant *compute* work?

**Apple never says, and one piece of wording cuts against it.** The Performance category is defined
as recommendations *"by avoiding expensive and redundant operations **in the rendering
pipeline**"* — the only category scoped to rendering by its own wording, and the one that would
house "this dispatch produces a buffer nothing reads." **Don't promise a reader that redundant
compute work gets flagged.**

What *is* supportable:

- **Unused resources are flagged type-agnostically** — *"showing you all the unused resources in
  your frame"*, and the Memory viewer's **Use** category *"tracks whether commands accessed
  resources in the captured frame."* An unread output buffer should surface, and structurally the
  no-outgoing-edge mechanism applies verbatim to a buffer node.
- **Redundant buffer bindings ARE flagged** — the API Usage exemplar is about *buffers*. A compute
  encoder re-binding the same weight buffers before every dispatch is squarely in scope. This is
  the insight a matmul-heavy backend is most likely to trip.
- **Over-serialization is diagnosed by the Performance timeline, not here.** *"If you observe
  nonoverlapping work, check whether your GPU work is overserialized. Also, use concurrent compute
  passes wherever possible so dispatches that touch different resources can execute concurrently."*
  The Dependencies viewer tells you what the constraints *are*; the timeline tells you whether
  they're costing you. Open both.

---

## 4. Sibling viewers, with compute applicability

| Viewer | Compute verdict | Gate |
| --- | --- | --- |
| **Dependencies** | **Useful** — nodes, buffer resources, both edge kinds, modes, heap highlighting, pass attribution. Load/store half is dead. | none |
| **Memory viewer** | **Fully useful** — buffer Length vs Allocated Size, heap Used Size + Hazard Tracking Mode, Use category, group by **Command Encoder** *"to understand the behavior of your specific compute and render passes"*, CSV export. | none |
| **Bound Resources** | **Fully useful** — has a dedicated compute-pass section list; the **Access** column and **Accessed** filter answer "did the kernel actually touch this binding" (explicitly bindless-aware). | none |
| **Pipeline State viewer** | **Useful** — explicitly covers `MTLComputePipelineState`. | none |
| **Buffer inspection** | **Fully useful** — your primary data-verification tool. | none |
| **Performance timeline** | **Useful** — dedicated **Compute** track, occupancy/limiter/bandwidth counters, concurrency guidance. | Apple GPUs; profiling |
| **GPU counters** | **Mostly useful** — the per-command article is literally titled "…and compute dispatch performance". Vertex counters dead. | Apple GPUs; profiling |
| **Pipeline statistics** | **Mostly useful** — ALU / Memory / Control flow / **Sync (barrier)** / **Sync (atomics)** apply; Sync (wait pixel) doesn't. | profiling |
| **Shader editor / profiler** | **Fully useful** for kernels — per-line weights + pie charts. | embedded sources; profiling; **pie charts need Apple GPU family 4+** |
| **Shader debugger** | **Fully useful** — explicitly supports compute dispatch, **auto-selects the first threadgroup**, region of interest = other threads in the threadgroup, selective function debugging. | embedded sources |
| **Performance heat maps** | **Useful, with a sharp caveat** — *"available for render command encoders, render pipeline states, and **compute dispatches**. However, they **don't support compute command encoders or compute pipeline states**."* Select an individual dispatch. Compute pixel = thread location, or a **SIMD group** past 8192. **Inactive Threads** directly diagnoses bad grid sizing. | **A17 Pro / M3+**; profiling |
| **Shader cost graph** | **Useful** — *"Selecting a compute pipeline state shows the compute shader cost graph."* Pipeline states only. | **A17 Pro / M3+**; profiling |
| **Attachments / geometry viewer / visual artifacts** | **Not applicable.** | — |

Note the asymmetry worth not conflating: **heat maps exclude compute pipeline states; the shader
cost graph requires them.** Both are A17/M3+.

**The compute story across the debugger as a whole is much stronger than inside the Dependencies
article specifically.** The shader debugger, heat maps, cost graph, bound resources, and memory
viewer all name compute explicitly. Dependencies is the outlier — architecturally type-agnostic,
written up almost entirely through a render lens.

---

## 5. What the capture must contain

| To use | You need |
| --- | --- |
| Dependencies, Memory, Bound Resources, Pipeline State, buffer/texture inspection | nothing beyond a valid `.gputrace` |
| Performance timeline, counters, pipeline statistics, per-line shader stats | **profile** the trace (Profile after Replay, or Profile on the Summary viewer). Without it *"the performance section doesn't show any statistics."* |
| Shader editor, shader debugger | **embedded shader sources** — Produce Debugging Information → *"Yes, include source code"* |
| A legible graph at all | **labels** — `MTLResource.label`, `pushDebugGroup`/`popDebugGroup`, `insertDebugSignpost`. Unlabeled, the graph is a wall of "MTLBuffer 8". |
| Replay | *"GPU trace files are only compatible with devices of the same type, the same GPU, and the same operating system."* Export with **Embed performance data** to open a trace on any Mac. |

**The capture-scope trap for a headless compute workload.** If `defaultCaptureScope` is nil,
*"Xcode defines the default capture scope using drawable presentation boundaries."* A compute
library never presents a drawable, so the default boundary **never fires** — select **command
queue**, **device**, or a custom scope instead. (Apple doesn't spell out this consequence, but its
own guidance does say "your rendering **or compute** loop.") The env-var route
`MTL_CAPTURE_ENABLED=1` (macOS 14+) is the practical one for a CLI test harness; see
`gpu-capture-and-shader-validation.md`.

One profiling subtlety that changes what timings mean: the debugger profiles in **Concurrent** mode
by default. **Serial** mode *"forces each pass to run only after the previous pass finishes, which
adds precision to the data report for each pass without overlap, but it doesn't represent runtime
performance."*

---

## 6. `gpudebug` — macOS 27, and not here yet

Verified absent on Xcode 26.6: `gpucapture`, `gpudebug`, `metalperftrace` are all missing, and
`man gpudebug` has no entry. WWDC26/357 states the gate:

> *"**macOS 27 introduces new command-line tools which support fully autonomous agent workflows:
> `gpucapture` for capturing a GPU frame, and `gpudebug` for analyzing it.**"*

Session model: `gpudebug -t trace.gputrace` creates a numbered session with a REPL; sessions
persist across disconnects (`-s <id>` to reattach, `exit --terminate` to end). `--oneshot` *"pays
the full trace load cost on every invocation"*, so reuse a session for anything multi-step. Remote
devices need Xcode running for device discovery.

Tree roots: `commands`, `performance`, `api_calls`, `resources`. Navigation `go`/`list`, inspection
`info`, extraction `fetch`, traversal `next`/`prev`, plus bidirectional draw↔API-call links.

**It has no dependency-query command.** No `deps`, `producers`, or `consumers` in anything Apple
publishes. WWDC26 narrative mentions inspecting *"data flow through the pipeline"*, but that's
prose, not a documented command — treat "gpudebug can query dependencies" as unsupported. Also:
every documented example is a render scenario, and `fetch` is only ever shown writing attachment
PNGs, though buffer rows do advertise a `fetch` action with undocumented output format.

---

## 7. Acting on what you see

Apple ships no "fix your dependency graph" article. What exists, collected:

- **Buffer consolidation** — the clearest actionable statement in the corpus, and the only one
  connecting allocation strategy to *dependency-tracking cost*: *"If you see many small buffers,
  consolidate those that the system uses together into a single buffer, or allocate the buffers on
  a heap. These alternative allocation strategies save memory and **require less work to track
  dependencies** between commands accessing those resources."*
- **Concurrency over merging** — *"use concurrent compute passes wherever possible so dispatches
  that touch different resources can execute concurrently."* And *"Avoid too many small passes.
  There's setup time between passes."*
- **Storage modes / volatility** — switch to memoryless where valid; *"If you think that you might
  use a resource in the future that you're not currently using, mark it as volatile rather than
  simply releasing it."*
- **Removing redundant barriers: not documented.** No article discusses dropping fences or events
  based on what the graph shows. The nearest thing is `MTLHazardTrackingMode`'s own trade-off:
  *"You can improve the runtime performance of commands you send to an `MTLCommandQueue` by
  creating resources with `MTLHazardTrackingMode.untracked` and synchronizing access to those
  resources yourself."* That's an API doc, not a workflow.

---

## 8. Honest gaps

1. **The three detail levels have no names** — zoom thresholds (~25/50/150%), not modes.
2. **No enumerated insight catalogue exists** — four categories, no rule list.
3. **"Synchronzation" is Apple's live typo** in the mode list.
4. The **gear button** in the Dependencies bottom bar is documented nowhere.
5. **Generic read/write icons are never illustrated** — the compute glyphs are unknown.
6. **Compute pass thumbnails are undescribed.**
7. **Compute-only workloads are never addressed as a case** — not one sentence, screenshot, or
   example anywhere in the Metal-debugger tree covers a trace with zero render passes.
8. **"Redundant compute work" is not a documented diagnostic.**
9. **Barrier/fence-removal guidance does not exist.**
10. **These articles carry no availability metadata at all.**
11. **`gpudebug` has no dependency-query command.**
