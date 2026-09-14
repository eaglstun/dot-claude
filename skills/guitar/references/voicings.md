# Common chord voicings

Pre-computed voicings for the catalog. Write these into `chords.md` as bare voicing lines, then run `python .claude/skills/guitar/scripts/gen_chord_diagrams.py chords.md` to expand them into `chord` blocks automatically. The script skips blocks that already have a diagram.

Single-chord stdout test: `python .claude/skills/guitar/scripts/gen_chord_diagrams.py "x 0 2 2 2 0"`

## Guitar voicings (low → high: E A D G B E)

**A family**

| Chord  | Voicing       | Notes                               |
| ------ | ------------- | ----------------------------------- |
| A      | `x 0 2 2 2 0` | open                                |
| Am     | `x 0 2 2 1 0` | open, fret 1 on B string            |
| A7     | `x 0 2 0 2 0` | open                                |
| Amaj7  | `x 0 2 1 2 0` | open, fret 1 on G string            |
| Asus2  | `x 0 2 2 0 0` | open                                |
| Asus4  | `x 0 2 2 3 0` | open                                |
| A6     | `x 0 2 2 2 2` | open, high E = 6th (F#)             |
| A7sus4 | `x 0 0 0 3 3` | open strings give D (sus4) + G (♭7) |

**B / Bb family**

| Chord  | Voicing       | Notes                         |
| ------ | ------------- | ----------------------------- |
| Bb     | `x 1 3 3 3 1` | barre 1st fret, A shape       |
| Bbm7   | `x 1 3 1 2 1` | barre 1st fret, Am7 shape     |
| Bbmaj7 | `x 1 3 2 3 1` | barre 1st fret, Amaj7 shape   |
| B      | `x 2 4 4 4 2` | barre 2nd fret, A shape       |
| Bm     | `x 2 4 4 3 2` | barre 2nd fret                |
| B7     | `x 2 1 2 0 2` | open, fret 1 on D string      |
| Bsus2  | `x 2 4 4 2 2` | barre 2nd, sus2 on B string   |
| Bsus4  | `x 2 4 4 5 2` | barre 2nd, fret 5 on B string |

**C family**

| Chord | Voicing       | Notes                         |
| ----- | ------------- | ----------------------------- |
| C     | `x 3 2 0 1 0` | open                          |
| Cmaj7 | `x 3 2 0 0 0` | open                          |
| C6    | `x 3 2 2 1 0` | open, high E rings, 6th = A   |
| Cm7   | `x 3 5 3 4 3` | barre 3rd fret, Am7 shape     |
| C#m   | `x 4 6 6 5 4` | barre 4th fret, Am shape      |
| C#m7  | `x 4 6 4 5 4` | barre 4th, B on G string (m7) |

**D family**

| Chord | Voicing       | Notes                         |
| ----- | ------------- | ----------------------------- |
| D     | `x x 0 2 3 2` | open                          |
| Dm    | `x x 0 2 3 1` | open, fret 1 on high E        |
| Dm7   | `x x 0 2 1 1` | open, C+F on B/high E (m7)    |
| Dmaj7 | `x x 0 2 2 2` | open                          |
| Dadd9 | `x x 0 2 3 0` | open, high E (9th) rings open |
| D/F#  | `2 x 0 2 3 2` | F# on low E, strings 5 muted  |

**E family**

| Chord | Voicing       | Notes                               |
| ----- | ------------- | ----------------------------------- |
| E     | `0 2 2 1 0 0` | open                                |
| Em    | `0 2 2 0 0 0` | open                                |
| Em7   | `0 2 2 0 3 0` | open, fret 3 on B string (D = m7)   |
| Em7b5 | `0 1 0 0 3 x` | open, ♭5 B♭ on A-1, mute high E     |
| Eadd9 | `0 2 2 1 0 2` | open, fret 2 on high E (F# = 9th)   |
| E6    | `0 2 2 1 2 0` | open, fret 2 on B string (C# = 6th) |
| Esus4 | `0 2 2 2 0 0` | open                                |

**F family**

| Chord | Voicing       | Notes                                                     |
| ----- | ------------- | --------------------------------------------------------- |
| F     | `1 3 3 2 1 1` | full barre 1st fret, E shape                              |
| F7    | `1 3 1 2 1 1` | barre 1st fret, E7 shape (Eb on D = ♭7)                   |
| F#m   | `2 4 4 2 2 2` | full barre 2nd fret, Em shape                             |
| F#m7  | `2 4 4 2 2 0` | barre 2nd, open high E = E (m7) — diagram spans frets 1–4 |

**G family**

| Chord | Voicing       | Notes                            |
| ----- | ------------- | -------------------------------- |
| G     | `3 2 0 0 0 3` | open                             |
| G7    | `3 2 0 0 0 1` | open, fret 1 on high E (F = ♭7)  |
| Gm    | `3 5 5 3 3 3` | full barre 3rd fret, Em shape    |
| G#m   | `4 6 6 4 4 4` | full barre 4th fret, Em shape    |
| Gsus4 | `3 x 0 0 1 3` | open D+G, fret 1 on B (C = sus4) |

## Bass root positions (quick ref)

Use the lowest comfortable position as the root for the tab's left half.

| Root | Lowest position | Next position |
| ---- | --------------- | ------------- |
| E    | E-0 (open)      | D-2           |
| F    | E-1             | D-3           |
| F#   | E-2             | D-4           |
| G    | E-3             | D-5           |
| G#   | E-4             | D-6           |
| A    | A-0 (open)      | E-5           |
| Bb   | A-1             | E-6           |
| B    | A-2             | E-7           |
| C    | A-3             | E-8           |
| C#   | A-4             | E-9           |
| D    | D-0 (open)      | A-5           |
| Eb   | D-1             | A-6           |
