# keys.md format

Keyboard cheat-sheet for a song — an **in-key / out-of-key map** for whoever's on keys.
It answers one question fast: _which notes are safe to play and which to avoid?_ Optional
file — produce when a keyboard part is wanted.

This is NOT a per-chord voicing reference (that's what guitar `chords.md` is). It's a
performance aid keyed to the song's scale.

````markdown
# Song Title — Keys

**Artist / context · Key of <KEY> · ~<bpm> bpm**

Stay on the **<key> scale** and you can't go wrong: **<7 scale notes>**.
<one-line callout of the easiest trap note, e.g. F vs F♯>.

## Keyboard map — ✓ play, ✗ avoid

```
            C♯   D♯        F♯   G♯   A♯      ← black keys
            ███  ███       ███  ███  ███
             ✗    ✗*        ✓    ✗    ✗
        ┌────┬────┬────┬────┬────┬────┬────┐
        │ C  │ D  │ E  │ F  │ G  │ A  │ B  │   ← white keys
        │ ✓  │ ✓  │ ✓  │ ✗  │ ✓  │ ✓  │ ✓  │
        └────┴────┴────┴────┴────┴────┴────┘
          ✓ play (in key, <KEY>)   ✗ avoid (out of key)
          <the in-key black key(s)> — the only black key(s) you play
          *<note> good ONLY over the <chord> chord (see below)
```

## In key — mash these

**<scale notes, · separated>** ← the 7 home notes

## Out of key — avoid (passing tones only)

**<the 5 non-scale notes, · separated>**

## The one exception

<call out any borrowed chord that brings a non-scale tone, and when it's OK to play it>

## Chords

| Chord | Notes | In key?     |
| ----- | ----- | ----------- |
| ...   | ...   | ✓ / ✗ + why |

**Progression (verify against the track):**

- Section: **chords**
````

## Keys format rules

- Title: `# Song Title — Keys`; subtitle line with key + bpm
- **Pick the key first.** Diatonic = the 7 major-scale (or relevant mode) notes → ✓.
  The other 5 chromatic notes → ✗.
- The keyboard map is one octave C→B. White-key row always shows all 7 (C D E F G A B);
  black-key row shows the 5 sharps aligned above the gaps. Mark each ✓ or ✗.
- Exactly one in-key note is usually a black key (e.g. F♯ in G) — call it out so it
  doesn't read as "all black keys bad."
- **Borrowed / secondary chords:** if a chord pulls in a non-scale tone (a B major in G
  brings D♯), mark that note ✗ on the map with a `*` and explain in "The one exception"
  that it's good _only_ over that chord.
- Chords table: list each chord's notes and whether it's fully diatonic; flag the
  borrowed ones and which accidental they introduce.
- Keep it honest — if chords came from a tab site, say so and tell the player to
  verify B vs Bm-style ambiguities against the recording.
- No fretboard / tuning tables — this is a keyboard sheet.
