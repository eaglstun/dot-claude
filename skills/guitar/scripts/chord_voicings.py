#!/usr/bin/env python3
"""
chord_voicings.py — find and rank playable guitar voicings for a chord.

Used by gen_pdf.py to build the boxed guitar chart: a chord's voicing advances
to a more interesting position each new section it appears in (plain major/minor
chords skip their standard first-position shape and start on non-standard ones;
complex chords start simplest and climb).

A voicing is the usual list of 6 ints (low→high E A D G B E), each None (muted),
0 (open), or a fret number — the same shape `chord_svg.render_chord_svg` draws.
Everything is computed from the chord name via chart_lib, so it needs no chart.py.
"""
from __future__ import annotations

import itertools
from functools import lru_cache

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from chart_lib import parse_chord, note_pc  # noqa: E402

OPEN_MIDI = [40, 45, 50, 55, 59, 64]  # E A D G B E, low→high
_ESSENTIAL_LABELS = ("3", "b3", "sus4", "sus2", "b7", "maj7", "6")


@lru_cache(maxsize=256)
def voicings_for(name: str, max_pos: int = 9) -> tuple[tuple, ...]:
    """Ranked playable voicings, simplest/lowest first.

    Searches each neck position for the fullest playable shape whose lowest
    string is the chord's bass note (slash bass on `X/Y`, else the root) and
    that contains the chord's defining tones. Returns a tuple of voicings, each
    a tuple of 6 items (None/0/int).
    """
    pc = parse_chord(name)
    tones = set(pc.chord_tone_pcs())
    bass_pc = note_pc(pc.slash_bass or pc.root)
    if pc.slash_bass:
        tones.add(bass_pc)  # the slash bass is playable even if not a chord tone
    root_pc = pc.root_pc
    essential = {root_pc}
    for off, label in pc.interval_at.items():
        if label in _ESSENTIAL_LABELS:
            essential.add((root_pc + off) % 12)

    seen: set[tuple] = set()
    out: list[tuple] = []
    for p in range(max_pos + 1):
        options: list[list] = []
        for om in OPEN_MIDI:
            opt = [None]
            # open strings only belong to nut-position shapes; up the neck the
            # shape must be fully fretted so it draws as a clean windowed diagram
            # with an "Nfr" position label instead of a stretched open hybrid.
            frets = ([0] if p <= 1 else []) + list(range(max(1, p), p + 4))
            for f in sorted(set(frets)):
                if (om + f) % 12 in tones:
                    opt.append(f)
            options.append(opt)

        best = None
        for combo in itertools.product(*options):
            sounding = [(i, f) for i, f in enumerate(combo) if f is not None]
            if len(sounding) < 4:
                continue
            lo, hi = sounding[0][0], sounding[-1][0]
            if (OPEN_MIDI[lo] + combo[lo]) % 12 != bass_pc:
                continue
            if any(combo[j] is None for j in range(lo, hi + 1)):
                continue  # sounding strings must be contiguous (no inner mutes)
            pcs = {(OPEN_MIDI[i] + f) % 12 for i, f in sounding}
            if not essential <= pcs:
                continue
            fretted = [f for _, f in sounding if f > 0]
            span = (max(fretted) - min(fretted)) if fretted else 0
            if span > 3:
                continue
            score = (-len(sounding), span, -len(pcs), sum(fretted))
            if best is None or score < best[0]:
                best = (score, combo)
        if best:
            v = best[1]
            if v not in seen:
                seen.add(v)
                out.append(v)
    return tuple(out)


def is_plain_triad(name: str) -> bool:
    """True for a bare major or minor chord (no 7th/extension/slash)."""
    pc = parse_chord(name)
    return pc.quality in ("", "m") and not pc.slash_bass


def voicing_pool(name: str) -> list[list]:
    """The progression pool for a chord, simplest→most interesting.

    Plain major/minor chords skip their standard first-position shape (the user
    wants non-standard positions); complex chords keep everything, simplest
    first. Falls back to whatever was found if skipping would empty the pool.
    """
    vs = [list(v) for v in voicings_for(name)]
    if not vs:
        return []
    if is_plain_triad(name) and len(vs) > 1:
        return vs[1:]
    return vs


if __name__ == "__main__":
    def fmt(v):
        return " ".join("x" if x is None else str(x) for x in v)
    for ch in sys.argv[1:] or ["D", "F#m", "Dmaj7", "A7/D", "Eadd9"]:
        print(f"{ch:12}", " | ".join(fmt(v) for v in voicing_pool(ch)))
