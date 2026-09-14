---
semantic_id: "1FM5vqdUKXawIKJ_eN2RULGy4IDlAAAK"
related_ids:
  - "3MQ9nqZUKHby4KO-foWQVQuy4eqlQAAO"
  - "TPIICudaaHayNJK6PcGyUVfwpYgpQAAG"
---

# Nintendo Entertainment System / Famicom (2C02 PPU) — hardware truth and how to fake it

**NES 1985 (Famicom 1983). Ricoh 2A03 CPU + Ricoh 2C02 PPU.**

Where the Atari 2600 had no framebuffer at all, the NES has one made of **tiles**: a grid
of 8×8 patterns, composited against 64 sprites, with color assigned at a coarser grid than
the tiles themselves. That last mismatch — **color resolution is half the tile
resolution** — is the console's signature, and it's the thing most "NES-style" work
forgets.

If you take one design rule into a modern renderer: **the NES draws detail at 8×8 and
color at 16×16, and the disagreement between those two grids is the whole look.**

## The numbers

|                         | NTSC (2C02)                                                                          | PAL (2C07)                                |
| ----------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------- |
| CPU                     | Ricoh **2A03** @ 1.789773 MHz (6502 core, **no decimal mode**, integrated APU + DMA) | 2A07 @ 1.662607 MHz                       |
| PPU clock               | 5.369318 MHz = **3× CPU**                                                            | 5.320342 MHz = **3.2× CPU**               |
| CPU RAM                 | **2 KB** work RAM                                                                    | same                                      |
| PPU memory              | 2 KB VRAM (nametables) + 256 B OAM + **32 B palette RAM**                            | same                                      |
| framebuffer             | 256×240, top/bottom ~8 rows overscanned → **256×224 visible**                        | 256×240, less cropping in practice        |
| pixel aspect            | **8:7** (256×224 displays as ≈292×224 ≈ 4:3)                                         | ≈ 1.386:1 (wider still)                   |
| scanlines per frame     | 262 = **240 visible** + 1 post-render + 20 VBlank + 1 pre-render                     | 312 = 240 visible + 1 + **70 VBlank** + 1 |
| PPU cycles per scanline | 341                                                                                  | 341                                       |
| frame rate              | **60.0988 Hz**                                                                       | 50.007 Hz                                 |
| master palette          | 64 indices `$00`–`$3F`, **54 visually distinct**                                     | same indices, different NTSC/PAL decode   |
| max colors onscreen     | **25** (12 bg + 12 sprite + 1 shared backdrop)                                       | same                                      |

The PAL VBlank is **70 scanlines vs NTSC's 20** — three and a half times as much time to
push VRAM updates. This is why sloppy PAL conversions ran music and gameplay slow (code
written to a 60 Hz frame budget) while well-done ones could afford more per-frame graphics
work. Not a visual tell, but it explains why some PAL versions look and feel different.

## The color system

This is the part worth internalizing; everything else is detail.

|                     | count                                                     |
| ------------------- | --------------------------------------------------------- |
| master palette      | 64 entries, hardware-fixed, **you cannot define a color** |
| background palettes | 4 × 3 colors + **1 shared backdrop** = 13                 |
| sprite palettes     | 4 × 3 colors + transparency = 12                          |
| **onscreen total**  | **25**                                                    |

Palette RAM is 32 bytes at `$3F00`–`$3F1F`. Entry 0 of every palette mirrors the backdrop
at `$3F00`, which is why the backdrop is shared and free everywhere — and why so many NES
screens have big fields of one flat color.

**You pick indices, not colors.** There is no RGB anywhere in the machine. The 2C02
generates an NTSC composite signal directly, so every RGB table you'll find is a _decode_,
and they disagree: FCEUX's default, Nestopia's YUV, Bisqwit's NTSC generator, the NESdev
`.pal` files. **Pick one and stay on it** — mixing tables produces colors that don't sit
together.

### The master palette (FCEUX default decode)

