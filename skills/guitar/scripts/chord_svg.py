#!/usr/bin/env python3
"""
chord_svg.py — graphical (SVG) chord-diagram renderer for OWNER/OPERATORS charts.

This is the graphical twin of gen_chord_diagrams.render_diagram(): it takes the
same voicing input (a list of None/0/int, low→high E A D G B E) and emits a real
fretboard box — nut bar, string/fret grid, filled finger dots, o/× markers, barre
bar, and a "Nfr" position label for higher voicings.

Used by gen_pdf.py to replace ASCII ```chord blocks with actual shapes in PDFs.

Usage:
    python chord_svg.py "x 3 2 0 1 0"            # print SVG to stdout
    python chord_svg.py "4 6 6 4 4 4" -o gsm.svg # write SVG to a file
"""
from __future__ import annotations

import sys

# --- geometry (px at scale 1) ------------------------------------------------
STRINGS = 6
STRING_GAP = 12      # horizontal gap between strings
FRET_GAP = 16        # vertical gap between fret lines
PAD_TOP = 20         # room above the nut for o/× markers
PAD_BOTTOM = 8
PAD_LEFT = 11
PAD_RIGHT = 22       # room to the right for the "Nfr" label
MIN_FRETS = 4        # always draw at least this many fret spaces for a clean box

# Default colors (overridable via CSS — every element also carries a class)
_CSS = """
.chord-diagram .grid{stroke:#555;stroke-width:1;fill:none}
.chord-diagram .nut{stroke:#222;stroke-width:3.2}
.chord-diagram .dot{fill:#181818}
.chord-diagram .barre{stroke:#181818;fill:none;stroke-linecap:round}
.chord-diagram .marker{fill:#444;stroke:#444}
.chord-diagram .pos{fill:#444;font:italic 9px sans-serif}
.chord-diagram .name{fill:#181818;font:600 11px sans-serif}
"""


def parse_voicing(s: str) -> list | None:
    """Parse the first 6 whitespace tokens of `s` into a voicing list.

    Tokens beyond the sixth (e.g. ' — barre 2nd fret') are ignored, so a full
    voicing line from chords.md can be passed directly. Returns None if the
    first six tokens are not a valid voicing.
    """
    tokens = s.strip().split()
    if len(tokens) < STRINGS:
        return None
    out = []
    for t in tokens[:STRINGS]:
        if t.lower() == "x":
            out.append(None)
        elif t in ("0", "o", "O"):
            out.append(0)
        else:
            try:
                n = int(t)
            except ValueError:
                return None
            out.append(n if n > 0 else 0)
    return out


def _window(voicing: list) -> tuple[int, int, bool]:
    """Return (start_fret, n_frets, show_nut) for the display window.

    Mirrors gen_chord_diagrams' logic: open/nut chords start at fret 1 with a
    nut bar; higher closed voicings start at their lowest fret and get a label.
    """
    fingered = [v for v in voicing if isinstance(v, int) and v > 0]
    has_open = any(v == 0 for v in voicing)
    if not fingered:
        return 1, MIN_FRETS, True
    min_f, max_f = min(fingered), max(fingered)
    is_nut = min_f == 1
    if has_open or is_nut:
        start = 1
    else:
        start = min_f
    n_frets = max(MIN_FRETS, max_f - start + 1)
    return start, n_frets, start == 1


def _detect_barre(voicing: list) -> tuple[int, int, int] | None:
    """Return (start_string, end_string, fret) for a barre, or None.

    A barre is a contiguous run of fretted strings (no open/muted string inside
    the run) at least 4 strings wide whose two endpoints sit on the chord's
    lowest fret. The widest such run wins.
    """
    fretted = {j: v for j, v in enumerate(voicing) if isinstance(v, int) and v > 0}
    if not fretted:
        return None
    f = min(fretted.values())
    best: tuple[int, int, int] | None = None
    j = 0
    while j < STRINGS:
        if j in fretted:
            k = j
            while k + 1 < STRINGS and (k + 1) in fretted:
                k += 1
            ends = [x for x in range(j, k + 1) if fretted[x] == f]
            if len(ends) >= 2:
                a, b = ends[0], ends[-1]
                if (b - a + 1) >= 4 and (best is None or (b - a) > (best[1] - best[0])):
                    best = (a, b, f)
            j = k + 1
        else:
            j += 1
    return best


