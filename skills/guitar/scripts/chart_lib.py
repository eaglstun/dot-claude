"""
chart_lib.py — shared theory + renderers for the OWNER/OPERATORS chart generator.

Used by gen_chart.py. Per-song chart.py files import Chord and Song from here.

Key principle: the user supplies (string, fret) bass positions — never the
note name. The library computes the note from string+fret. This makes
fret-arithmetic bugs structurally impossible.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# ---------------------------------------------------------------------------
# Note math
# ---------------------------------------------------------------------------

NOTES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTES_FLAT  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Open notes by string letter. Bass = E A D G; guitar = E A D G B E.
BASS_OPEN = {"E": "E", "A": "A", "D": "D", "G": "G"}
GUITAR_OPEN = ["E", "A", "D", "G", "B", "E"]   # low → high


def normalize_name(s: str) -> str:
    """Normalize unicode accidentals and natural sign."""
    return s.replace("♯", "#").replace("♭", "b").replace("♮", "").strip()


def note_pc(name: str) -> int:
    """Pitch class (0-11) of a note name. Accepts sharps and flats."""
    n = normalize_name(name)
    if n in NOTES_SHARP:
        return NOTES_SHARP.index(n)
    if n in NOTES_FLAT:
        return NOTES_FLAT.index(n)
    raise ValueError(f"unknown note name: {name!r}")


def note_at(open_letter: str, fret: int) -> int:
    """Pitch class produced by playing `fret` on a string opened to `open_letter`."""
    return (note_pc(open_letter) + fret) % 12


def pc_name(pc: int, prefer_sharp: bool = True) -> str:
    return (NOTES_SHARP if prefer_sharp else NOTES_FLAT)[pc % 12]


# ---------------------------------------------------------------------------
# Chord parser — chord name → set of pitch-class offsets from root
# ---------------------------------------------------------------------------

# semitone offset from root for each interval label
INTERVAL = {
    "1": 0, "b9": 1, "9": 2, "b3": 3, "#9": 3, "3": 4,
    "11": 5, "sus4": 5, "#11": 6, "b5": 6, "5": 7, "b13": 8, "#5": 8,
    "13": 9, "6": 9, "bb7": 9, "b7": 10, "maj7": 11,
    "sus2": 2, "add9": 2, "add11": 5, "add13": 9, "2": 2, "4": 5,
}

# Display name for each interval (used in label prefixes / descriptions)
INTERVAL_LABEL = {
    1: "b9", 2: "9", 3: "b3", 4: "3", 5: "11", 6: "#11", 7: "5",
    8: "b13", 9: "6", 10: "b7", 11: "maj7",
}


@dataclass
class ParsedChord:
    name: str           # original input ("Bm7(9,b13)")
    root: str           # "B"
    slash_bass: str | None  # "F#" if "/F#", else None
    pcs: set[int]       # set of pitch-class offsets from root, e.g. {0, 3, 7}
    interval_at: dict[int, str]  # pc-offset → label ({0:"1", 3:"b3", ...})
    quality: str        # "m", "maj7", "7", "sus4", "" (for major), etc.

    @property
    def root_pc(self) -> int:
        return note_pc(self.root)

    def chord_tone_pcs(self) -> set[int]:
        """Absolute pitch classes (0-11) for every chord tone."""
        return {(self.root_pc + i) % 12 for i in self.pcs}


def parse_chord(name: str) -> ParsedChord:
    raw = name
    s = normalize_name(name)

    slash_bass = None
    if "/" in s:
        s, slash_bass = s.split("/", 1)
        slash_bass = normalize_name(slash_bass)

    m = re.match(r"^([A-G][#b]?)(.*)$", s)
    if not m:
        raise ValueError(f"can't parse chord name: {raw!r}")
    root, qual = m.group(1), m.group(2)

    extensions: list[str] = []
    pm = re.search(r"\(([^)]+)\)", qual)
    if pm:
        extensions = [e.strip() for e in pm.group(1).split(",")]
        qual = re.sub(r"\([^)]+\)", "", qual)

    interval_at: dict[int, str] = {}

    def add(label: str):
        st = INTERVAL[label] % 12
        interval_at[st] = label

    add("1")
    quality_marker = ""

    # First: scan for `sus2`/`sus4`/`no3` anywhere in qual (they can follow
    # the 7 — e.g. "F#7sus4"). They suppress the 3rd entirely.
    sus_marker = None
    sm = re.search(r"sus[24]?", qual)
    if sm:
        sus_marker = sm.group(0)
        qual = qual[:sm.start()] + qual[sm.end():]

    no3 = "no3" in qual
    if no3:
        qual = qual.replace("no3", "")

    # triad
    if qual.startswith("dim"):
        add("b3"); add("b5"); qual = qual[3:]; quality_marker = "dim"
    elif qual.startswith("aug"):
        add("3"); add("#5"); qual = qual[3:]; quality_marker = "aug"
    elif sus_marker:
        if sus_marker == "sus2":
            add("sus2")
        else:
            add("sus4")
        add("5")
        quality_marker = sus_marker
    elif no3:
        add("5"); quality_marker = "no3"
    elif qual.startswith("m") and not qual.startswith("maj"):
        add("b3"); qual = qual[1:]; quality_marker = "m"
    else:
        add("3")

    # 5 (skipped if already settled)
    if 6 not in interval_at and 7 not in interval_at and 8 not in interval_at:
        add("5")

    # 7 / maj7 / 6
    # 7th / extended-dominant logic.
    # X7   = root + 3 + 5 + b7
    # X9   = root + 3 + 5 + b7 + 9       (dom9)
    # X11  = ... + b7 + 9 + 11           (dom11)
    # X13  = ... + b7 + 9 + 13           (dom13)
    # Xmaj7 = ... + maj7 (no b7)
    # Xmaj9 = ... + maj7 + 9
    # X6   = root + 3 + 5 + 6
    # X69  = root + 3 + 5 + 6 + 9
    if qual.startswith("maj"):
        # maj7, maj9, maj11, maj13
        m_ext = re.match(r"maj(\d+)", qual)
        if m_ext:
            top = int(m_ext.group(1))
            add("maj7")
            for ext_num in [9, 11, 13]:
                if ext_num <= top:
                    add(str(ext_num))
            qual = qual[len(m_ext.group(0)):]
            quality_marker += m_ext.group(0)
    elif qual.startswith("M7"):
        add("maj7"); qual = qual[2:]; quality_marker += "maj7"
    else:
        # X7 / X9 / X11 / X13 — dominant family
        m_ext = re.match(r"^(7|9|11|13)(?!\d)", qual)
        if m_ext:
            top = int(m_ext.group(1))
            add("b7")
            for ext_num in [9, 11, 13]:
                if ext_num <= top:
                    add(str(ext_num))
            qual = qual[len(m_ext.group(0)):]
            quality_marker += m_ext.group(0)
        elif qual.startswith("69"):
            add("6"); add("9"); qual = qual[2:]; quality_marker += "69"
        elif qual.startswith("6"):
            add("6"); qual = qual[1:]; quality_marker += "6"

    # add9 / add11 / etc. before paren extensions
    am = re.match(r"add(\d+)", qual)
    if am:
        ival = am.group(1)
        if ival in INTERVAL:
            add(ival)
            qual = qual[len(am.group(0)):]
            quality_marker += f"add{ival}"

    # paren extensions: (9), (b13), (9,11)
    for ext in extensions:
        ext = normalize_name(ext)
        if ext in INTERVAL:
            add(ext)

    # b13 / b9 in qual (e.g. "G#mb13")
    bm = re.match(r"b(\d+)", qual)
    if bm:
        cand = "b" + bm.group(1)
        if cand in INTERVAL:
            add(cand)

    return ParsedChord(
        name=raw,
        root=root,
        slash_bass=slash_bass,
        pcs=set(interval_at.keys()),
        interval_at=interval_at,
        quality=quality_marker,
    )


# ---------------------------------------------------------------------------
# Position parsing — "A-5" → ("A", 5), "D-open" → ("D", 0)
# ---------------------------------------------------------------------------

POS_RE = re.compile(r"^([EADG])-(\d+|open)$")


def parse_position(s: str) -> tuple[str, int]:
    m = POS_RE.match(s.strip())
    if not m:
        raise ValueError(f"bad bass position {s!r} — expected like 'A-5' or 'D-open'")
    fret = 0 if m.group(2) == "open" else int(m.group(2))
    return m.group(1), fret


# ---------------------------------------------------------------------------
# Bass targets & positions — for the lead-sheet-flow bass chart
# ---------------------------------------------------------------------------

def bass_target(chord_name: str) -> str:
    """The note the bass plays for a chord: slash bass if present, else root."""
    c = parse_chord(chord_name)
    return c.slash_bass if c.slash_bass else c.root


def _fret_for(note: str, string_letter: str) -> int:
    """Fret (0-11) producing `note`'s pitch class on a bass string."""
    return (note_pc(note) - note_pc(BASS_OPEN[string_letter])) % 12


