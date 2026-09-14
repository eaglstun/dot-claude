# Visualization (@strudel/draw)

`@strudel/draw` (1.2.6 here) renders patterns to a canvas. Importing it registers the viz
methods on the Pattern prototype. There is **no REPL** in this bare project, which decides
what actually renders — see the table.

## The methods

All are chainable Pattern methods. Two render styles:

- **no prefix** (`.pianoroll()`) → draws to a full-page background canvas.
- **`_` prefix** (`._pianoroll()`) → draws inline within a code block (REPL-only; irrelevant here).

### What renders WITHOUT a repl — the `draw` vs `onPaint` rule (verified by reading 1.2.6 source)

Each viz method is implemented one of TWO ways, and that decides how you wire it (all six
render fine here — `index.js` ships a one-word `VIZ` switch that handles both kinds):

- **Self-wired** — runs its own `requestAnimationFrame` loop, so you just call it and play:
  - `.pianoroll()` → `this.draw(...)`.
  - `.scope()` / `.tscope()` / `.spectrum()` / `.fscope()` → `this.analyze(id).draw(...)`
    (tap an analyser node, render its data; `.scope` is an alias for `.tscope`). The `ctx`
    defaults to `getDrawContext()`. **Do NOT wrap these in your own `.draw()`** — it reuses
    the same draw `id` and cancels their loop, leaving a blank canvas. (This bit me.)
- **onPaint** — `.pitchwheel()`, `.punchcard()`, `.spiral()` use `this.onPaint(...)`, which
  has no built-in loop (a REPL drives it). Drive them yourself: `pattern.getPainters()` →
  run the painters inside a `.draw()` loop (see below).

| Method                                           | Impl               | How to use here                                   |
| ------------------------------------------------ | ------------------ | ------------------------------------------------- |
| `.pianoroll(opts)`                               | `draw`             | call it, done                                     |
| `.scope()`/`.tscope()`/`.spectrum()`/`.fscope()` | `analyze().draw()` | call it, done — **don't re-wrap in `.draw()`**    |
| `.pitchwheel(opts)`                              | `onPaint`          | `getPainters()` + `.draw()` — looks great         |
| `.punchcard(opts)` / `.spiral(opts)`             | `onPaint`          | `getPainters()` + `.draw()` (spiral: tune `size`) |
| `.color("cyan")`                                 | —                  | sets viz color, accepts patterns                  |

**Beware "a canvas exists" ≠ "it's drawing."** `getDrawContext()` creates a fullscreen
canvas as a side effect, so an onPaint method can leave a _blank_ canvas sitting there.
Verify by sampling pixels or eyeballing, not by `document.querySelector('canvas')`. (Also:
`requestAnimationFrame` is throttled in background tabs, so a viz may look dead in headless
checks but render fine once the tab is focused — screenshots are the honest test.)

### Driving onPaint viz WITHOUT a repl — `getPainters()` + `.draw()`

You don't actually need a repl. `.onPaint(fn)` just stashes painter functions in the
pattern's state; `pattern.getPainters()` returns them. Run them inside `pianoroll`'s
self-sufficient `.draw()` loop and every onPaint viz works. This is exactly what `index.js`
does — one `visualize()` covers pianoroll, pitchwheel, spiral, punchcard, scope, spectrum:

```js
function visualize(pattern) {
  const viz = pattern[VIZ](VIZ_OPTS[VIZ] || {});
  if (VIZ === "pianoroll") return viz; // already self-sufficient
  const painters = viz.getPainters(); // the onPaint callbacks
  const drawTime = [-2, 2]; // [lookbehind, lookahead] in cycles
  return viz.draw(
    (haps, time) => {
      const ctx = getDrawContext();
      painters.forEach((paint) => paint(ctx, time, haps, drawTime));
    },
    { lookbehind: 2, lookahead: 2, id: 1 },
  );
}
```

The painter signature is `(ctx, time, haps, drawTime)`. `index.js` ships a one-word `VIZ`
switch. (Note: `scope`/`spectrum`/`tscope`/`fscope` are NOT onPaint — they self-wire via
`analyse().draw()`; pass them through, don't re-wrap. Spiral's `size` is a **pixel radius**,
default 80 — `size: 0.9` gives a 0.9px dot.) Viz paint light-on-transparent, so the page
needs a **dark background** (`index.html` sets `body { background: #0b0b12 }`).

## Color palettes — recoloring the viz

A viz has TWO colorable parts, and they read color from different places:

- **Structure** (pitchwheel ring + pitch-class dots, spiral arms, scope/spectrum baseline) →
  the theme `foreground`. Change it with **`setTheme({ ...getTheme(), foreground, background })`**
  (from `@strudel/draw`). Must be a single color.
