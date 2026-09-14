---
name: musicviz
description: Turn an audio file into a Winamp-style music-visualization video — spectrum bars, oscilloscope, scrolling spectrogram, or stereo vectorscope, in 16:9, 9:16, or 1:1. Also a stereo "phase doctor" for L/R correlation, stereo width, mono compatibility, and phase problems. Use when the user wants to visualize a song/track as a video, make an audiogram or lyric-video background, or check/fix whether audio is out of phase or mono-compatible.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: kzQArUM6XzcK1BKXaiid5m-aYMYSEAAO
  related_ids: '["AiTNqHEqK7VumAhuaGqNZDOpQPU3YAAD","B_QgbjDv0zcp1Q8HYjii1LTZAMObQAAJ"]'
  topic_id: v2:LNDH
  topic_path: metal-renderer
---

# musicviz

Winamp-style visualizers from any audio file, rendered locally with **ffmpeg's
native audio-visualization filters** plus a universal palette colorizer. Fast
(C-speed filters, no per-frame Python), no dependencies beyond ffmpeg.

## Use the bundled driver

**[`scripts/visualize.py`](scripts/visualize.py)** does everything — it builds the
ffmpeg filtergraph, colorizes, composites over a background, adds glow, sizes the
canvas, and muxes the audio back in. **Run it with `-h` for the full flag list —
run it, don't read its source.** The header of `-h` has copy-paste examples.

```bash
scripts/visualize.py song.mp3                                   # bars · winamp · 1080p TV
scripts/visualize.py song.wav --preset scope   --palette ice    --format social
scripts/visualize.py song.flac --preset spectrum --palette magma --res 720
scripts/visualize.py track.mp3 --palette "#ff0080,#00e5ff,#ffffff"   # custom hex ramp
scripts/visualize.py song.mp3 --list-presets     # or --list-palettes
```

## Phase doctor (stereo / phase health)

**[`scripts/analyze.py`](scripts/analyze.py)** inspects an audio file's stereo field —
L/R correlation, stereo width (mid/side), mono fold-down cancellation, a per-section
timeline, and inter-channel delay detection — then prints a plain verdict and, if
warranted, the exact ffmpeg command to fix it. Read-only; it never touches the input.

```bash
scripts/analyze.py song.mp3               # verdict + timeline
scripts/analyze.py mix.wav --segments 20  # finer timeline
scripts/analyze.py track.flac --json      # machine-readable
```

Diagnoses four states, each with a matched fix: **polarity-inverted** (flip one channel),
**inter-channel delay** (time-align with `adelay`), **phasey / mono-incompatible** (narrow
sides with `stereotools`), and **healthy** (do nothing). Delay detection is guarded so a
genuinely-wide mix isn't misread as a timing offset. Uses numpy if available (FFT
cross-correlation), else a stdlib fallback (`--force-stdlib`). "Correlated / near-mono" is
NOT a defect — a positive correlation is mono-safe; only negative correlation or heavy mono
cancellation is a real problem.

## The four presets (the "look")

| preset           | what it is                    | notes                                                                |
| ---------------- | ----------------------------- | -------------------------------------------------------------------- |
| `bars` (default) | height-reactive spectrum bars | color runs bottom→top through the palette (classic winamp green→red) |
| `scope`          | oscilloscope / waveform line  | glowing trace; `--smooth` calms the motion (see below)               |
| `spectrum`       | scrolling spectrogram         | log frequency axis; fills in over the length of the track            |
| `lissajous`      | stereo vectorscope            | needs a **stereo** file to draw a figure; mono → a diagonal          |

## Palettes

Three ways to specify `--palette`:

- **Named** (built into the skill): `winamp ice neon vapor sunset gold crimson emerald mono`
- **ffmpeg built-ins**: `turbo magma inferno plasma viridis cividis spectral cool heat fiery blues green helix`
- **Arbitrary hex ramp**: comma-separated stops, e.g. `"#001a00,#00ff00,#ff0000"` (2–4 colors, low→high)

## Adjustable knobs

`--smooth` (**scope only**, 0..1, default 0 = off) adds phosphor persistence to calm a
frantic waveform. `showwaves` draws a fresh, NON-OVERLAPPING audio window every frame,
so the raw trace strobes; `0.88` is a good start (~3x calmer), `0.93` calmer still,
above `0.95` it fills into a solid slab. It runs on the gray mask *before* the palette,
which is what keeps the colours — see the note under Gotchas.

`--gain` (sensitivity / bar height; for `lissajous` this is the zoom / fill) · `--glow`
(bloom px, `0`=off) · `--decay` (lissajous phosphor-trail persistence 0..1; `0`=no trail,
`0.95`=long smooth trails) · `--bg` (hex color) · `--bg-image FILE` (image behind the viz)
· `--mirror` · `--fps` · `--start`/`--duration` (render a slice) · `--crf` (quality)
· `--dry-run` (print the ffmpeg command).

For a lush, smooth `lissajous`, render at `--fps 60` — the phosphor trails read much
smoother than 30. Bump `--gain` above 1 to fill more of the frame (a wide-stereo track
fills more than a mono-correlated one), but too high clips at the edges.

## Format & resolution

`--format tv|social|square` (or an explicit `WxH`) × `--res 1080|720|480|360`. All
canvases are rounded to even dimensions (codec requirement). Output is H.264/AAC
`.mp4` with `+faststart`.

## Notes & gotchas

- **showcqt (bars) needs even width/height** — the script rounds for you; if you pass
  an explicit `WxH`, keep it even.
- **`pseudocolor` works in gbrp plane order** (`c0→G, c1→B, c2→R`) — the script already
  accounts for this when generating custom-palette expressions. Don't "fix" the channel
  order if editing.
- **Smooth the MASK, never the colourised video.** Both obvious post-hoc fixes fail:
  `lagfun` on RGB maxes each channel independently and leaves grey/pink smears, and
  `tmix` averages bright peaks with dark background so the palette washes out. Worse,
  the mask doubles as the **alpha**, so averaging it makes peaks translucent, which
  drops them down the height ramp and turns yellow into green. `lagfun` on the gray8
  mask takes the max, so the live trace stays crisp and full-brightness with a decaying
  ghost behind it. That is what `--smooth` does.
- **Glow must blend in RGB.** The bloom uses `blend=screen`, which produces a purple/green
  wash if it runs on YUV chroma; the script pins the chain to `gbrp` before the blend and
  converts to `yuv420p` only at the very end.
- Deeper reference (per-preset filtergraphs, palette math, adding a preset/palette):
  [`references/presets.md`](references/presets.md).
