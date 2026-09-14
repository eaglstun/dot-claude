# Live performance and arrangement

Sources: [Patterns](https://tidalcycles.org/docs/reference/patterns/), [Time](https://tidalcycles.org/docs/reference/time/), [Workshop](https://tidalcycles.org/docs/patternlib/tutorials/workshop/)

## Streams and stopping

`d1` through `d16` are conventional stream actions. `p "name"` and numbered `p`
forms provide named/numbered streams. Re-evaluating a stream schedules its new
pattern; it does not create a second independent copy under the same name.

```haskell
d1 $ s "bd*4"
d1 silence
hush
panic
once $ s "crash"
```

`hush` stops patterns; `panic` also kills active SuperDirt synths. Keep `panic`
reachable during experiments involving long releases, feedback, or rapid retriggering.

## Tempo

Tempo is cycles per second (cps), not inherently BPM. If one cycle represents four
beats, `cps = bpm / 60 / 4`. The standard boot commonly provides:

```haskell
setcps (128/60/4)
```

Do not silently assume four beats per cycle. Infer the user's cycle convention from
the arrangement or ask when the conversion matters.

## Develop a pattern safely

Start with structure, then pitch/sample choice, then dynamics and effects:

```haskell
base = s "bd*4 [~ sd]*2"
d1 $ every 8 (jux rev) $ sometimesBy 0.2 (fast 2) $ base
  # gain "0.9 0.7 1 0.75"
```

Use `every` for legible form, `sometimesBy` for bounded probability, `off` for
echoes/canons, and `within` for localized transformations. Keep randomness out of
structurally essential hits unless the user asks for instability.

## Transitions and hygiene

Transition names and signatures have changed across versions. Verify the installed
version before prescribing `xfade`, `anticipate`, `clutch`, `jump`, or timed variants.

- Give layers distinct streams/orbits when independent effects are needed.
- Control reverb/delay feedback before increasing density.
- Preserve a dry or rhythmically simple anchor while transforming another layer.
- Prefer small evaluable definitions during a live set.
- `resetCycles` changes the cycle origin; use it intentionally.

