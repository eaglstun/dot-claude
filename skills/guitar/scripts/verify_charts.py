#!/usr/bin/env python3
"""
Audit every chords.md and bass.md in songs/ for music-theory accuracy.

What it checks
--------------

bass.md (lead-sheet flow format):
  - Every position in the Positions table has correct fret-to-note
    arithmetic in standard bass tuning (E A D G).
  - The Positions table covers the bass target note (root, or slash bass)
    of every chord that appears in the chord rows.
  - Sections and chord rows agree with the song's lead.md (the bass chart
    mirrors it).
  - Notes named in `_bass: ..._` cues match the slash chords in their row.

chords.md:
  - Voicings are encoded either as a "x 2 4 4 3 2" line OR as a chord-
    diagram block. We parse the diagram by walking the fret rows and
    reading `*` markers.
  - Every fingered string produces a pitch class in the named chord.
  - Slash chords have the correct bass note.
  - The lowest sounding note is the root or, for slash chords, the slash
    bass.

cross-file:
  - Every chord name in chords.md appears in bass.md and vice versa.
"""
from __future__ import annotations

import re, sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))  # for chart_lib

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
GUITAR_OPEN = ["E", "A", "D", "G", "B", "E"]   # low → high
BASS_OPEN_BY_LETTER = {"E": "E", "A": "A", "D": "D", "G": "G"}


def normalize_name(n: str) -> str:
    # also strip natural sign (♮) used to mark "borrowed natural" notes
    return (n.replace("♯", "#").replace("♭", "b").replace("♮", "").strip())


def normalize_note(n: str) -> str:
    n = normalize_name(n)
    if len(n) == 2 and n[1] == "b":
        idx = (NOTES.index(n[0]) - 1) % 12
        return NOTES[idx]
    return n


def note_at(open_note: str, fret: int) -> str:
    base = NOTES.index(normalize_note(open_note))
    return NOTES[(base + fret) % 12]


def pc(note: str) -> int:
    return NOTES.index(normalize_note(note))


# ---------------------------------------------------------------------------
# Chord pitch-class generation
# ---------------------------------------------------------------------------

INTERVAL_SEMITONES = {
    "1": 0, "b2": 1, "b9": 1, "2": 2, "9": 2, "b3": 3, "#9": 3, "3": 4,
    "4": 5, "11": 5, "b5": 6, "#11": 6, "5": 7, "b6": 8, "b13": 8,
    "6": 9, "13": 9, "bb7": 9, "b7": 10, "7": 10, "maj7": 11,
    "sus2": 2, "sus4": 5, "add9": 2, "add11": 5, "add13": 9,
}


def parse_chord(name: str) -> Tuple[str, Set[int], Optional[str], Dict[int, str]]:
    """Delegate to chart_lib's parser — one chord grammar for the whole skill."""
    from chart_lib import parse_chord as _parse
    c = _parse(name)
    slash = normalize_note(c.slash_bass) if c.slash_bass else None
    return normalize_note(c.root), set(c.pcs), slash, c.interval_at


# ---------------------------------------------------------------------------
# Guitar parsing — supports BOTH "x 2 4 4 3 2" voicing lines AND chord-
# diagram blocks.
# ---------------------------------------------------------------------------

def parse_voicing_line(line: str) -> Optional[List[Optional[int]]]:
    line = line.strip()
    # strip italicized annotation that follows " — "
    line = re.split(r"\s+—\s+", line)[0]
    line = re.split(r"\s+-\s+", line)[0]
    parts = line.split()
    if len(parts) != 6:
        return None
    out = []
    for p in parts:
        if p.lower() == "x":
            out.append(None)
        elif p.isdigit():
            out.append(int(p))
        else:
            return None
    return out


