# GPU / Metal options around the FFglitch pipeline

Researched + locally verified 2026-07 (M4 Max, Metal 4, macOS 25.x). Rule that
shapes everything: **the glitch stays a CPU bitstream edit — that's the art.**
The GPU's roles are (a) faster delivery transcodes and (b) pixel-space post that
runs _after_ the glitch is baked, or that consumes FFglitch's exported JSON as
data. Nothing here touches ffedit's inner loop.

Key machine facts (verified): Homebrew **ffmpeg 8.1.2** (`/opt/homebrew/bin/ffmpeg`)
has `prores_videotoolbox`, `h264_videotoolbox`, `hevc_videotoolbox`, `-hwaccel
videotoolbox`, and the `coreimage` filter. **ffgac has none of these** — hardware
paths always go through system ffmpeg. M4 Max has 2 hardware ProRes engines.
AVFoundation can't open raw `.m2v` (no MPEG-2) — ffmpeg-pipe harnesses are
codec-agnostic; AVFoundation ones only work post-ProRes.

## 1. Hardware ProRes delivery — do this today (zero effort)

Swap the Resolve delivery hop to the hardware ProRes engine via system ffmpeg:

```bash
ffmpeg -i mosh.m2v -c:v prores_videotoolbox -profile:v hq -pix_fmt p210le mosh_prores.mov
```

Profiles: `proxy|lt|standard|hq|4444|xq`; 10-bit 4:2:2 is `p210le`. No quality
anxiety: ProRes is a fixed-ladder intra codec — Apple's hardware implementation
is the reference one, no rate-control to starve high-entropy glitch frames.
Far faster than realtime even at 4K.

**Keep `libx264 -crf 18` for final web/social.** `h264_videotoolbox -q:v 65`
works on Apple Silicon but hardware rate control smooths exactly the
high-entropy datamosh texture that is the point. Hardware H.264/HEVC = quick
approval drafts only.

## 2. MV JSON → vector maps → Resolve Fusion "Vector Distortion" — ✅ BUILT

**[`scripts/mv2maps.py`](../scripts/mv2maps.py)** (stdlib-only, verified): bakes
each frame's exported `mv.forward` grid into 16-bit RGB PNGs — one pixel per
macroblock, X displacement in R, Y in G, neutral = 32768 mid-gray.

```bash
ffedit -i ready.m2v -f mv -e mv.json
mv2maps.py mv.json -o maps/ --scale 2048   # warns if values clip
```

Fusion wiring: import `maps/` as an image sequence → footage to
VectorDistortion.Input, maps to `.Distort`, X Channel=Red, Y Channel=Green,
offset 0.5, Scale slider to taste. GPU/Metal-accelerated inside Resolve.
Buys what pure FFglitch can't: clip B's motion field warping clip C's pixels,
keyframeable, stackable with grades, reusable on future footage.

Caveats: MPEG-2 MVs are **half-pel** (exported `[2,0]` ≈ 1 px); intra frames
emit a neutral frame automatically; Resolve's bilinear upsample of the tiny map
gives smooth warps — insert a nearest-neighbor Resize before it to keep the
blocky 16×16 macroblock look instead.

## 3. `glitchgpu` — Swift+Metal compute CLI on ffmpeg rawvideo pipes — ✅ BUILT

**[`scripts/glitchgpu/glitchgpu.swift`](../scripts/glitchgpu/glitchgpu.swift)**
(single file; binary compiled alongside). Raw BGRA on stdin → MSL compute
kernel → raw BGRA on stdout. Codec-agnostic: reads the raw `.m2v` master
directly through a pipe. Verified at **~645 fps at 720p** (M4 Max, trails).

```bash
# build (once, or after edits)
swiftc -O glitchgpu.swift -o glitchgpu

# use — any effect slots into the standard delivery pipe:
ffmpeg -i mosh.m2v -f rawvideo -pix_fmt bgra - \
| glitchgpu --size 1920x1080 --fx trails --decay 0.94 \
| ffmpeg -f rawvideo -pix_fmt bgra -s 1920x1080 -r 30 -i - \
    -c:v prores_videotoolbox -profile:v hq out.mov
```

Effects (all verified end-to-end):

| `--fx`   | look                                                                                                      | params                                 |
| -------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `trails` | video-feedback ghosting, `max(cur, hist*decay)`                                                           | `--decay 0..1` (0.9–0.96 sweet spot)   |
| `mvwarp` | displace pixels by an FFglitch MV export — one clip's motion warping another's pixels                     | `--mv mv.json --gain N`                |
| `chroma` | RGB split growing toward frame edges                                                                      | `--gain` (px at edge)                  |
| `scan`   | CRT scanlines + animated sine row jitter                                                                  | `--gain` strength                      |
| `sort`   | TRUE per-scanline pixel sort — runs of pixels with luma in the band sort by luma; pixels outside stay put | `--lo 0.15 --hi 0.85` (~356 fps @720p) |

