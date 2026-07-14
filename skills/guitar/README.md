# guitar

Claude Code skill for creating and formatting **OWNER/OPERATORS song charts** — lead sheets, guitar chord charts (with ASCII fretboard diagrams), and bass tablature — in the established echoes-and-static format. Canonical examples live in `songs/echoes-and-static/`. Installed on the Mac and Pi 5.

## Output

Three Markdown files per song, plus optional `drums.md`, `keys.md`, and `cello.ly`:

| File             | Contents                                                           |
| ---------------- | ------------------------------------------------------------------ |
| `lead.md`        | Lead sheet — sections, chord rows, lyrics                          |
| `chords.md`      | Guitar voicings by chord family + ASCII fretboard diagrams         |
| `bass.md` | Bass tab positions (low + high) per chord                          |
| `drums.md`       | Optional — tempo, section breakdown, bar ranges                    |
| `keys.md`        | Optional — keyboard in-key / out-of-key note map                   |
| `cello.ly`       | Optional — engraved cello part (LilyPond, real bass-clef notation) |

## Usage

`SKILL.md` drives the workflow: count bars, group chords by family, compute voicings from `references/tuning.md` + `references/voicings.md`, then write the files. Auto-fill fretboard diagrams with:

```bash
python scripts/gen_chord_diagrams.py chords.md
```

`scripts/` also has chart generation and verification; format specs live in `formats/`, theory guidance in `references/`.

## PDF export

Render charts to print-ready PDFs — ASCII chord diagrams become real graphical fretboard shapes, guitar chords lay out as a card grid, bass tabs stay monospace:

```bash
python scripts/gen_pdf.py songs/<slug>            # lead.pdf, chords.pdf, bass.pdf, drums.pdf
```

The markdown keeps its ASCII diagrams (still renders on GitHub); the PDF is a separate prettier rendering via `weasyprint` + `markdown-it-py`. SVG diagrams are drawn by `scripts/chord_svg.py`.

## Cello sheet music

The cello part is real engraved notation, not Markdown — `cello.ly` is LilyPond source that renders to print-ready bass-clef sheet music:

```bash
python scripts/gen_cello.py songs/<slug>          # cello.ly -> cello.pdf
python scripts/gen_cello.py songs/<slug> --png    # also a cropped PNG preview
```

Requires `lilypond` (`brew install lilypond`). Shared engraving style lives in `references/cello-style.ily`; authoring rules and the template are in `formats/cello.md`.
