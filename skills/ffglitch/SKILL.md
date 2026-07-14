---
name: ffglitch
version: 1.0.0
public: true
description: >-
  Glitch-art multimedia bitstream editing with FFglitch (Ramiro Polla). Edit codec
  internals (motion vectors, quantizers, macroblocks, DCT/DC coefficients) WITHOUT
  re-encoding. Use when the user wants to glitch/databend a video or JPEG/PNG, manipulate
  motion vectors, datamosh, pixel-sort, corrupt-but-keep-playable a bitstream, prep a
  glitch-friendly file (forced MVs, infinite GOP), perform live glitches (MIDI/keyboard),
  or mentions ffedit / ffgac / fflive / FFglitch.
semantic_id: "4xVLsTcOCiEL5CGEa6-nHP-bgvWzQAAI"
related_ids:
  - "kzQArUM6XzcK1BKXaiid5m-aYMYSEAAO"
  - "IBrO0wnBIiMeIwXJuaYtnJ-D4Xl3wAAF"
topic_id: "v2:HHNO"
topic_path: "mixed"
---

# FFglitch

A **multimedia bitstream editor** built on FFmpeg, by Ramiro Polla. The whole trick:
it edits values _inside_ an encoded bitstream — motion vectors, quantizers, macroblock
types, DCT coefficients — and rewrites a still-valid file **without re-encoding**
(Polla calls this _transplication_). So the glitch is real and structural, not a
post-filter painted on top. Closer to performing surgery on the file than to applying
an Instagram filter.

**Local install (v0.10.2, macOS aarch64):** `~/Documents/AI/ffglitch`
The binaries are **not on `$PATH`** — call them by absolute path (`FFG=~/Documents/AI/ffglitch`),
or add the dir to `$PATH` for a session. They are large self-contained static builds;
no FFmpeg install needed (this _is_ a custom FFmpeg fork).

**Shortcuts:** [`scripts/ffglitch.py`](scripts/ffglitch.py) (stdlib only) wraps the
binaries — `features`, `prep`, `export`, `apply`, `script`, `play` — and
[`scripts/datamosh.py`](scripts/datamosh.py) is a one-shot datamosher (I-frame kill
plus bloom, auto-preps any input). Run either with `-h`.

## The three (four) binaries

| Binary       | What it is                                                      | Use it to                                                                                                                                                         |
| ------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`ffedit`** | The bitstream editor                                            | Export codec data to JSON, glitch it, apply it back. Or run a script that mutates frames as they pass through. **The main event.**                                |
| **`ffgac`**  | "Universal media converter" = `ffmpeg` made _dumber_ on purpose | **Prep** source into a glitch-friendly encode (force motion vectors everywhere, infinite GOP, no scene-cut keyframes) so glitches propagate instead of resetting. |
| **`fflive`** | Media player that runs FFglitch scripts in **real time**        | Perform glitches live, driven by keyboard / MIDI / ZeroMQ. The VJ tool.                                                                                           |
| **`qjs`**    | Standalone QuickJS interpreter (with MIDI + ZMQ built in)       | Test/debug script logic outside the media pipeline; write controller bridges.                                                                                     |

Typical pipeline: **`ffgac` (prep a cooperative encode) → `ffedit` (glitch it) →
one final transcode to deliver.** Supported codecs: MPEG-1/2, MPEG-4 part 2,
JPEG/MJPEG, PNG/APNG. H.264/H.265 expose nothing — always prep first.

## Core ffedit commands

```bash
$FFG/ffedit -i input.m2v                                      # 1. inspect: what features can THIS file glitch?
$FFG/ffedit -i input.m2v -f mv -e data.json                   # 2. export motion vectors to JSON ...
$FFG/ffedit -i input.m2v -f mv -a data.json -o glitched.m2v   #    ... edit the JSON, apply it back
$FFG/ffedit -i input.m2v -s myglitch.js -o glitched.m2v       # 3. script mode: mutate every frame programmatically
```

Always inspect an unknown file first; the available "features" depend entirely on the
codec, and nothing listed means prep with `ffgac` instead of fighting it. Script mode
is the real power: a script exports `setup(args)` and `glitch_frame(frame)`, in
JavaScript or Python3. Full API, types, and write rules are in scripting.md.

## References - load on demand

- **[references/recipes.md](references/recipes.md)** - start here for video projects: the prep→glitch→preview→deliver pipeline, effect menu, datamosh + bloom, pixel sorting, Resolve/ProRes delivery. _Read when glitching any actual video, or picking an effect._
- **[references/features.md](references/features.md)** - every feature (`mv`, `q_dc(t)`, `qscale`, `mb`, `info`, `dqt`, `dht`, `gmc`, `idat`) per codec, with the exact JSON shape of each. _Read when hand-editing exported JSON or choosing what to glitch._
- **[references/scripting.md](references/scripting.md)** - full scripting API: `setup`/`glitch_frame`, MV/MV2DArray types, read-vs-write cell rules, Python setup, ffgac's pixel-level `filter(args)` API. _Read before writing or debugging any glitch script._
- **[references/ffgac-prep.md](references/ffgac-prep.md)** - all prep recipes: MPEG-2/MPEG-4/libxvid flags, JPEG `-dqt`, PNG filter-row scripting, pixelsort, pipes. _Read when encoding source into a glitch-friendly file._
- **[references/live.md](references/live.md)** - fflive real-time rig: keyboard (SDL), MIDI (RtMidi), ZeroMQ APIs with working poll-loop patterns. _Read when performing live._
- **[references/gpu-post.md](references/gpu-post.md)** - Metal/GPU options around the pipeline: ProRes delivery, MV-JSON→Resolve Fusion warps, the glitchgpu Metal CLI, DCTL. _Read when delivering to Resolve or adding GPU post._
- **[references/gotchas.md](references/gotchas.md)** - the fine print: MV grid orientation, `dup()`, overflow, JSON fields never to touch, Python env, `-sp` limits. _Read when a script or export behaves strangely._

Ready-to-run scripts (all verified on this install): `scripts/datamosh.py`,
`scripts/mv2maps.py` (MV JSON → Resolve Fusion displacement maps),
`scripts/glitchgpu/` (Metal compute post: trails/mvwarp/chroma/scan/sort —
build with `swiftc -O glitchgpu.swift -o glitchgpu`),
`scripts/dctl/FFGlitchLook.dctl` (Resolve Color-page glitch looks; installed
to the system LUT dir), `scripts/mv_amplify.js`,
`scripts/examples/mv_drift.js`, `scripts/examples/mv_sine.js`,
`scripts/examples/dc_streak.js`, `scripts/examples/mv_glide.py`.

## Always-true gotchas

- **`.mpg` is rejected.** Glitch raw `.m2v` or MPEG-4-in-`.avi`, never an MPEG Program
  Stream. Containers: rawvideo/AVI/MOV only — no MKV.
- **Read cells with `c[0]`/`c[1]`, write with `MV(x,y)`.** Assigning a plain `[x,y]`
  array throws (JS; Python takes plain lists).
- **`-mb_type_script`/`-pict_type_script` are broken in this build** (macOS
  aarch64 0.10.2) — even official scripts fail; details + workaround in
  ffgac-prep.md.
