# topazlabs/video-upscale

Model page: <https://replicate.com/topazlabs/video-upscale>

Topaz Labs' **video super-resolution + frame interpolation** on Replicate — their consumer product (Topaz Video AI / Video Enhance AI) exposed as an API endpoint. Upscales to 720p / 1080p / 4K and optionally interpolates up to 120 fps in a single pass. This is the commercial-grade, identity-preserving upscaler — the same engine used for film restoration and deliverables. Latest version: `f4dad23b...` (2025-04-24). **866k+ runs** — by far the most-used video upscaler on Replicate.

## When to pick this over alternatives

- **Pick it over `cswry/seesr` or other diffusion-based upscalers** when you need **faithful** super-res — Topaz is faithful-tier (preserves identity, doesn't hallucinate detail), which matters for people, products, client deliverables, evidence, or anything where "shot at higher resolution" is the goal. Diffusion upscalers hallucinate and shift identity.
- **Pick it over `recraft-ai/recraft-creative-upscale` image-model chains** for video — those work per-frame and you lose temporal stability. Topaz understands video (uses motion information across frames).
- **Pick it when you also need frame interpolation** — `target_fps` interpolates in the same pass; no second model call for smoothing. Great for 24→60 or 30→120 conversions.
- **Skip it** if your source is already high-resolution and at your target framerate — nothing to do. Also skip for severely degraded sources (VHS grain, heavy compression artifacts) where a diffusion upscaler like `cswry/seesr` might do better at imagining lost detail.

## Input schema

| Field               | Type         | Required | Default    | Description                                                                               |
| ------------------- | ------------ | -------- | ---------- | ----------------------------------------------------------------------------------------- |
| `video`             | string (URI) | yes      | —          | Source video file. Local paths auto-uploaded by `run_model.py`.                           |
| `target_resolution` | enum         |          | `"1080p"`  | `720p`, `1080p`, or `4k`. Target short-edge or standard broadcast resolution.             |
| `target_fps`        | integer      |          | `60`       | Output frame rate, range `15–120`. Set equal to source fps if you don't want interpolation.|

Three fields total — refreshingly simple surface for a powerful model.

### Resolution choice

- **`720p`** — basic upscaling for web delivery or low-bandwidth targets. Rarely the right choice unless your source is below 720p.
- **`1080p`** — the default; broadcast-standard, reasonable balance of quality and file size.
- **`4k`** — for cinematic delivery, large-display playback, or mastering. **~4× the cost and time** of 1080p. Only pick 4K if the distribution target actually uses it.

### Target FPS choice

- Leave equal to source fps (e.g. 24 → 24, 30 → 30) if you don't want interpolation.
- 24 → 60 / 30 → 60 is the most common use — smooths pans, handheld, sports.
- 24 → 120 / 60 → 120 is for slow-motion post-processing — you can slow by 2.5× and still have 48 fps playback.
- Above the source's native framerate = interpolation. Below it = frame skipping (rarely desired).

## Output

**Bare URI string** — single `.mp4`. Saved as `topazlabs_video-upscale_0.mp4` by `run_model.py`.

## Pricing and runtime

Pricing not in schema — confirm on the model page. Topaz is **premium-tier** for video models on Replicate. Runtime scales non-linearly with `target_resolution × target_fps × duration`:

- Default example (short clip → 4K @ 60 fps) ran **~7 minutes** (438 s)
- 1080p @ 60 fps on a 10 s clip: budget 1–3 minutes
- 4K @ 120 fps: budget long — easily 10+ minutes per clip

Run short test clips first to see actual runtime/cost on your footage before batch jobs.

## Examples

**Default — 1080p @ 60 fps**, the safest/cheapest useful setting:

```json
{
  "video": "./source_720p_24fps.mp4"
}
```

```bash
python scripts/run_model.py topazlabs/video-upscale \
    --input-file input.json \
    --output ./out/
```

**4K master** — for delivery to high-resolution platforms:

```json
{
  "video": "./hero_1080p_24fps.mp4",
  "target_resolution": "4k",
  "target_fps": 60
}
```

**Preserve native framerate, just upscale resolution** — no interpolation, cheaper:

```json
{
  "video": "./interview_720p_30fps.mp4",
  "target_resolution": "1080p",
  "target_fps": 30
}
```

**High-framerate slow-mo prep** — upscale + interpolate to 120 for 2× slowdown in post:

```json
{
  "video": "./action_shot_60fps.mp4",
  "target_resolution": "1080p",
  "target_fps": 120
}
```

## Strengths / gotchas

**Good at:**

- Identity-preserving upscaling — faces stay recognizable, text stays readable, product shots stay faithful to the original
- Temporal stability — no flicker or shimmer across frames (uses inter-frame motion information)
- Combined upscale + interpolate in one pass — no need to chain two models
- Large format leaps (720p → 4K) without the artifacts you get from naive frame-by-frame upscaling
- Client/commercial work — Topaz is the same engine used in professional restoration pipelines

**Gotchas:**

- **Very slow at 4K + high fps.** The default-example 4K @ 60 fps run took 7+ minutes for a short clip. A 30-second clip at 4K @ 120 fps can push 20–30 minutes. Check `target_resolution × target_fps × duration` before committing to a batch.
- **Expensive at 4K.** Cost scales with output pixels; 4K is ~4× 1080p. Call out the cost before running 4K on anything longer than ~15 seconds.
- **No hallucination — faithful only.** Will *not* invent detail that isn't present in the source. If the source is heavily blurred or VHS-grade, Topaz can't recover lost information. For that use `cswry/seesr` (diffusion SR) — but accept that you'll lose identity fidelity.
- **`target_fps` interpolates; it doesn't judder-detect.** If the source has intentional strobing or film-style 24 fps cadence, interpolating to 60 will smooth out that creative choice. Match source fps if preserving the look matters.
- **Ignores source audio changes on interpolation.** Audio is preserved but not stretched — interpolating frames doesn't change playback duration, just smooths motion. Good.
- **720p input → 4K output = ~5.5× scale factor**, which is past the usually-safe 4× upscale. Quality holds better than most models at this range, but expect some softness vs true-shot 4K.
- **Container/codec:** feed standard mp4/mov/h.264. Exotic codecs may fail to decode.
- **Resolution is short-edge nominally.** Aspect ratio is preserved from source. A 4:3 1080p source at `target_resolution: "1080p"` stays 4:3.
- **Pre-stabilize before upscaling.** Topaz doesn't stabilize; jittery handheld stays jittery. Run a stabilizer first (Premiere / After Effects / ffmpeg `vidstabdetect` + `vidstabtransform`) for best results.
- **Version pin:** `topazlabs/video-upscale:f4dad23bbe2d0bf4736d2ea8c9156f1911d8eeb511c8d0bb390931e25caaef61`. Pin for commercial-deliverable reproducibility since Topaz updates rotate the bare-slug target.