def parse_chord_diagram(block: str) -> Optional[List[Optional[int]]]:
    """
    Parse a fenced ``chord`` block. Return a 6-string voicing list:
    None for muted, int (fret number) for fingered.

    Format spec:
      - Optional top row with `o` (open) and `x` (muted) markers in the
        column positions of those strings. Spaces in other columns mean
        "fingered, fret > 0".
      - Then either `===========` (nut, fret-1 baseline) or
        `N -----------` (start at fret N, where N >= 2).
      - Then alternating finger-rows ( `* | | | | |` style ) and dash-
        lines (`-----------`).

    Layout: each row is 6 columns at positions 0,2,4,6,8,10. We walk the
    columns: for each string find the earliest finger-row containing `*`
    in that column, plus the start fret offset.
    """
    raw_lines = [ln for ln in block.split("\n") if ln.rstrip()]
    if not raw_lines:
        return None

    # Determine whether the first line is a top row (open/muted) or the
    # nut/start-fret line.
    top_row = None
    cursor = 0
    if "===" not in raw_lines[0] and not re.match(r"^\s*\d+\s*-+", raw_lines[0]):
        # top row of o/x markers (may also include spaces for fingered)
        top_row = raw_lines[0]
        cursor = 1

    # Next line tells us start fret
    if cursor >= len(raw_lines):
        return None
    nut_line = raw_lines[cursor]
    cursor += 1

    if "===" in nut_line:
        start_fret = 1
    elif re.match(r"^\s*-+\s*$", nut_line):
        # Older format: leading dashline acts as nut for fret-1 chords
        start_fret = 1
    else:
        m = re.match(r"^\s*(\d+)\s*-+", nut_line)
        if not m:
            return None
        start_fret = int(m.group(1))

    # Remaining lines alternate finger-row / dash-line.
    finger_rows: List[str] = []
    for ln in raw_lines[cursor:]:
        if re.match(r"^\s*-+\s*$", ln):
            continue
        if re.match(r"^\s*=+\s*$", ln):
            continue
        finger_rows.append(ln)

    # Each row should contain 6 column markers at positions 0,2,4,6,8,10
    # within the visible content (after possible leading 2-space indent).
    # Determine the column origin from the nut/dash line: the 6-string field
    # is the 11-char block where dashes are.
    nut_match = re.search(r"[-=]+", nut_line)
    if nut_match:
        column_origin = nut_match.start()
    else:
        column_origin = len(nut_line) - len(nut_line.lstrip())

    voicing: List[Optional[int]] = [None] * 6
    found = [False] * 6

    def get_col(row: str, string_idx: int) -> str:
        col = column_origin + string_idx * 2
        if col < len(row):
            return row[col]
        return " "

    if top_row is not None:
        for string_idx in range(6):
            ch = get_col(top_row, string_idx)
            if ch == "o":
                voicing[string_idx] = 0
                found[string_idx] = True
            elif ch == "x":
                voicing[string_idx] = None
                found[string_idx] = True

    for fret_offset, row in enumerate(finger_rows):
        for string_idx in range(6):
            if found[string_idx]:
                continue
            if get_col(row, string_idx) == "*":
                voicing[string_idx] = start_fret + fret_offset
                found[string_idx] = True

    for i in range(6):
        if not found[i]:
            voicing[i] = None

    return voicing


def extract_chord_sections(text: str) -> List[Tuple[str, str]]:
    """Return list of (chord_name, body) for each `### Chord` section."""
    sections = []
    for m in re.finditer(r"^### (.+?)\n(.*?)(?=^### |\Z)",
                         text, re.MULTILINE | re.DOTALL):
        head = m.group(1)
        # Strip italic annotation: "### Chord _(note)_"
        chord = re.split(r"\s+_", head)[0].strip()
        sections.append((chord, m.group(2)))
    return sections


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

POSITION_RE = re.compile(r"([EADG])-(\d+|open)")
CUE_NOTE_RE = re.compile(r"([A-G][#♯b♭]?)\s*\(([EADG])-(\d+|open)\)")


def _bass_sections(path: Path):
    """Parse a lead-sheet-flow file (lead.md or bass.md) via chart_lib."""
    from chart_lib import parse_lead
    return parse_lead(path.read_text())[1]


