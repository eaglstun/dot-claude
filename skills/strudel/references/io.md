# Input / Output (MIDI · OSC · MQTT)

From strudel.cc/learn/input-output. **Read the compatibility note first** — this project
installs only `@strudel/web` + `@strudel/draw`, so the MIDI/OSC **sinks** that actually send
are not present, even though the control names are.

## What's available in THIS project (verified)

- **Present** (control names, registered as Pattern methods): `midichan`, `midicmd`, `ccn`,
  `ccv`, `control`, `midibend`, `miditouch`, `progNum`. You can build patterns with them.
- **NOT present**: the `.midi()` and `.osc()` output sinks, plus `midin`, `midikeys`,
  `midiport`, `sysex`, `mqtt`. These live in `@strudel/midi` / `@strudel/osc`, which aren't
  installed. Calling `.midi()` here throws "not a function". To actually send MIDI you'd add
  `@strudel/midi` (and a MIDI bus like the macOS IAC Driver).

So: the docs below are the real Strudel API; treat MIDI/OSC output as "needs an extra package"
until `@strudel/midi`/`@strudel/osc` is added to `package.json`.

## MIDI output

| Function                               | Signature                   | Does                                                        |
| -------------------------------------- | --------------------------- | ----------------------------------------------------------- |
| `.midi(out?, opts?)`                   | `.midi('IAC Driver')`       | send notes to a MIDI device/IAC bus (needs `@strudel/midi`) |
| `.midichan(n)`                         | `1`–`16`                    | MIDI channel (defaults to 1)                                |
| `.midiport(out)`                       | `.midiport('<0 1 2 3>')`    | pick output device; pattern to switch devices               |
| `.midicmd(cmd)`                        | `"clock*48,<start stop>/2"` | system real-time: clock, start, stop, continue              |
| `.control([cc, v])` / `.ccn(n).ccv(v)` | `[74, sine.slow(4)]`        | control change; `ccn`=CC number, `ccv`=value 0–1            |
| `.progNum(p)`                          | `"<0 1 2>"`                 | program change (0–127) — switch presets                     |
| `.midibend(p)`                         | `sine.range(-0.4,0.4)`      | pitch bend, −1..1                                           |
| `.miditouch(p)`                        | `sine.range(0,1)`           | key aftertouch, 0..1                                        |
| `.sysex(id, data)`                     | `0x43, "0x79:0x09:…"`       | system-exclusive bytes (needs `@strudel/midi`)              |

```js
// (with @strudel/midi installed)
chord("<C^7 A7>").voicing().midi("IAC Driver");
note("c a f e")
  .control([74, sine.slow(4)])
  .midi(); // CC 74 LFO sweep
midicmd("clock*48,<start stop>/2").midi("IAC Driver"); // MIDI clock out
```

**midimaps**: `midimaps({ mymap: { lpf: { ccn: 74, min: 0, max: 20000, exp: 0.5 } } })`
registers a name→CC map; `defaultmidimap({ lpf: 74 })` sets the default used when none is named.

## MIDI input (needs `@strudel/midi`)

- **`midin(name?)`** → `const cc = await midin('IAC Driver Bus 1'); note("c a").lpf(cc(0).range(0,1000))`
  — receive control-change as a signal.
- **`midikeys(name?)`** → `const kb = await midikeys('KeyStep'); kb().s("tri")` — play from a
  MIDI keyboard (fixed note length).

## OSC (needs SuperCollider + SuperDirt + `@strudel/osc`)

- **`.osc()`** — sends each hap as an OSC message for SuperCollider / SuperDirt. If the audio
  engine target is set to OSC, `.osc()` is implicit. Setup: run SuperDirt, then `pnpm run osc`
  to forward messages.

## MQTT (send-only)

- **`.mqtt(broker, topic)`** — publishes control patterns as JSON (`{"s":"sax","speed":2}`).
  Strudel can only send over MQTT, not receive. Needs a websocket-capable broker.
