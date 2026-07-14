# FFglitch scripting API

`ffedit -s script.js` (or `-s script.py`) runs your code over the bitstream during
_transplication_: ffedit decodes each frame, hands you the requested codec data as live
objects, you mutate them in place, and ffedit rewrites a valid bitstream with your
changes. **No re-encode.** Scripts are ES modules (QuickJS) or Python3.

`fflive -s script.js input` runs the _same_ script in real time inside the player —
great for performing with MIDI/keyboard. Use `qjs script.js` to unit-test pure logic.

## The two exported functions

```javascript
export function setup(args) { ... }          // called once, before any frame
export function glitch_frame(frame, stream) { ... }   // called once per frame
```

### `setup(args)`

| `args` field    | dir        | meaning                                                                                                                        |
| --------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `args.features` | read/write | array of features to decode, e.g. `["mv"]`. **Set this** so the data you want lands on `frame`. Equivalent to `-f` on the CLI. |
| `args.input`    | read       | input filename                                                                                                                 |
| `args.output`   | read/write | output filename; you can set it here instead of `-o`                                                                           |
| `args.params`   | read       | the value passed via `-sp <JSON>` (string/number/object). Guard with `"params" in args`.                                       |

```javascript
export function setup(args) {
  args.features = ["mv"];
  let tail = "params" in args ? args.params : 10; // -sp 10
  // stash tail in a module-scope variable for glitch_frame to use
}
```

> **`-sp` rejects floating-point numbers.** `-sp 2.5` errors with "floating point
> numbers are not supported". Pass an integer (`-sp 3`), or pass a JSON string and parse
> it yourself (`-sp '"2.5"'` → `parseFloat(args.params)`). A float _default literal
> inside the script_ is fine — the limit is only the `-sp` command-line parser.

### `glitch_frame(frame, stream)`

- `frame` — one key per selected feature, holding that feature's data object.
  The shapes match the exported JSON exactly — see features.md. Verified live
  (v0.10.2, `features = ["mv","q_dc","qscale","info"]` on MPEG-2):
  - `frame.mv` — `.forward` / `.backward` (each an `MV2DArray`, or missing when
    that direction doesn't exist), `.fcode` (Int32FFArray), `.overflow` (write
    `"truncate"` before out-of-range MV math).
  - `frame.q_dc` / `frame.q_dct` — `.data` = plain Arrays `[plane][row][col]`
    (plane 0=Y, 1=Cb, 2=Cr; one cell per 8x8 block; numbers for `q_dc`, arrays
    of coefficients for `q_dct`), `.v_count`/`.h_count` (Int32FFArray). Mutate
    cells in place; skip `null`/`undefined` cells.
  - `frame.qscale` — `.slice` = Array of per-slice objects.
  - `frame.info` — `.pict_type` ("I"/"P"/"B"), `.interlaced`, `.mb_type` grid.
    Read-only intel: branch on frame type, find intra blocks.
- `stream` — informational: `stream.codec` (string), `stream.stream_index` (int).

Features you request but that don't exist on a given frame simply aren't on
`frame` — always null-check:

```javascript
export function glitch_frame(frame) {
  const fwd = frame.mv?.forward;
  if (!fwd) return;
  // ... mutate fwd ...
}
```

## Motion vector data types

A single motion vector is a 2-element pair **`[ horizontal, vertical ]`** (the `MV` /
`MVRef` types). Construct one with `MV(h, v)`.

`frame.mv.forward` is an **`MV2DArray`** — a 2-D grid of MVs, one per macroblock:

| member                        | what it does                                            |
| ----------------------------- | ------------------------------------------------------- |
| `.width`, `.height`           | grid dimensions (in blocks)                             |
| `.fill(MV(h,v))`              | set every cell to the same MV                           |
| `.dup()`                      | **deep copy** — use before accumulating across frames   |
| `.add(other)` / `.sub(other)` | elementwise add/subtract another `MV2DArray`            |
| `.div(mv)` / `.mul(mv)`       | elementwise divide/multiply by an `MV` (e.g. `MV(n,n)`) |
| `.assign(other)`              | copy another array's values into this one               |
| `new MV2DArray(w, h)`         | fresh zeroed grid of that size                          |