Rows are brightness, columns are hue. Column `$x0` is grey, `$x1`–`$xC` are hues,
`$xD`–`$xF` are the blacks and greys below.

|       | `$x0`     | `$x1`     | `$x2`     | `$x3`     | `$x4`     | `$x5`     | `$x6`     | `$x7`     | `$x8`     | `$x9`     | `$xA`     | `$xB`     | `$xC`     | `$xD`     | `$xE`     | `$xF`     |
| ----- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- |
| `$0x` | `#757575` | `#24188e` | `#0000aa` | `#45009e` | `#8e0075` | `#aa0010` | `#a60000` | `#7d0800` | `#412c00` | `#004500` | `#005100` | `#003c14` | `#183c5d` | `#000000` | `#000000` | `#000000` |
| `$1x` | `#bebebe` | `#0071ef` | `#2038ef` | `#8200f3` | `#be00be` | `#e70059` | `#db2800` | `#cb4d0c` | `#8a7100` | `#009600` | `#00aa00` | `#009238` | `#00828a` | `#000000` | `#000000` | `#000000` |
| `$2x` | `#ffffff` | `#3cbeff` | `#5d96ff` | `#cf8aff` | `#f779ff` | `#ff75b6` | `#ff7561` | `#ff9a38` | `#f3be3c` | `#82d310` | `#4ddf49` | `#59fb9a` | `#00ebdb` | `#797979` | `#000000` | `#000000` |
| `$3x` | `#ffffff` | `#aae7ff` | `#c7d7ff` | `#d7cbff` | `#ffc7ff` | `#ffc7db` | `#ffbeb2` | `#ffdbaa` | `#ffe7a2` | `#e3ffa2` | `#aaf3be` | `#b2ffcf` | `#9efff3` | `#c7c7c7` | `#000000` | `#000000` |

```js
// FCEUX default 2C02 palette, index $00-$3F, sRGB. Row-major: index = row * 16 + col.
export const NES_PALETTE = [
  0x757575, 0x24188e, 0x0000aa, 0x45009e, 0x8e0075, 0xaa0010, 0xa60000,
  0x7d0800, 0x412c00, 0x004500, 0x005100, 0x003c14, 0x183c5d, 0x000000,
  0x000000, 0x000000, 0xbebebe, 0x0071ef, 0x2038ef, 0x8200f3, 0xbe00be,
  0xe70059, 0xdb2800, 0xcb4d0c, 0x8a7100, 0x009600, 0x00aa00, 0x009238,
  0x00828a, 0x000000, 0x000000, 0x000000, 0xffffff, 0x3cbeff, 0x5d96ff,
  0xcf8aff, 0xf779ff, 0xff75b6, 0xff7561, 0xff9a38, 0xf3be3c, 0x82d310,
  0x4ddf49, 0x59fb9a, 0x00ebdb, 0x797979, 0x000000, 0x000000, 0xffffff,
  0xaae7ff, 0xc7d7ff, 0xd7cbff, 0xffc7ff, 0xffc7db, 0xffbeb2, 0xffdbaa,
  0xffe7a2, 0xe3ffa2, 0xaaf3be, 0xb2ffcf, 0x9efff3, 0xc7c7c7, 0x000000,
  0x000000,
];
```

**Why 54 and not 64.** `$xE` and `$xF` are black in every row (8 entries), `$0D` and `$1D`
are also black (2 more) — 10 black entries collapsing to one. `$20` and `$30` are both
pure white. 64 − 9 − 1 = **54 distinct**.

`$0D` is a special hazard: it's a "blacker than black" signal below the NTSC blanking
level. Emulators clamp it to `#000000`, but on real hardware and on some capture gear it
makes the picture roll or the sync wobble. Period art guides told you never to use it.
`$0F` is the black you want.

### The two authentic global effects

The PPU had exactly two screen-wide effects, both single bits in PPUMASK (`$2001`), and
both are correct to use because they're inside the hardware's vocabulary:

- **Grayscale** (bit 0) ANDs the palette index with `$30`, collapsing every color to its
  brightness row's grey. Games used it for damage flashes and freeze frames.
