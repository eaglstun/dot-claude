# Setup, boot, and debugging

Sources: [Installation](https://tidalcycles.org/docs/getting-started/), [The Boot File](https://tidalcycles.org/docs/configuration/boot-tidal/), [Upgrading](https://tidalcycles.org/docs/getting-started/upgrading/), [Tidal releases](https://github.com/tidalcycles/Tidal/releases)

## The stack

A native setup has independently versioned pieces: GHC/Cabal and `tidal`; an editor
integration; `BootTidal.hs`; SuperCollider; SuperDirt; optional sc3-plugins; samples;
and the audio/MIDI system. Diagnose the failing layer before reinstalling everything.

The project has announced development moving from GitHub to Codeberg. Use the official
Tidal website for user documentation and verify the current upstream repository before
giving source-development instructions.

## Inspect before changing

```text
ghc --version
cabal list --installed tidal
```

Locate the editor's actual `BootTidal.hs`; editing another copy has no effect. Check
imports, target host/port, latency, process-ahead, frame timespan, stream count, and
custom definitions.

## Failure map

- Haskell error: minimize it; inspect `$`, `#`, grouping, numeric types, and installed
  signatures. Use the Haskell skill for non-DSL errors.
- Editor does not start Tidal: inspect plugin logs, boot path, GHCi, and package env.
- Tidal starts but no audio: test `d1 $ s "bd"`; compare OSC ports and start SuperDirt.
- SuperDirt receives events but is silent: inspect server/device/channels, samples,
  SynthDef errors, routing, effects, and gain.
- Timing is late or unstable: distinguish fixed latency from jitter; adjust target
  latency/process-ahead conservatively and check buffer/CPU load.
- Function not in scope: compare installed version/imports with the documentation.

## Discipline and updating

Test boot changes in a fresh session because a running session can retain definitions.
Back up a working boot file before migrations. Do not delete `.cabal`, `.ghc`, package
environments, or Quarks as a first response; those broad resets disturb unrelated work.

Tidal, SuperDirt, editor integrations, and boot templates evolve together. Record
versions, preserve custom definitions, consult the current upgrade page, then validate
a sample, synth, effect, and any MIDI route.

