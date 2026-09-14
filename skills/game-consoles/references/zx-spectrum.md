---
semantic_id: "TPIICudaaHayNJK6PcGyUVfwpYgpQAAG"
related_ids:
  - "3MQ9nqZUKHby4KO-foWQVQuy4eqlQAAO"
  - "1FM5vqdUKXawIKJ_eN2RULGy4IDlAAAK"
---

# Sinclair ZX Spectrum (ULA) — hardware truth and how to fake it

Sinclair Research, 1982, UK. A Zilog Z80A and a single custom ULA driving a 256×192
1-bit screen with **two colours per 8×8 character cell** — the machine of colour clash,
INK and PAPER attributes, and a fiercely saturated 15-colour palette. Not a console (a
£125 British home computer with a rubber keyboard), but it earns a place on this shelf
because its graphics constraint is the most _legible_ of any 8-bit machine and the one
that maps most cleanly onto a modern shader.

The Spectrum stores its screen as **two separate layers at two different resolutions**:

- a **1-bit-per-pixel bitmap** at 256×192 — pure detail, no colour information at all
- an **attribute layer** at 32×24 — one byte per 8×8 cell, holding two colours

That is **chroma subsampling, 8×8, with a 1-bit luma**. The detail is eight times finer
than the colour. Every visual signature of the machine falls out of that one split, and it
also tells you exactly how to reproduce it: threshold a luma pass, quantize a colour pass
at 1/8 resolution, combine.

If you take one design rule into a modern renderer: **draw the shape in 1 bit, and colour
it in blocks that don't line up with it.**

## The numbers

|                      | 48K                                                  | 128K / +2 / +3                                  |
| -------------------- | ---------------------------------------------------- | ----------------------------------------------- |
| CPU                  | Zilog **Z80A @ 3.5 MHz** (14 MHz / 4)                | 3.546895 MHz (17.734475 / 5)                    |
| RAM                  | 16K or **48K**                                       | 128K in 16K banked pages                        |
| display              | **256×192** pixels + a solid border                  | same                                            |
| bitmap               | **6144 bytes**, 1 bit per pixel                      | same                                            |
| attributes           | **768 bytes**, one per 8×8 cell (32×24)              | same                                            |
| total screen RAM     | 6912 bytes                                           | same, ×2 (shadow screen for page-flipping)      |
| T-states per frame   | 69888 (224 per line × 312 lines)                     | 70908 (228 × 311)                               |
| frame rate           | **50.08 Hz**                                         | 50.02 Hz                                        |
| palette              | **15 colours** (8 hues × 2 brightness, black shared) | same                                            |
| colours per 8×8 cell | **2** — and they must share the BRIGHT bit           | same                                            |
| sound                | **1-bit beeper**, CPU-driven, port `$FE` bit 4       | + **AY-3-8912**, 3 channels + noise + envelopes |
| hardware sprites     | **none**                                             | none                                            |
| hardware scrolling   | **none**                                             | none                                            |

**Pixels are square.** 256×192 is exactly 4:3, so unlike the 2600 (1.6:1) and the NES
(8:7), a Spectrum image needs **no aspect correction at all** — integer upscale and stop.
This is genuinely unusual for the era and it's the one place the Spectrum is _easier_ than
its contemporaries.

There are no sprites, no scrolling hardware, and no blitter. Every pixel moved is the Z80
moving it, which is why so many Spectrum games are flick-screen rather than scrolling, and
why the ones that do scroll (_Cybernoid_, _Rex_) were showing off.

## The attribute byte

One byte per 8×8 cell, and it is the whole colour system:

```text
 bit  7      6       5  4  3     2  1  0
      FLASH  BRIGHT  PAPER       INK
             │       │           └── foreground colour, 0-7
             │       └────────────── background colour, 0-7
             └────────────────────── applies to BOTH, not one
```

- **INK** colours the 1 bits of the bitmap, **PAPER** the 0 bits. Two colours per cell,
  full stop.
- **BRIGHT is per cell, not per colour.** You cannot put bright red next to normal blue in
  the same 8×8 block. This halves your effective palette inside any given cell: you get 2
  of the 8 normal colours, or 2 of the 8 bright ones — never a mix.