- **Color emphasis** (bits 5–7) attenuates the two channels you did _not_ emphasize by
  roughly 25%, giving eight whole-screen tints. This is why FCEUX ships 512 palette
  entries rather than 64 — 8 emphasis combinations × 64. The right way to do a lightning
  flash, a night filter, or an underwater tint. **On PAL the red and green bits are
  swapped**, so an emphasis effect tinted wrong on the other standard.

A bloom pass, a color grade, or an alpha fade is none of these. Fade-outs on real hardware
were done by _swapping palette entries_ down a hand-authored ramp, frame by frame.

## The tile system, and where the look comes from

| structure           | size                                 | what it means                                                                                  |
| ------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| **pattern table**   | 2 × 4 KB, **256 tiles each**         | 8×8 tiles, **2 bits per pixel** (4 values: 3 colors + transparent/backdrop), 16 bytes per tile |
| **nametable**       | 32 × 30 tile indices = 960 bytes     | one screen of background, exactly 256×240                                                      |
| **attribute table** | 64 bytes per nametable               | **this is the important one**                                                                  |
| **OAM**             | 256 bytes = **64 sprites** × 4 bytes | Y, tile, attributes, X                                                                         |

**The attribute table is the whole ballgame.** Each of its 64 bytes covers a **32×32 pixel**
area and is split into four 2-bit fields, one per **16×16 quadrant**. Those 2 bits choose
which of the 4 background palettes that 16×16 block uses.

So: **tiles are 8×8, but color is assigned per 16×16.** Four tiles at a time must share a
3-color palette. When a foreground object's colors and a background's colors want
different palettes inside the same block, one of them loses — and that's **attribute
clash**, the single most identifiable NES artifact. Look at any NES screenshot and you'll
find blocky color seams that don't follow the artwork's outlines. Sprites are exempt
(a sprite carries its own palette), which is why NES art puts anything needing precise
color into a sprite.

Two nametables exist in the 2 KB of VRAM; the other two addresses **mirror** them,
horizontally or vertically depending on cartridge wiring (or four-screen with extra RAM on
the cart). Mirroring choice determines whether a game scrolls cleanly side-to-side or
up-and-down — which is why so many NES games are strictly one or the other.

### Sprites

- **64 total**, 8×8 or 8×16. In 8×16 mode the sprite pattern budget halves to 128 patterns.
- **Flip X and Y only.** No rotation, no scaling, ever.
- **8 per scanline.** The ninth and beyond are simply dropped. Games rotated the OAM start
  index every frame so the dropouts _moved_ between actors instead of consistently hiding
  the same one — that's why enemies strobe in _Contra_ and _Gradius_.
- **Sprite 0 hit**: a status flag set when a non-transparent pixel of sprite 0 overlaps a
  non-transparent background pixel. It has nothing to do with gameplay collision — it's a
  **raster timing signal**, used to detect "the beam has reached row N" so the game could
  change the scroll register mid-frame. That's how _Super Mario Bros._ keeps a fixed status
  bar above a scrolling world. Later mappers (MMC3) provided a proper scanline IRQ instead.

### The pattern budget shapes the art

256 tiles per table, typically one table for background and one for sprites. A full screen
is 960 tile slots drawing from 256 unique patterns, so **background art repeats by
construction** — brick runs, cloud motifs, repeated window rows, the same bush and the same
cloud (famously the same tiles, recolored, in _SMB_). Symmetry and mirroring stretch the
budget further. If your "NES-style" background has 900 unique 8×8 cells, it doesn't read as
NES no matter what palette it uses.

### Dithering was hand-drawn

The PPU had no dithering hardware. Every checkerboard you remember was **drawn by an
artist**, in 8×8 tiles, alternating two colors _of the same palette_. There was also no
alpha: "transparency" was either flicker (draw every other frame) or a 2×2 checker.

Consequence for reproduction: don't run error diffusion or blue noise before quantizing.
Those produce aperiodic, content-following clusters — right for a 1-bit Macintosh, wrong
here. Use a **2×2 checker locked to the 256×240 grid**, between two entries of the block's
own palette. Anything finer than the pixel grid, or crossing a palette boundary, is an
anachronism.

