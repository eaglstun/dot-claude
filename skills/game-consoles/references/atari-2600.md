---
semantic_id: "3MQ9nqZUKHby4KO-foWQVQuy4eqlQAAO"
related_ids:
  - "1FM5vqdUKXawIKJ_eN2RULGy4IDlAAAK"
  - "TPIICudaaHayNJK6PcGyUVfwpYgpQAAG"
---

# Atari 2600 (TIA) — hardware truth and how to fake it

**Atari VCS / 2600, 1977. The Television Interface Adaptor (TIA) has no framebuffer.**

That is the single fact everything else falls out of. There is no screen memory to draw
into. The TIA holds roughly one scanline's worth of state — a background color, a 20-bit
playfield, two 8-bit players, two missiles, a ball — and the CPU rewrites those registers
in the ~22 CPU cycles of horizontal blank between lines. The program _is_ the raster. This
is "racing the beam," and it's why 2600 games look like nothing else: the picture is
horizontal strips, and the only thing that changes cheaply between strips is color.

If you take one design rule from this file into a modern renderer: **the 2600 varies
freely down the screen and barely at all across it.**

## The numbers

|                           | NTSC                                                                 | PAL                                                       |
| ------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------- |
| CPU                       | MOS **6507** @ 1.19 MHz (3.579545 / 3)                               | 1.18 MHz (3.546894 / 3)                                   |
| RAM                       | **128 bytes** total (in the 6532 RIOT; the stack lives here too)     | same                                                      |
| ROM                       | 4 KB address window; bigger carts bankswitch (F8=8K, F6=16K, F4=32K) | same                                                      |
| color clocks per scanline | 228 (68 HBLANK + **160 visible**)                                    | same                                                      |
| CPU cycles per scanline   | **76** (228 / 3)                                                     | same                                                      |
| scanlines per frame       | 262 = 3 VSYNC + 37 VBLANK + **192 visible** + 30 overscan            | 312 = 3 + 45 + **228 visible** + 36                       |
| frame rate                | ~60 Hz                                                               | ~50 Hz                                                    |
| master palette            | **128** (16 hues × 8 luminances)                                     | 104 usable (16 hues × 8, but 4 hue rows collapse to grey) |
| colors per scanline       | **4**                                                                | 4                                                         |

SECAM units are a different animal entirely: the palette collapses to **8 colors** (3-bit
RGB — black, blue, red, magenta, green, cyan, yellow, white), with luminance driving the
index. SECAM 2600 screenshots look garish and wrong to American eyes for this reason.

### Pixel aspect ratio — read this before rendering anything

160 visible color clocks across, 192 visible lines down, displayed on a 4:3 screen.

```text
PAR = (4/3) / (160/192) = 1.6 : 1
```

**2600 pixels are 1.6× wider than they are tall.** Conveniently, 160 × 1.6 = 256, and
256 : 192 is exactly 4:3 — so the correct presentation of a 160×192 buffer is a
**non-integer horizontal stretch to 256×192** (or any integer multiple: 512×384,
1024×768). Rendering 160×192 as square pixels is the single most common mistake in
"Atari-style" work, and it makes everything look tall and cramped instead of wide
and chunky.

PAL: 160×228 at 4:3 → PAR ≈ 1.9:1. Even wider.

## What the TIA can actually draw

Five movable object types and a background. That's the whole vocabulary.

| object                    | width                                                      | notes                                                                          |
| ------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **playfield** (PF)        | 20 bits × **4 color clocks** = 80 clocks = half the screen | the other half is a **mirror** or a **repeat** of the same 20 bits (CTRLPF D0) |
| **player 0 / 1** (GRP0/1) | 8 bits, each 1, 2 or 4 clocks wide                         | NUSIZ also gives **2 or 3 copies** at close/medium/wide spacing                |
| **missile 0 / 1**         | 1 bit, 1/2/4/8 clocks wide                                 | color-locked to its player                                                     |
| **ball** (BL)             | 1 bit, 1/2/4/8 clocks wide                                 | color-locked to the playfield                                                  |

