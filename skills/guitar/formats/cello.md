# cello.ly format

The cello part — real engraved staff notation, not tab or chord charts. Unlike the
other files (Markdown), the cello part is a **LilyPond source file** (`cello.ly`)
that renders to print-ready sheet music a cellist reads off a stand.

It is bass-clef, single-staff, and structured to mirror `lead.md`: every section in
`lead.md` becomes a boxed rehearsal mark (`\mark`) at the right bar, so the cellist
and the band are talking about the same Intro / Verse / Chorus.

## What the cello plays (default)

Default content is a **bowed bass line following the chord roots**, voiced for the
cello's comfortable range (roughly C2–G3 for roots; go up to C4–C5 for a melodic
line). Derive the notes the same way `bass.md` derives bass positions — the
root motion is identical; the cello just plays it as sustained, bowed pitches with
real rhythm instead of fret numbers.

When the song wants a melodic or counter-line instead of roots, write that — note it
in the `subtitle` (e.g. `subtitle = "Cello — counter-line"`) so it's unambiguous.

## Template

```lilypond
\version "2.26.0"
\include "cello-style.ily"          % shared paper / staff size / rehearsal-mark style

\header {
  title    = "Song Title"
  subtitle = "Cello"
  composer = "OWNER/OPERATORS"
}

cello = \relative c {
  \clef bass \key g \major \time 4/4 \tempo 4 = 92

  \mark "Intro"   g2 d   | c b4 a |
  \mark "Verse"   d4 d d d | g,1   |
  \mark "Chorus"  \repeat volta 2 { c2 d | g,1 } \bar "|."
}

\score {
  \new Staff \with { instrumentName = "Vc." shortInstrumentName = "Vc." }
    \cello
  \celloLayout                       % defined in cello-style.ily
}
```

## Rules

- **Header**: `title` = song title (matches `lead.md` `# Title`); `subtitle = "Cello"`
  (or `"Cello — <role>"` when it isn't the root line); `composer = "OWNER/OPERATORS"`.
  Tagline is suppressed by the include — don't re-add it.
- **Always `\include "cello-style.ily"`** and end the `\score` with `\celloLayout`.
  Both come from `references/cello-style.ily`; `gen_cello.py` puts that dir on the
  include path, so the bare filename resolves from any song directory.
- **Clef / key / time / tempo** go once at the top of the `cello` variable. Key and
  time come from the song; tempo from `meta.md` (omit `\tempo` if unknown).
- **Sections = rehearsal marks**: one `\mark "Section Name"` per `lead.md` section,
  placed at that section's first bar. Section names must match `lead.md` headers
  (without the bar range). These render as boxed letters via the shared style.
- **Bars must total the same** as `lead.md` (see its "Bar counting" rules). One
  `\mark` per section; bar numbers are auto-printed at each system start.
- **Pitch**: LilyPond `\relative c` octave entry — `c` = C3 area in bass clef; `,`
  drops an octave (`g,` `c,`), `'` raises. Keep roots in C2–G3; reach higher only for
  a deliberate melodic line. Sanity-check octaves against `bass.md` roots.
- **Repeats**: use `\repeat volta 2 { … }` for repeated sections instead of writing
  them twice, matching how `lead.md` numbers chorus repeats.
- **End** the part with `\bar "|."`.
- This is the one output that is **not** Markdown and is **not** produced by
  `gen_pdf.py` — render it with `gen_cello.py` (see SKILL.md → "Cello engraving").
