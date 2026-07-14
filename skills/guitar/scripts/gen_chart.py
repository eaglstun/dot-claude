#!/usr/bin/env python3
"""
gen_chart.py — generate chords.md and bass.md from a song's chart.py.

Usage:
    python gen_chart.py <song-dir>               # generate both files in-place
    python gen_chart.py <song-dir> --only bass   # just bass.md
    python gen_chart.py <song-dir> --check       # validate only, don't write

Each song dir must contain a `chart.py` defining:

    SONG = Song(title="...")
    CHORDS = {"Bm": Chord(...), ...}
    BASS_CUES = {"A7/D · F#7sus4/D": "Stay on D ...", ...}   # optional

The generator validates that every bass position is a chord tone of its
chord (catches fret-arithmetic errors). It then writes:

    <song-dir>/chords.md          (guitar voicings + diagrams + quick ref)
    <song-dir>/bass.md            (lead-sheet-flow bass chart: mirrors
                                   lead.md's sections/rows/lyrics with inline
                                   bass cues + a Positions table up top)

The bass chart is built from the song's lead.md, so lead.md must exist and
be current before regenerating. BASS_CUES keys are chord names (or ` · `-
joined chord sequences) anchoring each hand-written feel cue to the first
lead.md row that contains them; a key that matches no row is an error.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from chart_lib import (
    Chord, Song, parse_chord, validate_positions,
    chord_tone_description, note_at, pc_name, normalize_name,
    bass_target, positions_for_note, primary_position, parse_lead,
)
from gen_chord_diagrams import parse_voicing, render_diagram


# ---------------------------------------------------------------------------
# Loading the per-song chart.py
# ---------------------------------------------------------------------------

def load_chart(song_dir: Path):
    chart_path = song_dir / "chart.py"
    if not chart_path.exists():
        raise FileNotFoundError(f"missing {chart_path}")

    spec = importlib.util.spec_from_file_location(
        f"chart_{song_dir.name}", chart_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    song = getattr(module, "SONG", None)
    chords = getattr(module, "CHORDS", None)
    if song is None or chords is None:
        raise ValueError(f"{chart_path} must define SONG and CHORDS")
    bass_cues = getattr(module, "BASS_CUES", {})
    return song, chords, bass_cues


# ---------------------------------------------------------------------------
# Validation pass
# ---------------------------------------------------------------------------

def validate(chords: dict[str, Chord]) -> list[str]:
    errors: list[str] = []
    for name, chord in chords.items():
        # Bass positions must be chord tones
        all_pos = chord.bass_low + chord.bass_high
        if all_pos:
            errors += validate_positions(name, all_pos)

        # Guitar voicing must produce only chord tones
        voicing = parse_voicing(chord.guitar)
        if voicing is None:
            errors.append(f"{name}: unparseable guitar voicing {chord.guitar!r}")
            continue
        parsed = parse_chord(name)
        chord_tones = parsed.chord_tone_pcs()
        if parsed.slash_bass:
            chord_tones.add(__import__("chart_lib").note_pc(parsed.slash_bass))

        guitar_open = ["E", "A", "D", "G", "B", "E"]
        for i, fret in enumerate(voicing):
            if fret is None:
                continue
            actual = note_at(guitar_open[i], fret)
            if actual not in chord_tones:
                errors.append(
                    f"{name}: guitar string {guitar_open[i]} fret {fret} "
                    f"produces {pc_name(actual)} — not a chord tone"
                )

        # Slash chord: lowest fingered string should be the slash bass
        if parsed.slash_bass:
            from chart_lib import note_pc
            slash_pc = note_pc(parsed.slash_bass)
            for i, fret in enumerate(voicing):
                if fret is None:
                    continue
                actual = note_at(guitar_open[i], fret)
                if actual != slash_pc:
                    errors.append(
                        f"{name}: slash chord but lowest sounding note is "
                        f"{pc_name(actual)} (expected {parsed.slash_bass})"
                    )
                break

    return errors


# ---------------------------------------------------------------------------
# Render chords.md
# ---------------------------------------------------------------------------

PREAMBLE_GUITAR = """\
Guitar, standard tuning. Strings written low → high: **E A D G B E**.
Numbers are fret positions; `x` = muted, `o` = open. Barre marked in
notes. These are common/recommended voicings — adjust to taste or to
match specific lines in the track.
"""

def render_chords_md(song: Song, chords: dict[str, Chord]) -> str:
    out: list[str] = []
    out.append(f"# {song.title} — Chord Charts\n")
    out.append(PREAMBLE_GUITAR)

    families = _group_by_family(chords)
    for fam, names in families.items():
        out.append(f"\n## {fam} family\n")
        for name in names:
            chord = chords[name]
            desc = chord.chord_note or chord_tone_description(name)
            out.append(f"\n### {name} _({desc})_\n")
            note = chord.guitar_note or _auto_guitar_note(chord.guitar)
            out.append(f"\n{chord.guitar} — {note}\n")
            voicing = parse_voicing(chord.guitar)
            diagram = render_diagram(voicing)
            out.append("\n```chord\n" + diagram + "\n```\n")

    out.append(_quick_ref_table(song, "Chords"))
    return "".join(out)


def _auto_guitar_note(voicing_str: str) -> str:
    voicing = parse_voicing(voicing_str)
    if voicing is None:
        return ""
    fingered = [v for v in voicing if v is not None and v > 0]
    if not fingered:
        return "open"
    if 1 in fingered:
        return "open / nut chord"
    return f"position {min(fingered)}"


# ---------------------------------------------------------------------------
# Render bass.md — lead-sheet flow
#
# The bass chart mirrors lead.md top to bottom: same sections, same chord
# rows, same lyric cue lines. Bass-specific info rides inline: an italic
# `_bass: ..._` cue under any row with slash chords (the note isn't the
# root), and hand-authored feel cues from chart.py's optional BASS_CUES.
# One compact Positions table up top replaces the old per-chord tab library.
# ---------------------------------------------------------------------------

# one source line — flow files render soft breaks as real breaks in the PDF
PREAMBLE_BASS = (
    "Standard tuning, low→high: **E A D G**. Play the chord root; on slash "
    "chords (`X/Y`) play the slash note `Y` — inline `bass:` cues call these "
    "out. Positions written `String-fret` (`A-5` = A string, 5th fret); the "
    "table below shows where every note in the song lives.\n"
)


def _pretty_note(note: str) -> str:
    n = normalize_name(note)
    if len(n) == 2:
        return n[0] + {"#": "♯", "b": "♭"}[n[1]]
    return n


def _collapse(chords: list[str]) -> list[str]:
    """Collapse consecutive duplicates: [D, D, F#m, F#m] → [D, F#m]."""
    out: list[str] = []
    for c in chords:
        if not out or out[-1] != c:
            out.append(c)
    return out


def _parse_cue_anchor(key: str) -> list[str]:
    """BASS_CUES key → chord-name sequence. 'A7/D · F#7sus4/D' → 2 names."""
    return [normalize_name(p.strip().strip("`")) for p in key.split("·")]


def _row_matches_anchor(row_chords: list[str], anchor: list[str]) -> bool:
    """True if `anchor` is a contiguous subsequence of the collapsed row."""
    seq = _collapse(row_chords)
    n = len(anchor)
    return any(seq[i:i + n] == anchor for i in range(len(seq) - n + 1))


def _auto_slash_cue(row_chords: list[str]) -> str | None:
    """Inline cue for slash chords in a row, or None if the row is all roots."""
    slashes = []  # (chord_name, target_note) unique, in order
    for name in _collapse(row_chords):
        parsed = parse_chord(name)
        if parsed.slash_bass and (name, parsed.slash_bass) not in slashes:
            slashes.append((name, parsed.slash_bass))
    if not slashes:
        return None

    targets = {t for _, t in slashes}
    all_slash = all(parse_chord(n).slash_bass for n in row_chords)
    if all_slash and len(targets) == 1:
        note = slashes[0][1]
        return f"_bass: {_pretty_note(note)} ({primary_position(note)}) throughout_"

    parts = [f"{name} → {_pretty_note(t)} ({primary_position(t)})"
             for name, t in slashes]
    return f"_bass: {' · '.join(parts)}_"


def _positions_table(sections) -> str:
    """One row per unique bass target note, in order of first appearance."""
    targets: list[str] = []
    for sec in sections:
        for row in sec.rows:
            for name in row.chords:
                t = bass_target(name)
                if t not in targets:
                    targets.append(t)

    lines = ["## Positions", "",
             "| Note | Low (E/A) | Octave up (D/G) |",
             "| ---- | --------- | --------------- |"]
    for t in targets:
        low, high = positions_for_note(t)
        lines.append(f"| {_pretty_note(t)} | {' · '.join(low)} | {' · '.join(high)} |")
    return "\n".join(lines)


def render_bass_md(song: Song, lead_text: str,
                   bass_cues: dict[str, str] | None = None) -> str:
    bass_cues = bass_cues or {}
    _, sections = parse_lead(lead_text)
    if not sections:
        raise ValueError("lead.md has no sections — can't build the bass chart")

    # cue anchors fire once, at the first row they match
    pending_cues = [(key, _parse_cue_anchor(key), text)
                    for key, text in bass_cues.items()]

    out: list[str] = [f"# {song.title} — Bass", "", PREAMBLE_BASS.rstrip(), ""]
    out.append(_positions_table(sections))

    for sec in sections:
        out.extend(["", f"## {sec.header}"])
        seen_auto_cues: set[str] = set()
        for row in sec.rows:
            out.extend(["", row.raw])
            if row.lyric:
                out.append(row.lyric)

            matched_hand_cue = False
            for key, anchor, text in list(pending_cues):
                if _row_matches_anchor(row.chords, anchor):
                    out.append(f"_{key} — {text}_")
                    pending_cues.remove((key, anchor, text))
                    matched_hand_cue = True

            if not matched_hand_cue:
                cue = _auto_slash_cue(row.chords)
                if cue and cue not in seen_auto_cues:
                    out.append(cue)
                    seen_auto_cues.add(cue)

    if pending_cues:
        unmatched = ", ".join(repr(k) for k, _, _ in pending_cues)
        raise ValueError(f"BASS_CUES never matched a lead.md row: {unmatched}")

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Quick-reference table (shared)
# ---------------------------------------------------------------------------

def _quick_ref_table(song: Song, value_header: str) -> str:
    if not song.sections:
        return ""
    rows = ["\n## Quick reference — play order\n",
            f"\n| Section | {value_header} |",
            "| --- | --- |"]
    for section_name, section_chords in song.sections:
        chord_str = " · ".join(section_chords)
        rows.append(f"| {section_name} | {chord_str} |")
    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------------------
# Family grouping
# ---------------------------------------------------------------------------

def _group_by_family(chords: dict[str, Chord]) -> dict[str, list[str]]:
    fams: dict[str, list[str]] = defaultdict(list)
    for name, chord in chords.items():
        fams[chord.family].append(name)
    # stable order: families in insertion order, names within in insertion order
    return dict(fams)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("song_dir", help="path to songs/<slug>/ directory")
    parser.add_argument("--check", action="store_true",
                        help="validate only, don't write files")
    parser.add_argument("--only", choices=["chords", "bass"],
                        help="generate just one of the two files")
    args = parser.parse_args()

    song_dir = Path(args.song_dir).resolve()
    if not song_dir.is_dir():
        print(f"not a directory: {song_dir}", file=sys.stderr)
        return 2

    song, chords, bass_cues = load_chart(song_dir)
    errors = validate(chords)
    if errors:
        print(f"VALIDATION FAILED for {song.title} ({len(errors)} issues):")
        for e in errors:
            print(f"  - {e}")
        return 1

    if args.check:
        print(f"OK: {song.title} — {len(chords)} chords valid")
        return 0

    if args.only in (None, "chords"):
        if not chords:
            # empty CHORDS marks a song whose chords.md is hand-written —
            # never overwrite it with a generated (and empty) chart
            print("CHORDS is empty — skipping chords.md")
        else:
            chords_md = song_dir / "chords.md"
            chords_md.write_text(render_chords_md(song, chords))
            print(f"Wrote {chords_md.relative_to(song_dir.parent.parent)}")

    if args.only in (None, "bass"):
        lead_path = song_dir / "lead.md"
        if not lead_path.exists():
            print(f"missing {lead_path} — the bass chart mirrors lead.md",
                  file=sys.stderr)
            return 2
        bass_md = song_dir / "bass.md"
        bass_md.write_text(
            render_bass_md(song, lead_path.read_text(), bass_cues))
        print(f"Wrote {bass_md.relative_to(song_dir.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
