# Mini-notation

The string DSL inside `note("…")`, `sound("…")`, `n("…")`, and most controls. One string =
one cycle of structure unless an operator says otherwise. Whitespace separates events; the
cycle is divided **evenly** among the top-level events.

## Core operators

| Syntax       | Name             | Meaning                                                |
| ------------ | ---------------- | ------------------------------------------------------ |
| `a b c`      | sequence         | three events, each 1/3 of the cycle                    |
| `~`          | rest             | silence for that slot — `"bd ~ sd ~"`                  |
| `[a b]`      | sub-sequence     | group; the bracket takes one slot, split inside it     |
| `[a b, c d]` | stack (parallel) | comma = play groups simultaneously                     |
| `<a b c>`    | alternation      | one per cycle, cycling: cycle0→a, cycle1→b, …          |
| `a*2`        | fast / repeat    | play `a` twice in its slot (`"bd*4"` = 4 kicks)        |
| `a/2`        | slow             | play `a` every other cycle                             |
| `a!3`        | replicate        | `a a a` (distinct events, unlike `*` which subdivides) |
| `a@3`        | elongate         | `a` takes 3 units of weight vs neighbors               |
| `a?`         | degrade          | randomly drop `a` ~50% of cycles (`a?0.3` for 30%)     |
| `a:3`        | sample index     | pick variant 3 of sample `a` (`"sd:3"`)                |
| `a . b c`    | feet             | `.` splits a sequence into weighted groups             |
| `(3,8)`      | euclid           | Euclidean rhythm: 3 hits spread over 8 steps           |
| `(3,8,2)`    | euclid+rotate    | …rotated by 2                                          |

## Worked examples

```js
sound("bd*4"); // 4 kicks across the cycle
sound("bd sd"); // kick, snare — half each
sound("bd [sd sd]"); // kick (1/2), then two fast snares (1/2)
sound("bd <sd cp>"); // kick + alternating snare/clap each cycle
sound("hh*8"); // straight eighth hats
sound("bd(3,8)"); // tresillo kick: x..x..x.
sound("bd!3 sd"); // bd bd bd sd  (4 even slots)
sound("bd@3 sd"); // bd holds 3x as long as sd
note("c e g, c2 g2"); // chord stacked over a bassline (comma)
note("<c e g>*4"); // arpeggiate: one note per 1/4, cycling the set
sound("hh*16?"); // 16 hats, each randomly dropped ~half the time
```

## Sub-sequence nesting

Brackets nest arbitrarily; each level subdivides its parent's slot evenly.

```js
sound("bd [~ sd] bd [sd sd sd]");
// slot1: bd | slot2: rest+snare | slot3: bd | slot4: three snares
```

## Polymeter `{ }`

`{a b c}%4` plays the sequence at a fixed step count (4) regardless of its length, so
sequences of different lengths drift against each other.

```js
sound("{bd sd hh}%4"); // 4 steps/cycle drawn from a 3-element loop
sound("{bd sd, hh hh hh}%8"); // two layers, both stepped at 8
```

## Note names (in `note(...)`)

Letter + optional accidental + octave: `c4`, `fs3`, `eb2`. Accidentals are spelled out,
**not** with `#`:

- **Sharp = `s`** → `cs4`, `fs3`, `gs5`. `c#4` does **not** parse — you get `not a note`.
- **Flat = `b`** → `eb3`, `ab2`, `bb1`.
- Chords are commas inside brackets: `note("[cs4,e4,gs4]")` (an A-major-ish triad).

If you'd rather write `#` in source for readability, convert before it hits Strudel:
`note(str.replaceAll("#","s"))`.

## Operators are patterns too

Numbers in operators can themselves be patterns:

```js
sound("bd*<2 4>"); // 2 kicks one cycle, 4 the next
sound("hh*[8 16]"); // 8 then 16 within the same cycle
```

## Tips

- Prefer `*` for subdividing a beat, `!` for literal repeats you might transform individually.
- `~` is your friend for groove — `"bd ~ ~ bd ~ ~ bd ~"` reads the rhythm at a glance.
- Euclid `(k,n)` covers most "world rhythm" needs: `(5,8)` `(7,16)` `(3,8)` etc.
- Anything you can write as a control value (`gain`, `speed`, `pan`) can be mini-notation:
  `.gain("1 0.5 0.8 0.5")`, `.pan("0 1")`, `.speed("<1 2 -1>")`.
