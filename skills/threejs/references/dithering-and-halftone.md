---
semantic_id: "JZQkJVAhZxGIrLwC4kqk1Bl5MZ12cAAK"
related_ids:
  - "hGznKXSR0bGZDF5epWuH1BlYm5FGMAAG"
  - "I9hiKcAf4mforBIKEB8EjJl44f70sAAJ"
---
# Dithering, halftone and 1-bit rendering in Three.js

Reducing a continuous image to a few tones on purpose — Atkinson dithering, ordered
(Bayer) dithering, blue noise, and where each one can actually run.

**Version note:** written from a desktop **r180** project (CAPRICCIO). The GPU techniques
here are plain GLSL injected via `onBeforeCompile` and work unchanged on r132; only the
import paths differ. The CPU technique is version-independent. What does _not_ transfer to
the phone-in-headset project is the assumption of a full-screen post pass — see
`visual-effects-without-postprocessing.md` for why that is avoided there.

## Atkinson dithering — the actual algorithm

Bill Atkinson, Apple, ~1984. It is what the original Macintosh looked like.

Raster order, one pixel at a time:

```
old = value + error already pushed onto this pixel
new = old > threshold ? 1 : 0
err = (old - new) / 8

distribute err to six neighbours:

          *   +1/8  +1/8
   +1/8  +1/8  +1/8
          +1/8
```

Offsets: `(x+1,y) (x+2,y) (x-1,y+1) (x,y+1) (x+1,y+1) (x,y+2)`

**Six shares of one eighth leave. Two eighths are discarded.** Only ¾ of the error
propagates, and that deliberate leak is the entire signature: highlights blow to paper
white and shadows crush to solid ink, so large flat areas snap clean instead of fuzzing.

Compare Floyd–Steinberg, which conserves _all_ of the error (7/16, 3/16, 5/16, 1/16) and
looks muddier and flatter as a result.

### The three visual tells

Useful for judging whether an imitation is working:

1. **Aperiodic clusters** — no repeating structure anywhere.
2. **Short serpentine "worms"** in midtones, because error walks forward along the scan.
3. **Clean voids** — big areas of pure paper or pure ink, not an even speckle.

### Working CPU implementation

```js
function atkinsonDither(
  img,
  ink = [0x2b, 0x1a, 0x52],
  paper = [0xf6, 0xe0, 0xef],
) {
  const c = document.createElement("canvas");
  const w = (c.width = img.width),
    h = (c.height = img.height);
  const g = c.getContext("2d");
  g.drawImage(img, 0, 0);
  const id = g.getImageData(0, 0, w, h),
    d = id.data;

  // work in linear-ish luminance, one float per pixel
  const lum = new Float32Array(w * h);
  for (let i = 0, j = 0; i < lum.length; i++, j += 4)
    lum[i] = (0.2126 * d[j] + 0.7152 * d[j + 1] + 0.0722 * d[j + 2]) / 255;

  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      const old = lum[i];
      const q = old > 0.5 ? 1 : 0;
      const err = (old - q) / 8; // 6 shares leave, 2 are thrown away
      lum[i] = q;
      if (x + 1 < w) lum[i + 1] += err;
      if (x + 2 < w) lum[i + 2] += err;
      if (y + 1 < h) {
        if (x > 0) lum[i + w - 1] += err;
        lum[i + w] += err;
        if (x + 1 < w) lum[i + w + 1] += err;
      }
      if (y + 2 < h) lum[i + 2 * w] += err;
    }

  for (let i = 0, j = 0; i < lum.length; i++, j += 4) {
    const on = lum[i] < 0.5;
    d[j] = on ? ink[0] : paper[0];
    d[j + 1] = on ? ink[1] : paper[1];
    d[j + 2] = on ? ink[2] : paper[2];
    d[j + 3] = 255;
  }
  g.putImageData(id, 0, 0);
  return c;
}
```

## Why it cannot be a fragment shader

**Atkinson is error diffusion, and error diffusion is sequential.** Pixel (0,0) must resolve
before (1,0), which must resolve before (2,0), because each one modifies its neighbours'
input. A fragment shader evaluates every pixel independently with no knowledge of what its
neighbours decided.