def _fmt_pos(string_letter: str, fret: int) -> str:
    return f"{string_letter}-{'open' if fret == 0 else fret}"


def positions_for_note(note: str) -> tuple[list[str], list[str]]:
    """(low, high) position lists for a note: low = E/A strings, high = D/G.

    Each list is sorted by ascending fret and formatted like 'A-5' / 'E-open'.
    """
    low = sorted(((_fret_for(note, s), s) for s in ("E", "A")))
    high = sorted(((_fret_for(note, s), s) for s in ("D", "G")))
    return ([_fmt_pos(s, f) for f, s in low], [_fmt_pos(s, f) for f, s in high])


def primary_position(note: str) -> str:
    """The go-to low-neck position for a note — lowest fret on the E or A string."""
    return positions_for_note(note)[0][0]


# ---------------------------------------------------------------------------
# lead.md parser — the bass chart mirrors the lead sheet's flow
# ---------------------------------------------------------------------------

_CHORD_TOKEN_RE = re.compile(r"^[A-G][#♯b♭]?")


@dataclass
class LeadRow:
    raw: str                    # original "| D //// | ... |" line, verbatim
    chords: list[str]           # chord tokens in playing order (dupes kept)
    lyric: str | None = None    # the line immediately below the row, verbatim


@dataclass
class LeadSection:
    header: str                 # "Intro — bars 1-18" (without the ##)
    rows: list[LeadRow] = field(default_factory=list)


