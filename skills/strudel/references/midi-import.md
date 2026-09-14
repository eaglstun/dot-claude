# Importing a MIDI part into Strudel

When you have a tracked MIDI part (a bassline, lead, drum groove exported from a
DAW / Guitar Pro) and want the Strudel arrangement to match it, don't eyeball it
— read the actual notes and transcribe. Two helper scripts live in
`scripts/` (Python, need `mido`: `pip install mido` — file parsing only, no
`python-rtmidi` required).

## 1. Inspect — `scripts/dump_midi.py`

Prints every note as `bar / beat / length(beats) / name / velocity`, plus a
per-bar grouped view. Use it first to understand register, rhythm, and how the
MIDI's bars line up with the song's `form`.

```
python3 scripts/dump_midi.py FILE.mid [--beats-per-bar 4] [--track N]
```

What to look at:

- **Bar range** — where does the part actually start? (Demo parts often have a
  silent intro; e.g. `echoes2-bass2.mid` enters at bar 10, the turnaround.)
- **Fractional beat offsets** — clustering at `.49/.50` = straight eighths,
  `.53/.54` = light swing, `.25/.75` = sixteenth subdivisions.
- **Durations** — lots of `0.5` = eighth-note line; `0.1` = grace/ghost notes;
  `1.0` = sustained quarters.
- **Alignment check** — match a few bars' pitches against the song's chord map
  (`form` + voicings). If MIDI bar N's notes spell the chord at `form[N-1]`, the
  numbering lines up and you can transcribe straight onto `form`.

## 2. Transcribe — `scripts/midi_to_strudel.py`

Quantizes onsets to a grid and emits a JS array literal of per-bar
mini-notation strings (`~` = rest), ready to `cat(...)` one bar per cycle.

```
python3 scripts/midi_to_strudel.py FILE.mid \
  --grid 16 --first-bar 1 --last-bar 148 --var BASS_MIDI > songs/echoes-bass.js
```

- `--grid` — slots per bar. **16** keeps grace notes and walking fills; **8** is
  cleaner but drops sixteenth ornaments. Pick by what the `--dump` offsets showed.
- `--first-bar` / `--last-bar` — pad/trim so song bar 1 maps to output index 0
  (bars before the part enters become `"~"`).
- Note names come out with `#`; the song's `m()` helper converts `#`→`s` at build.

Then in the song, build the layer from the array (inside the build function, per
the after-init rule):

```js
import { BASS_MIDI } from "./echoes-bass.js";
// ...
const bass = cat(...BASS_MIDI.map((bar) => note(m(bar))))
  .s("sawtooth")
  .lpf(720)
  ./* envelope + effects */ gain(0.82)
  .orbit(1);
```

## Gotchas

- **It's a snapshot, not a live link.** Re-export the MIDI → re-run the script to
  refresh. The generated file's header comment records the exact command.
- **A grid loses sustain.** A held quarter (`len 1.0`) becomes one hit + rests on
  the grid, so it reads staccato. For a busy line that's fine (keep the synth
  envelope plucky); for a sustained line, lengthen notes or use a coarser grid.
- **Anticipations** (notes at beat ~3.99 that lead into the next bar) clamp to the
  last slot of their bar — close enough rhythmically, but not a true tie-over.
- **Polyphony** collapses: one onset per slot is kept (earliest). `midi_to_strudel.py`
  is built for monophonic-ish parts (bass, lead), not chords. `midi_to_tidal.py`
  handles chords — see below.

---

# Importing a MIDI part into TidalCycles

`scripts/midi_to_tidal.py` is the Haskell-Tidal sibling. Same quantize-to-a-grid
approach, same `dump_midi.py` inspection step first, but it emits Haskell
bindings instead of a JS array, and it handles two things the Strudel script
doesn't: chords and note length.

```
python3 scripts/midi_to_tidal.py FILE.mid --list-tracks
python3 scripts/midi_to_tidal.py FILE.mid --track 3 --grid 2 --mono --name gameBass
```

