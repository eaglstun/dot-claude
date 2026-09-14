# lucataco/depth-anything-video

Model page: <https://replicate.com/lucataco/depth-anything-video>
Paper: <https://arxiv.org/abs/2401.10891>
GitHub: <https://github.com/lucataco/cog-depth-anything-video>
License: Apache 2.0 (upstream Depth Anything)

**Per-frame monocular depth estimation** applied to a full video file — returns a depth-map video where pixel intensity encodes distance from the camera (brighter = closer). Cog-packaged wrapper around **Depth Anything** (Lihe Yang et al., 2024), the ViT-family foundation model for zero-shot depth. Useful as a **control signal** for downstream video models (depth-conditioned ControlNets, relighting, parallax/2.5D compositing, fake-3D effects) rather than a consumer-facing output on its own. Latest version: `91436914...` (2024-02-09, stable since).

## When to pick this over alternatives

- **Pick it over per-frame image-depth calls** (running `lucataco/depth-anything` on extracted frames) for convenience — this endpoint handles decode → per-frame depth → re-encode to video in one call. Equivalent quality, less scripting.
- **Pick it over MiDaS-family models** for zero-shot robustness. Depth Anything was trained on 1.5M labeled + 62M unlabeled images; it generalizes to outdoor/indoor/drone/stylized footage better than older depth models.
- **Pick `vits` encoder by default** — Small variant, fast, nearly as good as Large on most footage. Upgrade to `vitl` only if you see depth errors on difficult scenes (transparent surfaces, mirrors, heavily textured foliage).
- **Skip it** if you need absolute metric depth (meters) — Depth Anything outputs **relative** depth. For metric depth, look at specialized models like ZoeDepth or Metric3D.

## Input schema

| Field     | Type         | Required | Default  | Description                                                                                                                  |
| --------- | ------------ | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `video`   | string (URI) | yes      | —        | Source video file. Local paths auto-uploaded by `run_model.py`. Standard container/codec combos work (mp4 / mov / h.264).    |
| `encoder` | enum         |          | `"vits"` | ViT backbone size — `vits` (Small, default), `vitb` (Base), `vitl` (Large). Bigger = more accurate depth, slower / costlier. |

That's the entire input surface — two fields. No resolution, fps, or output format controls; it matches the source.

### `encoder` tradeoffs

| Encoder | Params | Speed        | Quality                                                 | When to use                                                                  |
| ------- | ------ | ------------ | ------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `vits`  | ~25M   | Fastest      | Great on most footage                                   | Default. Use unless you see specific depth errors.                           |
| `vitb`  | ~97M   | ~2× slower   | Noticeably sharper on fine detail (hair, foliage edges) | Mid-tier — use when `vits` leaves edges blurry.                              |
| `vitl`  | ~335M  | ~4–5× slower | Best — handles reflective/transparent surfaces better   | Use for difficult scenes (glass, water, mirrors) where `vits` visibly fails. |

## Output

**Bare URI string** — single `.mp4` of the same duration and framerate as the input, with depth encoded as grayscale (standard Depth Anything colormap on some versions). Saved as `lucataco_depth-anything-video_0.mp4` by `run_model.py`.

## Pricing and runtime

Not listed explicitly — confirm on the model page. Typical lucataco utility wrappers run on A40 or L40S at a few cents per minute of video. Default example predicted a short dolphin clip in **~17.6 seconds** on `vits`. Budget roughly **real-time to 2× real-time** on `vits`, 4–8× real-time on `vitl`.

## Examples

**Default — depth map of a short clip at fastest setting:**

```json
{
  "video": "./driveby.mp4"
}
```

```bash
python scripts/run_model.py lucataco/depth-anything-video \
    --input-file input.json \
    --output ./out/
```

**High-quality pass on a difficult scene** (mirrors, glass, fine foliage):

```json
{
  "video": "./rainy_storefront.mp4",
  "encoder": "vitl"
}
```

**As a preprocess for a depth-conditioned video effect** — pipe the depth output into a compositing tool, fake-3D parallax node, or depth-aware relighting step:

```bash
python scripts/run_model.py lucataco/depth-anything-video \
    --input '{"video": "./hero.mp4", "encoder": "vitb"}' \
    --output ./out/

# Downstream: composite original RGB + depth mask in ffmpeg / After Effects / Nuke
ffmpeg -i ./hero.mp4 -i ./out/lucataco_depth-anything-video_0.mp4 \
    -filter_complex "[0:v][1:v]blend=all_mode=multiply" \
    ./hero_depth_modulated.mp4
```

## Strengths / gotchas

**Good at:**

- Zero-shot depth on varied footage — indoor, outdoor, drone, stylized, animation
- Per-frame temporal stability is acceptable out of the box (not perfect — see gotcha below)
- Simple API — two fields, no tuning burden, sensible `vits` default

**Gotchas:**

- **Relative, not metric, depth.** Brightness encodes "closer vs further within this clip," not "X meters." Don't feed into pipelines that assume calibrated depth without post-normalization.
- **No built-in temporal smoothing.** Each frame is processed independently — fast motion or thin structures (wires, hair) can flicker between frames. For downstream uses that require temporally stable depth (optical-flow-driven effects, 2.5D parallax over long takes), apply a temporal filter post-hoc (`ffmpeg -vf minterpolate` with `scd=none` or a median-of-N-frames filter).
- **No fps / resolution control.** Output matches input. Pre-downscale before submission if the source is huge — 4K input will cost 4× the 1080p version for the same information.
- **Encoder choice is the only tuning knob.** If `vits` output has visible errors (depth bleeding across object edges, confusion on reflective surfaces), jump straight to `vitl` — `vitb` rarely fixes what `vits` got wrong, it only sharpens what was already close.
- **Not for talking-head close-ups.** Depth Anything is tuned for scenes with a depth gradient. On tight portraits against a neutral background you'll get a near-flat output — consider `meta/sam-2` or a segmentation model instead.
- **Reflective / transparent surfaces confuse all encoders.** `vitl` is best, but don't expect it to cleanly separate a reflection in a window from the content behind the glass — that's a known limitation of the architecture, not a bug.
- **Version pin:** `lucataco/depth-anything-video:9143691405afc64c7952499a1e81e3f779535a8916c8da7154a9995f145d5e6d` — the model has been stable since 2024-02, but pin if you want byte-reproducible depth across reruns for compositing work.