def audit_bass(path: Path) -> List[str]:
    """Audit a lead-sheet-flow bass.md."""
    issues: List[str] = []
    text = path.read_text()

    # --- Positions table: fret arithmetic ---
    table_notes: Set[str] = set()
    pos_block_m = re.search(r"^## Positions\n(.*?)(?=^## |\Z)", text,
                            re.MULTILINE | re.DOTALL)
    if not pos_block_m:
        issues.append("  no ## Positions table")
    else:
        for row_m in re.finditer(r"^\|\s*([A-G][#♯b♭]?)\s*\|(.+)\|\s*$",
                                 pos_block_m.group(1), re.MULTILINE):
            note = normalize_note(row_m.group(1))
            table_notes.add(note)
            for s, fret_s in POSITION_RE.findall(row_m.group(2)):
                fret = 0 if fret_s == "open" else int(fret_s)
                actual = note_at(s, fret)
                if actual != note:
                    issues.append(
                        f"  Positions: {row_m.group(1)} lists {s}-{fret_s} "
                        f"but that fret produces {actual}"
                    )

    # --- body rows: mirror lead.md, cover every bass target ---
    try:
        bass_sections = _bass_sections(path)
    except Exception as e:
        issues.append(f"  cannot parse chord rows ({e})")
        return issues
    bass_sections = [s for s in bass_sections if s.header != "Positions"
                     and not s.header.startswith("Positions")]

    lead_path = path.parent / "lead.md"
    if lead_path.exists():
        lead_sections = _bass_sections(lead_path)
        lead_map = [(s.header, [r.chords for r in s.rows]) for s in lead_sections]
        bass_map = [(s.header, [r.chords for r in s.rows]) for s in bass_sections]
        if lead_map != bass_map:
            lead_headers = [h for h, _ in lead_map]
            bass_headers = [h for h, _ in bass_map]
            if lead_headers != bass_headers:
                issues.append(
                    f"  sections don't mirror lead.md "
                    f"(lead: {lead_headers} / bass: {bass_headers})"
                )
            else:
                for (h, lrows), (_, brows) in zip(lead_map, bass_map):
                    if lrows != brows:
                        issues.append(f"  section '{h}': chord rows don't "
                                      f"mirror lead.md")
    else:
        issues.append("  no lead.md next to bass.md — can't verify mirror")

    # every chord's bass target (slash bass or root) must be in the table
    seen_chords: Set[str] = set()
    for sec in bass_sections:
        for row in sec.rows:
            seen_chords.update(row.chords)
    for chord_name in sorted(seen_chords):
        try:
            root, _, slash, _ = parse_chord(chord_name)
        except Exception as e:
            issues.append(f"  {chord_name}: cannot parse name ({e})")
            continue
        target = normalize_note(slash) if slash else root
        if table_notes and target not in table_notes:
            issues.append(
                f"  {chord_name}: bass target {target} missing from "
                f"Positions table"
            )

    # --- inline `_bass: ..._` cues: fret arithmetic ---
    for cue_m in re.finditer(r"^_bass:\s*(.+?)_\s*$", text, re.MULTILINE):
        for note, s, fret_s in CUE_NOTE_RE.findall(cue_m.group(1)):
            fret = 0 if fret_s == "open" else int(fret_s)
            actual = note_at(s, fret)
            if actual != normalize_note(note):
                issues.append(
                    f"  cue '{cue_m.group(1)}': {note} ({s}-{fret_s}) is "
                    f"WRONG — that fret produces {actual}"
                )

    return issues


