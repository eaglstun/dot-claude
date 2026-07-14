# musicviz

Winamp-style music-visualization videos from any audio file, rendered locally with
ffmpeg. No cloud, no pip deps.

```bash
scripts/visualize.py song.mp3
scripts/visualize.py song.wav --preset scope --palette ice --format social --res 1080
```

- **Presets:** `bars` (spectrum bars) · `scope` (oscilloscope) · `spectrum` (scrolling
  spectrogram) · `lissajous` (stereo vectorscope)
- **Palettes:** named (`winamp ice neon vapor sunset gold crimson emerald mono`), ffmpeg
  built-ins (`turbo magma inferno …`), or an arbitrary hex ramp `"#ff0080,#00e5ff,#fff"`
- **Formats:** `tv` (16:9) · `social` (9:16) · `square` (1:1), at `--res 1080|720|480|360`
- **Knobs:** `--gain --glow --bg --bg-image --mirror --fps --start --duration --crf`

**Phase doctor:** `scripts/analyze.py song.mp3` inspects stereo/phase health
(correlation, width, mono fold-down, per-section timeline, delay detection) and prints a
verdict + the ffmpeg command to fix polarity/delay/phasey audio. Read-only.

See [`SKILL.md`](SKILL.md) for the overview, `scripts/visualize.py -h` for every flag, and
[`references/presets.md`](references/presets.md) for internals (filtergraphs, palette math,
the gbrp channel-order and glow/YUV gotchas, how to add a preset or palette).

`output/` holds a couple of demo renders made from a synthetic stereo test tone.

Requires: `ffmpeg` on PATH (tested with 8.1.2) and Python 3.