And four color registers, all 7-bit (D7–D1; D0 is ignored):

- `COLUBK` — background
- `COLUPF` — playfield **and ball**
- `COLUP0` — player 0 **and missile 0**
- `COLUP1` — player 1 **and missile 1**

**That's the 4-colors-per-scanline limit**, and it is not a soft limit — those are
literally the only four registers feeding the video output on a given line. There is no
attribute table, no per-tile palette, no way to buy a fifth color without changing a
register mid-line (which some games do, and it costs precise cycle counting).

Two escape hatches worth knowing because they show up in real games:

- **Score mode** (`CTRLPF` D1): the left half of the playfield takes `COLUP0` and the
  right half takes `COLUP1`. Built for two-player score displays at the top of the screen —
  which is why so many 2600 games have exactly that: two differently-colored numbers,
  symmetric, at the top.
- **Priority** (`CTRLPF` D2): playfield and ball draw _in front of_ the players instead of
  behind. Normal order is P0/M0 → P1/M1 → PF/BL → BK.

### Positioning is asymmetric, and it shapes the art

**Vertical** position costs nothing structural — you just write the sprite bitmap at the
right scanline. So vertical motion is smooth and per-pixel.

**Horizontal** position is a nightmare: you strobe `RESP0` at the moment the beam is where
you want the sprite, which quantizes to a 3-clock CPU cycle, then fine-tune by −8..+7
clocks with `HMP0` + `HMOVE`. `HMOVE` works by extending horizontal blank on that
scanline, which paints the leftmost **8 pixels black** — the famous **"HMOVE comb"** of
dark notches down the left edge of the screen. Later games hid them; earlier ones didn't.

There is also **no text mode and no character generator.** Title screens use the
"48-pixel sprite" trick: both players set to three close copies, with the bitmap registers
rewritten mid-scanline on a strict cycle budget, producing one 48-clock-wide graphic. This
is why 2600 title lettering is wide, blocky, centred, and usually only one or two words.

### Hardware collision detection

15 collision bits, all pairs of (P0, P1, M0, M1, BL, PF), latched until you strobe `CXCLR`.
Free, exact, and one reason 2600 gameplay feels crisp despite everything else. If you're
modelling gameplay in this style, collision is object-vs-object boolean, not physics.

## Sound — the limits that define it

**Two channels, and only 32 pitches each. The 2600 cannot play in tune, and that is not a
matter of taste or of bad composers — it is arithmetic.**

Three registers per channel, and that's the entire synthesizer:

| register          | bits  | what it does                                                 |
| ----------------- | ----- | ------------------------------------------------------------ |
| `AUDC0` / `AUDC1` | 4     | waveform / distortion select, 16 modes (table below)         |
| `AUDF0` / `AUDF1` | **5** | frequency divider, **0–31**. This is the only pitch control. |
| `AUDV0` / `AUDV1` | 4     | volume 0–15. No envelope hardware of any kind.               |

Base audio clock: **31399.5 Hz** NTSC (31113.1 Hz PAL), = CPU clock / 38.

### The AUDC modes

| `AUDC` | waveform                |     | `AUDC` | waveform                       |
| ------ | ----------------------- | --- | ------ | ------------------------------ |
| `$0`   | set to 1 (silence)      |     | `$8`   | **9-bit poly — white noise**   |
| `$1`   | 4-bit poly              |     | `$9`   | 5-bit poly                     |
| `$2`   | div 15 → 4-bit poly     |     | `$A`   | **div 31 : pure tone**         |
| `$3`   | 5-bit poly → 4-bit poly |     | `$B`   | set last 4 bits to 1 (silence) |
| `$4`   | **div 2 : pure tone**   |     | `$C`   | **div 6 : pure tone**          |
| `$5`   | **div 2 : pure tone**   |     | `$D`   | **div 6 : pure tone**          |
| `$6`   | **div 31 : pure tone**  |     | `$E`   | div 93 : pure tone             |
| `$7`   | 5-bit poly → div 2      |     | `$F`   | 5-bit poly div 6               |

