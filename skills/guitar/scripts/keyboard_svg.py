#!/usr/bin/env python3
"""
keyboard_svg.py — draw a piano chord diagram as an SVG.

Renders a 2-octave keyboard with a dot on each played note. The first note in
the spec is treated as the root/bass and drawn as a hollow ring; the rest are
solid dots. Dot colour flips per key (dark on white keys, light on black keys)
so it stays visible either way. This is the keyboard sibling of chord_svg.py
(which draws guitar fretboards).

Spec format: a space-separated note list, first note = bass/root, e.g.
    "G B D"        -> G major, root position
    "D# B F#"      -> B/D# (D# in the bass)

CLI:
    python keyboard_svg.py "G B D" -o test.svg
    python keyboard_svg.py "D F# A"        # SVG to stdout
"""
from __future__ import annotations

import argparse
import sys

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# geometry
WW, WH = 16, 78          # white key width / height
BW, BH = 9, 48           # black key width / height
N_OCT = 2                # octaves drawn
N_WHITE = 7 * N_OCT      # white keys total
W = N_WHITE * WW
H = WH

WHITE_KEY = "#ffffff"
BLACK_KEY = "#1c1c1c"
KEY_STROKE = "#333333"

# semitone (within octave) -> white-key index within octave
WHITE_ST = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
# black semitone -> the white-key index it sits to the right of
BLACK_ST_LEFT = {1: 0, 3: 1, 6: 3, 8: 4, 10: 5}
# white-local indices that have a black key to their right
BLACK_AFTER = [0, 1, 3, 4, 5]


def pc(name: str) -> int:
    name = name.strip().replace("♯", "#").replace("♭", "b")
    if not name:
        raise ValueError("empty note")
    letter = name[0].upper()
    base = NOTES.index(letter)
    for ch in name[1:]:
        if ch == "#":
            base += 1
        elif ch == "b":
            base -= 1
    return base % 12


def build_voicing(notes: list[str]) -> list[int]:
    """Stack notes ascending from the bass; returns absolute semitones (0-23+)."""
    positions: list[int] = []
    prev = -1
    for i, n in enumerate(notes):
        p = pc(n)
        if i == 0:
            pos = p              # bass sits at its pitch class in the low octave
        else:
            pos = p
            while pos <= prev:
                pos += 12
        positions.append(pos)
        prev = pos
    return positions


def _dot(cx: float, cy: float, r: float, on_black: bool, is_root: bool) -> str:
    color = "#f4f4f4" if on_black else "#141414"
    if is_root:
        fill = BLACK_KEY if on_black else WHITE_KEY
        return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                f'fill="{fill}" stroke="{color}" stroke-width="1.8"/>')
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{color}"/>'


def render_keyboard_svg(notes: list[str]) -> str:
    positions = build_voicing(notes)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W}" height="{H}">']

    # white keys
    for i in range(N_WHITE):
        parts.append(f'<rect x="{i*WW}" y="0" width="{WW}" height="{WH}" '
                     f'fill="{WHITE_KEY}" stroke="{KEY_STROKE}" stroke-width="1"/>')
    # black keys
    for octave in range(N_OCT):
        for local in BLACK_AFTER:
            gidx = octave * 7 + local
            x = (gidx + 1) * WW - BW / 2
            parts.append(f'<rect x="{x:.1f}" y="0" width="{BW}" height="{BH}" '
                         f'fill="{BLACK_KEY}" stroke="{KEY_STROKE}" stroke-width="1" rx="1.5"/>')

    # dots
    for idx, pos in enumerate(positions):
        octave, semi = pos // 12, pos % 12
        is_root = idx == 0
        if semi in WHITE_ST:
            gw = octave * 7 + WHITE_ST[semi]
            cx = gw * WW + WW / 2
            cy = WH - 13
            parts.append(_dot(cx, cy, 5.0, on_black=False, is_root=is_root))
        else:
            gw = octave * 7 + BLACK_ST_LEFT[semi]
            cx = (gw + 1) * WW
            cy = BH - 9
            parts.append(_dot(cx, cy, 4.2, on_black=True, is_root=is_root))

    parts.append("</svg>")
    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notes", help='space-separated notes, bass first, e.g. "G B D"')
    ap.add_argument("-o", "--out", help="write SVG here (default: stdout)")
    args = ap.parse_args()

    svg = render_keyboard_svg(args.notes.split())
    if args.out:
        with open(args.out, "w") as f:
            f.write(svg)
        print(f"Wrote {args.out}")
    else:
        sys.stdout.write(svg + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
