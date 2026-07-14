# chords.md format

Guitar voicings by chord family + quick-reference table.

```markdown
# Song Title — Chord Charts

Guitar, standard tuning. Strings written low → high: **E A D G B E**.
Numbers are fret positions; `x` = muted, `o` = open. Barre marked in
notes. These are common/recommended voicings — adjust to taste or to
match specific lines in the track.

## Family Name

### Chord Name _(optional note on chord quality)_

## Quick reference — all chords in play order
```

## Section Chords

Intro Chord · Chord · Chord

## Guitar chart rules

- Group chords by root-note family (C family, F family, G family, etc.)
- Within each family, order: root chord → maj7/min7 → sus → add → slash variants
- Voicing tab: six strings, space-separated, `x` for muted, fret number for fingered, `0` for open
- Annotation after the tab: one short note — `open`, `barre Nth fret`, `A-shape`, `partial open (notes)`
- For barre chords: note the fret and shape (`barre 4th fret, Am shape`)
- For slash chords: note which string carries the bass note
- For complex extensions: list the characteristic interval tones in the annotation (e.g., `F# · G# (9) · B (11)`)
- Quick-reference table groups sections, not individual chords — one row per section or section group

## Chord diagram spec (`chord` fenced blocks)

Each voicing tab block is followed immediately by a ` ```chord ``` ` block showing an ASCII fretboard diagram.

**Format rules:**

- Open strings (`0`) → `o` on the top row; muted strings (`x`) → `x` on the top row; fingered strings → ` ` (space) on the top row
- Top row is omitted entirely if there are no open or muted strings
- Nut line (when chord includes fret 1): `===========` (11 chars)
- There should be at least two frets
- Higher-position start line: `N -----------` where N is the lowest fret number; subsequent fret lines are `-----------` (indented to match)
- Finger markers: `*` at the fret where the string is fingered; `|` for all other strings on that row
- Bottom fret line: `-----------` (closing the diagram)
- Width: 11 chars of pipe/star/spaces per row (`X | X | X | X | X | X` — 6 chars + 5 spaces)
- Depth: one pair of (fret-line + note-row) per fret from min to max fret used

**Example — C (x 3 2 0 1 0):**

```
x     o   o
===========
| | | | * |
-----------
| | * | | |
-----------
| * | | | |
-----------
```

**Example — G#m (4 6 6 4 4 4), barre at 4:**

```
4 -----------
  * | | * * *
  -----------
  | | | | | |
  -----------
  | * * | | |
  -----------
```

**Generation:** Use `.claude/skills/guitar/scripts/gen_chord_diagrams.py` to auto-insert diagrams. The script skips any voicing block already followed by a `chord` block.

## PDF rendering

These ASCII `chord` blocks are for the markdown. When exporting to PDF (`scripts/gen_pdf.py`), each block is replaced with a real **graphical** SVG fretboard diagram drawn by `scripts/chord_svg.py` — same voicing input, but with a nut bar, filled finger dots, `o`/`×` markers, a barre bar, and an `Nfr` position label for higher voicings. A barre is only drawn across a genuine full/half barre: a contiguous run of fretted strings (no open/muted string inside it) at least 4 strings wide, with both endpoints on the lowest fret — so finger chords like D (`x x 0 2 3 2`) stay as separate dots.
