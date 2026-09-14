---
name: game-consoles
description: Hardware reference for classic consoles and 8-bit computers as style targets in modern renderers and synths. Use to reproduce a machine's real display, palette, sprite, timing, and sound constraints, or diagnose why retro-styled visuals or audio feel wrong.
metadata:
  public: 'true'
  semantic_id: ZG04XjdUwmewJb7M-NoRwNuw2WmwEAAO
  related_ids: '["ZG0w579Q2TWZLYoC9HqDQJlYMcmzAAAF","1FM5vqdUKXawIKJ_eN2RULGy4IDlAAAK"]'
---

# Game consoles as style references

Reference notes on classic console hardware, aimed at **reproducing the look in a modern
renderer** rather than at writing 6502.

**Scope note:** 8-bit home computers live here too when they're a useful style target —
the ZX Spectrum is in the index below, and a C64 or Apple II would belong here as well.
The shelf is organised by _the machine you're imitating_, not by whether it had a
cartridge slot.

The premise: a console's aesthetic is not a filter, it's a **stack of constraints**, and
the look comes from which ones you honour. Slapping a palette on a modern render gets you
about 20% of the way there. The other 80% is the geometry of the limits — the block size
of the playfield, the color budget per scanline, the flicker from multiplexing more
objects than the hardware could show at once.

## The constraint stack

Work down this list for any console. Each layer is a separate decision about honour vs.
fake, and you should make it deliberately:

1. **Raster** — native pixel grid, and the **pixel aspect ratio**. This is the one people
   skip and it's the most visible. Almost no console had square pixels. Rendering an
   Atari 2600 look at 160×192 square is wrong by a factor of 1.6 horizontally.
2. **Palette** — the master set of colors the hardware could produce at all.
3. **Simultaneity limits** — how many of those colors could be onscreen _at once_, and at
   what spatial granularity (per scanline, per 8×8 tile, per 16×16 attribute block).
   This is usually where the signature look lives.
4. **Object limits** — sprite counts, per-scanline sprite limits, size/scale/flip
   capabilities, and what happens when you exceed them (drop-out, flicker).
5. **Motion & timing** — framerate, scroll granularity, 30 Hz flicker from object
   multiplexing, the shear/tear artifacts of mid-frame register changes.
6. **Output chain** — composite artifacts, NTSC color bleed, phosphor, scanline gaps,
   overscan. Optional, and easy to overdo. A period-accurate render with a modern clean
   signal often reads better than one buried in CRT sim.

Honouring 1–4 makes it _read_ as the machine. Layer 6 is seasoning.

**Sound is a second, independent stack**, and each file has a section on it. The same
discipline applies: the character lives in the _limit_, not the waveform. Work down
**pitch quantization** (what notes the divider can actually produce — the 2600 can't play
in tune and the arithmetic proving it is in its file), **timbre count** (how many distinct
voices exist — usually three or fewer), **channel count and what competes for them**,
**envelope resolution** (almost always the CPU writing volume at frame rate, so dynamics
are stepped at 50/60 Hz), and **mixing** (the NES sums its channels non-linearly; ignore
that and the mix is wrong in a way you can hear but not name). Every one of these is a
line or two of code, and skipping them is what makes a reproduction sound like a generic
chiptune instead of like the machine.

## Index

- **references/atari-2600.md** — the TIA and the beam. 160×192 with **1.6:1 wide pixels**,
  128 NTSC colors but only **4 per scanline**, a 40-block playfield made of 4-color-clock
  chunks that mirrors at screen centre, 2 players + 2 missiles + 1 ball and nothing else,
  no framebuffer, no text mode. Includes the verified 128-entry NTSC palette, the PAL/SECAM
  differences, the visual tells (horizontal symmetry, per-scanline color bars, sprite
  flicker, the HMOVE comb), and shader/CPU recipes for each.
- **references/nes.md** — the 2C02 PPU. 256×240 at **8:7**, a fixed 64-entry palette
  (54 distinct) with **25 onscreen**, and the constraint that defines the machine: tiles
  are 8×8 but **color is assigned per 16×16 attribute block**, which is where attribute
  clash comes from. Includes the palette as a table and an array, the nametable/attribute/
  OAM structure, the 256-tile pattern budget that forces background repetition, sprite
  limits and sprite-0-hit raster splits, the grayscale and color-emphasis bits, the five
  APU channels and why the triangle's missing volume envelope matters, plus honour-vs-fake
  guidance and native reproduction notes.
- **references/zx-spectrum.md** — the ULA. Not a console (a 1982 British home computer),
  included because its constraint is the most legible of the three and the easiest to
  shade: the screen is **two layers at two resolutions**, a 1-bit 256×192 bitmap plus a
  32×24 attribute layer holding **2 colours per 8×8 cell that must share a brightness
  bit**. Chroma subsampling with a 1-bit luma, essentially. **Square pixels** — the one
  machine here needing no aspect correction. Includes the verified 15-colour palette, the
  attribute byte layout, the non-linear screen address formula, colour clash and the
  monochrome-first art direction that grew up around it, the 1-bit beeper, and a full
  cell-search + Bayer-dither reproduction recipe.

**The three are instructively different, and none of them is "low resolution plus a
palette."** The 2600 varies colour freely _down_ the screen and almost not at all _across_
it, with no tiles and no framebuffer. The NES has a tile grid and varies colour in both
axes, but at half the resolution of its own detail. The Spectrum goes furthest: detail and
colour are **separate layers**, one 1-bit and one at 1/8 resolution, which is why its
clash is the most severe and its art the most deliberately monochrome.

A useful ladder for colour granularity: **2600 = per scanline → NES = per 16×16 block →
Spectrum = per 8×8 cell, but only two colours.**

## Related

- **Three.js implementation of the NES look**:
  `skills/threejs/references/nes-palette-and-sprite-limits.md` — the toon-ramp pre-pass,
  the 16×15 attribute pass with palette-choice hysteresis, resolve/composite, and the
  sRGB-vs-linear matching trap. Written against r180 with a full-screen post pass
  available. That file is the _how_; `references/nes.md` here is the _what_, and the
  palette array lives here only — don't duplicate it.
- `threejs/references/dithering-and-halftone.md` for 1-bit and ordered-dither reduction,
  which is the right tool when a target palette is small.
- The `beaglebros` skill for the adjacent 8-bit _home computer_ sensibility (Apple II),
  which is a voice and a design attitude rather than a hardware spec.
