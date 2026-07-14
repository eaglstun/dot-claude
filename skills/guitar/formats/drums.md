# drums.md format

Drum part notes — tempo, section breakdown, bar ranges, layers. Optional file — only produce when drum notes are provided as source material.

```markdown
# Song Title — Drums

152 bpm

## Intro — bars 1-2

1-2 _(no drums — synth/pad only)_

## Intro — bars 3-10

3-6 bass drum, snare
_"first lyric line for this phrase"_
7-10 bass drum, snare, hi-hats on quarters
_"next lyric line"_

## Chorus 1 — bars 27-36

27 break
28-34 bass drum, snare, hi-hats on eighths
35-36 break

## Bridge A — bars 53-64

53-54 bass drum, snare, hi-hats on quarters _(half-time)_
55-56 bass drum _(half-time)_
63-64 bass drum, snare, hi-hats on quarters

## Outro — bars 138-150

138-145 bass drum, snare, ride on quarters _(half-time)_
146-150 _(fade out)_
```

## Drums format rules

- Title: `# Song Title — Drums`
- Tempo: one line immediately below the title — e.g., `152 bpm`
- Section headers: `## Section Name — bars X-Y` — same format as `lead.md`; section names must match exactly (same numbering — Chorus 1, Verse 3, etc.)
- Sub-phrases: `bar-range  description  *(annotation)*`
  - Bar range left-aligned; pad with spaces so descriptions align within each section
  - Descriptions: instrument layers as a comma-separated list
  - Standard instruments: `bass drum`, `snare`, `hi-hats`, `ride`, `floor toms`, `crash`, `break`, `fill`
  - Subdivisions: `on quarters`, `on eighths`, `on sixteenths`
  - Annotations: `*(half-time)*`, `*(fade out)*`, `*(no drums — brief note)*` — italics at end of line
- Sections with no drums: use `*(no drums — brief note)*` on the bar-range line
- Lyrics: under each bar-range phrase that carries vocals, add the matching lyric on the next line, indented to align with the description, in italics and quoted — `_"lyric line"_`. Pull lyrics verbatim from `lead.md`. Instrumental phrases get no lyric line.
