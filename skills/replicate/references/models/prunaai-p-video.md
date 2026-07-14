# prunaai/p-video

Model page: https://replicate.com/prunaai/p-video

Fast, cheap video generation from Pruna. Handles **text-to-video, image-to-video, start-end-to-video, and audio-to-video** in a single endpoint. Generates a 5-second 720p clip in ~10s, and has a built-in **draft mode** that's 4× faster and ~4× cheaper for iteration.

## Modes (inferred from which optional inputs are set)

| Mode                   | How to trigger                                                    |
| ---------------------- | ----------------------------------------------------------------- |
| **Text-to-video**      | Just `prompt`. `aspect_ratio` applies.                            |
| **Image-to-video**     | Set `image`. `aspect_ratio` ignored (taken from image).           |
| **Start-end-to-video** | Set `image` (first frame) + `last_frame_image`.                   |
| **Audio-to-video**     | Set `audio`. `duration` is ignored (output matches audio length). |

## Input schema

| Field                   | Type         | Required | Default    | Description                                                                                           |
| ----------------------- | ------------ | -------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| `prompt`                | string       | ✅       | —          | Text prompt.                                                                                          |
| `image`                 | string (URI) |          | —          | First-frame image for image-to-video. Supports jpg/jpeg/png/webp.                                     |
| `last_frame_image`      | string (URI) |          | —          | Last-frame image (use with `image` for start-end morph).                                              |
| `audio`                 | string (URI) |          | —          | Conditioning audio for audio-to-video. Supports flac/mp3/wav.                                         |
| `duration`              | integer      |          | `5`        | Seconds, range 1–20. Ignored when `audio` is provided.                                                |
| `aspect_ratio`          | enum         |          | `"16:9"`   | One of `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`, `1:1`. Ignored when `image` is provided.           |
| `resolution`            | enum         |          | `"720p"`   | One of `720p`, `1080p`.                                                                               |
| `fps`                   | enum         |          | `24`       | One of `24`, `48`.                                                                                    |
| `draft`                 | boolean      |          | `false`    | Draft mode — 4× faster, lower quality, 4× cheaper. Use for iteration.                                 |
| `prompt_upsampling`     | boolean      |          | `true`     | Auto-enhance the prompt. Usually helpful; turn off only if your prompt is already precise.            |
| `save_audio`            | boolean      |          | `true`     | Include audio in the output MP4.                                                                      |
| `disable_safety_filter` | boolean      |          | **`true`** | ⚠ Default is `true` (filter OFF), opposite of most models. Flip to `false` if you want safety checks. |
| `seed`                  | integer      |          | random     | For reproducibility.                                                                                  |
| `no_op`                 | boolean      |          | `false`    | Health-check mode: returns status without running inference. Rarely needed.                           |

## Output

Single URI to the generated video (MP4). Saved as `prunaai_p-video_0.mp4`.

## Pricing

Billed **per second of output video**:

| Resolution | Normal  | Draft mode |
| ---------- | ------- | ---------- |
| 720p       | $0.02/s | $0.005/s   |
| 1080p      | $0.04/s | $0.01/s    |

Reference costs:

- 5s @ 720p normal = **$0.10**
- 5s @ 720p draft = **$0.025**
- 10s @ 1080p normal = **$0.40**

This is among the cheapest video generation on Replicate. For rapid prompt iteration, default to `draft: true` and only turn it off for the final render.

## Strengths / notable fits

- Talking avatars, lip-sync, close-up subjects
- Product animation
- Short-form social content
- Rapid iteration (draft mode)

## Examples

**Text-to-video (draft):**

```bash
python scripts/run_model.py prunaai/p-video \
    --input '{
      "prompt": "a neon-lit tokyo alley with steam rising from a ramen stall",
      "duration": 5,
      "resolution": "720p",
      "draft": true
    }' \
    --output ./out/
```

**Image-to-video:**

```bash
python scripts/run_model.py prunaai/p-video \
    --input '{
      "prompt": "camera slowly pushes in, wind rustles leaves",
      "image": "./photo.jpg",
      "duration": 5
    }' \
    --output ./out/
```

**Audio-to-video (lip-sync style):**

```bash
python scripts/run_model.py prunaai/p-video \
    --input '{
      "prompt": "a friendly presenter in a bright studio speaking to camera",
      "image": "./presenter.jpg",
      "audio": "./voiceover.mp3"
    }' \
    --output ./out/
```

## Gotchas

- `disable_safety_filter` defaults to `true` — generations are unfiltered by default. Set it to `false` if you need safety checks (e.g. for user-submitted prompts).
- `duration` is silently ignored when you pass `audio` — the output tracks the audio length.
- `aspect_ratio` is silently ignored when you pass `image` — taken from the image dimensions.
- Draft mode is noticeably lower quality; fine for blocking out a shot, not for finals.