Output is paste-able straight into a Tidal buffer (where `Sound.Tidal.Context`
is already imported):

```haskell
gameBass :: [String]
gameBass =
  [ "gs2 as2"
  , "b2 cs3"
  , "b2 ~"
  ]

gameBassP :: ControlPattern
gameBassP = cat (map (note . parseBP_E) gameBass)
```

You get the raw bars _and_ the assembled pattern, because the bars are the thing
you'll actually want to edit.

## The octave trap

**Tidal's middle C is `c5`, not `c4`.** Its note parser defaults to octave 5, so
`c5` == `c` == `0` == MIDI 60. Verified against tidal-1.10.1 rather than
remembered:

```
c -> [0.0]    c5 -> [0.0]    c4 -> [-12.0]    cs5 -> [1.0]    df5 -> [1.0]
```

`midi_to_strudel.py` uses the general-MIDI convention (`n // 12 - 1`, MIDI 60 →
`c4`). Feed _its_ output to Tidal and every note plays an octave low while
sounding entirely plausible — nothing errors, the intervals are all correct, the
part is just wrong. `midi_to_tidal.py` uses `n // 12`; `--octave-offset -1`
switches back to GM naming if you need to compare the two.

Sharps also differ: Tidal spells them `cs`/`df`, so no `#`→`s` fixup helper is
needed at the far end.

## What it does that the Strudel one doesn't

- **Chords.** Simultaneous onsets in a slot become mini-notation stacks,
  `"[b2,cs6] b3 [b2,b5] [b3,fs5]"`. Pitches are deduped (layered tracks double
  them constantly), sorted low-to-high, and capped by `--max-voices` (default 4,
  lowest kept). `--mono` gives you the old one-note-per-slot behaviour.
- **Note length.** `--legato` emits a second array of durations measured in grid
  slots, and wires it up:

  ```haskell
  gameBassP = cat (zipWith step gameBass gameBassLegato)
    where step n l = note (parseBP_E n) # legato (parseBP_E l)
  ```

  Without it, a held whole note reads as a staccato hit like it does in Strudel.

- **Proper note-off pairing**, so those durations are real — including
  `note_on` with velocity 0, which is how plenty of DAWs write note-off.
- **`--list-tracks`**, which prints each track's name, note count and pitch range.
  Worth running first on anything from a DAW; a six-track arrangement transcribed
  as one part is mush.
- **`--numeric`** emits semitones-from-middle-C (`"-28 -26"`) instead of names,
  for when you want to do arithmetic on the pattern.

## Pick the grid from the part, not from habit

`--grid 16` is the safe default for a busy line and completely wrong for a slow
one. The bass in `gamemusic.mid` is half notes; at grid 16 it transcribes as

```
"gs2 ~ ~ ~ ~ ~ ~ ~ as2 ~ ~ ~ ~ ~ ~ ~"
```

and at `--grid 2` as `"gs2 as2"`. Both are correct. Only one is usable. Run
`dump_midi.py` and look at the fractional beat offsets before choosing.

## The limit that isn't the script's fault

MIDI is absolute and linear; Tidal is cyclic and nested. The converter bridges
the notation, not the structure — and a flat 16-slot grid is a piano roll
written in text. It is inert under exactly the functions you converted it to
use: `every 3 (fast 2) $ note "c5 ~ ~ g4 ~ ~ ~ ~ …"` just plays the piano roll
twice as fast, because there's no phrase for `every` to grab.

So treat the output as step one — it gets the notes right, which is the tedious
part and the part you'd get wrong by ear. Then restructure by hand: collapse
repeats into `<c5 e5>`, find where a rhythm is really `euclid 3 8`, split a bar
into `[a2 ~]*2`. That second pass is where it stops being a transcription and
starts being a pattern.

Same snapshot caveat as the Strudel script: re-export the MIDI, re-run the
command in the generated header comment.
