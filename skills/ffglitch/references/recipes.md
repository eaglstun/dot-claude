# Glitch recipes for video projects

Effect-first cookbook. Every recipe here was run and visually verified against the
local FFglitch 0.10.2 install. `FFG=~/Documents/AI/ffglitch`;
`scripts/` paths are relative to this skill.

## The project pipeline

Real footage in, deliverable out — four stages, keep them separate:

```text
1. PREP      ffgac: re-encode source into a glitch-friendly .m2v
2. GLITCH    ffedit -s script.js (repeatable, parameterized) — chain multiple passes
3. PREVIEW   fflive out.m2v  (or decode spot-frames to PNG, see below)
4. DELIVER   one final transcode to an edit/share codec
```

```bash
# 1. prep (or: scripts/ffglitch.py prep input.mov)
$FFG/ffgac -i input.mov -c:v mpeg2video -mpv_flags +forcemv+nopimb \
  -g max -sc_threshold max -f mpeg2video -an ready.m2v

# 2. glitch — passes chain fine; each output is still a valid .m2v
$FFG/ffedit -i ready.m2v -s mv_sine.js -sp 8 -y -o pass1.m2v
$FFG/ffedit -i pass1.m2v -s dc_streak.js -y -o pass2.m2v

# 3. spot-check a frame without watching the whole clip
$FFG/ffgac -i pass2.m2v -ss 3 -frames:v 1 -y check.png

# 4. deliver (see "Delivering" below)
```

Prep knobs that change the look:

- `-qscale:v 2` = clean source, subtle glitches; `-qscale:v 8+` = crunchy blocks
  that make every glitch louder.
- Default mpeg2 prep has **no B-frames**; add `-bf 2` if a script wants
  `frame.mv.backward`.
- Glitches propagate until the next I-frame. `-g max` = one keyframe total =
  maximum propagation.

## Effect menu (motion vectors)

All run as `$FFG/ffedit -i in.m2v -s <script> [-sp N] -y -o out.m2v`.

| Effect             | Look                                                             | Script                                               |
| ------------------ | ---------------------------------------------------------------- | ---------------------------------------------------- |
| **Drift**          | whole frame slides/melts in one direction, compounds over GOP    | `scripts/examples/mv_drift.js`                       |
| **Sine warp**      | rows shear on a traveling wave — liquid, seasick ripple          | `scripts/examples/mv_sine.js` (`-sp` = amplitude px) |
| **Amplify**        | every real motion exaggerated N× — jittery, hyperactive          | `scripts/mv_amplify.js`                              |
| **Temporal smear** | motion averaged over N frames — dreamy dragging trails           | smear example in scripting.md (`-sp` = tail length)  |
| **Freeze**         | `fill(MV(0,0))` — motion deleted, only DC deltas update; ghostly | one-liner, see scripting.md pattern starters         |

MV effects need P-frames with coded vectors → always work on `+forcemv` preps;
sparse or absent on wild files.

## Effect menu (coefficients — works on MPEG-2 _and_ JPEG)

| Effect                | Look                                                           | How                                                                         |
| --------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **DC streaks/scars**  | vertical bands of blown-out brightness dragging across the GOP | `scripts/examples/dc_streak.js` (`-sp` = boost, try 200–600)                |
| **Coefficient noise** | fizzing blocky texture                                         | script on `q_dct`: perturb random AC cells in `data[plane][y][x]` arrays    |
| **Quant crunch**      | uniform deep-fried blockiness                                  | export `-f qscale`, raise slice values, apply; or JPEG `dqt` table scale-up |

## Datamosh (the big one)