- **Notes** (pitchwheel polygon, pianoroll/punchcard bars, and the scope/spectrum line, which
  reads the active hap's color) → **`pattern.color(c)`**. `c` can be a single hex or a
  mini-notation string that cycles hues per cycle (`"<#ff5fd2 #ff7a18 #ffd166>"`).

You need **both** — `setTheme` alone misses the notes, `.color()` alone leaves the ring/dots
the default blue. (Verified: pitchwheel ring stays blue under `.color()` until `setTheme`
recolors it; the scope line follows `.color()`.) Don't bother trying to `setTheme` the scopes
specifically — `@strudel/web`'s scope reads a _separate_ theme object with no exported setter,
but it picks up `.color()` from the hap anyway.

A swappable-palette helper (this is what `index.js` ships — `PALETTE` is a one-word switch):

```js
import { getTheme, setTheme } from "@strudel/draw";

const PALETTES = {
  ice: { bg: "#0b0b12", fg: "#7cd0ff", color: "#7cd0ff" }, // cool blue
  ember: { bg: "#150a06", fg: "#ff7a18", color: "#ff7a18" }, // warm orange
  acid: { bg: "#07120a", fg: "#9dff4f", color: "#9dff4f" }, // green
  vapor: { bg: "#140a1f", fg: "#ff5fd2", color: "#ff5fd2" }, // magenta
  mono: { bg: "#000000", fg: "#f5f5f5", color: "#f5f5f5" }, // high-contrast white
  gold: { bg: "#120f06", fg: "#ffd166", color: "#ffd166" }, // amber
  sunset: { bg: "#1a0a12", fg: "#ff7a18", color: "<#ff5fd2 #ff7a18 #ffd166>" }, // multi-hue
  rainbow: {
    bg: "#08080c",
    fg: "#5fb0ff",
    color: "<#ff5f5f #ffb05f #fff75f #5fff8f #5fb0ff #b05fff>",
  },
};

function applyPalette(pattern, name) {
  const p = PALETTES[name] || PALETTES.ice;
  document.body.style.background = p.bg;
  setTheme({ ...getTheme(), background: p.bg, foreground: p.fg });
  return pattern.color(p.color);
}
```

Hex `#` is fine in `.color()` (unlike note mini-notation, where `#` fails — use `s` there).

## Option objects (from the docs)

- **pianoroll / punchcard**: `cycles`, `playhead`, `vertical`, `labels`, `flipTime`,
  `flipValues`, `fold`, `smear`, `overscan`, `active`, `inactive`, `background`, `fill`,
  `stroke`, `hideInactive`, `colorizeInactive`, `fontFamily`, `minMidi`, `maxMidi`, `autorange`.
- **spiral**: `stretch`, `size`, `thickness`, `cap`, `inset`, `playheadColor`, `playheadLength`,
  `steady`, `activeColor`, `fade`, `logSpiral`.
- **scope**: `align`, `color`, `thickness`, `scale`, `pos`, `trigger`.
- **spectrum**: `thickness`, `speed`, `min`, `max`.

```js
note("c2 a2 eb2").pianoroll({ labels: 1, fold: 1 });
s("sawtooth").scope({ thickness: 2 });
n("<0 4 <2 3> 1>*3").spectrum();
note("c2 a2 eb2").euclid(5, 8).spiral({ steady: 0.96 }); // repl-only render
```

## Manual wiring (the reliable path here)

`pattern.draw(callback, options)` runs `callback(haps, time)` every animation frame.
`getDrawContext()` gives the shared canvas 2D context; `cleanupDraw()` tears the loop down.

```js
import { pitchwheel, getDrawContext, cleanupDraw } from "@strudel/draw";

pattern
  .draw(
    (haps, time) => {
      const ctx = getDrawContext();
      pitchwheel({
        haps: haps.filter((h) => h.isActive(time)),
        ctx,
        mode: "polygon", // or "dot"
        circle: 1,
        hapRadius: 8,
      });
    },
    { lookbehind: 0, lookahead: 1, id: 1 }, // window in CYCLES, not seconds
  )
  .play();
```

Call `cleanupDraw()` on Stop (the Stop button already does, alongside `hush()`).

## Lower-level building blocks (in @strudel/web)

If you want to roll your own scope/spectrum: `.analyze(id)` tags a signal for analysis,
then `drawTimeScope(...)` / `drawFrequencyScope(...)` (and `fft`, `analysers`) read it.
These exist in `@strudel/web` and are what `.scope()`/`.spectrum()` use internally.

## Tips

- For a quick look at any pattern, `.pianoroll()` beats hand-wiring every time.
- `lookahead`/`lookbehind` are in **cycles** (`lookahead: 1` ≈ one bar ahead), not seconds.
- One `getDrawContext()` canvas is shared; give concurrent draws distinct `id`s.