Sixteen modes, but several are duplicates (`$4`/`$5`, `$6`/`$A`, `$C`/`$D`) and two are
silence — so there are really **about nine usable timbres**, of which three are tones,
five are polynomial noise of various coarseness, and one is a hybrid.

### Why it's out of tune

Pitch is a single integer division of a fixed clock:

```text
f = 31399.5 / (divisor × (AUDF + 1))
```

where `divisor` comes from the AUDC mode. That's a **harmonic series**, not a scale. The
consequences, computed from the formula rather than asserted:

- **Octaves are exact** (any AUDF _n_ and 2*n*+1 pair), because doubling a divisor halves a
  frequency. So the machine is perfectly in tune with itself at the octave and nowhere else.
- **Resolution is backwards from what music needs.** With `AUDC $C` (div 6), stepping AUDF
  from 0 to 1 drops the pitch **a full octave** in one step. Stepping from 30 to 31 moves it
  **55 cents**. High notes are unreachably sparse; low notes are crowded with near-duplicates.
- **The usable musical octave sits at AUDF 9–19** in div-6 mode, and here is what's actually
  available in it:

| AUDF | Hz    | nearest note | error       |
| ---- | ----- | ------------ | ----------- |
| 9    | 523.3 | C5           | **+0.2 ¢**  |
| 10   | 475.8 | A♯4          | +35.2 ¢     |
| 11   | 436.1 | A4           | −15.4 ¢     |
| 12   | 402.6 | G4           | **+46.0 ¢** |
| 13   | 373.8 | F♯4          | +17.7 ¢     |
| 14   | 348.9 | F4           | −1.7 ¢      |
| 15   | 327.1 | E4           | −13.4 ¢     |
| 16   | 307.8 | D♯4          | −18.4 ¢     |
| 17   | 290.7 | D4           | −17.4 ¢     |
| 18   | 275.4 | C♯4          | −11.0 ¢     |
| 19   | 261.7 | C4           | **+0.2 ¢**  |

C and F are effectively perfect. **G is 46 cents sharp — very nearly a quarter tone**, so
far off it sits between G and A♭ and belongs to neither. A is 15 cents flat. That single
row is why 2600 music sounds drunk: the tonic and subdominant are solid and the dominant
is a train wreck, in every key at once.

Both channels divide the _same_ clock with the _same_ divider set, so you cannot detune one
to fix the other, and two-part harmony inherits both errors simultaneously.

### The other limits

- **No envelope hardware.** Every attack, decay and fade is the CPU writing `AUDV` on a
  schedule, and the CPU is already busy racing the beam. Envelopes therefore get updated at
  best once per scanline, usually once per frame — 60 Hz, stepped, audibly quantized.
- **No samples.** You can PWM `AUDV` for crude digitized audio, at the cost of essentially
  the entire CPU. A handful of games did it for a second or two of speech.
- **Two channels total**, shared with sound effects. A laser firing takes the bassline with
  it. That interruption is a period tell in itself.

### Reproducing it

Don't reach for a pitch-shifted square wave — reproduce the **divider**:

1. Pick an AUDC mode; take its divisor (2, 6, 31, 93) or its polynomial.
2. Quantize every note to `f = 31399.5 / (divisor × (AUDF + 1))`, AUDF integer 0–31.
   **Snap to the available pitch, don't correct toward the intended one.** The wrongness is
   the sound.
3. Generate the tone modes as hard square waves (no anti-aliasing, no band-limiting — the
   aliasing is period-correct), and the poly modes as the actual LFSRs: 4-bit, 5-bit and
   9-bit maximal-length shift registers, clocked at the divided rate.
4. Quantize volume to 16 levels and update it no faster than 60 Hz.

In Web Audio, a `ScriptProcessor`/`AudioWorklet` running the LFSRs directly is both easier
and more faithful than trying to assemble it from `OscillatorNode`s. Same for
`AVAudioSourceNode` on Apple platforms.