def _row_chords(row_line: str) -> list[str]:
    """Chord tokens from a lead-sheet chord row, in order."""
    # drop "(N bars)" annotations and italic "*(...)*" notes
    s = re.sub(r"\*\([^)]*\)\*", "", row_line)
    s = re.sub(r"\(\d+\s+bars?\)", "", s)
    chords = []
    for cell in s.split("|"):
        for tok in cell.split():
            if _CHORD_TOKEN_RE.match(tok):
                chords.append(normalize_name(tok))
    return chords


def parse_lead(text: str) -> tuple[str, list[LeadSection]]:
    """Parse a lead.md into (title, sections of chord rows + attached lyrics)."""
    title = ""
    sections: list[LeadSection] = []
    prev_row: LeadRow | None = None

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
            prev_row = None
        elif stripped.startswith("## "):
            sections.append(LeadSection(header=stripped[3:].strip()))
            prev_row = None
        elif stripped.startswith("|"):
            if not sections:
                raise ValueError("chord row before any ## section header")
            row = LeadRow(raw=stripped, chords=_row_chords(stripped))
            sections[-1].rows.append(row)
            prev_row = row
        elif stripped and prev_row is not None and prev_row.lyric is None:
            prev_row.lyric = stripped
        else:
            prev_row = None

    return title, sections


