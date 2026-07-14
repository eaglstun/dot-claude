# lead.md format

The lead sheet — sections, chord rows, lyrics.

```markdown
# Song Title

## Section Name — bars X-Y

| Chord //// | Chord //// | Chord //// | Chord //// |
Lyric line goes here on the next line

| Chord //// | Chord //// | (2 bars)
Lyric that spans the shorter row

## Next Section — bars N-M

| Chord //// | Chord //// | Chord //// | Chord //// |
| Chord //// | Chord //// | Chord //// | Chord //// |
```

## Lead sheet rules

- Title: `# Song Title` — no tempo, key, or meta (those live in `meta.md`)
- Section headers: `## Section Name — bars X-Y` (em dash, space on both sides)
- Chord rows: `| Chord //// | Chord //// |` — four slashes per beat group (4/4 default)
  - Three slashes `///` = 3-beat bar (only use when the section genuinely alternates meter)
  - Partial rows: add `(N bars)` annotation at end of line
- Lyrics: one line immediately after the chord row they accompany — no blank line between
- Blank line between rows within a section; blank line before every `##` header
- Chord names: use standard symbols — `maj7`, `m7`, `sus2`, `sus4`, `add9`, `dim`, `/Bass`
  - Slash chords: `E6/C#` (chord/bass)
  - Extended chords: `F#m7(9,11)`, `C#m7(9,b13)` — parentheses, comma-separated
- Special section notes: `*(half-time feel)*`, `*(cutoff)*` — italics at end of line
- No tempo, key, or bar-count labels inside section headers — just name and bar range
- Chorus repeats: use a distinct number (Chorus 1, Chorus 2 …) even if the chords are identical
- Instrumental sections with no lyrics: chord rows only, no placeholder text

## Bar counting

1. Count actual chord bars in the content (one chord with slashes = one bar)
2. When the raw source gives explicit bar ranges for later sections, work backwards to calibrate earlier sections
3. If the source bar count in a header conflicts with the content, trust the content
4. Document the final bar total in the quick-reference table of `bass.md`

## Lyric formatting rules

- One lyric line per chord row — the lyric goes immediately below its chord row, no blank line
- If two chord rows share one lyric phrase (e.g., a 4-bar line with a 2-bar line), put the lyric under the first row only
- If a chord row is purely instrumental, leave it bare — no lyric, no placeholder
- Capitalization: match source material (sentence case for lyrics, not title case)
- Punctuation: preserve as-is from source; add a comma only if the source uses one
- Lyrics that continue across a line break: write on one line in the chart (no artificial line breaks mid-phrase)
- Single-word or fragment lyrics at section endings (e.g., "Drift in a—") keep the dash to signal a cutoff
