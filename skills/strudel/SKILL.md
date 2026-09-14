---
name: strudel
description: Write, debug, and play Strudel live-coding music patterns. Use for mini-notation, rhythm and melody, effects, visualizations, MIDI/OSC, browser-project work, or playback through the dj-claude tools. Use tidal-cycles for native Tidal code.
metadata:
  version: 1.0.0
  public: 'true'
  semantic_id: AiTNqHEqK7VumAhuaGqNZDOpQPU3YAAD
  related_ids: '["kzQArUM6XzcK1BKXaiid5m-aYMYSEAAO","KCyLbTIJso-NGBQjISoP6DC7UWcNUAAA"]'
---

# Strudel

Strudel is a JavaScript port of Tidal Cycles — a language for making music by writing
patterns. Everything is a `Pattern`: a function from a cycle of time to a list of
events (`haps`). You build sound by composing patterns with methods, then `.play()`.

## Project layout

Paths below (`index.js`, `songs/`, `vite.config.js`) are relative to the Strudel project
root. The patterns still apply in other layouts; the file names may not.

- Entry: `index.js` builds a pattern and wires it to the Play/Stop buttons in `index.html`.
- Boot: `await initStrudel({ prebake: () => samples("github:tidalcycles/dirt-samples") })`
  loads everything and registers pattern methods (`.bank()`, `.jux()`, …) on the prototype.
- Run: `yarn dev` (Vite, Yarn 4 PnP — no `node_modules`). Audio only starts **after a user
  click** — browser autoplay policy.
- On **@strudel/web 1.3.0 / @strudel/draw 1.2.6**. `vite.config.js` dedupes `@strudel/core`
  (shared transitive dep of web + draw) — without it core warns "loaded more than once."
- Songs so far: `songs/echoes-and-static.js`, `songs/echoes-bass.js`, `songs/glitch-demo.js`.

## The one mental model that matters

A pattern repeats every **cycle** (≈ one bar; default `cps` ≈ 0.5, so ~2s/cycle).
A string passed to `note()`, `sound()`, `n()` etc. is **mini-notation** — a tiny DSL where
`"a b c"` means "play a, b, c evenly across one cycle." You spend most of your time
(1) writing mini-notation strings and (2) chaining transform methods onto patterns.

```js
import { note, sound, stack, n } from "@strudel/web";

sound("bd sd bd sd"); // four-on-the-floor-ish
note("c e g").sound("piano"); // a melody on a sound
stack(sound("bd*4"), sound("hh*8")); // layer patterns simultaneously
```

## Minimal recipe (matches index.js)

```js
stack(
  sound("bd*4").gain(0.9),
  sound("~ sd ~ sd").room(0.3),
  note("c2 eb2 g2 bb1").sound("sawtooth").lpf(800),
).play(); // .play() starts the scheduler; hush() stops everything
```

