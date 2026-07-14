# ffgac — preparing glitch-friendly encodes

`ffgac` is `ffmpeg` with extra options that make the encoder **deliberately dumb**
(GAC = Glitch Artists Collective). Normal FFmpeg works hard to keep video clean: it
only writes motion vectors where there's motion, inserts intra-blocks to repair
P-frames, and drops keyframes at scene cuts. Every one of those "smart" behaviors
_heals_ glitches. `ffgac` lets you turn them off so corruption **propagates and
compounds** down the GOP instead of resetting.

It's a full FFmpeg fork, so all the usual `ffmpeg` syntax works:
`ffgac [infile opts] -i in ... [outfile opts] out`. Below are the glitch-specific extras.

## The workhorse recipe (MPEG-1/2)

Re-encode anything into a long-GOP MPEG-2 **raw elementary stream** that glitches will
travel across:

```bash
ffgac -i input.mov -c:v mpeg2video \
  -mpv_flags +forcemv+nopimb \
  -g max -sc_threshold max \
  -f mpeg2video -an glitchready.m2v
```

| flag                  | effect                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------ |
| `-c:v mpeg2video`     | encode MPEG-2 video                                                                                          |
| `-mpv_flags +forcemv` | write motion vectors on **every** block, even still ones — gives `ffedit -f mv` something to grab everywhere |
| `-mpv_flags +nopimb`  | "no P-frame intra macroblocks" — stop the encoder repairing P-frames with clean blocks                       |
| `-g max`              | maximum GOP size — kills ffmpeg's 600-frame GOP cap; one keyframe, then P-frames forever                     |
| `-sc_threshold max`   | disable scene-change detection so cuts don't force fresh keyframes                                           |
| `-f mpeg2video`       | **raw elementary stream** muxer + `.m2v` extension — NOT `.mpg` (ffedit rejects Program Streams)             |
| `-an`                 | drop audio (optional; keeps the file simple while glitching video)                                           |

Combine flags with `+`: `-mpv_flags +forcemv+nopimb`. Add `-qscale:v N` to fix
quantization, or `-b:v` for bitrate, as with normal ffmpeg. **Don't write `.mpg`** —
that's an MPEG Program Stream and `ffedit` will refuse it; `.m2v` + `-f mpeg2video`
gives the raw stream it can edit. (`scripts/ffglitch.py prep` does this automatically.)