- **FLASH** swaps INK and PAPER on a timer, **0.64 s per full cycle** (16 frames each
  state at 50 Hz). Used for cursors, menu highlights, "PRESS ANY KEY". Sparingly — it's
  obnoxious, and period software knew it.

### The palette

Three bits, one per gun, with **blue in the low bit**: `bit0 = blue, bit1 = red,
bit2 = green`. Two brightness levels, produced by dropping the output voltage to ~85% —
which lands the non-bright components at `$D8` rather than `$FF`.

| value | colour  | normal (BRIGHT 0) | bright (BRIGHT 1) |
| ----- | ------- | ----------------- | ----------------- |
| 0     | black   | `#000000`         | `#000000`         |
| 1     | blue    | `#0000d8`         | `#0000ff`         |
| 2     | red     | `#d80000`         | `#ff0000`         |
| 3     | magenta | `#d800d8`         | `#ff00ff`         |
| 4     | green   | `#00d800`         | `#00ff00`         |
| 5     | cyan    | `#00d8d8`         | `#00ffff`         |
| 6     | yellow  | `#d8d800`         | `#ffff00`         |
| 7     | white   | `#d8d8d8`         | `#ffffff`         |

**15 distinct colours**, because black has no bright variant.

```js
// index = colour 0-7, plus 8 if BRIGHT. Entries 0 and 8 are both black.
export const ZX_PALETTE = [
  0x000000, 0x0000d8, 0xd80000, 0xd800d8, 0x00d800, 0x00d8d8, 0xd8d800,
  0xd8d8d8, 0x000000, 0x0000ff, 0xff0000, 0xff00ff, 0x00ff00, 0x00ffff,
  0xffff00, 0xffffff,
];
```

Note what this palette _is_: full-saturation primaries and secondaries at two intensities.
**There are no intermediate tones, no browns, no greys except white's two steps, and no
shading ramp anywhere.** You cannot make a colour darker — only less bright, once. That
single fact drives the whole visual style: shading on the Spectrum is **dithering**, done
in the 1-bit bitmap between the cell's own two colours. Which is why Spectrum art is full
of crosshatch and checkerboard texture where other machines would use a gradient.

### The border

The border is a solid colour set by the low 3 bits of port `$FE` — **non-bright only**, 8
choices, no pattern, no bitmap. It's a real part of the composition: loading screens,
title frames, and the tape-loading stripes all live there. Changing it mid-frame at
precise T-state offsets gives horizontal band effects, the Spectrum's version of a raster
trick, and it's how demos draw "outside" the screen.

## The screen memory layout, and why it matters

The bitmap is famously **not** linear. For pixel row `y` (0–191) and byte column `x` (0–31):

```text
addr = 0x4000 | ((y & 0xC0) << 5) | ((y & 0x07) << 8) | ((y & 0x38) << 2) | x
attr = 0x5800 + (y >> 3) * 32 + x
```

Three fields interleaved: the screen is split into **thirds** (top/middle/bottom, `y & $C0`),
then within a third the _pixel row within a character_ (`y & $07`) sits in a higher address
bit than the _character row_ (`y & $38`). Consecutive scanlines are 256 bytes apart; every
8th scanline jumps back.

Two consequences that show up on screen:

- **Vertical movement is expensive**, horizontal is cheap. A byte-aligned horizontal shift
  is a memory copy; a one-pixel vertical shift is an address recalculation per row. Games
  are built around this.
- **Loading and clearing paint in that order.** The characteristic way a Spectrum screen
  fills in — bands appearing interleaved rather than top-to-bottom — is this layout being
  written linearly.

Also relevant: the lower 16K of RAM is **contended** — the ULA is fetching display data
from it, and the CPU stalls when it collides. Code and data in contended RAM run roughly
20–40% slower. On a 48K machine you moved the hot loops up high. This is why some games
feel jerky in ways unrelated to how much they're drawing.

## Colour clash, properly understood

**Attribute clash** (or colour clash) is _the_ Spectrum artifact: a sprite moves across a
differently-coloured background and drags rectangular colour fringes with it, because the
sprite can only recolour whole 8×8 cells, and each cell holds one pair of colours for
everything inside it.