Two clips, one bitstream: clip B's motion vectors animate clip A's pixels.
Verified tool: [`scripts/datamosh.py`](../scripts/datamosh.py) — preps non-.m2v
inputs automatically, drops each later clip's I-frame, splices at picture
boundaries (safe on MPEG-1/2: start codes can't occur inside slice data).

```bash
scripts/datamosh.py A.mov B.mov -o mosh.m2v                # classic I-frame kill
scripts/datamosh.py A.mov B.mov -o mosh.m2v --bloom 15     # + P-frame duplication
scripts/datamosh.py A.mov B.mov C.mov -o mosh.m2v --size 640x360 --qscale 4
```

- **I-frame kill:** the cut never "arrives" — B's motion smears A's picture
  until B's content gradually asserts itself.
- **Bloom (`--bloom N`):** the first P-frame after the splice repeats N times, so
  its motion re-applies and compounds — the classic blooming surge. More = gooier.
- Clips must share resolution/framerate — pass `--size`/`--rate` to force it.
- Moshes are fragile in players that seek (no keyframes to land on). Preview with
  `fflive`; transcode for delivery.

Chaos variant (official "cat videos" recipe): normalize many clips to same-size
MPEG-2 with short GOPs (`-g 90 -qscale:v 6 -r 30 -s 1280x720 -f rawvideo`),
`split --bytes=1M` them, shuffle, `cat` back together (first chunk must start
with an I-frame), then "bake" by re-encoding the corrupted stream once. Part 2
of that tutorial does it frame-precise instead: `ffgac -i clip.mpg -vcodec copy
frames/f_%04d.raw` splits per-frame losslessly, then `cat` any shuffle of the
`.raw` frame files — no corruption, no bake needed. Both are datamosh without a
single script.

## JPEG glitching

```bash
$FFG/ffedit -i photo.jpg -f q_dc -e dc.json      # export DC coefficients
#  ...mangle dc.json (or use a script with args.features=["q_dc"])...
$FFG/ffedit -i photo.jpg -f q_dc -a dc.json -y -o glitched.jpg
```

Features: `q_dc`/`q_dct` (coefficients), `dqt` (the 8x8 quant table —
`{"tables": [[64 values]]}`), `dht` (huffman table — edit at your peril).
`dc_streak.js` works unmodified on JPEGs. MJPEG-in-.avi = per-frame JPEG
glitching of video.

## Pixel sorting (ffgac vf_script)

Not a bitstream glitch — a pixel effect during encode, but it lives in the same
toolbox and stacks with everything above (sort first, then prep+glitch the
sorted footage). Verified script in ffgac-prep.md ("Pixelsorting" section —
note `reverse_sort` and the range arrays are mandatory despite the docs):

```bash
$FFG/ffgac -i input.mov -vf script=file=pixelsort.js -an sorted.mp4
```

## Live performance

The whole glitch pipeline runs in real time: `ffgac` prep piped into `fflive`
running the same script, driven by keyboard/MIDI/ZeroMQ. Webcam, YouTube
streams, and screen capture all work as sources. See **live.md** for the rig
and the input APIs.

## Delivering (Resolve / social / web)

The glitched `.m2v` is the _master_ — keep it. But it's a raw elementary stream
with one keyframe: editors and players hate seeking in it. Final step, transcode
ONCE (this bakes the glitch into pixels, which is exactly what you want at
delivery):

```bash
# into DaVinci Resolve: hardware ProRes via SYSTEM ffmpeg (ffgac lacks videotoolbox)
# — M4 Max ProRes engines, faster than realtime, reference-quality ProRes
ffmpeg -i mosh.m2v -c:v prores_videotoolbox -profile:v hq -pix_fmt p210le mosh_prores.mov

# fallback (software, any machine)
$FFG/ffgac -i mosh.m2v -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le mosh_prores.mov

# straight to web/social — keep libx264: hardware H.264 rate control smooths
# exactly the high-entropy glitch texture you're trying to keep
$FFG/ffgac -i mosh.m2v -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart mosh.mp4
```

## GPU post passes (after the glitch, before/at delivery)

Two working tools extend the pipeline on the GPU — see **gpu-post.md** for
details and Fusion wiring:

```bash
# 1. bake the glitch's motion field into displacement maps for Resolve Fusion
scripts/mv2maps.py mv.json -o maps/ --scale 2048

# 2. Metal compute effects in the delivery pipe (~645 fps @ 720p):
#    trails (feedback ghosting), mvwarp (MV-JSON-driven warp), chroma, scan,
#    sort (TRUE per-scanline pixel sort: --lo/--hi luma band, ~356 fps @ 720p)
ffmpeg -i mosh.m2v -f rawvideo -pix_fmt bgra - \
| scripts/glitchgpu/glitchgpu --size 1920x1080 --fx trails --decay 0.94 \
| ffmpeg -f rawvideo -pix_fmt bgra -s 1920x1080 -r 30 -i - \
    -c:v prores_videotoolbox -profile:v hq out.mov
```

The killer combo: `mvwarp` with a _different clip's_ MV export — datamosh
aesthetics on clean footage, fully reversible.

Also installed: `scripts/dctl/FFGlitchLook.dctl` — RGB shift / scanlines /
wave shear / block-quantize sliders on the Resolve Color page (already copied
to the system LUT dir; restart Resolve, Effects → DCTL → FFGlitchLook).

Audio stays out of the glitch pipeline (`-an` in prep); mux it back here:
`-i mosh.m2v -i original.mov -map 0:v -map 1:a -shortest`.

## Chaining & parameter sweeps

Scripts are deterministic — same input + script + `-sp` = same output. Sweep a
parameter to audition looks fast:

```bash
for sp in 2 6 12 24; do
  $FFG/ffedit -i ready.m2v -s mv_sine.js -sp $sp -y -o sine_$sp.m2v
  $FFG/ffgac -i sine_$sp.m2v -ss 3 -frames:v 1 -y sine_$sp.png
done
```

Then eyeball the PNGs and commit to a value. (Claude can read the PNGs and
compare, too.)

## Gotchas specific to project work

- **Chain passes on .m2v, not .mp4.** Every intermediate must stay a glitchable
  elementary stream; only the last hop leaves the format.
- **Don't re-prep a glitched file** — re-encoding heals the glitch (encoder sees
  the corrupt pixels as ground truth and encodes them cleanly... which does bake
  a look in, occasionally useful, usually not what you meant).
- **Timecode burn-in / overlays** go in the delivery transcode, never before prep.
- **Long clips:** `q_dct` JSON exports get huge (~2 MB/s of 320x240). Script mode
  streams; prefer it for anything longer than a shot.
