# fflive — real-time glitching & live control (MIDI / keyboard / ZeroMQ)

`fflive` is "a hacked up ffplay" that runs the same `-s` glitch scripts as ffedit,
but live, on screen. Same script, three lifecycles: `ffedit` renders to file,
`fflive` performs it in real time, `qjs` unit-tests the logic.

```bash
$FFG/fflive -i input.avi -s script.js -sp 42
```

Useful flags (from `fflive -h`, v0.10.2): `-fs` fullscreen, `-an` no audio,
`-ss <sec>` seek, `-x/-y` window size, `-noborder`, `-alwaysontop`,
`-window_title`, `-scaling_quality nearest` (crisp pixels), `-nodisp`,
`-seek_interval <sec>`. Plus `-asap` (used throughout the official tutorial:
don't pace to input framerate).

## The canonical live rig (official tutorial one-liner)

ffgac preps a glitch-friendly stream and pipes it straight into fflive running a
script — live glitching of any source:

```bash
$FFG/ffgac -i input.mov -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 \
  -fcode 6 -g max -sc_threshold max -f rawvideo pipe: \
| $FFG/fflive -i pipe: -s mv_average.js -fs -asap
```

- `-fcode 6` widens the legal MV range so big glitch vectors don't clamp.
  (Docs note `-fcode` may be removed in a future version.)
- Sources can be anything ffgac reads: webcam on macOS is
  `-f avfoundation -i 0`, a YouTube stream is
  `yt-dlp -o - '<url>' | ffgac -i pipe: ... | fflive -i pipe: ...`.
- ffedit also does pipes since 0.10.1 (`-i pipe:`/`-o pipe:`), enabling
  `ffgac | ffedit -s glitch.js | ffgac` chains.

## Live input — general model

All input is **poll-based** in scripts (no callbacks): each `glitch_frame()` call,
drain the event/message queue, update module-scope state, apply to the frame.
SDL works **only in fflive**; RtMidi and ZeroMQ work in ffgac, ffedit, _and_
fflive (yes — MIDI can drive a file render or an encode too).

### Keyboard / joystick (SDL)

```javascript
const sdl = new SDL();
let pan = new MV(0, 0);

export function setup(args) {
  args.features = ["mv"];
}

export function glitch_frame(frame) {
  while (true) {
    const e = sdl.getEvent(); // null when queue is empty
    if (e === null) break;
    if (e.type === SDL.SDL_KEYDOWN) {
      if (e.sym === SDL.SDLK_LEFT) pan.add_h(-2);
      if (e.sym === SDL.SDLK_RIGHT) pan.add_h(2);
      if (e.sym === SDL.SDLK_UP) pan.add_v(-2);
      if (e.sym === SDL.SDLK_DOWN) pan.add_v(2);
    }
  }
  const fwd = frame.mv?.forward;
  if (!fwd) return;
  frame.mv.overflow = "truncate";
  fwd.add(pan);
}
```

Event fields: keyboard `{type, state, repeat, scancode, sym, mod}` (constants on
the global `SDL` object: `SDL.SDL_KEYDOWN/KEYUP`, `SDL.SDLK_*`,
`SDL.SDL_SCANCODE_*`); joystick axis `{which, axis, value −32768..32767}`;
buttons `{which, button, state}`. Also `sdl.numJoysticks()`,
`sdl.joystickOpen(i)`, `sdl.gameControllerOpen(i)`.

### MIDI (RtMidi)

```javascript
import * as rtmidi from "rtmidi";
const midi = new rtmidi.In();

export function setup(args) {
  args.features = ["mv"];
  // midi.getPortCount() / midi.getPortName(i) to enumerate
  midi.openPort(0, "ffglitch");
}

let amount = 0;
export function glitch_frame(frame) {
  while (true) {
    const msg = midi.getMessage(); // e.g. [176, cc, value]; [] when empty
    if (!msg.length) break;
    if ((msg[0] & 0xf0) === 0xb0 && msg[1] === 4) amount = msg[2]; // CC4 fader
  }
  frame.mv?.forward?.add(MV(amount - 64, 0));
}
```

No callback support — poll `getMessage()` until empty. The official tutorial's
`helpers/midi.js` wraps this as a `MIDIInput` class with `onevent(cc, fn)` /
`onbutton(id, fn)` / `parse_events()` (clone
`github.com/ramiropolla/ffglitch-scripts` for it). `rtmidi.Out()` +
`sendMessage([...])` exists for sending.

### Network (ZeroMQ)

```javascript
import * as zmq from "zmq";
const ctx = new zmq.Context();
const sock = ctx.socket(zmq.PULL);

export function setup(args) {
  args.features = ["mv"];
  sock.bind("tcp://0.0.0.0:5555");
}

export function glitch_frame(frame) {
  while (true) {
    const data = sock.recv_str(zmq.DONTWAIT); // null when nothing pending
    if (data === null) break;
    // e.g. JSON.parse(data) → update effect params
  }
}
```

Socket types: `PAIR PUB SUB REQ REP DEALER ROUTER PULL PUSH XPUB XSUB STREAM`.
Typed receives: `recv_int/_bigint/_str/_uint8ffarray`; `send()` takes
null/number/BigInt/string/Uint8FFArray. `zmq.Poller` for multi-socket waits.
`MV2DArray` has (undocumented but used in official examples)
`.serialize()`/`new MV2DArray(bytes)` for shipping whole MV grids over the wire.
The bundled standalone `qjs` (0.10.2+) has MIDI + ZMQ built in — write external
controller bridges in the same JS dialect. This pairs naturally with anything
that can push JSON to a socket (a phone, a sequencer, an OpenClaw agent…).

## Performance notes

- The 0.10 MV types are fast: the official averaging script runs ~300 fps at SD;
  the docs claim real-time 4K glitching is reachable.
- Prefer whole-array ops (`fill/add/assign_h/compare_*` + masks) over per-cell
  JS loops — that's where the 20× speedup lives.
- `fflive` is macOS-native SDL here; window/fullscreen works out of the box on
  this install (binaries are static, no SDL install needed).