## The NTSC palette (verified)

16 hue rows (`$x0`) × 8 luminance columns (`$0x`, even values only — the low bit is
ignored). Register value = `hue << 4 | lum << 1`.

| hue               | $x0       | $x2       | $x4       | $x6       | $x8       | $xA       | $xC       | $xE       |
| ----------------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- |
| `$0` grey         | `#000000` | `#404040` | `#6c6c6c` | `#909090` | `#b0b0b0` | `#c8c8c8` | `#dcdcdc` | `#ececec` |
| `$1` gold         | `#444400` | `#646410` | `#848424` | `#a0a034` | `#b8b840` | `#d0d050` | `#e8e85c` | `#fcfc68` |
| `$2` orange       | `#702800` | `#844414` | `#985c28` | `#ac783c` | `#bc8c4c` | `#cca05c` | `#dcb468` | `#e8cc7c` |
| `$3` br. orange   | `#841800` | `#983418` | `#ac5030` | `#c06848` | `#d0805c` | `#e09470` | `#eca880` | `#fcbc94` |
| `$4` pink         | `#880000` | `#9c2020` | `#b03c3c` | `#c05858` | `#d07070` | `#e08888` | `#eca0a0` | `#fcb4b4` |
| `$5` purple       | `#78005c` | `#8c2074` | `#a03c88` | `#b0589c` | `#c070b0` | `#d084c0` | `#dc9cd0` | `#ecb0e0` |
| `$6` purple-blue  | `#480078` | `#602090` | `#783ca4` | `#8c58b8` | `#a070cc` | `#b484dc` | `#c49cec` | `#d4b0fc` |
| `$7` blue         | `#140084` | `#302098` | `#4c3cac` | `#6858c0` | `#7c70d0` | `#9488e0` | `#a8a0ec` | `#bcb4fc` |
| `$8` blue         | `#000088` | `#1c209c` | `#3840b0` | `#505cc0` | `#6874d0` | `#7c8ce0` | `#90a4ec` | `#a4b8fc` |
| `$9` lt. blue     | `#00187c` | `#1c3890` | `#3854a8` | `#5070bc` | `#6888cc` | `#7c9cdc` | `#90b4ec` | `#a4c8fc` |
| `$A` turquoise    | `#002c5c` | `#1c4c78` | `#386890` | `#5084ac` | `#689cc0` | `#7cb4d4` | `#90cce8` | `#a4e0fc` |
| `$B` green-blue   | `#00402c` | `#1c5c48` | `#387c64` | `#509c80` | `#68b494` | `#7cd0ac` | `#90e4c0` | `#a4fcd4` |
| `$C` green        | `#003c00` | `#205c20` | `#407c40` | `#5c9c5c` | `#74b474` | `#8cd08c` | `#a4e4a4` | `#b8fcb8` |
| `$D` yellow-green | `#143800` | `#345c1c` | `#507c38` | `#6c9850` | `#84b468` | `#9ccc7c` | `#b4e490` | `#c8fca4` |
| `$E` orange-green | `#2c3000` | `#4c501c` | `#687034` | `#848c4c` | `#9ca864` | `#b4c078` | `#ccd488` | `#e0ec9c` |
| `$F` lt. orange   | `#442800` | `#644818` | `#846830` | `#a08444` | `#b89c58` | `#d0b46c` | `#e8cc7c` | `#fce08c` |

**127 distinct, not 128** — `$FC` and `$2E` are both `#e8cc7c`.

The same caveat as every console palette applies: the TIA has **no RGB output**. It emits
an NTSC composite phase, so any RGB table is one decode among several. This is the Stella
default (the one Lospec, most emulators, and most pixel-art tooling agree on). Alternative
decodes shift hues noticeably. **Pick one table and stay on it** — mixing sources produces
colors that don't sit together.