# ---------------------------------------------------------------------------
# Chord dataclass — the per-chord input to the generator
# ---------------------------------------------------------------------------

@dataclass
class Chord:
    family: str                   # "D", "B minor", "F#" — for `## D family` headers
    guitar: str                   # "x 2 4 4 3 2"
    guitar_note: str = ""         # "barre 2nd fret, Am shape" — annotation
    bass_low: list[str] = field(default_factory=list)   # ["A-2", "E-7", ...]
    bass_high: list[str] = field(default_factory=list)
    chord_note: str = ""          # extra annotation for `_(...)` after chord name
                                  # if empty, we auto-generate from chord tones


@dataclass
class Song:
    title: str                    # "Caught in the Chaos"
    sections: list[tuple[str, list[str]]] = field(default_factory=list)
    # [("Intro", ["Bm","Bm","G",...]), ("Verse 1", [...]), ...]
    # Used to build the quick-reference table at the bottom of each file.


# ---------------------------------------------------------------------------
# Validation — every position must be a chord tone of its chord
# ---------------------------------------------------------------------------

def validate_positions(chord_name: str, positions: Iterable[str]) -> list[str]:
    """Return a list of error messages, or [] if every position is a chord tone."""
    errors = []
    pc = parse_chord(chord_name)
    chord_tones = pc.chord_tone_pcs()
    if pc.slash_bass:
        chord_tones.add(note_pc(pc.slash_bass))
    for p in positions:
        try:
            string, fret = parse_position(p)
        except ValueError as e:
            errors.append(str(e))
            continue
        actual_pc = note_at(string, fret)
        if actual_pc not in chord_tones:
            actual_name = pc_name(actual_pc)
            interval_pc = (actual_pc - pc.root_pc) % 12
            errors.append(
                f"{chord_name}: position {p} produces {actual_name} "
                f"({interval_pc} semitones from {pc.root}) — not a chord "
                f"tone of {chord_name}"
            )
    return errors


# ---------------------------------------------------------------------------
# Bass tab grid renderer
# ---------------------------------------------------------------------------

TAB_WIDTH = 13


def _column_layout(positions: list[tuple[str, int]]) -> dict[tuple[str, int], int]:
    """
    Assign a column 0..12 to each position. Sorted by ascending fret. No two
    positions on different strings may share a column.

    Strategy: try to place each position at column = fret (so the visual
    layout tracks fret position naturally). On collision or overflow, bump
    rightward by 2.
    """
    if not positions:
        return {}

    string_order = {"E": 0, "A": 1, "D": 2, "G": 3}
    sorted_pos = sorted(positions, key=lambda p: (p[1], string_order[p[0]]))

    cols: list[int] = []
    used: set[int] = set()
    for (_, fret) in sorted_pos:
        target = fret
        # need at least 2 columns past previous to leave a dash separator
        if cols:
            target = max(target, cols[-1] + 2)
        # 2-digit frets need 2 contiguous columns; clip to TAB_WIDTH-2 in that case
        max_col = TAB_WIDTH - (2 if fret >= 10 else 1)
        target = min(target, max_col)
        # if collision (multiple positions at same fret on different strings),
        # bump
        while target in used:
            target += 1
        used.add(target)
        cols.append(target)

    return dict(zip(sorted_pos, cols))


