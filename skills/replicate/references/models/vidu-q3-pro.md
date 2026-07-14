# vidu/q3-pro

Model page: https://replicate.com/vidu/q3-pro

High-fidelity video generation with three modes in one endpoint, up to 16 seconds at 1080p with synchronized audio.

## Modes (inferred from which image inputs are set)

| Mode                   | How to trigger                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------- |
| **Text-to-video**      | No `start_image` or `end_image`, just a `prompt`. `aspect_ratio` applies.               |
| **Image-to-video**     | Set `start_image` only. `aspect_ratio` is ignored (taken from image).                   |
| **Start-end-to-video** | Set both `start_image` and `end_image`. Their aspect ratios must match within 0.8–1.25. |

## Input schema

| Field          | Type         | Required | Default  | Description                                                                                             |
| -------------- | ------------ | -------- | -------- | ------------------------------------------------------------------------------------------------------- |
| `prompt`       | string       | ✅       | —        | Text prompt for video generation. Max 5000 chars.                                                       |
| `start_image`  | string (URI) |          | —        | Start frame. Alone → image-to-video. With `end_image` → start-end mode. Supports png/jpeg/jpg/webp.     |
| `end_image`    | string (URI) |          | —        | End frame. Only valid together with `start_image`. Aspect ratios must be within 0.8–1.25 of each other. |
| `duration`     | integer      |          | `5`      | Seconds. Range: 1–16.                                                                                   |
| `aspect_ratio` | enum         |          | `"16:9"` | One of `16:9`, `9:16`, `3:4`, `4:3`, `1:1`. Text-to-video only (ignored when images given).             |
| `resolution`   | enum         |          | `"720p"` | One of `540p`, `720p`, `1080p`.                                                                         |
| `audio`        | boolean      |          | `true`   | Generate synchronized dialogue and SFX.                                                                 |
| `seed`         | integer      |          | random   | For reproducibility.                                                                                    |

Local image paths for `start_image` / `end_image` are auto-uploaded by `run_model.py`.

## Output

A single URI to the generated video (MP4). Saved as `vidu_q3-pro_0.mp4`.

## Pricing

Billed **per second of output video**, by resolution:

| Resolution | Rate    | 5s clip | 16s clip |
| ---------- | ------- | ------- | -------- |
| 540p       | $0.07/s | $0.35   | $1.12    |
| 720p       | $0.15/s | $0.75   | $2.40    |
| 1080p      | $0.16/s | $0.80   | $2.56    |

540p is a notably cheap draft tier — use it for iteration, then upgrade resolution only for the final.

## Examples

**Text-to-video:**

```bash
python scripts/run_model.py vidu/q3-pro \
    --input '{
      "prompt": "a lone astronaut walking across a neon-lit martian plain at dusk, wide cinematic shot",
      "duration": 8,
      "resolution": "720p",
      "aspect_ratio": "16:9"
    }' \
    --output ./out/
```

**Image-to-video** (animate a single image):

```bash
python scripts/run_model.py vidu/q3-pro \
    --input '{
      "prompt": "camera slowly pushes in, wind rustles the leaves",
      "start_image": "./photo.jpg",
      "duration": 5
    }' \
    --output ./out/
```

**Start-end-to-video** (morph between two keyframes):

```bash
python scripts/run_model.py vidu/q3-pro \
    --input '{
      "prompt": "smooth transformation from day to night over the valley",
      "start_image": "./day.jpg",
      "end_image": "./night.jpg",
      "duration": 6,
      "resolution": "1080p"
    }' \
    --output ./out/
```

## Strengths / limitations

**Good at:**

- Complex motion and temporal consistency
- Natural camera movements
- Synchronized audio (dialogue + SFX + ambient)
- Smooth keyframe morphs (unusual among video models)

**Weak at / gotchas:**

- Text rendering inside the video is unreliable — don't expect readable captions/signs.
- Rapid hand movements can look unnatural.
- No fine-grained audio/music control; you get what you get.
- Start/end aspect-ratio mismatch (outside 0.8–1.25) will reject the request.