## Audio (2A03 APU)

Five channels, and their _inequality_ is the character:

| channel          | control                                                                           | notes                                                      |
| ---------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| pulse 1, pulse 2 | 4 duty cycles (12.5 / 25 / 50 / 75%), 4-bit volume, sweep unit                    | the melody and harmony                                     |
| triangle         | **no volume control** — it's on or off, fixed 4-bit stepped wave                  | the bass, and it's always the same loudness                |
| noise            | 4-bit volume, two LFSR modes: 32767-step (hiss) and 93-step (**tonal, metallic**) | percussion                                                 |
| DMC              | 1-bit delta samples, 7-bit output                                                 | drums and voice clips; **steals CPU cycles** while playing |

The triangle having no volume envelope is why NES basslines don't fade — they cut. The
short-mode noise is the distinctive metallic ping nothing else makes. Emulating "NES
audio" with four equal square waves misses both.

### The limits, precisely

**Pitch** is an 11-bit period register, `t` = 0–2047, and the two channel families divide
differently:

```text
pulse:     f = 1789773 / (16 × (t + 1))     t < 8 mutes the channel entirely
triangle:  f = 1789773 / (32 × (t + 1))     one octave lower for the same t
```

So the pulse channels reach from **54.6 Hz up to ~12.4 kHz**, and the triangle an octave
below that. Unlike the 2600, the divider is 11 bits rather than 5, so the tuning error is
small through the musical range — but it is **not zero, and it grows with pitch**: near the
top of the register consecutive `t` values are a semitone or more apart. High lead lines
drift sharp; the same note played two octaves up is measurably not the same note.

**Timbre is nearly fixed.** Four duty cycles, of which **25% and 75% are the same waveform
phase-inverted** and therefore sound identical — so there are **three** pulse timbres, ever.
The triangle's shape can't be changed at all. There is no filter, no ring modulation, no
oscillator sync (all of which the C64's SID had, which is why the two machines are never
mistaken for each other).

**Envelopes** are 4-bit volume with a decay unit, per pulse and noise channel. The
triangle has _no volume control whatsoever_ — it's gated on or off by its length and linear
counters, and because those counters can't cut it instantly, killing the triangle mid-note
produces the characteristic **click/pop** at the end of NES basslines.

**Noise has 16 preset periods.** Not a frequency register — a lookup table. You cannot tune
a snare; you pick one of sixteen. The short mode (93-step LFSR) is the metallic one.

**The DMC has 16 preset sample rates**, maxing at ~33.1 kHz, playing 1-bit deltas into a
7-bit accumulator. It is not a sampler: you cannot set an arbitrary rate or pitch, and each
sample byte **steals CPU cycles via DMA**. That theft is famous for corrupting controller
reads mid-DMA, which is why NES games read the gamepad twice and compare.

**The mixing is non-linear**, and this is the tell people most often miss. Each channel has
its own DAC and they interact:

```text
pulse_out = 95.88 / ((8128 / (pulse1 + pulse2)) + 100)
tnd_out   = 159.79 / ((1 / (triangle/8227 + noise/12241 + dmc/22638)) + 100)
output    = pulse_out + tnd_out
```

Two pulses at full volume are **quieter than twice one pulse**, and a loud DMC sample
audibly ducks the triangle and noise sharing its group. Sum the channels linearly in a
reproduction and the mix will be subtly, consistently wrong — too loud and too flat. The
common linear approximation, if you need one, is
`0.00752×(p1+p2) + 0.00851×tri + 0.00494×noise + 0.00335×dmc`.

**No expansion audio — on the NES.** The Famicom's cartridge connector carried an audio
return pin, so Japanese carts could add chips: VRC6 (2 extra pulses + sawtooth), VRC7 (FM),
N163 (wavetable), FDS, MMC5, Sunsoft 5B. **The western NES does not connect that pin**, so
no US cartridge can do it. If a "NES soundtrack" has FM or sawtooth in it, it's a Famicom
soundtrack — worth being specific about which machine you mean.