```js
// Row-major, hue 0..15 × lum 0..7. index = hue * 8 + (colubk >> 1 & 7)
export const TIA_NTSC = [
  0x000000, 0x404040, 0x6c6c6c, 0x909090, 0xb0b0b0, 0xc8c8c8, 0xdcdcdc,
  0xececec, 0x444400, 0x646410, 0x848424, 0xa0a034, 0xb8b840, 0xd0d050,
  0xe8e85c, 0xfcfc68, 0x702800, 0x844414, 0x985c28, 0xac783c, 0xbc8c4c,
  0xcca05c, 0xdcb468, 0xe8cc7c, 0x841800, 0x983418, 0xac5030, 0xc06848,
  0xd0805c, 0xe09470, 0xeca880, 0xfcbc94, 0x880000, 0x9c2020, 0xb03c3c,
  0xc05858, 0xd07070, 0xe08888, 0xeca0a0, 0xfcb4b4, 0x78005c, 0x8c2074,
  0xa03c88, 0xb0589c, 0xc070b0, 0xd084c0, 0xdc9cd0, 0xecb0e0, 0x480078,
  0x602090, 0x783ca4, 0x8c58b8, 0xa070cc, 0xb484dc, 0xc49cec, 0xd4b0fc,
  0x140084, 0x302098, 0x4c3cac, 0x6858c0, 0x7c70d0, 0x9488e0, 0xa8a0ec,
  0xbcb4fc, 0x000088, 0x1c209c, 0x3840b0, 0x505cc0, 0x6874d0, 0x7c8ce0,
  0x90a4ec, 0xa4b8fc, 0x00187c, 0x1c3890, 0x3854a8, 0x5070bc, 0x6888cc,
  0x7c9cdc, 0x90b4ec, 0xa4c8fc, 0x002c5c, 0x1c4c78, 0x386890, 0x5084ac,
  0x689cc0, 0x7cb4d4, 0x90cce8, 0xa4e0fc, 0x00402c, 0x1c5c48, 0x387c64,
  0x509c80, 0x68b494, 0x7cd0ac, 0x90e4c0, 0xa4fcd4, 0x003c00, 0x205c20,
  0x407c40, 0x5c9c5c, 0x74b474, 0x8cd08c, 0xa4e4a4, 0xb8fcb8, 0x143800,
  0x345c1c, 0x507c38, 0x6c9850, 0x84b468, 0x9ccc7c, 0xb4e490, 0xc8fca4,
  0x2c3000, 0x4c501c, 0x687034, 0x848c4c, 0x9ca864, 0xb4c078, 0xccd488,
  0xe0ec9c, 0x442800, 0x644818, 0x846830, 0xa08444, 0xb89c58, 0xd0b46c,
  0xe8cc7c, 0xfce08c,
];
```

Note the **luminance ramp runs down the columns, hue across the rows** — the opposite of
most modern palette layouts. Practical consequence: picking "the same color, darker" is a
column move and it's _reliable_, while picking a different hue at matched brightness is a
row move. Real 2600 art leans hard on that: it shades by luminance within one hue, because
that's the cheap, always-available operation.

## Visual tells — what actually makes it read as a 2600

Ranked by how much each one does for you:

1. **Horizontal mirror symmetry.** The playfield's right half mirrors (or repeats) its
   left half. Mazes, walls, tunnels, cave systems on the 2600 are symmetric because the
   hardware gave that away for free and asymmetry cost a mid-line register rewrite.
   _Adventure_'s rooms, _Pitfall_'s pits, _Combat_'s arenas — all reflections.
2. **4-color-clock chunk width.** Playfield pixels are **4× wider than a sprite pixel**.
   Backgrounds are made of big blocky slabs while the little guy running around is
   comparatively fine-detailed. That size _disparity_ between background and sprite is a
   dead giveaway and almost nobody reproduces it.
3. **Per-scanline color bands.** Changing `COLUBK` between lines is nearly free, so skies,
   sunsets, and rainbow bars are everywhere. Free vertical gradients, zero horizontal
   variation. If your retro render has a lovely horizontal gradient, it isn't a 2600.