The NES has the same class of problem at 16×16 with 4 palettes of 3. The Spectrum's is far
more severe — **2 colours, at 8×8, sharing a brightness bit** — and unlike the NES it's
happening on a machine with no sprite hardware, so the artifact lands on the player's own
character constantly.

The important thing for reproduction is that **artists designed around it**, and the
workarounds are themselves the look:

- **Monochrome-first art.** Draw everything in white-on-black and place colour only where
  it can't clash — a coloured status panel, a coloured background band, coloured static
  scenery well away from anything that moves. An enormous number of Spectrum games are
  effectively black-and-white with decorative colour, _by design_. If your reproduction
  paints everything in colour, it will look wrong even though it's obeying the rules.
- **Cell-aligned everything.** Sprites moved in 8-pixel steps so they never straddled a
  cell boundary. Chunky, snapping motion — a tell in itself.
- **Attribute-only graphics.** Some games ignored the bitmap entirely and drew in 32×24
  colour blocks, which is 8× less memory to push. Very fast, very coarse.
- **Colour by band.** Sky cyan, ground green, in horizontal strips 8 pixels tall, because
  a horizontal split costs nothing.

## Sound

The 48K has **one bit**. Port `$FE` bit 4 drives the speaker cone directly; every waveform
is the CPU toggling it on a timed loop, and the CPU can do nothing else while it does.
That's why 48K games either have music or gameplay, rarely both.

The remarkable part is what people got out of it: **multichannel beeper engines** (Tim
Follin, Jonathan Dunn, later Music Box) interleave several square waves by rapidly
switching the single bit between them, producing 3+ apparent voices with a distinctive
buzzy, gritty timbre and an audible high-frequency whine underneath. That whine is the
tell — it isn't a clean chiptune, it's a 1-bit approximation of one and it sounds like it.

The 128K adds an **AY-3-8912**: 3 square-wave channels, noise, hardware envelopes. Same
chip family as the Atari ST and Amstrad CPC, and much cleaner. A "Spectrum sound"
reproduction has to pick which machine it means — they sound nothing alike.

### 48K beeper — the limits

**There is no sound hardware.** That's the whole specification. One bit of one output port
wired to a piezo speaker, and no timer, no counter, no oscillator, no DAC.

|               |                                                 |
| ------------- | ----------------------------------------------- |
| channels      | **1**, in the sense that there is one bit       |
| volume        | **none** — a bit is high or low                 |
| waveform      | whatever the CPU has time to toggle             |
| timing source | **the 50 Hz frame interrupt**, and nothing else |
| CPU cost      | **all of it**                                   |

Consequences, each of which is audible:

- **Sound blocks the game.** A tone is a counted `DJNZ` loop; while it runs, nothing else
  does. This is why so many 48K games have a title tune and then near-silence during play,
  and why sound effects make the action visibly stutter.
- **No volume, so dynamics are pulse width.** Varying the duty cycle of the toggling
  changes perceived loudness and timbre together — you cannot fade without also changing
  the tone.
- **Pitch accuracy depends on loop cycle counts**, so the scale is quantized by Z80
  instruction timing, and it drifts differently depending on whether the loop is running in
  contended or uncontended RAM.
- **Multichannel is time-division multiplexing.** Engines (Tim Follin, Jonathan Dunn, later
  Music Box / Beepola) interleave several virtual oscillators onto the single bit. Every
  added voice halves the effective switching resolution and adds intermodulation, producing
  the characteristic gritty buzz with a **high-frequency whine sitting under everything**.
  That whine is the artifact of the multiplexing itself. It is the sound of the machine and
  you should not filter it out.
- **Digitized samples exist** — 1-bit PWM, a few seconds at most, consuming the entire CPU
  and usually the whole screen too.

### 128K AY-3-8912 — the limits

Real sound hardware, clocked at **1.7734 MHz**, and much better behaved — but with its own
hard edges:

|            |                                                                              |
| ---------- | ---------------------------------------------------------------------------- |
| channels   | 3 tone, **square wave only, fixed 50% duty**                                 |
| tone pitch | 12-bit period, `f = 1773400 / (16 × period)` → **27 Hz to 110 kHz**          |
| noise      | **one** generator, 5-bit period, mixable into any channel                    |
| volume     | 4-bit per channel (16 steps)                                                 |
| envelope   | **one** generator, 8 shapes, 16-bit period, **shared by all three channels** |

