#!/usr/bin/env python3
"""
musicviz — turn any audio file into a Winamp-style visualization video.

Wraps ffmpeg's native audio-visualization filters (showcqt / showwaves /
showspectrum / avectorscope) plus a universal `pseudocolor` colorizer so every
preset shares the same palette system. No pip deps — just Python 3 + ffmpeg.

QUICK START
    ./visualize.py song.mp3
    ./visualize.py song.wav --preset bars --palette winamp --format tv --res 1080
    ./visualize.py song.flac --preset spectrum --palette magma --format social
    ./visualize.py song.mp3 --palette "#ff0080,#00e5ff,#ffffff"   # custom hex ramp

PRESETS  (the "look")   --list-presets for details
    bars       height-reactive spectrum bars (the classic)   [default]
    scope      oscilloscope / waveform line
    spectrum   scrolling spectrogram
    lissajous  stereo vectorscope (X/Y phase art)

PALETTES  (--list-palettes)
    named custom ...... winamp ice neon vapor sunset gold crimson emerald mono
    ffmpeg built-ins .. turbo magma inferno plasma viridis cividis spectral
                        cool heat fiery blues green helix
    arbitrary ......... comma-separated hex, e.g.  "#001a00,#00ff00,#ff0000"

FORMAT / RESOLUTION
    --format  tv|landscape (16:9)  ·  social|vertical (9:16)  ·  square (1:1)
              or an explicit  WxH   (e.g. --format 1600x900)
    --res     1080 | 720 | 480 | 360   (the long edge; ignored if WxH given)

COMMON KNOBS
    --bg 0x0a0a12     background color (hex; ignored if --bg-image)
    --bg-image FILE   image behind the viz (scaled+cropped to fill)
    --gain 1.0        sensitivity / bar height (0.3 quiet ... 3.0 hot)
    --glow 6          bloom radius in px (0 = off)
    --mirror          mirror the viz horizontally (bars/scope)
    --fps 30
    --start 12 --duration 30    render only a slice of the audio
    --dry-run         print the ffmpeg command and exit
    -o OUT.mp4        output path (default: <audio>_<preset>_<palette>.mp4)

Run with -h for the full flag list.
"""
import argparse, os, shlex, subprocess, sys

# ---- named custom palettes: list of (pos 0..1, (r,g,b)) --------------------
PALETTES = {
    "winamp":  [(0.0,(0,26,0)),   (0.45,(0,255,0)),  (0.72,(255,255,0)), (1.0,(255,0,0))],
    "ice":     [(0.0,(0,0,16)),   (0.5,(0,179,255)), (1.0,(255,255,255))],
    "neon":    [(0.0,(10,0,20)),  (0.5,(255,0,230)), (1.0,(0,255,242))],
    "vapor":   [(0.0,(26,11,46)), (0.5,(255,113,206)),(1.0,(1,205,254))],
    "sunset":  [(0.0,(26,0,51)),  (0.4,(255,46,99)), (0.75,(255,154,60)),(1.0,(255,226,154))],
    "gold":    [(0.0,(20,13,0)),  (0.6,(255,184,0)), (1.0,(255,243,192))],
    "crimson": [(0.0,(20,0,4)),   (0.55,(200,0,40)), (1.0,(255,180,120))],
    "emerald": [(0.0,(0,18,10)),  (0.5,(0,200,120)), (1.0,(200,255,180))],
    "mono":    [(0.0,(0,0,0)),    (1.0,(255,255,255))],
}
# ffmpeg pseudocolor built-in presets, exposed by name
PSEUDO_PRESETS = {"turbo","magma","inferno","plasma","viridis","cividis","spectral",
                  "cool","heat","fiery","blues","green","helix"}

# 16:9, 9:16, 1:1 canvases keyed by long-edge resolution
ASPECTS = {
    "tv":        lambda r: (round16(r*16/9), r),
    "landscape": lambda r: (round16(r*16/9), r),
    "social":    lambda r: (r, round16(r*16/9)),
    "vertical":  lambda r: (r, round16(r*16/9)),
    "square":    lambda r: (r, r),
}

def round16(x):  # even + friendly to codecs
    return int(round(x/2))*2

def even(x):
    return int(round(x/2))*2