4. **Sprite flicker.** Only two players exist. Games needing four objects show two per
   frame and alternate — **30 Hz flicker**, very visible, and universally accepted at the
   time. Reproduce it and people feel the machine immediately.
5. **Only four colors on any horizontal line** — but different fours on different lines.
   Objects at the same height therefore share a palette; objects at different heights
   don't have to.
6. **Wide pixels** (§ PAR above).
7. **The HMOVE comb** — black notches on the left 8 pixels of scanlines where objects
   moved. Period-authentic for pre-~1980 titles, and a nice deliberate grubbiness.
8. **Massive overscan crop.** Real sets cut a lot; games kept action well inside. Wide
   margins are correct, not lazy.

## Reproducing it in Three.js / WebGL

**Pass 1 — render tiny.** `WebGLRenderTarget(160, 192)` with `NearestFilter` on both
min and mag, `generateMipmaps: false`. Never render big and downsample; you want real
160-wide rasterization, not a blur.

**Pass 2 — quantize.** Full-screen quad, and here's the part that needs a design decision:
**per-scanline 4-color selection is not a per-fragment operation.** A fragment can't see
its whole row. Two workable structures:

- _Authored palettes (accurate, cheap)._ You choose the 4 colors for each scanline band up
  front, as art direction, and upload them as a **4×192 palette texture**. The fragment
  shader reads `texelFetch(palTex, ivec2(i, gl_FragCoord.y), 0)` for i in 0..3 and snaps
  to the nearest of those four. This is what a real game did — the palette was a decision,
  not a search. Recommended default.
- _Derived palettes (automatic, costlier)._ A compute/CPU pass reduces each row of the
  160×192 buffer to 4 colors (median cut or k-means on ~160 samples × 192 rows — small
  enough to do on the CPU per frame if you must), writes the same 4×192 texture, and the
  shader is identical. Use when the content is dynamic and unart-directed. Add temporal
  hysteresis or the palette will crawl between frames.

Snap each chosen color to the nearest `TIA_NTSC` entry once, offline, not per fragment.

```glsl
// nearest-of-four, per scanline. palTex is 4 x 192, NearestFilter.
vec3 snap4(vec3 c, int y) {
  vec3 best = vec3(0.0); float bestD = 1e9;
  for (int i = 0; i < 4; i++) {
    vec3 p = texelFetch(palTex, ivec2(i, y), 0).rgb;
    vec3 d = c - p;              // compare in linear or Oklab, NOT sRGB —
    float dd = dot(d, d);        // sRGB distance mismatches human perception
    if (dd < bestD) { bestD = dd; best = p; }
  }
  return best;
}
```

**Playfield chunkiness.** Quantize background/environment geometry to 4-pixel-wide
columns _before_ quantizing color, and mirror around x = 80:

```glsl
float px   = floor(gl_FragCoord.x);          // 0..159
float mirr = px < 80.0 ? px : 159.0 - px;    // reflect (CTRLPF D0 = 1)
float chunk = floor(mirr / 4.0);             // 0..19, the 20 playfield bits
```

