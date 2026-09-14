#!/usr/bin/env python3
"""
gen_chord_diagrams.py — chord diagram generator for OWNER/OPERATORS charts.

Usage:
    python gen_chord_diagrams.py chords.md        # expand voicing lines in-place
    python gen_chord_diagrams.py "x 3 2 0 1 0"   # print single diagram to stdout

A "voicing line" is any bare line with exactly 6 space-separated tokens,
each being x/o/0 or a fret number (1-12). The script inserts a ```chord```
block immediately after each voicing line that isn't already followed by one.
"""
import re
import sys


def parse_voicing(s: str) -> list | None:
    tokens = s.strip().split()
    if len(tokens) != 6:
        return None
    result = []
    for t in tokens:
        if t.lower() == 'x':
            result.append(None)      # muted
        elif t in ('0', 'o', 'O'):
            result.append(0)         # open
        else:
            try:
                n = int(t)
                result.append(n if n > 0 else 0)
            except ValueError:
                return None
    return result


def render_diagram(voicing: list) -> str:
    """
    Strings are ordered low→high: E A D G B E (indices 0–5).

    Three format cases:
      - Nut chord (fret 1 is fingered): no indent, ===========  nut line
      - Near-open chord (has open strings, fret 1 not fingered):
            2-space indent, plain -----------  opening, show from fret 1
      - High barre (no open strings, no fret 1):
            2-space indent, N ----------- opening, show from min fret
    """
    has_open = any(v == 0 for v in voicing)
    has_muted = any(v is None for v in voicing)
    fingered = [v for v in voicing if v is not None and v > 0]
    is_nut = 1 in fingered

    lines = []
    prefix = '' if is_nut else '  '

    # Top row — open/muted indicators (omit entirely if all strings are fingered)
    if has_open or has_muted:
        indicators = []
        for v in voicing:
            if v is None:
                indicators.append('x')
            elif v == 0:
                indicators.append('o')
            else:
                indicators.append(' ')
        top = ' '.join(indicators).rstrip()
        lines.append(prefix + top)

    # Display range
    if not fingered:
        start_fret, end_fret = 1, 2
    else:
        min_fret = min(fingered)
        max_fret = max(fingered)
        start_fret = 1 if (has_open or is_nut) else min_fret
        end_fret = max(max_fret, start_fret + 1)

    # Opening line
    if is_nut:
        lines.append('===========')
    elif has_open:
        lines.append('  -----------')     # near-open: no fret number
    else:
        lines.append(f'{start_fret} -----------')   # barre: show position

    # Fret rows — one (note-row + separator) pair per fret
    for fret in range(start_fret, end_fret + 1):
        row = ['*' if v == fret else '|' for v in voicing]
        lines.append(prefix + ' '.join(row))
        lines.append(prefix + '-----------')

    return '\n'.join(lines)


# Matches a line with exactly 6 space-separated voicing tokens
_VOICING_PAT = re.compile(r'^(?:[xoO0]|\d+)(?: (?:[xoO0]|\d+)){5}$')


def _is_voicing_line(line: str) -> bool:
    return bool(_VOICING_PAT.match(line.strip()))


def process_file(path: str) -> None:
    with open(path) as f:
        lines = f.readlines()

    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)

        if _is_voicing_line(line.rstrip('\n')):
            # Scan ahead (up to 5 non-blank lines) for an existing ```chord block,
            # stopping early if we hit a heading or another voicing line.
            j = i + 1
            already_done = False
            non_blank_seen = 0
            while j < len(lines) and non_blank_seen < 5:
                s = lines[j].strip()
                if s.startswith('```chord'):
                    already_done = True
                    break
                if s.startswith('#') or _is_voicing_line(s):
                    break
                if s:
                    non_blank_seen += 1
                j += 1

            if not already_done:
                voicing = parse_voicing(line.strip())
                if voicing is not None:
                    diagram = render_diagram(voicing)
                    out.append('```chord\n')
                    for dl in diagram.split('\n'):
                        out.append(dl + '\n')
                    out.append('```\n')

        i += 1

    with open(path, 'w') as f:
        f.writelines(out)
    print(f'Updated: {path}')


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]
    # If it looks like a voicing string (6 tokens), treat it as one; otherwise it's a file path
    voicing = parse_voicing(arg)
    if voicing is not None:
        print(render_diagram(voicing))
    else:
        process_file(arg)


if __name__ == '__main__':
    main()
