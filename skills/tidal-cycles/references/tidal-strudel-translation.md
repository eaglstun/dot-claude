# Tidal and Strudel translation

Sources: [Tidal mini-notation](https://tidalcycles.org/docs/reference/mini_notation/), [Strudel documentation](https://strudel.cc/learn/), [Tidal repository](https://github.com/tidalcycles/Tidal), [Strudel repository](https://github.com/tidalcycles/strudel)

Tidal and Strudel share the cycle/pattern model and much mini-notation, but they are
different host languages and runtimes. Translate intent, not punctuation alone.

| Native Tidal | Strudel | Note |
|---|---|---|
| `s "bd sd"` | `sound("bd sd")` | sample pattern |
| `n "0 2 4"` | `n("0 2 4")` | numeric pattern |
| `p # gain x` | `p.gain(x)` | control application |
| `fast 2 p` | `p.fast(2)` | method form is common in Strudel |
| `stack [a,b]` | `stack(a,b)` | concurrent patterns |
| `d1 $ p` | `p.play()` / REPL evaluation | lifecycle differs |
| `hush` | `hush()` | stop syntax differs |

## Important differences

- Native Tidal uses Haskell application, `$`, composition, currying, lists, and type
  inference. Strudel uses JavaScript functions, methods, arrays, and callbacks.
- Similar mini-notation can differ in edge cases or function signatures by version.
- Tidal normally emits OSC to SuperDirt. Strudel may use WebAudio, samples, MIDI, OSC,
  or another output path; browser initialization is Strudel-specific.
- Native Tidal maps note zero to `c5`, while Strudel commonly treats middle C as `c4`.
  Confirm pitches by MIDI number before transcribing.
- SuperDirt controls depend on the actual engine and installed definitions.

## Translation method

1. Record cycle length, tempo convention, onsets, durations, rests, concurrency, and
   stochastic behavior.
2. Translate mini-notation only where both parsers support the same construct.
3. Translate host-language combinators into the target's composition style.
4. Map controls and output engine explicitly.
5. Verify octave/pitch, samples, randomness, and transitions by ear and, when
   possible, by inspecting generated events.

Use the Strudel skill for runnable JavaScript and initialization gotchas. Use this
skill for native Haskell Tidal and judging semantic equivalence.

