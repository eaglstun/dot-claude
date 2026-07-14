#!/usr/bin/env python3
"""Thin wrapper around the user's local FFglitch binaries (ffedit / ffgac / fflive).

Stdlib only. Resolves the binary directory from $FFGLITCH_DIR, else the known
install path. Every subcommand is a friendly front for the underlying binary and
passes any extra args straight through after `--`.

Run any subcommand with -h for its options. Quick tour:

    ffglitch.py features  in.m2v
    ffglitch.py prep      in.mov -o ready.m2v          # glitch-friendly re-encode
    ffglitch.py export    ready.m2v -f mv -o mv.json
    ffglitch.py apply     ready.m2v mv.json -f mv -o out.m2v
    ffglitch.py script    ready.m2v glitch.js -o out.m2v --sp 10
    ffglitch.py play      out.m2v                       # fflive player

IMPORTANT containers: ffedit does NOT accept MPEG Program Stream (.mpg). Glitch
raw elementary streams (.m2v for MPEG-2) or MPEG-4-part-2 in .avi. `prep` picks
the right one for you from the codec.
"""
import argparse
import os
import shutil
import subprocess
import sys

DEFAULT_DIR = "${HOME}/Documents/AI/ffglitch"


def ffg_dir():
    d = os.environ.get("FFGLITCH_DIR", DEFAULT_DIR)
    if not os.path.isdir(d):
        sys.exit(f"FFglitch dir not found: {d}\n"
                 f"Set $FFGLITCH_DIR or install to {DEFAULT_DIR}")
    return d


def binary(name):
    d = ffg_dir()
    p = os.path.join(d, name)
    if os.path.exists(p):
        return p
    p = shutil.which(name)          # fall back to $PATH
    if p:
        return p
    sys.exit(f"binary '{name}' not found in {d} or on $PATH")


def run(argv):
    print("+ " + " ".join(argv), file=sys.stderr)
    return subprocess.run(argv).returncode


# --- subcommands ------------------------------------------------------------

def cmd_features(a):
    # ffedit -i FILE with no output prints supported features for the codec
    return run([binary("ffedit"), "-i", a.input] + a.rest)


def cmd_export(a):
    argv = [binary("ffedit"), "-i", a.input]
    if a.feature:
        argv += ["-f", a.feature]
    argv += ["-e", a.output] + a.rest
    return run(argv)


def cmd_apply(a):
    argv = [binary("ffedit"), "-i", a.input]
    if a.feature:
        argv += ["-f", a.feature]
    argv += ["-a", a.data, "-y", "-o", a.output] + a.rest
    return run(argv)


def cmd_script(a):
    argv = [binary("ffedit"), "-i", a.input, "-s", a.script]
    if a.sp is not None:
        argv += ["-sp", a.sp]
    argv += ["-y", "-o", a.output] + a.rest
    return run(argv)


def cmd_prep(a):
    # Make ffmpeg "dumber" so glitches propagate. Pick container by codec.
    codec = a.codec
    out = a.output
    if out is None:
        ext = ".avi" if codec == "mpeg4" else ".m2v"
        base = os.path.splitext(os.path.basename(a.input))[0]
        out = f"{base}_glitchready{ext}"
    argv = [binary("ffgac"), "-i", a.input,
            "-c:v", codec,
            "-mpv_flags", "+forcemv+nopimb",
            "-g", "max", "-sc_threshold", "max", "-an"]
    if a.qscale is not None:
        argv += ["-qscale:v", str(a.qscale)]
    # raw mpeg2 needs the elementary-stream muxer forced
    if codec == "mpeg2video" and out.endswith((".m2v", ".mpv", ".raw")):
        argv += ["-f", "mpeg2video"]
    argv += ["-y", out] + a.rest
    rc = run(argv)
    if rc == 0:
        print(f"\nWrote {out}. Verify glitchable features with:\n"
              f"  {sys.argv[0]} features {out}", file=sys.stderr)
    return rc


def cmd_play(a):
    argv = [binary("fflive")]
    if a.script:
        argv += ["-s", a.script]
        if a.sp is not None:
            argv += ["-sp", a.sp]
    argv += [a.input] + a.rest
    return run(argv)


# --- arg parsing ------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        prog="ffglitch.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("features", help="list glitchable features for a file")
    s.add_argument("input")
    s.set_defaults(func=cmd_features)

    s = sub.add_parser("export", help="export codec data to JSON")
    s.add_argument("input")
    s.add_argument("-f", "--feature", help="e.g. mv, q_dc, mb (omit = all)")
    s.add_argument("-o", "--output", required=True, help="JSON out")
    s.set_defaults(func=cmd_export)

    s = sub.add_parser("apply", help="apply edited JSON back into a file")
    s.add_argument("input")
    s.add_argument("data", help="edited JSON")
    s.add_argument("-f", "--feature", help="same selection used on export")
    s.add_argument("-o", "--output", required=True)
    s.set_defaults(func=cmd_apply)

    s = sub.add_parser("script", help="run a JS/Python glitch script")
    s.add_argument("input")
    s.add_argument("script", help=".js or .py with setup()/glitch_frame()")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--sp", help="value passed to setup(args.params) via -sp")
    s.set_defaults(func=cmd_script)

    s = sub.add_parser("prep", help="ffgac re-encode into a glitch-friendly file")
    s.add_argument("input")
    s.add_argument("-o", "--output", help="default <name>_glitchready.<ext>")
    s.add_argument("--codec", default="mpeg2video",
                   choices=["mpeg2video", "mpeg4"])
    s.add_argument("--qscale", type=int, help="fix quantizer (e.g. 2-8)")
    s.set_defaults(func=cmd_prep)

    s = sub.add_parser("play", help="play (optionally with a live script) via fflive")
    s.add_argument("input")
    s.add_argument("-s", "--script", help="run this script live")
    s.add_argument("--sp", help="value for setup(args.params)")
    s.set_defaults(func=cmd_play)

    # Known args are parsed normally; anything left over (after `--` or plain)
    # is passed straight through to the underlying binary.
    a, extras = p.parse_known_args()
    if extras and extras[0] == "--":
        extras = extras[1:]
    a.rest = extras
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