New effects ≈ 30 lines of MSL added to the embedded source string (kernel
signature: src/dst textures + `Params{gain, decay, frame, lo, hi, n2}`).
`sort` implementation notes: one threadgroup per scanline, bitonic sort in
threadgroup memory (keys + packed colors, 16 KB each), composite key
`span_start*65536 + luma` so a single sort both anchors non-span pixels at
their own index and sorts each span internally. Width cap 4096 px (32 KB
threadgroup memory); MSL quirk hit: all thread-position attributes in a kernel
must share dimensionality (use `uint2` for all of them).

Metal gotchas encountered: runtime `makeLibrary(source:)` compiles fast-math by
default; `.storageMode = .shared` on unified memory (no blits for CPU I/O);
`Float16(NSNumber.floatValue)` — there's no `Float16(truncating:)`.

Rejected harnesses: MPSGraph (ML graph compiler — wrong tool), Core Image custom
kernels (buys tiling/color management this pipeline doesn't need, costs a
`-fcikernel` compile step), patching ffmpeg with a Metal filter (build
maintenance pain). ffmpeg's built-in `coreimage` filter = named CIFilters only
(`-vf coreimage=filter=CIBloom@default`) — free seasoning, no custom MSL.

## 4. DCTL transform shaders in Resolve — ✅ WRITTEN + INSTALLED

**[`scripts/dctl/FFGlitchLook.dctl`](../scripts/dctl/FFGlitchLook.dctl)** — one
DCTL, five Color-page sliders, every effect defaulting to off: RGB Shift
(edge-weighted chromatic aberration), Scanlines, Wave Amp/Freq/Phase
(keyframe Wave Phase to animate — DCTL has no frame counter), Block Size
(fake-macroblock pixelation). Installed to
`/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/` (the dir
Resolve's "Open LUT Folder" opens on this Mac — note: NOT `Fusion/LUT`).

**Honesty note:** DCTLs compile inside Resolve at load time — there's no
headless compiler, so this file follows the DCTL spec but is unverified until
first load. Restart Resolve → Color page → Effects → DCTL → FFGlitchLook; if
it doesn't appear in the DCTL dropdown, check Resolve's console for the
compile error and fix the line it names.

Hard limits stand: **no file I/O** (can't read MV JSON — route MV data through
images per #2), **no state across frames** (no trails), gather-only (**no true
pixel sorting** — glitchgpu's `sort` does that). OFX would lift all three but
is a C++ plugin project — only if a look becomes permanent.

## 5. Metal live preview — skip as a standalone project

`fflive` already owns bitstream-parameter liveness (keyboard/MIDI/ZMQ inside
ffedit's decode loop — no Metal layer can replicate that). A Metal preview only
helps for tweaking #3's kernel params: point the same `glitchgpu` at an MTKView
(+1 day on top of #3), and only if PNG spot-checks start to chafe.

## Adoption order

| Rank | Option                                                 | Effort     | Verdict                               |
| ---- | ------------------------------------------------------ | ---------- | ------------------------------------- |
| 1    | `prores_videotoolbox` delivery                         | one flag   | pure win; keep libx264 for web finals |
| 2    | MV maps → Fusion Vector Distortion                     | 1 evening  | best payoff/effort, no shader code    |
| 3    | `glitchgpu` compute CLI                                | 1 weekend  | trails, real pixel sort, MV shaders   |
| 4    | DCTL transforms                                        | hours each | useful within limits                  |
| 5    | `coreimage` filter in transcode                        | minutes    | seasoning only                        |
| —    | MPSGraph / ffmpeg Metal filter / OFX / hw H.264 finals | high       | not worth it                          |

Sources: Apple M4 tech specs (support.apple.com/121553), ffmpeg-devel `-q:v`
Apple-Silicon patch, Apple Metal-CI kernel reference PDF, WWDC20 #10021,
resolve.cafe DCTL docs, Fusion 9 Tool Reference, JayAreTV Vector Distortion.
Local: encoder listings of brew ffmpeg 8.1.2 vs ffgac 0.10.2.

### See also (shared GPU shelves)

Crosslink syntax per `~/.claude/references/gpu-rosetta.md` — skill-local files
link OUT to the shared shelves, never the reverse:

- [[apple-silicon:occupancy-and-threadgroup-memory]] — the 32 KB threadgroup-memory cap that sets glitchgpu's 4096-px sort width limit.
- [[apple-silicon:compute-kernels-and-dispatch]] — dispatchThreads vs dispatchThreadgroups semantics glitchgpu uses.
- [[apple-silicon:resource-storage-modes-and-options]] — why `.storageMode = .shared` means no blits on unified memory.
- [[apple-silicon:pipeline-and-library-compilation]] — runtime `makeLibrary(source:)` behavior incl. the fast-math default.
- [[metal:per-eye-temporal-accumulation]] — the headset renderer's cousin of glitchgpu's trails (accumulation without breaking stereo).