To stop: `hush()`. (The house project's Stop button also calls `cleanupDraw()`.)

## Composition — load music theory on demand

When the user asks to **compose, arrange, reharmonize, or develop musical
material**, also load and follow the `music-theory` skill before writing the
pattern. Use it to decide tonal center, mode, harmonic function, chord color,
voice leading, melodic contour, and tension/release; then express those choices
with Strudel patterns.

Do not load `music-theory` for implementation-only requests such as debugging
mini-notation, choosing effects or samples, adding visualization, converting an
already-written MIDI part, configuring MIDI/OSC, or controlling playback. Load
it later if one of those requests turns into a compositional decision.

## Reference files — read the one you need

- **`references/mini-notation.md`** — the string DSL: `*` `/` `[]` `<>` `,` `!` `@` `~` `?`
  `(3,8)` euclid, sub-sequences, polymeter. Read this first when writing pattern strings.
- **`references/functions.md`** — the pattern-transform vocabulary grouped by job:
  time (`fast`/`slow`/`rev`/`iter`), structure (`euclid`/`struct`/`segment`/`chop`),
  randomness (`sometimesBy`/`degradeBy`/`rand`), stereo/repeat (`jux`/`off`/`superimpose`/`ply`),
  conditionals (`every`/`when`/`firstOf`).
- **`references/sounds-and-effects.md`** — sources (`sound`/`note`/`n`/synths), sample
  banks, and the control/effect catalog (filters, envelopes, reverb, delay, distortion, pan).
- **`references/visualization.md`** — `@strudel/draw`: `pianoroll`, `pitchwheel`, `scope`,
  `spectrum`, `punchcard`, `spiral`, their option objects, the `_` prefix, the `.draw()`
  wiring the house project uses, and which methods actually render without a repl.
- **`references/io.md`** — input/output: MIDI (`midichan`/`midicmd`/`ccn`/`ccv`/`midibend`/
  `progNum`), OSC, MQTT — and the catch that the `.midi()`/`.osc()` sinks need extra packages
  not installed in the house project.
- **`references/dj-claude-mcp.md`** — the `dj-claude` MCP tools (`play_strudel`, `set_vibe`,
  `jam`, `conduct`, `play_preset`, …) for playing patterns without touching the browser.
- **`references/midi-import.md`** — turning a tracked MIDI part into Strudel _or Haskell
  TidalCycles_: `scripts/dump_midi.py` (inspect notes/bars/swing), `scripts/midi_to_strudel.py`
  (per-bar mini-notation array), and `scripts/midi_to_tidal.py` (Haskell bindings, with
  chords and `legato`). Read this when matching a pattern to an exported DAW/Guitar Pro
  part. `songs/echoes-bass.js` is a worked example. **The two transcribers disagree about
  octave numbering on purpose** — Tidal's middle C is `c5`, Strudel's is `c4`.

## Gotchas that will bite you

- **Build patterns AFTER `initStrudel()`, not at module top-level.** This is the one that
  silently wastes an hour. `initStrudel()` registers the prototype methods (`.jux`, `.lpf`,
  `.struct`, `.cps`, …) AND wires the mini-notation string parser. A pattern module whose
  `const`s call `note("...")`/`s("...")` at import time runs _before_ `index.js` awaits
  `initStrudel()`, so strings are treated as literal names — you get runtime errors like
  `not a note: "[fs3,a3]"` and `sound bd ~ ~ bd not found! Is it loaded?` even though the
  samples are loaded. **Fix:** build inside a function (or the click handler) that runs after
  init. See `songs/echoes-and-static.js` (everything is inside `echoesAndStatic()`) vs the
  original demo (pattern built inside the Play handler). `node --check` and an HTTP 200 will
  NOT catch this — only running it in the browser does.
- **Set tempo with `repl.setCps()`, NOT the `.cps()` control.** `pattern.cps(x)` sets a
  per-hap value the scheduler never reads back — the clock stays at the default **0.5 cps**
  and nothing audibly changes. `initStrudel()` resolves to the repl, so capture it and call
  `repl.setCps(bpm / 60 / beatsPerCycle)` (e.g. `154/60/4`). The @strudel/web repl exposes
  `setCps` only — no `setCpm` (that's a strudel.cc transpiler global). Verified: after
  `setCps(154/60/4)`, `repl.scheduler.cps === 0.6417`. See `index.js`.
- **Sharps are `s`, not `#`.** Strudel note names use `cs4`, `fs3`, `ds2` — `c#4` fails to
  parse (`not a note`). Flats use `b` (`eb3`, `ab2`, `bb1`). If you keep `#` in source for
  readability, convert at build time: `str.replaceAll("#","s")`.
- **`vowel` takes single letters.** `a e i o u` only — `vowel("oo")` logs
  `unknown vowel oo` and silently drops the formant. Use `vowel("<o a e>")`.
- **Audio needs a click.** Nothing makes sound until a user gesture. In the house project
  that's the Play button; don't expect `.play()` at module load to produce audio.
- **Sample names are plain.** `bd`, `sd`, `hh`, `oh` — not bank-prefixed. Use `:n` to pick a
  variant (`sd:3`) and `.bank("RolandTR909")` to switch kits.
- **Viz: two kinds, both work via `index.js`'s `VIZ` switch.** Self-wired ones run their own
  loop — `.pianoroll()` (`.draw()`) and `.scope()`/`.spectrum()`/`.tscope()`/`.fscope()`
  (`.analyze().draw()`); just call them. **Don't wrap the analyser scopes in your own
  `.draw()`** — same draw id, cancels their loop, blank canvas. The onPaint ones
  (`.pitchwheel()`, `.spiral()`, `.punchcard()`) have no loop, so drive them with
  `pattern.getPainters()` inside a `.draw()`. Viz paint light-on-transparent → page needs a
  dark background. See `references/visualization.md`.
- **`note()` vs `n()`:** `note("c e g")` = pitches. `n("0 2 4")` = sample index / scale degree
  (pair with `.scale(...)` for melodies, or `.sound("drums")` to pick samples).
