---
name: guitar
version: 1.0.0
public: true
description: >-
  Create or format lead sheets, guitar chord charts, bass tablature, and engraved cello
  sheet music for OWNER/OPERATORS songs. Use when asked to format a lead sheet, create
  chord charts, write bass tabs, write a cello part / cello sheet music, or produce song
  charts.
semantic_id: "siMZLeOLa7Wvl7or8yPd59-4xp2cUAAC"
related_ids:
  - "kzQArUM6XzcK1BKXaiid5m-aYMYSEAAO"
  - "aPwFGVu6RbetOrhRNi-Xh--qZJykcAAJ"
topic_id: "v2:FHNJ"
topic_path: "site-tools/mixed"
---

# Song Charts

Produces three Markdown chart files per song matching the established OWNER/OPERATORS format (plus an optional drums file).
Reference song: `songs/echoes-and-static/` — treat those three files as canonical examples.

## Files produced

| File        | Contents                                                                | Format spec         |
| ----------- | ----------------------------------------------------------------------- | ------------------- |
| `lead.md`   | Lead sheet — sections, chord rows, lyrics                               | `formats/lead.md`   |
| `chords.md` | Guitar voicings by chord family + quick-reference table                 | `formats/chords.md` |
| `bass.md`   | Bass chart in lead-sheet flow — mirrors `lead.md` with inline bass cues | `formats/bass.md`   |
| `drums.md`  | Drum part notes — tempo, section breakdown, bar ranges, layers          | `formats/drums.md`  |
| `keys.md`   | Keyboard in-key / out-of-key map (which notes to play vs avoid)         | `formats/keys.md`   |
| `cello.ly`  | Cello part — real engraved staff notation (LilyPond, bass clef)         | `formats/cello.md`  |

`drums.md`, `keys.md`, and `cello.ly` are optional — produce `drums.md` when drum source
notes are provided, `keys.md` when a keyboard cheat-sheet is wanted, and `cello.ly` when a
cello part is wanted. `keys.md` needs the song's key (derive it from the chords); it's an
in-key/out-of-key note map, not a voicing chart. `cello.ly` is the one **non-Markdown**
output: it's LilyPond source that engraves to real sheet music (engraving commands in
`references/rendering.md`), not tab or chord charts.

## Workflow

1. Read the raw `lead.md` and `meta.md` for the song
2. Count and verify bar numbers (rules in `formats/lead.md` → "Bar counting")
3. Identify all unique chords; group by family; compute voicings using `references/tuning.md` and `references/voicings.md`
4. Write `lead.md`, then the song's `chart.py` (see "chart.py pipeline"), then generate `chords.md` and `bass.md` from it
5. Cross-check: every chord in `lead.md` must appear in `chords.md`; `bass.md` mirrors `lead.md` by construction
6. If drum source notes are provided, format `drums.md` — section names and bar ranges must match `lead.md`
7. If a cello part is wanted, write `cello.ly` per `formats/cello.md` — bass-clef notation following the chord roots, one `\mark` per `lead.md` section; then engrave it (see `references/rendering.md`)
8. Do NOT include any tuning / fret reference table in any output file — it lives in `references/tuning.md` only

## chart.py pipeline

`chords.md` and `bass.md` are **generated**, not hand-written. Each song dir
carries a `chart.py` (source of truth) defining `SONG` (title + sections), `CHORDS`
(guitar voicings + bass positions, validated as chord tones), and optionally
`BASS_CUES` (hand-written bass feel cues keyed by chord name or `·`-joined chord
sequence — see `formats/bass.md`). Generate with:

```bash
python .claude/skills/guitar/scripts/gen_chart.py songs/<slug>              # both files
python .claude/skills/guitar/scripts/gen_chart.py songs/<slug> --only bass  # just bass.md
python .claude/skills/guitar/scripts/gen_chart.py songs/<slug> --check      # validate only
```

The bass chart is built from `lead.md` (it mirrors its sections, rows, and lyrics),
so keep `lead.md` current and regenerate `bass.md` whenever `lead.md`
changes. To change hand-written bass cues, edit `BASS_CUES` in `chart.py` and
regenerate — never edit `bass.md` directly. Audit generated files with
`scripts/verify_charts.py` (checks fret arithmetic, chord-tone membership, and
lead/bass/chords cross-file agreement).

## References - load on demand

- **`formats/<file>.md`** - the strict per-file format spec (one per output in the table above). _Read the spec for whichever output file you're currently writing._
- **`references/rendering.md`** - chord-diagram auto-fill (`gen_chord_diagrams.py`), print-ready PDF export (`gen_pdf.py`, including the never-split-a-section rule), and LilyPond cello engraving (`gen_cello.py`). _Read when filling diagrams into `chords.md`, exporting PDFs, engraving `cello.ly`, or touching those scripts._
- **`references/tuning.md`** - guitar + bass string-fret tables. _Read when computing any voicing._
- **`references/voicings.md`** - pre-computed guitar voicings for the catalog + bass root positions. _Read when picking voicings._
- **`references/theory.md`** - jazz chord colors, voice leading, when to reach for extensions. _Read when hunting for interesting chord choices._
- **`references/cello-style.ily`** - shared LilyPond paper / staff-size / rehearsal-mark style every `cello.ly` `\include`s. _Edit to restyle all cello parts at once._
