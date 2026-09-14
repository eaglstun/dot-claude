# Controls and SuperDirt

Sources: [Tutorial](https://tidalcycles.org/docs/getting-started/tutorial/), [Adding Synthesizers](https://tidalcycles.org/docs/configuration/adding_synthesizers/), [Adding Effects](https://tidalcycles.org/docs/configuration/adding_effects/), [SuperDirt repository](https://github.com/musikinformatik/SuperDirt)

## Boundary between Tidal and audio

Tidal schedules patterned control maps. SuperDirt receives OSC, finds samples or
SynthDefs, creates synth nodes, and performs effects/mixing. If events send but no
audio appears, inspect SuperCollider/SuperDirt before rewriting the pattern.

## Sources and pitch

```haskell
s "bd:0 bd:3"
n "c5 e5 g5" # s "superpiano"
midinote "60 64 67" # s "supersaw"
```

Common controls include `gain`, `pan`, `speed`, `begin`, `end`, `cut`, `orbit`,
`legato`, `attack`, `release`, `lpf`, `hpf`, `resonance`, `room`, `size`, `delay`,
`delaytime`, `delayfeedback`, `shape`, `crush`, and `coarse`. Availability and valid
ranges depend on the installed SuperDirt version and synth/effect graph.

`speed` changes sample playback speed and pitch. `n` selects a sample variant when
used with a sample bank, but supplies pitch to compatible synths. Do not assume every
SynthDef consumes every control.

## Samples and routing

SuperDirt's sample folders become sound names. `bd:3` is the fourth file in folder
`bd`; out-of-range indices commonly wrap. Custom sample folders must be loaded on the
SuperDirt side. Use a shared `cut` group to choke repeated samples. Use `orbit` for
routing; effects often maintain state per orbit.

## Effects and custom controls

A custom effect parameter must exist on both sides:

1. Tidal needs a typed control constructor such as `pF "myparam"` or `pI`.
2. SuperDirt needs a module or SynthDef that reads the OSC key.
3. The module must be placed in the intended signal-chain order.

Definitions frequently used should live in `BootTidal.hs`; SuperCollider definitions
belong in its startup configuration. Compiling a parameter in Tidal proves only that
the OSC key can be emitted—not that SuperDirt uses it.

## Diagnose silence

1. Confirm the SuperCollider server booted and SuperDirt reports its listening port.
2. Run `d1 $ s "bd"`.
3. Check output device, server volume, channels, orbit routing, and post-window errors.
4. Confirm the sample or SynthDef exists.
5. Compare Tidal target host/port with SuperDirt, normally localhost port `57120`.
6. Remove effects and custom controls, then add them back one at a time.