The two that actually constrain composition:

- **One noise generator for three channels.** Two different drum timbres cannot sound at
  once; they share a period register, so a hi-hat and a snare fight over it.
- **One envelope generator, shared.** A channel uses either its own fixed 4-bit volume _or_
  the global envelope — and there is only one envelope, at one rate, for the whole chip. You
  cannot give three voices three different decays. AY music therefore does its dynamics by
  **writing volume registers manually every frame**, which is why AY tunes have that stepped,
  50 Hz-quantized shape to their attacks.
- **No filter, no ring modulation, no oscillator sync, no PWM.** All the things that make a
  C64 SID recognisable are absent, and the AY sounds cleaner and thinner because of it.
- **Digi-drums**: rapid writes to the volume registers play samples, at the usual price of
  the entire CPU.

### Reproducing the sound

**For 48K beeper**, model the bit, not the note: run a 1-bit output at the Z80's toggle
resolution, generate voices by multiplexing, and keep the aliasing and the whine. A clean
square-wave synth with three independent oscillators will sound like a Game Boy, not a
Spectrum — the grit _is_ the identity.

**For 128K AY**, three hard square waves at fixed 50% duty, one shared LFSR noise source,
volume quantized to 16 steps and updated at 50 Hz, and one envelope generator that every
channel has to queue for.

## Visual tells — what makes it read as Spectrum

Ranked by how much each does for you:

1. **8×8 colour cells that don't align with the artwork** — the clash. Rectangular colour
   fringes around anything that moves.
2. **1-bit detail under flat colour.** Edges, texture, and shading are all monochrome
   patterning; colour is a coarse overlay. Get this split right and the rest follows.
3. **Dithered shading** — checkerboards and crosshatch, at pixel resolution, inside a
   cell's two colours. No gradients, ever.
4. **The saturated 15-colour palette** with its two-step brightness and no in-between
   tones. Spectrum images look electric and slightly harsh next to a C64's muted set.
5. **Large monochrome regions with sparse deliberate colour** — the design response, not a
   failure.
6. **The border** as a solid coloured frame around a 256×192 image.
7. **Square pixels** — no stretch.
8. **8-pixel snapped motion** for anything that needed to stay clean.

## Reproducing it

The two-layer split makes this the most mechanical of the three consoles in this shelf.
Render once, then run two independent reductions.

**Pass 0 — render at 256×192**, nearest everything, no MSAA, no tone mapping. Flatten the
lighting: you have two colours per cell and a dither, so a continuous gradient buys you
nothing and costs stability.

**Pass 1 — the attribute pass, one fragment per 8×8 cell (32×24 = 768 fragments).** Same
shape as the NES attribute pass, different search space. For each cell, read its 64 texels
and choose the (INK, PAPER, BRIGHT) triple minimising squared error, where each pixel is
assigned to whichever of the two colours is nearer:

- Candidates: **all pairs within one brightness set**. 8 colours → 28 unordered pairs, ×2
  brightness sets = **56 candidate pairs** per cell (black appears in both sets, so a few
  are duplicates — harmless).
- 64 texels × 56 pairs × 2 distance tests ≈ 7k ops per cell, 768 cells. Trivial on a GPU,
  fine on a CPU too.
- Write INK, PAPER and BRIGHT into a 32×24 target.

**Add hysteresis**, exactly as for the NES: a cell balanced between two pairs will flip
every frame and strobe. Keep last frame's choice unless the new one wins by ~15%.

**Pass 2 — resolve.** For each pixel: fetch its cell's two colours, **apply an ordered
Bayer dither to the luma before thresholding**, and pick INK or PAPER.

```glsl
// 4x4 Bayer, locked to the 256x192 grid — never to screen pixels
float bayer4(ivec2 p) {
  const int m[16] = int[16](0,8,2,10, 12,4,14,6, 3,11,1,9, 15,7,13,5);
  return float(m[(p.y & 3) * 4 + (p.x & 3)]) / 16.0;
}

vec3 resolve(vec2 uv, ivec2 px) {
  ivec2 cell = px >> 3;
  vec3 ink   = texelFetch(uInk,   cell, 0).rgb;
  vec3 paper = texelFetch(uPaper, cell, 0).rgb;
  vec3 c     = texelFetch(uScene, px, 0).rgb;

  // project the pixel onto the ink<->paper axis: 0 = paper, 1 = ink
  vec3  axis = ink - paper;
  float t    = clamp(dot(c - paper, axis) / max(dot(axis, axis), 1e-6), 0.0, 1.0);

  return t > bayer4(px) ? ink : paper;   // dither, then 1-bit threshold
}
```