Do not try to fake it with a ping-pong error buffer. Reading last frame's neighbour errors
is a _simultaneous relaxation_, not a raster scan — a different algorithm that happens to
be expensive. It needs several static frames to converge, so anything that moves (a walking
crowd, a flickering light, a panning camera) smears permanently.

### Where to run the real thing

Run true Atkinson **on the CPU, on stills**. If the app has any capture, export, photo mode
or screenshot feature, that is a one-time cost on an image that has already stopped moving,
and you can run the genuine 1984 algorithm honestly.

This is usually the better product decision anyway: the world renders in an homage, and the
artifact the user keeps is the real thing.

## Realtime: ordered vs blue noise

For the live frame you are choosing a **threshold pattern**, not diffusing error.

### Bayer (ordered) — cheap and it shows

```glsl
float bayer4(vec2 p) {
  vec2 q = floor(mod(p, 4.0));
  float i = q.x + q.y * 4.0;
  // 4x4 Bayer matrix, values 0..15
  float m = /* lookup */ 0.0;
  return (m + 0.5) / 16.0;
}
```

Two structural problems, neither fixable by tuning:

- **Only 16 threshold levels**, so tones band.
- **A fixed lattice that cannot see the image.** The same 4-pixel grid repeats everywhere
  regardless of content, which reads as a halftone _screen_ rather than a dither. Atkinson's
  signature is clusters that follow image content; a content-blind matrix cannot produce
  them.

Recognisable by the 45° crosshatch it leaves in midtones.

### Blue noise — the right realtime answer

A blue-noise threshold texture is aperiodic, has no visible lattice, and gives as many
threshold levels as the texture has bits. Generate it at load with **void-and-cluster**
(Ulichney) — procedural, ships zero bytes, tiles seamlessly:

```js
// 64x64 is plenty; generated once at startup, ~50ms
const tex = new THREE.DataTexture(bytes, 64, 64, THREE.RedFormat);
tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
tex.minFilter = tex.magFilter = THREE.NearestFilter; // never interpolate a threshold
tex.needsUpdate = true;
```

**Implementation note on void-and-cluster:** past half fill, the canonical phase-3 rule
("break the tightest cluster of zeros") is mathematically identical to phase 2's "fill the
largest void" on a torus, because zero-energy is a constant minus one-energy. One rule
serves both phases.

If a texture is genuinely unwelcome, interleaved gradient noise is a one-liner that still
beats Bayer comfortably:

```glsl
float ign(vec2 p) {
  return fract(52.9829189 * fract(0.06711056 * p.x + 0.00583715 * p.y));
}
```

### Two adjustments that buy most of the remaining gap

**1. Bias the threshold by local luminance gradient.** Clusters then bunch along edges the
way diffusion does, which is what makes it read as _diffusion_ rather than _screening_:

```glsl
float t = texture2D(uBlueNoise, uv * scale).r;
t = mix(t, 0.5, clamp(fwidth(luma) * k, 0.0, 1.0));   // edges pull toward mid
```

**2. Shape the contrast curve to mimic the ¾ error retention** before thresholding:

```glsl
l = clamp((l - 0.5) * 1.45 + 0.56, 0.0, 1.0);   // highlights blow, shadows crush
```

## Cell size — a period-accuracy note

Atkinson ran at **one pixel on a 512×342 screen**. On a 1500px-wide viewport, 1px cells are
proportionally about three times finer than a real Macintosh. Quantise the sample
coordinate so a "dither pixel" spans 2–4 screen pixels:

```glsl
vec2 cell = floor(gl_FragCoord.xy / uPxScale);
```

Also guard against supersampling averaging your 1-bit output back to grey: if the renderer
draws at a higher internal resolution and downscales, the cell must be large enough in
_final_ pixels, not render-target pixels.

## Honest labelling

Ordered dither with an Atkinson-shaped contrast curve **reads as** Atkinson and is not
Atkinson. If a project claims the real algorithm, it should be the real algorithm somewhere
specific — and it is worth saying which is which in the code, because the next person will
otherwise assume the realtime path is authentic and be confused when it does not match a
reference image.
