#!/usr/bin/env python3
"""
bass_tab_svg.py — per-bar bass phrases and their 4-string tab SVGs.

Used by gen_pdf.py to render the boxed bass lead sheet: each measure box shows
the chord name over a little 4-line tab staff (G/D/A/E, high→low). A bar with a
single chord gets an ascending root-plus-voicing arpeggio (the bass/slash note
at its lowest position, then up to three tones that most define the chord); a
split bar (e.g. "A // E //") shows each chord's bass note in sequence.

Everything is computed from the chord NAME via chart_lib, so the bass chart
reads straight from lead.md and never depends on chart.py's positions.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from chart_lib import parse_chord, note_pc  # noqa: E402

# Bass strings low→high, relative MIDI (E1=28). Only differences matter here.
OPEN = {"E": 28, "A": 33, "D": 38, "G": 43}
STRINGS_HIGH_TO_LOW = ("G", "D", "A", "E")


def _abs(string: str, fret: int) -> int:
    return OPEN[string] + fret


def _lowest_bass_pos(pc: int, max_fret: int = 7) -> tuple[str, int]:
    """Lowest-fret position for pitch class `pc` on the E or A string."""
    cands = []
    for s in ("E", "A"):
        for f in range(max_fret + 1):
            if (OPEN[s] + f) % 12 == pc % 12:
                cands.append((f, s))
    cands.sort()  # lowest fret wins; E before A on ties
    f, s = cands[0]
    return s, f


def _next_pos(pc: int, prev_abs: int, prev_fret: int,
              max_fret: int = 11) -> tuple[str, int]:
    """The next ascending note, placed at its most compact fret.

    Takes the lowest pitch of class `pc` above the previous note (an ascending
    arpeggio), then — since that exact pitch usually sits on two strings five
    frets apart — picks the LOWER fret so the hand crosses to a higher string
    instead of leaping up the neck. `prev_fret` breaks any remaining ties toward
    the nearest fret.
    """
    higher: list[tuple[int, int, int, str]] = []
    any_pos: list[tuple[int, int, int, str]] = []
    for s in STRINGS_HIGH_TO_LOW:
        for f in range(max_fret + 1):
            if (OPEN[s] + f) % 12 != pc % 12:
                continue
            entry = (_abs(s, f), f, abs(f - prev_fret), s)
            any_pos.append(entry)
            if _abs(s, f) > prev_abs:
                higher.append(entry)
    pool = higher or any_pos  # fall back if nothing higher is reachable
    pool.sort()  # lowest pitch, then lowest fret, then nearest previous fret
    _, f, _, s = pool[0]
    return s, f


def _characteristic_rank(label: str) -> int:
    """Lower = more defining of the chord's quality."""
    if label in ("3", "b3", "sus4", "sus2"):
        return 0
    if label in ("b7", "maj7", "6"):
        return 1
    if label in ("9", "11", "13", "b9", "#11", "b13", "#5", "b5"):
        return 2
    if label == "5":
        return 3
    return 4  # the root (as an upper tone over a slash bass) and anything else


def bass_phrase(chord_name: str, total: int = 4) -> list[tuple[str, int]]:
    """Ascending root-plus-voicing phrase for one chord.

    Returns up to `total` (string, fret) positions: the bass note (slash bass if
    present, else root) at its lowest position, then the most characteristic
    chord tones placed as an ascending arpeggio. Tones whose pitch class equals
    the bass note are skipped (no redundant repeats on slash chords).
    """
    pc = parse_chord(chord_name)
    bass = pc.slash_bass or pc.root
    bass_pc = note_pc(bass)

    s0, f0 = _lowest_bass_pos(bass_pc)
    phrase = [(s0, f0)]
    prev_abs = _abs(s0, f0)
    prev_fret = f0

    cands = []
    for off, label in pc.interval_at.items():
        tone_pc = (pc.root_pc + off) % 12
        if tone_pc == bass_pc:
            continue  # already sounding as the bass note
        if label == "1" and not pc.slash_bass:
            continue  # root == bass on a plain chord
        cands.append((_characteristic_rank(label), off, tone_pc))
    cands.sort()

    for _, _, tone_pc in cands[: max(0, total - 1)]:
        s, f = _next_pos(tone_pc, prev_abs, prev_fret)
        phrase.append((s, f))
        prev_abs = _abs(s, f)
        prev_fret = f
    return _tighten(phrase)


