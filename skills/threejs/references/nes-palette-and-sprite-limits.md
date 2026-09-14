---
semantic_id: "ZG0w579Q2TWZLYoC9HqDQJlYMcmzAAAF"
related_ids:
  - "JGziC21y2zWJnQoM4nCH3JF4G4umcAAM"
  - "ZG04XjdUwmewJb7M-NoRwNuw2WmwEAAO"
---

# NES-constrained rendering in Three.js

Making a 3D scene obey the NES PPU. This file is the **Three.js implementation**; the
hardware it implements — the 64-entry master palette with hex values, the 25-color
onscreen ceiling, the attribute-table structure, sprite limits, the two global PPU
effects, and the honour-vs-fake analysis — lives in
**`skills/game-consoles/references/nes.md`**. Read that first if you're deciding _what_ to
reproduce. Come here for _how_.

**Do not duplicate the palette array.** It has one home, in the hardware file.

**Version note:** written against **r180**, assumes a full-screen post pass is available.
The GLSL is plain and runs on r132 unchanged; only import paths differ. Do **not** drop
this into the phone-in-headset project — it is a multi-pass full-screen chain, which is
exactly what `visual-effects-without-postprocessing.md` says to avoid there.

## The four constraints this pipeline enforces

Recap only; the reasoning is in the hardware file.

|                 |                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------- |
| raster          | **256×240**, presented at **8:7** PAR, cropped to 224 visible rows                           |
| color           | 64-entry fixed master palette, **25 onscreen** (4 bg palettes × 3 + 4 sprite × 3 + backdrop) |
| **granularity** | one background palette per **16×16 pixel block** — this is the artifact that matters         |
| compositing     | opaque only. No alpha, no blending, no fog, no bloom                                         |

## The pipeline

Four passes. Everything is `NearestFilter`, `antialias: false`, no mipmaps, no tone
mapping.

```text
scene ──► [0] render 256×240, toon-ramped   ──► bgRT (opaque world)
                                            ──► spriteRT (actors, alpha)
      ──► [1] attribute pass @ 16×15        ──► attrRT (which bg palette per block)
      ──► [2] resolve + composite           ──► canvas, upscaled integer + 8:7
```

### Pass 0 — flatten the lighting first

The highest-leverage step, and it happens before any quantization. **Give materials a 3–4
step toon ramp.** A palette has three colors; if you hand the quantizer a continuous
Lambert gradient it will pick a different palette entry every few pixels and you get
noise where the NES had flat shape. Quantize a stepped image and the palette matcher has
almost nothing to decide.

```js
const rt = (w, h, alpha) =>
  new THREE.WebGLRenderTarget(w, h, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    format: alpha ? THREE.RGBAFormat : THREE.RGBFormat,
    depthBuffer: true,
    samples: 0, // MSAA would invent colors that are not in the palette
  });

renderer.toneMapping = THREE.NoToneMapping; // a tone curve moves every color off-palette
```

Use an **orthographic camera** unless you have a reason not to. The PPU had no
perspective, and — more practically — an ortho camera can be snapped to the world-units-
per-pixel grid, which kills the sub-pixel crawl that makes low-res 3D shimmer. A
perspective camera cannot be snapped; every pixel moves at a different rate and the
256×240 grid boils.

### Pass 1 — the attribute pass

Full-screen quad at **16×15** (one fragment per 16×16 block). Each fragment reads its own
256 source texels once and scores all four candidate palettes, then writes the winner.

```glsl
uniform sampler2D uScene;
uniform vec3 uPal[16];      // 4 palettes x 4 entries (entry 0 = shared backdrop)
varying vec2 vUv;

void main() {
  ivec2 base = ivec2(gl_FragCoord.xy) * 16;
  float err[4];
  for (int p = 0; p < 4; p++) err[p] = 0.0;

  for (int y = 0; y < 16; y++)
  for (int x = 0; x < 16; x++) {
    vec3 c = texelFetch(uScene, base + ivec2(x, y), 0).rgb;
    for (int p = 0; p < 4; p++) {
      float best = 1e9;
      for (int k = 0; k < 4; k++)
        best = min(best, distance(c, uPal[p * 4 + k]));
      err[p] += best * best;         // squared, so one bad pixel is not free
    }
  }

  int win = 0;
  for (int p = 1; p < 4; p++) if (err[p] < err[win]) win = p;
  gl_FragColor = vec4(float(win) / 3.0, 0.0, 0.0, 1.0);
}
```

240 fragments × 256 fetches ≈ 61k texel reads for the whole pass. Free.