def audit_guitar(path: Path) -> List[str]:
    issues: List[str] = []
    text = path.read_text()

    for chord_name, body in extract_chord_sections(text):
        try:
            root, pcs, slash, _ = parse_chord(chord_name)
        except Exception as e:
            issues.append(f"  {chord_name}: cannot parse name ({e})")
            continue
        if slash:
            # the slash bass is a legitimate tone anywhere in the voicing
            pcs = pcs | {(pc(slash) - pc(root)) % 12}

        # Try to find a "x 2 4 4 3 2" line first
        voicing: Optional[List[Optional[int]]] = None
        for ln in body.split("\n"):
            v = parse_voicing_line(ln)
            if v is not None:
                voicing = v; break

        # Otherwise try to parse the diagram block
        if voicing is None:
            diag = re.search(r"```chord\n(.*?)\n```", body, re.DOTALL)
            if diag:
                voicing = parse_chord_diagram(diag.group(1))

        if voicing is None:
            issues.append(f"  {chord_name}: no voicing or diagram found")
            continue

        produced: List[Tuple[int, str, int]] = []
        for i, fret in enumerate(voicing):
            if fret is None:
                continue
            n = note_at(GUITAR_OPEN[i], fret)
            produced.append((i, n, fret))

        if not produced:
            issues.append(f"  {chord_name}: voicing has no fingered strings")
            continue

        # Check 1: every fingered note is in the chord
        for i, n, f in produced:
            interval = (pc(n) - pc(root)) % 12
            if interval not in pcs:
                issues.append(
                    f"  {chord_name}: voicing produces {n} on string "
                    f"{GUITAR_OPEN[i]} fret {f} ({interval} semitones from "
                    f"{root}) — not a chord tone"
                )

        # Check 2: lowest note matches slash bass / is a reasonable inversion
        _, lowest_note, _ = produced[0]
        interval_low = (pc(lowest_note) - pc(root)) % 12
        if slash:
            if normalize_note(lowest_note) != slash:
                issues.append(
                    f"  {chord_name}: slash chord — lowest note is "
                    f"{lowest_note} but slash bass is {slash}"
                )
        elif interval_low not in (0, 3, 4, 7):
            # unusual inversion (not root, b3, 3, or 5)
            issues.append(
                f"  {chord_name}: lowest sounding note is {lowest_note} "
                f"({interval_low} semitones from {root}) — unusual inversion"
            )

    return issues


def chord_names(path: Path) -> Set[str]:
    text = path.read_text()
    names = set()
    for m in re.finditer(r"^### (.+?)$", text, re.MULTILINE):
        names.add(normalize_name(re.split(r"\s+_", m.group(1))[0].strip()))
    return names


def bass_chord_names(path: Path) -> Set[str]:
    """Chord names appearing in a lead-sheet-flow bass file's rows."""
    names: Set[str] = set()
    for sec in _bass_sections(path):
        if sec.header == "Positions":  # the note table, not a song section
            continue
        for row in sec.rows:
            names.update(normalize_name(c) for c in row.chords)
    return names


def main() -> int:
    # songs dir: CLI arg, else ./songs relative to the working directory
    songs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "songs"
    if not songs_dir.is_dir():
        print(f"not a directory: {songs_dir}", file=sys.stderr)
        return 2
    songs = sorted(p for p in songs_dir.iterdir() if p.is_dir())

    total = 0
    for song in songs:
        gpath = song / "chords.md"
        bpath = song / "bass.md"
        if not (gpath.exists() or bpath.exists()):
            continue

        out: List[str] = []
        if gpath.exists():
            for x in audit_guitar(gpath):
                out.append(f"  [chords.md]      {x.lstrip()}")
        if bpath.exists():
            for x in audit_bass(bpath):
                out.append(f"  [bass.md] {x.lstrip()}")
        if gpath.exists() and bpath.exists():
            g = chord_names(gpath); b = bass_chord_names(bpath)
            if not g:
                # chords.md with no ### sections is hand-written notes,
                # not a voicing chart — nothing to cross-check against
                g = b
            for missing in sorted(g - b):
                out.append(f"  [cross]          {missing!r} in chords.md but missing from bass.md")
            for missing in sorted(b - g):
                out.append(f"  [cross]          {missing!r} in bass.md but missing from chords.md")

        if out:
            print(f"\n=== {song.name} ===")
            for line in out:
                print(line)
            total += len(out)

    print(f"\n\nTotal issues: {total}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
