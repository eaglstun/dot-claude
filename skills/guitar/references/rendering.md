# Rendering: chord diagrams, PDF export, cello engraving

The commands and rules for turning finished chart files into diagrams, print-ready PDFs, and engraved cello sheet music. (Chart _generation_ itself, `gen_chart.py`, is covered in `SKILL.md`.)

## Diagram generation

`chords.md` voicing blocks are followed by fenced `chord` blocks (ASCII fretboard diagrams). Write voicings as bare lines first, then auto-fill diagrams:

```bash
python .claude/skills/guitar/scripts/gen_chord_diagrams.py chords.md
```

The script skips any voicing block already followed by a `chord` block. Single-chord stdout test: `python .claude/skills/guitar/scripts/gen_chord_diagrams.py "x 0 2 2 2 0"`. Full diagram format spec is in `formats/chords.md`.

## PDF export

Render any chart file to a print-ready PDF (US Letter). The ASCII `chord` blocks become **real graphical fretboard diagrams** (nut bar, finger dots, `o`/`×` markers, barre bars, position labels); guitar chords lay out as a 3-across card grid; bass tabs stay monospace.

```bash
python .claude/skills/guitar/scripts/gen_pdf.py songs/<slug>          # all files → lead.pdf, chords.pdf, bass.pdf, drums.pdf
python .claude/skills/guitar/scripts/gen_pdf.py songs/<slug> --files chords   # just chords.pdf
python .claude/skills/guitar/scripts/gen_pdf.py songs/<slug>/lead.md          # a single file
```

The markdown is untouched — it keeps its ASCII diagrams so it still renders in editors and on GitHub. The PDF is a separate, prettier rendering. Requires `weasyprint` + `markdown-it-py` (already installed). The SVG diagram renderer is `scripts/chord_svg.py` (test one shape: `python .claude/skills/guitar/scripts/chord_svg.py "x 3 2 0 1 0" -o test.svg`).

**Page breaks never split a section.** Each `## Section` (its header plus all its chord/lyric rows) is wrapped in a `break-inside: avoid` block, so a section is kept whole on one page rather than being cut across a page turn — these are printed and played from, and a section split by a page turn is unusable mid-song. If you change `gen_pdf.py`, preserve this behavior (the `.section` wrapping in `preprocess()` plus the matching CSS).

## Cello engraving

`cello.ly` is **not** Markdown and is **not** rendered by `gen_pdf.py`. It's LilyPond
source that engraves to real bass-clef sheet music. Render it with `gen_cello.py`:

```bash
python .claude/skills/guitar/scripts/gen_cello.py songs/<slug>          # cello.ly -> cello.pdf
python .claude/skills/guitar/scripts/gen_cello.py songs/<slug> --png    # also a cropped PNG preview
python .claude/skills/guitar/scripts/gen_cello.py songs/<slug>/cello.ly # explicit file
```

It shells out to `lilypond` (install: `brew install lilypond`) and adds `references/`
to the include path so `\include "cello-style.ily"` resolves from any song directory.
Authoring rules and the `cello.ly` template are in `formats/cello.md`; shared engraving
style (paper, staff size, boxed rehearsal marks) lives in `references/cello-style.ily`.