**Indexing one cell — read vs. write differ (verified against v0.10.2):**

```javascript
const fwd = frame.mv.forward; // grid is [row][col] == [mb_y][mb_x]
const c = fwd[y][x]; // an MV object (or null on a skipped block)
const h = c[0],
  v = c[1]; // READ: index it like a pair
fwd[y][x] = MV(h + 8, v); // WRITE: must be MV(...) or null
fwd[y][x] = [h + 8, v]; // ✗ THROWS: "can only be assigned 'null' or MV(x,y)"
```

So: `forward[y][x]` is row-major (`.height` rows × `.width` cols). A cell reads back as
an index-accessible `MV` object — but on assignment ffedit only accepts `MV(x,y)` or
`null`. Companion types `MV2DPtr`/`MV2DMask` exist for advanced selection.

More of the documented API (docs 0.10.2, quickjs section) — the fast whole-array
ops are where the ~20× speedup over per-cell JS loops lives:

- Every mathOp has `_h`/`_v` variants: `fwd.assign_h(0)` zeroes all horizontal
  components in one call (the official "mv sink and rise" effect is literally
  that one line). Scalars, `MV`s, or same-size arrays are accepted sources.
- `compare_eq/neq/gt/gte/lt/lte` (+ `_h`/`_v`) return an `MV2DMask`; pass an MV,
  a scalar (compared against squared magnitude), or a custom `compare(fn)`.
  Masks combine with `not/and/or/xor` and gate any mathOp via a trailing mask
  arg, plus `maskedForEach()` — "glitch only blocks moving faster than X".
- Single `MV`s have `magnitude()`, `magnitude_sq()`, `swap_hv()`, `clear()`.
  Arrays add `largest_sq()`/`smallest_sq()`, `reverse()`, `reverse_h()`,
  `reverse_v()`. `MV(...)` is an immutable constant; `new MV(...)` is mutable;
  `new MVRef(cell)` is a live reference into the grid.
- `MV2DArray.serialize()` → bytes and `new MV2DArray(bytes)` round-trip a whole
  grid (used by official ZeroMQ examples; not on the docs page).
- Typed arrays `Int8FFArray`…`Uint64FFArray` (+`FFPtr` views) with the usual
  JS array methods plus `.dup()` — these appear as `v_count`, `fcode`, pixel
  rows, etc.

Version gate: `export function` is **required** since 0.10 (the binary says so
if you forget); 2020-era blog scripts with bare `function glitch_frame` and
JSON-deep-copy idioms are pre-0.10 — translate before reusing.

Helpers in the JS environment: `Math.lround()` (rounds half-away-from-zero, handles
negatives the codec-correct way — prefer it over `Math.round` for MV math), plus
`print()`. SDL (keyboard/mouse/joystick), RtMidi (MIDI), and ZeroMQ bindings are
available, mainly useful under `fflive` for live control.

## Python scripting (verified setup on this Mac)

Same `setup`/`glitch_frame` model, but the API is dict/list-flavored. Two hard
requirements, discovered the fun way:

1. **`FFGLITCH_LIBPYTHON_PATH`** must point at a libpython dylib, or ffedit says
   "Could not find libpython in the usual places".
2. **numpy must be importable** in that same interpreter, or it aborts with
   `ModuleNotFoundError: No module named 'numpy'`.

Working combo on this machine (pyenv 3.14.2 has numpy):

```bash
export FFGLITCH_LIBPYTHON_PATH=$HOME/.pyenv/versions/3.14.2/lib/libpython3.14.dylib
ffedit -i in.m2v -s glitch.py -y -o out.m2v
```

API differences from JS (all verified on v0.10.2):