def render_bass_tab(low: list[str], high: list[str]) -> str:
    """
    Render a 4-string bass tab. Each half is exactly TAB_WIDTH chars.
    `low` and `high` are lists of "string-fret" strings.
    """
    low_pos  = [parse_position(p) for p in low]
    high_pos = [parse_position(p) for p in high]

    low_layout  = _column_layout(low_pos)
    high_layout = _column_layout(high_pos)

    lines = []
    for letter in ("G", "D", "A", "E"):  # high → low for visual stacking
        left  = ["-"] * TAB_WIDTH
        right = ["-"] * TAB_WIDTH

        for (s, f), col in low_layout.items():
            if s == letter:
                _place(left, col, f)
        for (s, f), col in high_layout.items():
            if s == letter:
                _place(right, col, f)

        lines.append(f"{letter} |{''.join(left)}||{''.join(right)}|")
    return "\n".join(lines)


def _place(buf: list[str], col: int, fret: int) -> None:
    digits = str(fret)
    # 2-digit frets need 2 contiguous slots; place starting at col, but if
    # that runs past the end, shift left
    if col + len(digits) > len(buf):
        col = len(buf) - len(digits)
    for i, d in enumerate(digits):
        buf[col + i] = d


# ---------------------------------------------------------------------------
# Bass label line — group positions by pitch, mark intervals, bold characteristics
# ---------------------------------------------------------------------------

def _is_characteristic(interval_label: str, chord_quality: str) -> bool:
    """
    Decide whether an interval is "characteristic" (gets bolded).
    Rule of thumb: tones that are explicitly named or implied by the chord
    name itself — b3 in minor, b7 in 7-chords, the maj7 in maj7, extensions
    in parens, sus tones in sus chords, b13 borrowed.
    """
    q = chord_quality
    if interval_label in ("b9", "9", "11", "#11", "b13", "13", "maj7"):
        return True
    if interval_label == "b7" and "7" in q:
        return True
    if interval_label == "b3" and "m" in q:
        return True
    if interval_label == "6" and "6" in q:
        return True
    if interval_label in ("sus2", "sus4") and "sus" in q:
        return True
    if interval_label == "b5" and "dim" in q:
        return True
    if interval_label == "#5" and "aug" in q:
        return True
    return False


def render_bass_label(chord_name: str,
                      low: list[str],
                      high: list[str]) -> str:
    """
    Build the "B(A-2, G-4) · D(D-open, A-5) · ..." label line.

    Groups all positions (low + high, deduped) by pitch class. Within each
    group, positions sorted low-string first then ascending fret.
    """
    chord = parse_chord(chord_name)
    chord_tones = chord.chord_tone_pcs()
    if chord.slash_bass:
        chord_tones.add(note_pc(chord.slash_bass))

    all_positions = list(set(low) | set(high))
    by_pc: dict[int, list[tuple[str, int]]] = {}
    for p in all_positions:
        s, f = parse_position(p)
        by_pc.setdefault(note_at(s, f), []).append((s, f))

    string_order = {"E": 0, "A": 1, "D": 2, "G": 3}
    groups = []
    # iterate chord tones in interval-from-root order (root first, then 3rd,
    # 5th, 7th, 9th, ...) by sorting on a "musical priority" key
    interval_priority = [0, 4, 3, 7, 6, 8, 10, 11, 2, 1, 5, 9]

    def sort_key(pc: int) -> int:
        ival = (pc - chord.root_pc) % 12
        try:
            return interval_priority.index(ival)
        except ValueError:
            return 99

    pcs_present = sorted(by_pc.keys(), key=sort_key)

    slash_pc = note_pc(chord.slash_bass) if chord.slash_bass else None

    for pc in pcs_present:
        positions = sorted(by_pc[pc],
                           key=lambda sp: (string_order[sp[0]], sp[1]))
        pos_strs = [
            f"{s}-{'open' if f == 0 else f}" for s, f in positions
        ]
        note_name = pc_name(pc)
        # Prefix interval label for non-root chord tones
        ival = (pc - chord.root_pc) % 12

        is_slash = (pc == slash_pc) and chord.slash_bass and \
                   chord.slash_bass != chord.root

        if is_slash:
            label = f"bass {note_name}({', '.join(pos_strs)})"
            groups.append(label)
            continue

        if ival == 0:
            # root — no interval prefix
            label = f"{note_name}({', '.join(pos_strs)})"
        else:
            ival_label = chord.interval_at.get(ival)
            if ival_label is None:
                # tone is not in the chord — caller should've validated
                ival_label = INTERVAL_LABEL.get(ival, str(ival))

            if _is_characteristic(ival_label, chord.quality):
                # bold and prefix
                pretty = ival_label.replace("b", "♭")
                label = f"**{pretty} {note_name}({', '.join(pos_strs)})**"
            else:
                label = f"{note_name}({', '.join(pos_strs)})"
        groups.append(label)

    return " · ".join(groups)