The dither must be locked to the **256×192 grid**, not the output resolution — dithering
after upscaling gives you a fine noise that no 8-bit machine could produce.

**Present:** integer upscale, `NearestFilter`, **no aspect correction**. Draw a solid
border frame around it in one of the 8 non-bright colours if you want the full picture.

Per-platform, the same interpolation gotcha as always:

| target           | small buffer                | nearest                             | present                                    |
| ---------------- | --------------------------- | ----------------------------------- | ------------------------------------------ |
| Three.js / WebGL | 256×192 `WebGLRenderTarget` | `NearestFilter` both, `samples: 0`  | integer-scaled quad, no stretch            |
| Metal            | 256×192 `MTLTexture`        | `.magFilter/.minFilter = .nearest`  | integer blit                               |
| SwiftUI          | 256×192 `CGImage`           | `.interpolation(.none)`             | `.aspectRatio(4.0/3.0, contentMode: .fit)` |
| Canvas 2D        | 256×192 backing canvas      | `ctx.imageSmoothingEnabled = false` | CSS `image-rendering: pixelated`           |

## What to honour and what to fake

| constraint                                            | recommendation                                                                                                                          |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 256×192, square pixels                                | **honour** — and enjoy not doing PAR maths for once                                                                                     |
| 15-colour palette, exact hex                          | **honour** — assertable, and the saturation is half the look                                                                            |
| **2 colours per 8×8 cell**                            | **honour** — the defining constraint                                                                                                    |
| **BRIGHT shared across the cell**                     | **honour** — cheap to implement, and skipping it silently doubles your palette and kills the look                                       |
| 1-bit bitmap + dither for all shading                 | **honour**                                                                                                                              |
| monochrome-first art direction                        | **honour** — this is the part that's a _design_ choice, not a shader; colour everything and it reads wrong even when the maths is right |
| the border                                            | honour if you want the full framing; it's free                                                                                          |
| 8-pixel snapped sprite motion                         | optional — very period, and it reads as intentional rather than broken                                                                  |
| FLASH attribute                                       | optional, use sparingly                                                                                                                 |
| non-linear screen memory                              | **fake / ignore** — there's no memory to lay out. Only relevant if you're deliberately animating a "loading" fill                       |
| contended memory timing                               | ignore                                                                                                                                  |
| 1-bit beeper timbre (48K)                             | **honour** — model the bit and the multiplexing whine, not three clean oscillators. Filtering the grit out leaves you with a Game Boy   |
| sound blocking the CPU (48K)                          | honour as a _composition_ rule — music or action, rarely both                                                                           |
| one shared noise generator + one shared envelope (AY) | **honour** — it's what forces AY dynamics into 50 Hz manual volume writes                                                               |
| AY square-only, no filter/ring-mod/sync               | honour — this is the whole difference between an AY and a SID                                                                           |

### The claim is assertable

Same test as the NES file, tightened: sample the framebuffer and verify that every pixel
is one of the 15 `ZX_PALETTE` values, **and** that within every 8×8 cell at most 2 distinct
values appear, **and** that those two share a brightness set. That's three assertions and
they either pass or they don't.

## Sources

- Palette values: [Lospec, ZX Spectrum](https://lospec.com/palette-list/zx-spectrum) — 15
  entries, `$D8` non-bright / `$FF` bright, from the ~85% output voltage of the non-bright
  level.
- Display file, attribute layout, clash and FLASH timing:
  [Wikipedia, ZX Spectrum graphic modes](https://en.wikipedia.org/wiki/ZX_Spectrum_graphic_modes)
  and [ZX Spectrum](https://en.wikipedia.org/wiki/ZX_Spectrum).
- Screen address formula and T-state timings: the standard ULA references in the
  World of Spectrum / SpectrumComputing technical documentation (48K 69888 T-states per
  frame, 128K 70908).