def _tighten(phrase: list[tuple[str, int]], max_fret: int = 11) -> list[tuple[str, int]]:
    """Pull any note that strays far up/down the neck back into the hand.

    The ascending build can leave one tone stranded (a dense chord's last note
    with nowhere to go but the 9th fret). Any note more than 4 frets off the
    median gets re-voiced to the same pitch class nearest the median fret. The
    bass note (index 0) is left at its low root position.
    """
    if len(phrase) < 3:
        return phrase
    frets = sorted(f for _, f in phrase)
    median = frets[len(frets) // 2]
    out = [phrase[0]]
    for s, f in phrase[1:]:
        if abs(f - median) <= 3:
            out.append((s, f))
            continue
        pc = (OPEN[s] + f) % 12
        alts = sorted(
            (abs(ff - median), ff, ss)
            for ss in STRINGS_HIGH_TO_LOW
            for ff in range(max_fret + 1)
            if (OPEN[ss] + ff) % 12 == pc
        )
        _, ff, ss = alts[0]
        out.append((ss, ff))
    return out


def bar_bass_notes(cell_chords: list[str]) -> list[tuple[str, int]]:
    """Bass notes to tab under one bar.

    One chord → its full arpeggio phrase. A split bar (multiple chords) → each
    chord's bass note in sequence, so the tab tracks the chord changes.
    """
    if not cell_chords:
        return []
    if len(cell_chords) == 1:
        return bass_phrase(cell_chords[0])
    out: list[tuple[str, int]] = []
    for name in cell_chords:
        pc = parse_chord(name)
        bass_pc = note_pc(pc.slash_bass or pc.root)
        out.append(_lowest_bass_pos(bass_pc))
    return out


def render_bass_phrase_svg(notes: list[tuple[str, int]]) -> str:
    """A fixed-size 4-line tab staff (G/D/A/E) with the phrase's fret numbers.

    Fixed pixel size so it drops into a fixed-width measure box; string labels
    ride at the far left of each line.
    """
    W, H = 126, 56
    pad_l, pad_r = 11, 5
    y = {s: 9 + i * 13 for i, s in enumerate(STRINGS_HIGH_TO_LOW)}  # 9,22,35,48

    p = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'xmlns="http://www.w3.org/2000/svg">']
    for s in STRINGS_HIGH_TO_LOW:
        p.append(f'<line x1="{pad_l}" y1="{y[s]}" x2="{W - pad_r}" y2="{y[s]}" '
                 f'stroke="#b8b8b8" stroke-width="1"/>')
        p.append(f'<text x="1" y="{y[s] + 3}" font-size="8" fill="#9a9a9a" '
                 f'font-family="monospace">{s}</text>')

    n = len(notes)
    x0 = pad_l + 5
    span = (W - pad_r) - x0
    for i, (s, f) in enumerate(notes):
        x = x0 + span * (i + 0.5) / n
        yy = y[s]
        p.append(f'<rect x="{x - 6:.1f}" y="{yy - 6}" width="12" height="12" fill="#ffffff"/>')
        p.append(f'<text x="{x:.1f}" y="{yy + 3.5:.1f}" font-size="10" fill="#1a1a1a" '
                 f'font-family="monospace" text-anchor="middle">{f}</text>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    for ch in sys.argv[1:] or ["D", "Dmaj7", "A7/D", "F#m", "Eadd9", "A6/F#"]:
        notes = bar_bass_notes([ch])
        print(ch, "->", notes)