def render_chord_svg(voicing: list, name: str | None = None, scale: float = 1.0) -> str:
    """Render `voicing` (low→high E A D G B E) to an SVG string."""
    start, n_frets, show_nut = _window(voicing)

    x0, y0 = PAD_LEFT, PAD_TOP
    grid_w = (STRINGS - 1) * STRING_GAP
    grid_h = n_frets * FRET_GAP
    w = PAD_LEFT + grid_w + PAD_RIGHT
    h = PAD_TOP + grid_h + PAD_BOTTOM
    if name:
        y0 += 14
        h += 14

    def sx(j: int) -> float:    # x of string j (0 = low E, 5 = high E)
        return x0 + j * STRING_GAP

    def fy(k: int) -> float:    # y of fret line k (0 = top)
        return y0 + k * FRET_GAP

    el: list[str] = []

    if name:
        el.append(
            f'<text class="name" x="{x0 + grid_w / 2:.1f}" y="{PAD_TOP + 2:.1f}" '
            f'text-anchor="middle">{name}</text>'
        )

    # fret lines
    for k in range(n_frets + 1):
        cls = "nut" if (k == 0 and show_nut) else "grid"
        el.append(
            f'<line class="{cls}" x1="{x0:.1f}" y1="{fy(k):.1f}" '
            f'x2="{x0 + grid_w:.1f}" y2="{fy(k):.1f}"/>'
        )
    # string lines
    for j in range(STRINGS):
        el.append(
            f'<line class="grid" x1="{sx(j):.1f}" y1="{y0:.1f}" '
            f'x2="{sx(j):.1f}" y2="{y0 + grid_h:.1f}"/>'
        )

    # position label for higher voicings
    if not show_nut:
        el.append(
            f'<text class="pos" x="{x0 + grid_w + 4:.1f}" y="{fy(0) + FRET_GAP * 0.62:.1f}">'
            f'{start}fr</text>'
        )

    # open / muted markers above the grid
    my = y0 - 7
    for j, v in enumerate(voicing):
        if v is None:
            el.append(
                f'<text class="marker mut" x="{sx(j):.1f}" y="{my + 4:.1f}" '
                f'text-anchor="middle" style="font:bold 10px sans-serif">×</text>'
            )
        elif v == 0:
            el.append(
                f'<circle class="marker opn" cx="{sx(j):.1f}" cy="{my:.1f}" r="2.8" '
                f'fill="none" stroke-width="1.1"/>'
            )

    # barre: draw a bar only across a genuine full/half barre — a contiguous run
    # of fretted strings (no open/muted gap inside it) at least 4 strings wide,
    # with both endpoints on the lowest fret. This avoids mistaking finger chords
    # like D (x x 0 2 3 2) for barres just because two strings share a fret.
    fingered = [(j, v) for j, v in enumerate(voicing) if isinstance(v, int) and v > 0]
    barre = _detect_barre(voicing)
    if barre is not None:
        a, b, bf = barre
        cy = fy(bf - start) + FRET_GAP / 2
        el.append(
            f'<line class="barre" x1="{sx(a):.1f}" y1="{cy:.1f}" '
            f'x2="{sx(b):.1f}" y2="{cy:.1f}" stroke-width="8.4"/>'
        )

    # finger dots
    for j, v in fingered:
        cy = fy(v - start) + FRET_GAP / 2
        el.append(f'<circle class="dot" cx="{sx(j):.1f}" cy="{cy:.1f}" r="4.1"/>')

    vw, vh = w, h
    pw, ph = w * scale, h * scale
    body = "".join(el)
    return (
        f'<svg class="chord-diagram" xmlns="http://www.w3.org/2000/svg" '
        f'width="{pw:.0f}" height="{ph:.0f}" viewBox="0 0 {vw:.0f} {vh:.0f}" '
        f'role="img"><style>{_CSS}</style>{body}</svg>'
    )


def main() -> int:
    args = [a for a in sys.argv[1:]]
    out_path = None
    if "-o" in args:
        i = args.index("-o")
        out_path = args[i + 1]
        del args[i : i + 2]
    if not args:
        print(__doc__)
        return 1
    voicing = parse_voicing(args[0])
    if voicing is None:
        print(f"could not parse voicing: {args[0]!r}", file=sys.stderr)
        return 2
    name = args[1] if len(args) > 1 else None
    svg = render_chord_svg(voicing, name=name)
    if out_path:
        with open(out_path, "w") as f:
            f.write(svg)
        print(f"wrote {out_path}")
    else:
        print(svg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