# ---- preset definitions ----------------------------------------------------
# render(W,H,fps,gain) -> ffmpeg chain applied to [0:a], ending in a gray8 stream
# colorize_by: 'position' (color by height via vertical ramp) or 'intensity'
def r_bars(W,H,fps,gain):
    barv = max(1.0, 17*gain)
    return (f"showcqt=s={W}x{H}:sono_h=0:axis=0:text=0:bar_g=5:"
            f"bar_v={barv:.2f}:count=6:fps={fps},format=gray8")
def r_scope(W,H,fps,gain):
    return (f"showwaves=s={W}x{H}:mode=line:draw=full:scale=sqrt:"
            f"rate={fps}:colors=white,format=gray8")
def r_spectrum(W,H,fps,gain):
    g = max(0.1, gain)
    return (f"showspectrum=s={W}x{H}:mode=combined:slide=scroll:scale=cbrt:"
            f"fscale=log:gain={g:.2f}:color=intensity:fps={fps},format=gray8")
def r_lissajous(W,H,fps,gain):
    z = max(0.2, 1.4*gain)
    # aaline = smooth trace, scale=sqrt spreads quiet detail to fill the frame,
    # lagfun adds phosphor-scope persistence (smoother motion, fuller figure).
    return (f"avectorscope=s={W}x{H}:draw=aaline:mode=lissajous:scale=sqrt:"
            f"zoom={z:.2f}:rate={fps}:rc=180:gc=180:bc=180:rf=12:gf=12:bf=12,"
            f"lagfun=decay={args.decay:.3f},format=gray8")

PRESETS = {
    "bars":      dict(fn=r_bars,      by="position",  glow=6),
    "scope":     dict(fn=r_scope,     by="position",  glow=5),
    "spectrum":  dict(fn=r_spectrum,  by="intensity", glow=0),
    "lissajous": dict(fn=r_lissajous, by="intensity", glow=6),
}

# ---- palette -> pseudocolor filter string ----------------------------------
def stops_to_exprs(stops):
    pts = [(p*255.0, rgb) for p,rgb in stops]
    exprs = []
    for ch in range(3):
        terms = []
        for i in range(len(pts)-1):
            x0,c0 = pts[i]; x1,c1 = pts[i+1]
            a=c0[ch]; b=c1[ch]; span=(x1-x0) or 1
            hi = f"lt(val,{x1})" if i < len(pts)-2 else f"lte(val,{x1})"
            terms.append(f"gte(val,{x0})*{hi}*({a}+({b-a})*(val-{x0})/{span})")
        exprs.append("+".join(terms))
    return exprs

def hex_to_rgb(h):
    h = h.strip()
    if h.startswith("#"):        h = h[1:]
    elif h[:2].lower() == "0x":  h = h[2:]
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        sys.exit(f"bad hex color: {h!r}")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def resolve_palette(spec):
    """Return an ffmpeg pseudocolor filter string (fed a gray input)."""
    s = spec.strip()
    if s in PSEUDO_PRESETS:
        return f"pseudocolor=preset={s}"
    if s in PALETTES:
        stops = PALETTES[s]
    elif "," in s or s.startswith("#"):
        cols = [hex_to_rgb(c) for c in s.split(",") if c.strip()]
        if len(cols) == 1:
            cols = [(0,0,0)] + cols
        n = len(cols)-1
        stops = [(i/n, cols[i]) for i in range(len(cols))]
    else:
        sys.exit(f"unknown palette {s!r}. Try --list-palettes.")
    r,g,b = stops_to_exprs(stops)
    # pseudocolor works in gbrp plane order: c0->G, c1->B, c2->R
    return f"pseudocolor=i=0:c0='{g}':c1='{b}':c2='{r}'"