Apply this **only** to the environment layer. Sprites keep 1-pixel granularity — the
disparity is the whole point (tell #2).

**Pass 3 — present.** Draw the 160×192 texture to a quad with aspect **256:192 (= 4:3)**,
`NearestFilter`, integer-scaled if you can (512×384, 1024×768) with the horizontal stretch
applied at the end. Don't let the stretch resample softly; nearest all the way.

**Flicker.** `object.visible = (frameCount & 1) === (objectIndex & 1)` for anything past
the second sprite, at 60 fps. If your renderer runs at 120, gate it to alternate every
_two_ frames — the tell is 30 Hz, not "every frame."

**Post-processing note:** this whole chain is a full-screen post pass, so it is fine on a
desktop r180 project and **wrong for the phone-in-headset r132 project**, where a
full-screen pass smears both eyes. See `threejs/references/visual-effects-without-postprocessing.md`.

## Reproducing it natively

The structure is identical — small offscreen target, nearest sampling, stretch at present.
The per-platform gotcha is always **turning interpolation off**, which is on by default
everywhere:

| target        | small buffer                              | nearest                                                                 | PAR stretch                                |
| ------------- | ----------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------ |
| Metal         | `MTLTexture` 160×192, render pass into it | `MTLSamplerDescriptor` `.magFilter = .nearest`, `.minFilter = .nearest` | final blit quad at 4:3                     |
| SwiftUI       | `Image` from a 160×192 `CGImage`          | `.interpolation(.none)`                                                 | `.aspectRatio(4.0/3.0, contentMode: .fit)` |
| Core Graphics | 160×192 `CGContext`                       | `ctx.interpolationQuality = .none`                                      | draw into a 4:3 rect                       |
| Canvas 2D     | 160×192 backing canvas                    | `ctx.imageSmoothingEnabled = false`                                     | CSS `image-rendering: pixelated` + 4:3 box |
| SDL / general | 160×192 render target                     | nearest scale mode                                                      | logical size 256×192                       |

`image-rendering: pixelated` on the CSS side is required _in addition to_ the canvas
setting — the canvas flag governs draws into it, the CSS property governs the browser's
upscale of the element.

## What to fake and what to honour

| constraint                                    | recommendation                                                                                                                                                                                |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 160×192 raster                                | **honour** — it's the foundation                                                                                                                                                              |
| 1.6:1 pixel aspect                            | **honour**, always                                                                                                                                                                            |
| 4 colors per scanline                         | **honour** — the highest-value single limit                                                                                                                                                   |
| playfield mirror symmetry                     | **honour** for environments; it's the strongest tell                                                                                                                                          |
| 4-clock playfield chunks vs 1-clock sprites   | **honour** — nearly free, rarely done, very effective                                                                                                                                         |
| 2 players / 2 missiles / 1 ball               | **fake** — draw as many objects as you like, but multiplex the _look_ with flicker                                                                                                            |
| 128 bytes of RAM                              | fake, obviously                                                                                                                                                                               |
| 32-step pitch divider (the out-of-tune scale) | **honour** — snap notes to `31399.5/(divisor×(AUDF+1))` and leave them wrong. It's most of the character, and correcting it is the one change that makes 2600 audio stop sounding like a 2600 |
| 2 channels shared with sound effects          | honour — the bassline dropping out when a laser fires is a period tell                                                                                                                        |
| polynomial noise timbres                      | honour — run the real 4/5/9-bit LFSRs; a noise-buffer sample is not the same thing                                                                                                            |
| CPU-written envelopes at 60 Hz                | honour — quantize volume changes to the frame, don't ramp smoothly                                                                                                                            |
| HMOVE comb                                    | optional; period-specific (pre-1980 feel)                                                                                                                                                     |
| composite bleed / scanlines / phosphor        | optional, and easy to overdo — try the clean version first                                                                                                                                    |

## Sources

- Palette values: [Lospec, Atari 2600 TIA (NTSC)](https://lospec.com/palette-list/atari-2600-tia-ntsc)
  (the Stella default decode; 127 distinct entries listed, `$FC` restored above as a
  duplicate of `$2E` to complete the 16×8 grid).
- Palette structure, PAL and SECAM behaviour:
  [Wikipedia, List of video game console palettes](https://en.wikipedia.org/wiki/List_of_video_game_console_palettes)
  and [Atari 2600 hardware](https://en.wikipedia.org/wiki/Atari_2600_hardware).
- Register semantics and timing: the _Stella Programmer's Guide_ (Steve Wright, 1979) and
  the AtariAge / `2600 Hardware` community documentation; Andrew Davie's
  ["Atari 2600 Programming for Newbies"](https://www.randomterrain.com/atari-2600-memories-tutorial-andrew-davie-11.html).
- Interactive color charts: [Random Terrain TIA color charts](https://www.randomterrain.com/atari-2600-memories-tia-color-charts.html).
