# musicviz — internals & extension reference

Read this when editing the filtergraph, adding a preset or palette, or debugging a
render. For day-to-day use just run `scripts/visualize.py -h`.

## The pipeline (one model for every preset)

Every preset produces a **grayscale intensity field** — brightness encodes signal
strength (or bar height). One shared colorizer turns that gray into color, so palettes
work identically across presets:

```
[0:a] ──▶ viz filter ──▶ format=gray8 ──┬─▶ [mA]  (alpha: where the viz is)
                                        └─▶ [mB]  (color source)

           position presets (bars, scope):
             [mB] × vertical ramp ──▶ format=gbrp ──▶ pseudocolor ──▶ rgb  [col]
           intensity presets (spectrum, lissajous):
             [mB] ─────────────────▶ format=gbrp ──▶ pseudocolor ──▶ rgb  [col]

[col] + [mA] ──alphamerge──▶ [fg]
[bg] + [fg] ──overlay──▶ [base]
[base] ──(optional glow: split, gblur, blend=screen in RGB)──▶ format=yuv420p ──▶ [v]
```

- **Alpha compositing decouples shape from color from background.** The viz shape is the
  alpha mask; the palette only paints where the mask is; the background is a fully
  independent color/image layer. This is why the background never picks up the palette's
  color-0 wash.
- **Position vs intensity coloring.** `bars`/`scope` multiply the mask by a top-bright
  vertical ramp (`geq=lum='40+215*(1-Y/H)'`) before colorizing, so color maps to _height_
  (winamp green→red). `spectrum`/`lissajous` colorize raw magnitude.

## Per-preset filters

| preset    | ffmpeg source filter    | key options                                                                           | color-by  |
| --------- | ----------------------- | ------------------------------------------------------------------------------------- | --------- |
| bars      | `showcqt`               | `sono_h=0:axis=0:text=0:bar_g=5:bar_v=<gain>:count=6`                                 | position  |
| scope     | `showwaves`             | `mode=line:draw=full:scale=sqrt`                                                      | position  |
| spectrum  | `showspectrum`          | `mode=combined:slide=scroll:scale=cbrt:fscale=log:gain=<gain>:color=intensity`        | intensity |
| lissajous | `avectorscope`→`lagfun` | `draw=aaline:mode=lissajous:scale=sqrt:zoom=<1.4·gain>` then `lagfun=decay=<--decay>` | intensity |

`--gain` maps per preset: bars → `bar_v` (bar height), spectrum → `gain` (dB scale),
lissajous → `zoom` (`1.4·gain`; higher fills more but clips at the edges). `scope` ignores
gain (its `scale=sqrt` already normalizes). `--decay` sets the lissajous `lagfun` phosphor
persistence (0 = no trail; ~0.95 = long smooth trails). Lissajous benefits a lot from
`--fps 60`.

## The framerate gotcha (do not "fix" the source rates away)

`overlay` takes its output timing from the **main** input — here `[bg]`. ffmpeg's `color`
(and `-loop 1` image) sources default to **25fps**, so without intervention the background
clamps the whole graph to 25fps and _drops_ the distinct frames the viz filter generated,
regardless of `--fps`. The script pins every synthetic source to the target rate
(`color=...:r={fps}`, `...,fps={fps}` on an image bg) and also passes `-r {fps}` to the
encoder. Verify a render's real rate with `ffprobe -count_frames` (nb_read_frames ÷
duration) — `r_frame_rate` alone can misreport.

## Palette math

`stops_to_exprs()` turns a list of `(pos 0..1, (r,g,b))` stops into three piecewise-linear
ffmpeg expressions of `val` (0–255 input luminance). Each segment:

```
gte(val,x0) * lt(val,x1) * ( a + (b-a)*(val-x0)/(x1-x0) )
```

summed across segments. **Use `gte()/lt()/lte()`, not `>=`/`<`** — ffmpeg's expression
parser rejects the operator forms.

### The gbrp channel-order gotcha (do not "fix")

`pseudocolor` operates in **gbrp plane order**: `c0→G, c1→B, c2→R`, regardless of the
`format` you feed it. So `resolve_palette()` assigns `c0=green_expr, c1=blue_expr,
c2=red_expr`. Verified: a black→cyan(0,179,255)→white ramp at mid-gray yields RGB
`01b3ff` (cyan) with this mapping, and `ff01b3` (magenta) without it.

Built-in ffmpeg presets (`--palette turbo` etc.) go straight through as
`pseudocolor=preset=NAME` — they define all channels internally, so the order gotcha
doesn't apply to them.

## The glow/YUV wash gotcha (do not "fix")

Bloom = `split → gblur one branch → blend=all_mode=screen`. `blend` is per-plane, so if
the stream is YUV, "screen" corrupts the U/V chroma planes → a flat purple/green wash over
the whole frame. Because `libx264` wants `yuv420p`, ffmpeg pushes YUV _up_ the graph unless
you pin it. The script does `[base]format=gbrp,split...blend=screen,format=yuv420p` — RGB
through the blend, YUV only at the encoder. (A PNG-output test looked fine and hid this bug
because PNG kept the chain in RGB — watch for that when spot-checking with stills.)

## Adding a preset

1. Write `r_yourpreset(W,H,fps,gain)` returning a filter chain applied to `[0:a]`, ending
   in `...,format=gray8`.
2. Register it in `PRESETS` with `by="position"` or `"intensity"` and a default `glow`.
3. Keep `showcqt`-family sizes even.

## Adding a named palette

Add to `PALETTES` a list of `(pos, (r,g,b))` stops, `pos` ascending 0→1, low energy first.
For a clean dark background, make the first stop dark/black — though with alpha compositing
the background comes from `--bg`, not stop-0, so it's not strictly required.

## Encoding

`libx264 -preset medium -crf 18 -pix_fmt yuv420p`, AAC 192k, `+faststart`, `-shortest`
(video length follows the audio). Bump `--crf` down for higher quality / up for smaller
files. For ProRes or transparency-preserving output you'd swap the codec block in `main()`.