### Reproducing it

1. Quantize pitch through the 11-bit period register, not to equal temperament — round `t`,
   then resynthesize the frequency from `t`. The drift at the top of the range is free
   authenticity.
2. Three pulse timbres only. Hard-edged, not band-limited.
3. Triangle at a fixed level, 16 quantization steps, and let it click when it stops.
4. Noise from a real 15-bit LFSR with both tap modes, at one of the 16 table periods.
5. **Mix with the non-linear formula.** One line, and it fixes a mix that would otherwise
   sound like a generic chiptune.

## Visual tells — what actually makes it read as NES

Ranked by how much each does for you:

1. **Attribute clash.** 16×16 color blocks that don't follow the artwork's edges. A render
   that quantizes to the NES palette per-pixel and stops there reads as generic retro, not
   as NES. This is the one everybody skips and it does the most work.
2. **Tile repetition** at 8×8, from a small pattern set. Backgrounds are _patterned_, not
   painted.
3. **Hard edges, zero blending.** The PPU composites opaque pixels. No alpha, no glow, no
   fog, no soft shadow — anywhere.
4. **A big flat backdrop color**, usually black or one saturated field, because it's free
   and shared.
5. **Sprite flicker** from the 8-per-scanline drop, rotating across actors.
6. **A hard horizontal split** where the status bar meets the playfield (sprite 0 hit /
   scanline IRQ), often with a color discontinuity across it.
7. **8:7 wide pixels** and the overscan crop to 224 rows.
8. **Three colors plus backdrop per region** — art that works in tight hue families, with
   shading done by picking a lighter entry in the same family, not by blending.

## Reproducing it

The NES-in-Three.js pipeline — toon-ramped render, a 16×15 attribute pass that scores all
four palettes per block, hysteresis to stop the blocks strobing, the resolve/composite
pass, and the sRGB-vs-linear matching trap — lives in
**`skills/threejs/references/nes-palette-and-sprite-limits.md`**. That file is the
implementation; this one is the hardware it's implementing. Don't duplicate the palette
array between them.

The general structure, renderer-agnostic:

1. Render at exactly **256×240**, nearest everything, no MSAA (it invents off-palette
   colors), no tone mapping (a tone curve moves every color off-palette).
2. **Flatten the lighting to a 3–4 step toon ramp before quantizing.** Highest-leverage
   step in the whole chain. A palette has three colors; hand the quantizer a continuous
   gradient and it picks a different entry every few pixels, giving noise where the NES had
   flat shape.
3. Choose the four background palettes **by hand**. That's what NES artists did and it's
   the only temporally stable answer — computing them per frame makes the whole screen
   shift hue when one bright object walks on.
4. Per 16×16 block, pick the best-fitting palette and snap; sprites/actors carry their own
   palette and quantize themselves.
5. **Integer upscale only** (3×, 4×), nearest — a fractional scale gives some source pixels
   more screen pixels than others and the grid visibly beats. **Then** apply 8:7
   horizontally, at the presentation layer, not by resampling the render target.

Per-platform, the recurring gotcha is that interpolation is on by default everywhere:

| target        | small buffer           | nearest                                                   | present                                    |
| ------------- | ---------------------- | --------------------------------------------------------- | ------------------------------------------ |
| Metal         | 256×240 `MTLTexture`   | `MTLSamplerDescriptor` `.magFilter/.minFilter = .nearest` | integer-scaled blit, then 8:7 stretch      |
| SwiftUI       | `CGImage` at 256×240   | `.interpolation(.none)`                                   | `.aspectRatio(4.0/3.0, contentMode: .fit)` |
| Core Graphics | 256×240 `CGContext`    | `ctx.interpolationQuality = .none`                        | draw into a 4:3 rect                       |
| Canvas 2D     | 256×240 backing canvas | `ctx.imageSmoothingEnabled = false`                       | CSS `image-rendering: pixelated`           |
| SDL / general | 256×240 render target  | nearest scale mode                                        | logical size 292×224                       |

