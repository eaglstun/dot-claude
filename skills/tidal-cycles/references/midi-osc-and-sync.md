# MIDI, OSC, and synchronization

Sources: [MIDI](https://tidalcycles.org/docs/configuration/MIDIOSC/midi/), [OSC](https://tidalcycles.org/docs/configuration/MIDIOSC/osc/), [Boot file](https://tidalcycles.org/docs/configuration/boot-tidal/)

## Choose the path

- SuperDirt MIDI: Tidal sends Dirt events to SuperDirt, which sends MIDI to a device.
- Direct custom OSC: define a Tidal target and message shape in `BootTidal.hs`.
- Controller input: map MIDI/OSC into stream controls; the path depends on the setup.
- Clock sync: determine whether the system uses Link, MIDI clock, or a bridge. These
  solve different synchronization problems.

## MIDI mapping

Native Tidal uses `0` for `c5`; MIDI note `60` is middle C, so direct numeric
conversions commonly offset by 60. Strudel generally spells middle C as `c4`; never
transpose a translation until the source convention is known.

Typical MIDI controls include note, channel, velocity, sustain, program change,
CC number/value, and pitch bend. Names differ by route and version; verify the current
official examples and installed boot definitions.

## Custom OSC targets

A target specifies name, host, port, latency, and scheduling behavior. A shape
specifies OSC path and argument keys/types. Tidal can include timing metadata such as
`cps`, cycle position, and event duration when those fields are declared.

If messages do not arrive:

1. Confirm host/interface and port.
2. Check UDP/firewall/container boundaries.
3. Confirm OSC path, argument order/types, encoding, bundles, and timetags.
4. Log or sniff locally before changing the pattern.
5. Check latency/time-base interpretation if messages schedule incorrectly.

Do not assume MIDI device indices remain stable after reconnect. Test hardware with
low gain/velocity and one note. Provide an all-notes-off path for stuck MIDI notes;
Tidal's `panic` primarily concerns SuperDirt synth nodes. Network-wide bindings and
firewall changes require explicit authorization.

