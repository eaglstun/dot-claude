#!/usr/bin/env python3
"""Datamosh MPEG-1/2 elementary streams by I-frame removal + optional P-frame bloom.

The classic mosh: concatenate clips but drop every clip-after-the-first's
I-frame, so its motion vectors animate the previous clip's pixels. Optionally
"bloom" each splice by duplicating the first P-frame N times, compounding its
motion before the clip plays on.

Works on raw MPEG-1/2 elementary streams (.m2v). Non-.m2v inputs are prepped
automatically via ffgac (mpeg2video, +forcemv+nopimb, infinite GOP, no audio).

Usage:
    datamosh.py A.mov B.mov [C.mov ...] -o mosh.m2v
    datamosh.py A.m2v B.m2v -o mosh.m2v --bloom 15       # bloom each splice
    datamosh.py A.mov B.mov -o mosh.m2v --size 640x480 --qscale 4

Verified against FFglitch 0.10.2. Picture scanning is safe on MPEG-1/2:
start codes (00 00 01 xx) are byte-aligned and cannot occur inside slice data.

Deliver the result by transcoding ONCE at the very end with regular ffmpeg
(or ffgac): ffgac -i mosh.m2v -c:v libx264 -pix_fmt yuv420p final.mp4
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

DEFAULT_DIR = "${HOME}/Documents/AI/ffglitch"

I_FRAME, P_FRAME, B_FRAME = 1, 2, 3
PICTURE_START = re.compile(b"\x00\x00\x01\x00")


def ffgac():
    d = os.environ.get("FFGLITCH_DIR", DEFAULT_DIR)
    p = os.path.join(d, "ffgac")
    if not os.path.exists(p):
        sys.exit(f"ffgac not found at {p} (set $FFGLITCH_DIR)")
    return p


def prep(path, tmpdir, size=None, rate=None, qscale=None):
    """Re-encode any input into a glitch-friendly raw MPEG-2 elementary stream."""
    out = os.path.join(tmpdir, os.path.splitext(os.path.basename(path))[0] + ".m2v")
    argv = [ffgac(), "-i", path, "-c:v", "mpeg2video",
            "-mpv_flags", "+forcemv+nopimb",
            "-g", "max", "-sc_threshold", "max", "-an"]
    vf = []
    if size:
        vf.append(f"scale={size.replace('x', ':')}")
    if vf:
        argv += ["-vf", ",".join(vf)]
    if rate:
        argv += ["-r", str(rate)]
    if qscale is not None:
        argv += ["-qscale:v", str(qscale)]
    argv += ["-f", "mpeg2video", "-y", out]
    print("+ " + " ".join(argv), file=sys.stderr)
    subprocess.run(argv, check=True, stderr=subprocess.DEVNULL)
    return out


def pictures(data):
    """Yield (start, end, pict_type) for every coded picture in the stream.

    pict_type: 1=I, 2=P, 3=B (picture_coding_type bits in the picture header).
    """
    idxs = [m.start() for m in PICTURE_START.finditer(data)]
    out = []
    for i, s in enumerate(idxs):
        e = idxs[i + 1] if i + 1 < len(idxs) else len(data)
        ptype = (int.from_bytes(data[s + 4:s + 6], "big") >> 3) & 0x7
        out.append((s, e, ptype))
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="clips in mosh order (2+)")
    ap.add_argument("-o", "--output", required=True, help="output .m2v")
    ap.add_argument("--bloom", type=int, default=0, metavar="N",
                    help="duplicate the first P-frame of each spliced clip N times")
    ap.add_argument("--size", help="prep: scale to WxH (all clips should match!)")
    ap.add_argument("--rate", help="prep: force frame rate (all clips should match)")
    ap.add_argument("--qscale", type=int, help="prep: fixed quantizer (2=clean, 8=crunchy)")
    a = ap.parse_args()

    if len(a.inputs) < 2:
        sys.exit("need at least two clips to mosh")

    with tempfile.TemporaryDirectory() as tmp:
        streams = []
        for path in a.inputs:
            if path.lower().endswith((".m2v", ".mpv")) and not (a.size or a.rate or a.qscale):
                streams.append(open(path, "rb").read())
            else:
                streams.append(open(prep(path, tmp, a.size, a.rate, a.qscale), "rb").read())

        out = bytearray(streams[0])
        for data in streams[1:]:
            pics = pictures(data)
            try:
                first_p = next(p for p in pics if p[2] == P_FRAME)
            except StopIteration:
                sys.exit("clip has no P-frames — prep it (this shouldn't happen after prep)")
            # drop sequence/GOP headers + I-frame: keep from the first P picture on
            if a.bloom:
                out += data[first_p[0]:first_p[1]] * a.bloom
            out += data[first_p[0]:]

    with open(a.output, "wb") as f:
        f.write(out)
    print(f"wrote {a.output} ({len(out)} bytes). Preview: fflive {a.output}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