| JS                       | Python                                       |
| ------------------------ | -------------------------------------------- |
| `args.features = ["mv"]` | `args["features"] = ["mv"]` (dict-style)     |
| `frame.mv?.forward`      | `frame.get("mv")`, then `mv.get("forward")`  |
| `MV2DArray` object       | plain `list` of rows                         |
| `fwd[y][x] = MV(h, v)`   | `row[i] = [h, v]` — plain lists are accepted |

In-place mutation of the nested lists propagates back into the bitstream (verified
by output diff). No `.dup()`/`.fill()` helpers — use Python list ops / numpy.
Example: [`scripts/examples/mv_glide.py`](../scripts/examples/mv_glide.py).
Reach for JS unless you specifically want Python — the tutorials are JS-first and
the JS types are richer.

## Worked example — temporal smear (averaging MVs over N frames)

Replaces each frame's motion vectors with a running average of the last `tail_length`
frames — produces a smooth, dragging "smear." From the official 0.10 tutorial; runs at
~300 fps. Note the **deep copy** before accumulation — the load-bearing detail.

```javascript
let prev_fwd_mvs = [];
let total_sum;
let tail_length = 10; // override with -sp <num>
let tail_length_mv;

export function setup(args) {
  args.features = ["mv"];
  if ("params" in args) tail_length = args.params;
  tail_length_mv = MV(tail_length, tail_length);
}

export function glitch_frame(frame) {
  const fwd_mvs = frame.mv?.forward;
  if (!fwd_mvs) return;
  frame.mv.overflow = "truncate";

  const deep_copy = fwd_mvs.dup(); // copy CLEAN values, not aliased
  prev_fwd_mvs.push(deep_copy);

  if (!total_sum) total_sum = new MV2DArray(fwd_mvs.width, fwd_mvs.height);

  if (prev_fwd_mvs.length > tail_length) {
    // drop the oldest frame
    total_sum.sub(prev_fwd_mvs[0]);
    prev_fwd_mvs = prev_fwd_mvs.slice(1);
  }
  total_sum.add(deep_copy);

  if (prev_fwd_mvs.length == tail_length) {
    // write the average back
    fwd_mvs.assign(total_sum);
    fwd_mvs.div(tail_length_mv);
  }
}
```

Run it:

```bash
ffedit -i input.m2v -s mv_average.js -sp 10 -o smeared.m2v
```

## ffgac's pixel-level `script` filter (different API!)

`ffgac -vf script=file=pix.js` runs a script per frame at the **pixel** level during
encode — generative sources / pixel math, not bitstream editing. It does NOT use
`setup`/`glitch_frame`; it exports a single `filter(args)` (verified):

```javascript
export function filter(args) {
  // args.frame_num  — frame counter
  // args.pts        — presentation timestamp
  // args.data       — [plane][row] pixel arrays (3 planes for yuv420p;
  //                    plane 0 is full-res luma: 96 rows for a 96-px-high frame)
  const luma = args.data[0];
  // mutate pixel values in place
}
```

```bash
ffgac -f lavfi -i testsrc2=duration=10:size=256x256 -vf script=file=pix.js -an out.mp4
```

## Pattern starters

- **Zero motion (freeze-ish):** `frame.mv.forward?.fill(MV(0,0))`
- **Constant drift:** `frame.mv.forward?.fill(MV(8, 0))` — everything slides right
- **Amplify existing motion:** multiply the array by `MV(3,3)` to exaggerate movement
- **Per-block chaos:** loop `.height`×`.width` and set each cell `fwd[y][x] = MV(...)`
  from your own function of `(x, y, frame_num)`
- **Row shear / waves:** per-row offset from `Math.sin(row, frame_num)` — see
  [`scripts/examples/mv_sine.js`](../scripts/examples/mv_sine.js)
- **DC scars:** add a constant to `frame.q_dc.data[0]` cells in a region — see
  [`scripts/examples/dc_streak.js`](../scripts/examples/dc_streak.js)
- **Frame-type branching:** `if (frame.info?.pict_type === "I") ...` (request
  `"info"` alongside your edit feature)