Extra prep knobs (from the official tutorial's canonical recipe):

- `-qscale:v 1` — highest quality; the tutorial preps with it so the glitch, not
  the encoder, supplies the dirt. Use 6–8 for crunchy blocks instead.
- `-fcode 6` — widen the coded MV range so large glitch vectors don't clamp
  (docs warn this option may be removed in a future version).
- `-bf 2` — add B-frames if a script wants `frame.mv.backward` (default is none).

## MPEG-4 part 2

Same idea, different codec — the official tutorial actually preps MPEG-4
(blockier look, `gmc` feature, works in `.avi`):

```bash
ffgac -i input.mov -c:v mpeg4 -mpv_flags +forcemv+nopimb -qscale:v 1 -fcode 6 \
  -g max -sc_threshold max -an glitchready.avi
```

For **libxvid** the equivalents are `-forcemv 1` (= `+forcemv`) and
`-intra_penalty max` (= `+nopimb`).

## MJPEG / JPEG — quantization glitches

JPEG glitching is about the **quantization tables** (DQT), not motion. Load a custom
table to force quality degradation or coefficient overflow:

```bash
ffgac -i photo.jpg -dct int -dqt dqt.json -y output.jpg
```

- `-dct int` — integer DCT (avoids fast-DCT overflow bugs)
- `-dqt dqt.json` — custom quantization coefficients; JSON has `"luma"` and
  `"chroma"` keys, 64 entries each. DC quant > 128 deliberately triggers
  decoder-dependent overflow — the glitch renders differently per browser/player.

Pair with `ffedit -f q_dc` / `-f q_dct` to inspect and edit the quantized coefficients
directly (run `ffedit -i your.jpg` to see the exact JPEG feature names available).

## PNG / APNG — filter-row scripting (0.10.1+)

PNG rows are predicted via a per-row filter type; lying about it corrupts
prediction beautifully. `-filter_row_script` exports `filter_row_func(args)` with
`args.png_filter_row` (the real filter fn), `dst`/`top`/`src` (Uint8FFPtr rows),
`bpp`. Filter constants: NONE=0, SUB=1, UP=2, AVG=3, PAETH=4. The docs example
filters with UP but _returns_ AVG — written ≠ used = cascading glitch:

```bash
ffgac -i input.jpg -filter_row_script png_filter.js -y glitched.png
```

Decode-side, `ffedit -i file.png` exposes `headers` and `idat` (rows; `row[0]` is
the filter_type byte — rewrite it per row).

## ⚠️ mb_type_script / pict_type_script — BROKEN in this build

Documented API: `-mb_type_script s.js` exports `mb_type_func(args)`, set
`args.mb_types[mb_y][mb_x]` to `1` (CANDIDATE_MB_TYPE_INTRA) or `2` (INTER);
`-pict_type_script s.js` exports `pict_type_func(args)` returning `"I"`/`"P"`.

**Verified broken on the macOS aarch64 0.10.2 build (2026-07):** even Ramiro's
own `pict_types.js` / `mb_type_midi.js` die on the first frame with an opaque
`[exception] / Error calling ..._func()` (the throw is outside the script body —
try/catch never fires; `-threads 1` doesn't help; mpeg2 and mpeg4 both fail).
Output truncates to 1 frame. **Workaround for I-frame placement:** standard
ffmpeg `-force_key_frames "expr:..."` at prep time. Per-macroblock control has
no workaround; re-test after any FFglitch upgrade.

## Pixel-level scripting (the `script` video filter)

`ffgac` ships a `script` filter that runs JS/Python per frame at the **pixel** level
(distinct from `ffedit`'s bitstream editing — this is during encode). The script
exports `filter(args)` — see scripting.md for the verified `args` contract:

```bash
ffgac -f lavfi -i testsrc2=duration=10:size=256x256 \
  -vf script=file=uv.js -an output.mp4
```

Useful for generative source material or pixel math that you then encode and hand to
`ffedit` for bitstream glitching.

### Pixelsorting (JS only, verified signature)

Inside `filter(args)`, `ffgac.pixelsort(data, [y0, y1], [x0, x1], options)` —
**the range arrays and `reverse_sort` are required** (the docs mark them
optional; the binary disagrees):

```javascript
export function setup(args) {
  args.pix_fmt = "yuv444p"; // or "gbrp" for RGB sorting
}
export function filter(args) {
  const data = args.data;
  ffgac.pixelsort(data, [0, data[0].height], [0, data[0].width], {
    mode: "threshold", // or "random"
    colorspace: "yuv", // yuv | rgb | hsv | hsl
    order: "horizontal", // "horizontal" | "vertical" (docs say rows/columns — examples win)
    trigger_by: "y", // channel letter of the colorspace
    sort_by: "y",
    threshold: [0.25, 0.8], // threshold mode; clength for random mode
    reverse_sort: false, // REQUIRED
  });
}
```

```bash
ffgac -r 30 -loop 1 -i photo.png -vf script=file=pixelsort.js -vframes 240 \
  -c:v libx264 -preset ultrafast -qp 0 -y sorted.mkv
```

## Pipes (0.10.1+)

ffgac, ffedit, and fflive all read/write `pipe:` — chain prep → glitch → play
without temp files:

```bash
ffgac -i input.mov -c:v mpeg4 -mpv_flags +forcemv+nopimb -qscale:v 1 -fcode 6 \
  -g max -sc_threshold max -f rawvideo pipe: \
| ffedit -i pipe: -s glitch.js -o pipe: \
| ffgac -i pipe: -c:v prores_ks out.mov
```

(The live variant — piping into `fflive` — is in live.md.)

## Tips

- **Two-stage by default:** `ffgac` to prep → `ffedit` to glitch. Don't try to do both
  at once.
- After prepping, **verify with `ffedit -i glitchready.m2v`** that `mv` (and friends)
  now show up as features. If they don't, the encode didn't expose them — adjust flags.
- Keep audio out of the glitch pipeline (`-an`); mux it back at the final transcode if
  you need it.
- ffedit only accepts containers `rawvideo`, `AVI`, and `MOV/MP4` (plus bare
  JPEG/PNG). No MKV; no audio glitching (audio in AVI/MOV passes through in sync).
- `ffgac -h full` dumps the entire (huge) FFmpeg-style option set; the flags above are
  the glitch-specific ones layered on top.
