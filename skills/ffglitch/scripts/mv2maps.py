#!/usr/bin/env python3
"""Bake FFglitch motion-vector JSON into a displacement-map image sequence.

Turns `ffedit -f mv -e mv.json` output into 16-bit RGB PNGs — one pixel per
macroblock, X displacement in R, Y in G, neutral (no motion) = mid-gray 32768.
Feed the sequence to DaVinci Resolve Fusion's Vector Distortion node and the
glitch clip's motion field warps ANY footage: keyframeable, GPU-accelerated,
reusable. Also works as input to glitchgpu's mvwarp (which reads the JSON
directly, so maps are mainly for Resolve).

    ffedit -i ready.m2v -f mv -e mv.json
    mv2maps.py mv.json -o maps/            # writes maps/mv_00000.png ...

Fusion wiring (Resolve):
  1. Import maps/ as an image sequence; set its clip length to match.
  2. MediaIn(footage) -> VectorDistortion.Input,
     MediaIn(maps)    -> VectorDistortion.Distort.
  3. X Channel = Red, Y Channel = Green, Center Bias / offset 0.5.
  4. Scale slider to taste. Bilinear upscaling of the tiny map = smooth warp;
     insert a Resize node (nearest neighbor) before it for blocky 16x16 looks.

MPEG-2 MVs are half-pel: an exported [2,0] is ~1 px right. --scale maps MV
units to the 16-bit range: pixel_value = 32768 + mv * scale. The default 256
means the full range covers MVs of ±128 half-pel; crank --scale for subtle
motion, lower it if values clip (the script reports clipping).

Stdlib only (zlib PNG writer). Verified against FFglitch 0.10.2 exports.
"""
import argparse
import json
import os
import struct
import sys
import zlib


def png16_rgb(width, height, pixels):
    """Write a 16-bit RGB PNG. pixels = flat list of (r, g, b) uint16 tuples."""
    raw = bytearray()
    i = 0
    for _y in range(height):
        raw.append(0)  # filter type: None
        for _x in range(width):
            r, g, b = pixels[i]
            raw += struct.pack(">HHH", r, g, b)
            i += 1

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, 0)  # 16-bit, RGB
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_file", help="ffedit -f mv export")
    ap.add_argument("-o", "--outdir", default="mv_maps", help="output directory")
    ap.add_argument("--scale", type=float, default=256.0,
                    help="16-bit units per MV half-pel unit (default 256)")
    ap.add_argument("--direction", choices=["forward", "backward"],
                    default="forward")
    ap.add_argument("--prefix", default="mv_", help="filename prefix")
    ap.add_argument("--stream", type=int, default=0, help="stream index")
    a = ap.parse_args()

    with open(a.json_file) as f:
        data = json.load(f)
    frames = data["streams"][a.stream]["frames"]
    os.makedirs(a.outdir, exist_ok=True)

    dims = None  # (cols, rows) from the first frame that has a grid
    for fr in frames:
        grid = (fr.get("mv") or {}).get(a.direction)
        if grid:
            dims = (len(grid[0]), len(grid))
            break
    if dims is None:
        sys.exit(f"no '{a.direction}' motion vectors in any frame of {a.json_file}")
    cols, rows = dims

    mid = 32768
    clipped = 0
    written = 0
    for n, fr in enumerate(frames):
        grid = (fr.get("mv") or {}).get(a.direction)
        pixels = []
        for y in range(rows):
            for x in range(cols):
                cell = grid[y][x] if grid else None
                if cell is None:
                    pixels.append((mid, mid, mid))  # intra/skipped: neutral
                    continue
                r = mid + int(cell[0] * a.scale)
                g = mid + int(cell[1] * a.scale)
                if not (0 <= r <= 65535 and 0 <= g <= 65535):
                    clipped += 1
                pixels.append((min(65535, max(0, r)),
                               min(65535, max(0, g)), mid))
        path = os.path.join(a.outdir, f"{a.prefix}{n:05d}.png")
        with open(path, "wb") as f:
            f.write(png16_rgb(cols, rows, pixels))
        written += 1

    print(f"wrote {written} maps ({cols}x{rows}) to {a.outdir}/", file=sys.stderr)
    if clipped:
        print(f"WARNING: {clipped} MV components clipped — lower --scale",
              file=sys.stderr)


if __name__ == "__main__":
    main()
