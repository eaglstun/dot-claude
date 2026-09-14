---
topic_id: "v2:NCBI"
topic_path: "apple-accelerate/vector-math"
semantic_id: "--0lTj89Q9OCaLOHo46M8mo2H04CkAAH"
related_ids:
  - "2r0NQtMtUhCqaTuFKuiN3n7-Sz_DwAAH"
  - "_-bsBuV9l9rySMOYA7aN4ChjXm7U8AAI"
---
# vImage — high-performance image processing

Source:

- https://developer.apple.com/documentation/accelerate/vimage
- https://developer.apple.com/documentation/accelerate/vimage/vimage_buffer
- https://developer.apple.com/documentation/accelerate/vimage-pixelbuffer (Swift `vImage.PixelBuffer`)
- https://developer.apple.com/documentation/accelerate/core_video_interoperation

vImage is Accelerate's image-processing library: convolution & morphology, geometric
resampling, format/colorspace conversion, histogram/tone operations, and alpha compositing —
all vectorized on the CPU, with Core Graphics and Core Video interop so it slots into real
pipelines.

## The buffer model

Everything operates on a `vImage_Buffer`:

```c
typedef struct { void *data; vImagePixelCount height, width; size_t rowBytes; } vImage_Buffer;
```

`rowBytes` is the **stride** (bytes per row, ≥ width·bytesPerPixel) — it can exceed the
minimum for alignment, so never assume `rowBytes == width*bpp`. Init a buffer to match a
CGImage with `vImageBuffer_InitWithCGImage`; get a CGImage back with
`vImageCreateCGImageFromBuffer`. The modern Swift face is `vImage.PixelBuffer<Format>`,
which is typed by pixel format and manages memory for you.

Pixel formats are `Planar8` / `PlanarF` (single channel) and `ARGB8888` / `RGBA8888` /
`ARGBFFFF` (interleaved). Many ops have a per-format variant (`vImageBoxConvolve_ARGB8888`).

## Operation families

- **Convolution & morphology:** `vImageConvolve_*` (box, Gaussian, general kernels),
  `vImageBoxConvolve` / `vImageTentConvolve` (fast blurs), `vImageDilate` / `vImageErode`,
  bokeh via multi-kernel convolution. Edge handling via a **flag** (see gotchas).
- **Geometry / resampling:** `vImageScale_*` (Lanczos-quality resize), `vImageAffineWarp_*`,
  `vImageShear`, `vImageRotate`, `vImageHorizontalReflect`.
- **Format & colorspace conversion:** `vImageConvert_*` between pixel layouts and bit depths,
  planar↔interleaved (`vImageConvert_ARGB8888toPlanar8`), premultiply/unpremultiply alpha,
  and `vImageMatrixMultiply` for colorspace matrices (RGB↔YUV, etc.).
- **Tone & color:** gamma (`vImageGamma`), `vImagePiecewisePolynomial`, histogram
  (`vImageHistogramCalculation`, `vImageEqualization`, `vImageContrastStretch`),
  per-channel curves, `vImageMatrixMultiply` for saturation/hue matrices.
- **Alpha compositing:** `vImagePremultipliedAlphaBlend`, clipping, flattening.
- **Core Video interop:** operate directly on `CVPixelBuffer`s for camera/video frames.

## Gotchas

- **`rowBytes` is a stride, not `width*bpp`.** vImage (and CVPixelBuffers) pad rows for
  alignment. Iterating with the wrong stride shears the image diagonally — the tell-tale
  "skewed rainbow" bug. Always use the buffer's own `rowBytes`.
- **Edge handling is a flag, not a default.** Convolution ops take a `vImage_Flags` — pass
  `kvImageEdgeExtend` / `kvImageTruncateKernel` / a background-color flag deliberately.
  Omitting it (`kvImageNoFlags`) leaves border pixels undefined → dark/garbage frames.
- **Premultiplied alpha bites resizing.** Scale/blur _premultiplied_ ARGB or you get dark
  halos around transparent edges; convert, operate, convert back if your source is
  unpremultiplied. Know which your CGImage is (`CGImageAlphaInfo`).
- **In-place isn't always safe.** Some ops allow `src == dst`; many (geometry, kernels that
  read neighbors) do not. Check per-function; when unsure, use a separate destination buffer.
- **You own the `data` pointer.** With the C `vImage_Buffer` API you `malloc`/`free` `data`
  yourself (or use `vImageBuffer_Init`). Leaks here are full framebuffers. The Swift
  `vImage.PixelBuffer` handles this — prefer it in Swift.
- **Format tags must match reality.** Calling `_ARGB8888` on RGBA data channel-swaps colors
  silently. Match the function suffix to the actual byte order.

### See also

- [[vdsp-signal-processing]] — 1D signals and generic 2D convolution live in vDSP; _images_
  (with pixel formats, edge modes, colorspaces) are vImage.
- [[simd-vectors-and-matrices]] — color/geometry transform _matrices_ fed to
  `vImageMatrixMultiply` are natural `simd` types.