# ---------------------------------------------------------------------------
# Auto-description for chord headers — `_(B, D, F# chord tones)_`
# ---------------------------------------------------------------------------

def chord_tone_description(chord_name: str) -> str:
    chord = parse_chord(chord_name)
    interval_priority = [0, 4, 3, 7, 6, 8, 10, 11, 2, 1, 5, 9]
    ordered = sorted(chord.pcs, key=lambda i: interval_priority.index(i)
                     if i in interval_priority else 99)
    notes = [pc_name((chord.root_pc + i) % 12) for i in ordered]
    return ", ".join(notes) + " chord tones"


# ---------------------------------------------------------------------------
# Self-test (run this module directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Spot-check the math
    assert note_at("E", 5) == note_pc("A"), "E string fret 5 should be A"
    assert note_at("G", 7) == note_pc("D"), "G string fret 7 should be D"
    assert note_at("D", 9) == note_pc("B"), "D string fret 9 should be B"

    # Chord parser
    bm = parse_chord("Bm7(9)")
    assert bm.root == "B"
    assert bm.pcs == {0, 3, 7, 10, 2}, f"Bm7(9) pcs wrong: {bm.pcs}"

    bm9b13 = parse_chord("Bm7(9,b13)")
    assert 8 in bm9b13.pcs, "Bm7(9,b13) should include b13"

    f7d = parse_chord("F#7sus4/D")
    assert f7d.slash_bass == "D"
    assert 5 in f7d.pcs and 7 in f7d.pcs and 10 in f7d.pcs

    # Validation flags non-chord-tones
    errs = validate_positions("C", ["G-7"])  # G-7 = D, not a tone of C major
    assert errs and "D" in errs[0], f"unexpected: {errs}"

    # Renderer round-trip on a simple chord
    # Bm = B + D + F#; positions A-2 (B), D-4 (F#), G-4 (B)
    label = render_bass_label("Bm", low=["A-2"], high=["D-4", "G-4"])
    assert "B(A-2, G-4)" in label, f"unexpected: {label}"
    assert "F#(D-4)" in label, f"unexpected: {label}"

    # Bass targets & positions
    assert bass_target("A7/D") == "D"
    assert bass_target("F#m") == "F#"
    assert primary_position("D") == "A-5"
    assert primary_position("F#") == "E-2"
    assert primary_position("E") == "E-open"
    low, high = positions_for_note("D")
    assert low == ["A-5", "E-10"], f"unexpected: {low}"
    assert high == ["D-open", "G-7"], f"unexpected: {high}"

    # lead.md parser
    lead = (
        "# Test Song\n\n## Intro — bars 1-4\n\n"
        "| D //// | D //// | (2 bars)\n\n"
        "| A // E // | F#m //// | *(half-time feel)*\n"
        "some lyric line\n"
    )
    title, sections = parse_lead(lead)
    assert title == "Test Song"
    assert sections[0].header == "Intro — bars 1-4"
    assert sections[0].rows[0].chords == ["D", "D"]
    assert sections[0].rows[1].chords == ["A", "E", "F#m"]
    assert sections[0].rows[1].lyric == "some lyric line"

    print("chart_lib self-test OK")
