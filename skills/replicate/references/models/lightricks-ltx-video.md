# lightricks/ltx-video

Model page: <https://replicate.com/lightricks/ltx-video>

GitHub: <https://github.com/Lightricks/LTX-Video>

LTX-Video is Lightricks' **fast open-source DiT video model** — it generates 24 FPS clips at 768x512 faster than realtime (a ~4s clip typically renders in ~10–12s of GPU time, though the full Replicate prediction with cold start usually lands near 60–90s). The small footprint and extreme speed make it the go-to pick whenever you need to iterate quickly or batch-generate many takes. Compared to peers: `bytedance/seedance-2.0` (much higher quality, slower, pricier), `pixverse/pixverse-v6` (cheap but closed), `kwaivgi/kling-v3-omni-video` (premium, 1080p, native audio, minutes per clip). Sweet spot: rapid iteration, batch generation, storyboard drafting, anywhere speed matters more than SOTA prompt adherence.

## Modes (inferred from whether `image` is set)

| Mode               | How to trigger                                                              |
| ------------------ | --------------------------------------------------------------------------- |
| **Text-to-video**  | Provide `prompt` only. `aspect_ratio` + `target_size` set the output shape. |
| **Image-to-video** | Set `image` to a URI / local path. `aspect_ratio` is ignored (from image).  |

## Input schema

| Field               | Type         | Required | Default                                                         | Description                                                                                                                           |
| ------------------- | ------------ | -------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`            | string       | ✅       | `"best quality, 4k, HDR, a tracking shot of a beautiful scene"` | Text prompt. **This model needs long, descriptive prompts** — short prompts produce noticeably worse output.                          |
| `negative_prompt`   | string       |          | `"low quality, worst quality, deformed, distorted"`             | Things to exclude from the video.                                                                                                     |
| `image`             | string (URI) |          | —                                                               | Optional starting frame. Enables image-to-video mode; `aspect_ratio` is ignored when set.                                             |
| `image_noise_scale` | number       |          | `0.15`                                                          | 0–1. Lower = sticks more closely to the input image. Only meaningful in image-to-video mode.                                          |
| `target_size`       | enum (int)   |          | `640`                                                           | One of `512`, `576`, `640`, `704`, `768`, `832`, `896`, `960`, `1024`. Controls output resolution.                                    |
| `aspect_ratio`      | enum         |          | `"3:2"`                                                         | One of `1:1`, `1:2`, `2:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `9:21`, `21:9`. Ignored if `image` is provided. |
| `cfg`               | number       |          | `3`                                                             | 1–20. How strongly the video follows the prompt. Higher = more literal, lower = more varied.                                          |
| `steps`             | integer      |          | `30`                                                            | 1–50. Denoising steps. Lower = faster but lower quality; `20–30` is a good speed/quality balance.                                     |
| `length`            | enum (int)   |          | `97`                                                            | Frames in the output. One of `97`, `129`, `161`, `193`, `225`, `257`. At 24 FPS: ~4s, ~5.4s, ~6.7s, ~8s, ~9.4s, ~10.7s.               |
| `model`             | enum         |          | `"0.9.1"`                                                       | Model version. One of `"0.9.1"`, `"0.9"`. Stick to `0.9.1` unless you need to reproduce older output.                                 |
| `seed`              | integer      |          | random                                                          | Set for reproducibility.                                                                                                              |

Notes:

- No `fps` / `width` / `height` / `num_frames` fields — use `target_size` + `aspect_ratio` + `length` instead. FPS is fixed at 24.
- Local paths for `image` are auto-uploaded by `run_model.py`.
- Frame counts are `8k+1` (enforced via the enum); resolutions are multiples of 32 via `target_size`.

## Output

Array of URIs, in practice length **1** — a single H.264 MP4 at 24 FPS. Saved locally as `lightricks_ltx-video_0.mp4` by `run_model.py`. Source filename on Replicate is `R8_LTX_00001.mp4`.

## Pricing

Billed **per run** (not per second). ~`$0.080` per run on Nvidia L40S, i.e. **~12 runs per $1**. This is one of the cheapest per-clip video models on Replicate and makes LTX-Video attractive for batch sweeps or draft passes before promoting to a higher-quality model.

Typical prediction time: ~60–90s end-to-end (cold start dominates; actual generation for a 97-frame clip is ~10–15s).

## Examples

**Text-to-video, short draft** (4s at 640 target, 3:2):

```bash
python scripts/run_model.py lightricks/ltx-video \
    --input '{
      "prompt": "A low-angle tracking shot gliding through a foggy pine forest at dawn. Shafts of golden sunlight cut between the trees. Dew glistens on the ferns. Slow, steady camera motion. Cinematic, shallow depth of field, 4k, HDR.",
      "length": 97,
      "target_size": 640,
      "aspect_ratio": "3:2",
      "steps": 30,
      "cfg": 3
    }' \
    --output ./out/
```

**Image-to-video** (animate a still — `aspect_ratio` is ignored):

```bash
python scripts/run_model.py lightricks/ltx-video \
    --input '{
      "prompt": "The woman slowly turns her head toward the camera and smiles faintly. Warm late-afternoon sunlight flickers across her face as leaves sway in the background. Subtle natural motion, real-life footage.",
      "image": "./portrait.jpg",
      "image_noise_scale": 0.15,
      "length": 129,
      "steps": 30
    }' \
    --output ./out/
```

**Longer, higher-res pass** (~10.7s at 768, 16:9, reproducible seed):

```bash
python scripts/run_model.py lightricks/ltx-video \
    --input '{
      "prompt": "Aerial drone shot descending over a neon-soaked Tokyo alleyway at night. Rain-slick pavement reflects the signs. A lone figure with an umbrella walks beneath a red paper lantern. Atmospheric fog, shallow depth of field, cinematic anamorphic look.",
      "length": 257,
      "target_size": 768,
      "aspect_ratio": "16:9",
      "steps": 40,
      "cfg": 3.5,
      "seed": 1234
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Speed. Often faster than realtime on the GPU itself — the fastest hosted video model in this skill's references.
- Very low cost per clip (~$0.08).
- Batch generation and parameter sweeps (try many seeds / prompts cheaply).
- Reasonable motion and temporal coherence for a small model.
- Open source — same weights can be run locally if needed.

**Weak at / gotchas:**

- **Short prompts produce poor output.** The model card explicitly warns: long, descriptive prompts (camera moves, lighting, subject detail, mood) are required. Treat one-liners as a bug.
- Prompt adherence and fine detail are below SOTA closed models (Seedance, Kling, Veo).
- Max duration is **257 frames ≈ 10.7s** at 24 FPS (fixed). No audio output.
- Max useful resolution is `target_size: 1024` and roughly 720x1280 (official recommendation); pushing the largest `target_size` with extreme aspect ratios can degrade quality.
- FPS is locked at 24 — no `fps` knob.
- `image_noise_scale` only matters in image-to-video; tweak it if the starting frame is being ignored or over-preserved.
- No `num_frames` / `width` / `height` fields — use `length` / `target_size` / `aspect_ratio`. The enums are strict; arbitrary values get rejected.