In the browser, `image-rendering: pixelated` is needed **in addition to**
`imageSmoothingEnabled = false` — the canvas flag governs draws into the canvas, the CSS
property governs the browser's upscale of the element.

## What to honour and what to fake

| constraint                                      | recommendation                                                                                                                                                                                                                                                                                                  |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 256×240 raster, 224-row crop                    | **honour**                                                                                                                                                                                                                                                                                                      |
| 8:7 pixel aspect                                | **honour**, always                                                                                                                                                                                                                                                                                              |
| 64-color master palette, 25 onscreen            | **honour** — and it's assertable, see below                                                                                                                                                                                                                                                                     |
| **16×16 attribute granularity**                 | **honour** — the highest-value single constraint                                                                                                                                                                                                                                                                |
| one palette per sprite/actor                    | **honour** — the meaningful half of the sprite rule                                                                                                                                                                                                                                                             |
| no alpha, no blending, no fog                   | **honour** — cheap, and violations are instantly visible                                                                                                                                                                                                                                                        |
| hand-authored 2×2 dither only                   | honour                                                                                                                                                                                                                                                                                                          |
| 256-tile pattern budget                         | **fake / ignore** in a 3D render — there are no tiles to count, and claiming a "tile limit" for a mesh scene is theatre. In 2D work, honour it; it's what makes backgrounds read right.                                                                                                                         |
| 8×8 sprite granularity, no rotation             | fake — a 3D actor isn't a sprite sheet                                                                                                                                                                                                                                                                          |
| 8 sprites per scanline                          | **optional, usually a mistake.** Real hardware drops _per scanline_, so a tall sprite is half-drawn; hiding a whole object is a visibly different artifact, and modern viewers read it as a bug. Make it a toggle, default off, and label it in code as an emulation of a hardware defect so nobody "fixes" it. |
| triangle-channel bass with no volume envelope   | **honour** — fixed level, 16 steps, and let it click when it cuts                                                                                                                                                                                                                                               |
| **non-linear channel mixing**                   | **honour** — one formula, and without it the mix reads as generic chiptune rather than NES                                                                                                                                                                                                                      |
| three pulse timbres (25% and 75% are identical) | honour — it's a smaller palette than people assume                                                                                                                                                                                                                                                              |
| 16 preset noise periods, 16 preset DMC rates    | honour — you pick from a table, you don't tune                                                                                                                                                                                                                                                                  |
| 11-bit pitch divider drift at high registers    | honour — round the period register, resynthesize from it                                                                                                                                                                                                                                                        |
| expansion audio (VRC6/VRC7/N163/FDS)            | **fake only if you mean Famicom** — the western NES cannot do it at all                                                                                                                                                                                                                                         |

### The claim is assertable

A 3D scene quantized to the NES palette **is not an NES game** and can't be — the console
couldn't draw a rotating mesh at all. What's reproduced is the console's _color system_,
faithfully, over geometry it never had. Worth saying so in the code, because attribute
clash makes people assume more authenticity than is being claimed.

If you want a real check on the claim, write the test: sample the framebuffer, and verify
that at most **25 distinct RGB values** appear and that every one of them is in
`NES_PALETTE`. That either passes or it doesn't.

## Sources

- Noel Berry, ["Making art for the NES"](https://noelberry.ca/posts/nes/index.html) — the
  artist's-eye version of the attribute and palette constraints.
- The [NESdev wiki](https://www.nesdev.org/wiki/) — `PPU_palettes`,
  `PPU_attribute_tables`, `PPU_nametables`, `PPU_sprite_evaluation`, `PPU_frame_timing`,
  `APU`. The authoritative source for every number above.
- FCEUX palette tables (`src/palettes/palettes.h`) for the RGB decode used here.
- [Wikipedia, List of video game console palettes](https://en.wikipedia.org/wiki/List_of_video_game_console_palettes)
  for the cross-console palette structure comparison.