# ---- filtergraph assembly --------------------------------------------------
def build_filter(W,H,fps,preset,palette,bg,glow,mirror,has_bg_image):
    p = PRESETS[preset]
    gray = p["fn"](W,H,fps,args.gain)
    color = resolve_palette(palette)
    parts = []

    # background layer — must run at target fps or overlay (main=bg) throttles
    # the whole graph down to the color source's 25fps default
    if has_bg_image:
        parts.append(f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                     f"crop={W}:{H},setsar=1,fps={fps}[bg]")
    else:
        parts.append(f"color=c={bg}:s={W}x{H}:r={fps}[bg]")

    # gray intensity field (the viz), split into alpha mask + color source
    mir = ",hflip" if mirror else ""
    parts.append(f"[0:a]{gray}{mir},split[mA][mB]")

    if p["by"] == "position":
        # color by vertical position: multiply mask by a top-bright ramp, then colorize
        parts.append(f"color=c=black:s={W}x{H}:r={fps},format=gray8,"
                     f"geq=lum='40+215*(1-Y/H)'[ramp]")
        parts.append(f"[mB][ramp]blend=all_mode=multiply,format=gbrp,{color},format=rgb24[col]")
    else:
        # color by intensity (magnitude)
        parts.append(f"[mB]format=gbrp,{color},format=rgb24[col]")

    # paint palette onto the viz shape, lay over background
    parts.append("[col][mA]alphamerge[fg]")
    parts.append("[bg][fg]overlay[base]")

    # optional bloom — force RGB so `screen` blends color, not YUV chroma
    if glow and glow > 0:
        parts.append(f"[base]format=gbrp,split[bb][gg];[gg]gblur=sigma={glow}[gg];"
                     f"[bb][gg]blend=all_mode=screen,format=yuv420p[v]")
    else:
        parts.append("[base]format=yuv420p[v]")

    return ";".join(parts)

# ---- main ------------------------------------------------------------------
def main():
    global args
    ap = argparse.ArgumentParser(
        description="Winamp-style music visualization video from any audio file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument("audio", nargs="?", help="input audio file")
    ap.add_argument("-o","--out", help="output .mp4 path")
    ap.add_argument("--preset", default="bars", choices=list(PRESETS))
    ap.add_argument("--palette", default="winamp")
    ap.add_argument("--format", default="tv", help="tv|social|square or WxH")
    ap.add_argument("--res", type=int, default=1080, choices=[1080,720,480,360])
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--bg", default="0x0a0a12")
    ap.add_argument("--bg-image", dest="bg_image")
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--glow", type=float, default=None, help="bloom px (default: per-preset)")
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--decay", type=float, default=0.90,
                    help="lissajous phosphor-trail persistence 0..1 "
                         "(0=no trail, 0.95=long smooth trails; default 0.90)")
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-presets", action="store_true")
    ap.add_argument("--list-palettes", action="store_true")
    args = ap.parse_args()

    if args.list_presets:
        for k,v in PRESETS.items():
            print(f"  {k:10s} colorize-by={v['by']:9s} default-glow={v['glow']}")
        return
    if args.list_palettes:
        print("named:   " + " ".join(PALETTES))
        print("ffmpeg:  " + " ".join(sorted(PSEUDO_PRESETS)))
        print('custom:  comma-separated hex, e.g. "#ff0080,#00e5ff,#ffffff"')
        return
    if not args.audio:
        ap.error("audio file required (or use --list-presets / --list-palettes)")
    if not os.path.isfile(args.audio):
        sys.exit(f"no such file: {args.audio}")

    # canvas size
    fmt = args.format.lower()
    if "x" in fmt and fmt.replace("x","").isdigit():
        W,H = (even(int(v)) for v in fmt.split("x"))
    elif fmt in ASPECTS:
        W,H = ASPECTS[fmt](args.res)
    else:
        sys.exit(f"bad --format {args.format!r} (tv|social|square|WxH)")

    glow = PRESETS[args.preset]["glow"] if args.glow is None else args.glow

    out = args.out or (f"{os.path.splitext(os.path.basename(args.audio))[0]}"
                       f"_{args.preset}_{args.palette.strip('#').replace(',','-')[:16]}.mp4")

    fg = build_filter(W,H,args.fps,args.preset,args.palette,args.bg,glow,
                      args.mirror,bool(args.bg_image))

    cmd = ["ffmpeg","-hide_banner","-y"]
    if args.start is not None:  cmd += ["-ss", str(args.start)]
    if args.duration is not None: cmd += ["-t", str(args.duration)]
    cmd += ["-i", args.audio]
    if args.bg_image:
        cmd += ["-loop","1","-i", args.bg_image]
    cmd += ["-filter_complex", fg,
            "-map","[v]","-map","0:a","-r",str(args.fps),
            "-c:v","libx264","-preset","medium","-crf",str(args.crf),
            "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest",
            "-movflags","+faststart", out]

    if args.dry_run:
        print(" ".join(shlex.quote(c) for c in cmd))
        return

    print(f"[musicviz] {args.preset} · {args.palette} · {W}x{H}@{args.fps} -> {out}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit("ffmpeg failed (see output above). Try --dry-run to inspect the command.")
    print(f"[musicviz] wrote {out}")

if __name__ == "__main__":
    main()