**Choose the four palettes by hand.** That is what NES artists did, and it is also the
only stable answer. Computing them per frame (median cut over the histogram) makes the
whole screen shift hue when one bright object enters — the same temporal-instability
failure described in `dithering-and-halftone.md`, one level up.

**Add hysteresis to the block choice.** A block sitting halfway between two palettes will
flip every frame and strobe. Ping-pong the 16×15 target and keep last frame's index
unless the new one wins by a margin:

```glsl
float prev = texture2D(uPrevAttr, vUv).r * 3.0;
int p0 = int(prev + 0.5);
if (err[win] > err[p0] * 0.85) win = p0;   // new must be 15% better to take over
```

That one line is the difference between "NES" and "NES with a fault".

### Pass 2 — resolve and composite

Background: read `attrRT` with `NearestFilter`, snap to that palette's 4 entries.
Sprites: each actor already carries its palette as a material uniform, so it quantizes
itself in its own fragment shader — no attribute pass needed, because on real hardware a
sprite's palette is per-sprite, not per-block. Actors write alpha 0 where they mean
transparency; composite is a hard `mix` on `alpha > 0.5`, never a blend.

The palette-match helper, shared by both:

```glsl
vec3 snap(vec3 c, vec3 pal[4]) {
  vec3 best = pal[0];
  float bd = 1e9;
  for (int k = 0; k < 4; k++) {
    float d = distance(c, pal[k]);
    if (d < bd) { bd = d; best = pal[k]; }
  }
  return best;
}
```

The PPU's two global effects — **grayscale** and **color emphasis** — also belong in this
pass, applied to the palette index or the looked-up color (see the hardware file for the
bit semantics). Both stay inside the hardware's vocabulary. A bloom pass does not.

## Color space — the gotcha that eats an afternoon

`NES_PALETTE` is **sRGB 8-bit**. A `WebGLRenderTarget` in r180 holds **linear working
space**. Matching linear scene values against sRGB palette floats picks wrong every time,
and wrong in a specific way: everything clumps toward the dark entries, because linear
values sit low.

Match in sRGB — it is both correct against the table and closer to perceptual than
nearest-neighbour in linear, which over-weights highlights:

```glsl
vec3 srgb = pow(max(texture2D(uScene, vUv).rgb, 0.0), vec3(1.0 / 2.2));
vec3 out_ = snap(srgb, pal);   // out_ is already display-referred
```

Then make sure nothing converts it again on the way to the canvas. **The test is an
eyedropper, and it takes ten seconds:** screenshot, pick a pixel, and it must read
_exactly_ `#0071EF`. Off by a few counts in every channel means a second output-color-space
conversion is being applied after your shader; off by a lot means you matched in the wrong
space. There is no "close enough" here — the entire premise is that only 25 exact values
appear on screen, and that is a property you can assert in a test:

```js
// sample the framebuffer: at most 25 distinct values, all of them in NES_PALETTE
```

## Presentation

- **Integer upscale only.** 3× or 4×, `NearestFilter`. A fractional scale gives some
  source pixels more screen pixels than others and the grid visibly beats.
- **Then apply 8:7 horizontally** if you want it period-correct — stretch the already
  integer-scaled image on the CSS/quad level, not by resampling the render target.
- Crop to the visible 224 rows, or draw the overscan rows in the backdrop color.

## Dithering: hand-authored, not blue noise

The hardware file explains why (the PPU had no dithering hardware — every checkerboard was
drawn by an artist). The implementation consequence here:

- Do not run error diffusion or blue noise before quantization. Both produce aperiodic,
  content-following clusters, which is the correct answer for a Macintosh and the wrong
  answer here — see `dithering-and-halftone.md` for why those techniques look the way they
  do.
- If you want dither, use a **2×2 checker locked to the 256×240 grid**, applied only
  between two entries of the block's own palette.

## The 8-sprites-per-scanline limit

You can emulate it. Consider carefully whether you should — the hardware file recommends
default-off, and this is why in engine terms.

The mechanism: sort actors by OAM index, walk the 240 scanlines, and for each scanline
past the eighth overlapping sprite, drop the rest. NES games rotated the OAM start index
every frame so the dropouts _flickered_ across actors instead of consistently hiding the
same one.

```js
// per frame, over screen-space Y spans; N < 64 so this is nothing
const order = actors.map((_, i) => (i + frame) % actors.length);
```

Three problems:

1. Real hardware drops **per scanline**, so a tall sprite is half-drawn. `mesh.visible` is
   per object. You can only approximate by hiding the whole actor, which is a visibly
   different artifact.
2. It needs screen-space bounds for every actor on the CPU each frame.
3. Modern players read it as a bug, not as a period detail.

Make it a toggle, default off, and label it in code as an emulation of a hardware defect
so the next person does not "fix" it.
