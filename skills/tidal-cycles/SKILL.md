---
name: tidal-cycles
description: >-
  Write, explain, debug, and configure TidalCycles live-coding patterns in Haskell,
  including mini-notation, pattern transformations, SuperDirt controls, tempo,
  transitions, custom boot configuration, and MIDI/OSC. Use for native Tidal code
  and Tidal-to-Strudel comparisons; use the Strudel skill for JavaScript/Strudel
  implementation and the Haskell skill for general Haskell language or build issues.
---

# Tidal Cycles reference

Tidal is a Haskell-embedded pattern language. It schedules event patterns—normally
as OSC messages to SuperDirt—while SuperCollider produces the audio. A cycle is the
primary unit of musical time; it is not inherently a bar or a fixed number of beats.

Before changing a local setup, inspect its Tidal version, `BootTidal.hs`, editor
plugin, SuperDirt startup file, and audio/MIDI routing. Do not assume an example from
the current documentation matches an older boot file or package version.

## Route the request

- Read [pattern-language.md](references/pattern-language.md) to write or explain
  patterns, mini-notation, composition operators, or time transformations.
- Read [controls-and-superdirt.md](references/controls-and-superdirt.md) for samples,
  notes, synths, effects, signal flow, and custom SuperDirt parameters.
- Read [performance.md](references/performance.md) for tempo, stream names,
  transitions, arrangement, randomness, and safe live-performance controls.
- Read [setup-and-debugging.md](references/setup-and-debugging.md) for installation,
  editor boot, `BootTidal.hs`, silence, latency, version, or connection failures.
- Read [midi-osc-and-sync.md](references/midi-osc-and-sync.md) for hardware MIDI,
  custom OSC targets, controller input, Link, and external synchronization.
- Read [tidal-strudel-translation.md](references/tidal-strudel-translation.md) when
  translating between native Tidal and Strudel or explaining their differences.

Load the `music-theory` skill as well when the request involves composing,
reharmonizing, arranging, or developing musical material. Load `haskell` for general
type errors, language extensions, Cabal/GHC problems, or custom library code beyond
Tidal's DSL. Load `strudel` when the output must run in JavaScript or strudel.cc.

## Working rules

1. Preserve the user's cycle structure and intended event onsets before adding
   ornamentation or effects.
2. Distinguish pattern transformations (`fast`, `rev`, `every`) from control
   parameters (`gain`, `speed`, `room`) and from stream actions (`d1`, `hush`).
3. Use parentheses or `$` deliberately. In Haskell, application binds tighter than
   infix operators; `#` combines control patterns and `$` extends to end of line.
4. Treat mini-notation as context-sensitive pattern syntax, not as a standalone
   sequencer. The surrounding function determines whether tokens mean sounds,
   notes, numbers, or controls.
5. Prefer `hush` for an orderly stop and `panic` when active SuperDirt synth nodes
   must also be killed.
6. Verify names and signatures against the installed Tidal version when compilation
   matters. The official docs can lead or lag released packages.

## Minimal native Tidal example

```haskell
d1 $ every 4 (fast 2)
   $ s "bd*4 [~ sd]*2"
  # gain 0.9

d2 $ n "<0 3 5 7>" # s "superpiano" # room 0.25
```

Evaluate complete expressions through the editor's Tidal integration. Stop them with
`d1 silence`, `d2 silence`, or `hush`.

