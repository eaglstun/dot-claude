# kwaivgi/kling-v3-omni-video

Model page: https://replicate.com/kwaivgi/kling-v3-omni-video

Kling 3.0 Omni — one endpoint, four workflows: text-to-video, image-to-video (start frame, optionally with end frame), reference-based generation (up to 7 character/style images), and prompt-driven video editing of an existing clip. Also supports multi-shot composition (up to 6 shots) and native audio.

## Modes (inferred from which inputs are set)

| Mode                        | How to trigger                                                                                                       |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Text-to-video**           | Just a `prompt` (+ optional `aspect_ratio`).                                                                         |
| **Image-to-video**          | Set `start_image` (optionally also `end_image` for a first-last-frame morph).                                        |
| **Reference-based**         | Set `reference_images` (up to 7). Refer to them in the prompt via `<<<image_1>>>`, `<<<image_2>>>`, etc.             |
| **Video restyle** (feature) | Set `reference_video` with `video_reference_type: "feature"` — copies style/camera from the reference.               |
| **Video edit** (base)       | Set `reference_video` with `video_reference_type: "base"` — prompt-driven edit of the reference. `duration` ignored. |
| **Multi-shot**              | Pass `multi_prompt` JSON array (max 6 shots). Shot durations must sum to `duration`.                                 |

## Input schema

| Field                  | Type          | Required | Default     | Description                                                                                         |
| ---------------------- | ------------- | -------- | ----------- | --------------------------------------------------------------------------------------------------- |
| `prompt`               | string        | ✅       | —           | Text prompt. Max 2500 chars. Can embed `<<<image_1>>>` / `<<<video_1>>>` template refs.             |
| `mode`                 | enum          |          | `"pro"`     | `"standard"` = 720p, `"pro"` = 1080p.                                                               |
| `duration`             | integer       |          | `5`         | Seconds, range 3–15. Ignored when `video_reference_type: "base"` (editing).                         |
| `aspect_ratio`         | enum          |          | `"16:9"`    | One of `16:9`, `9:16`, `1:1`. Required unless `start_image` or video editing is used.               |
| `start_image`          | string (URI)  |          | —           | First frame. .jpg/.jpeg/.png, max 10MB, min 300px, aspect ratio between 1:2.5 and 2.5:1.            |
| `end_image`            | string (URI)  |          | —           | Last frame. Requires `start_image`. Same file constraints.                                          |
| `reference_images`     | array of URIs |          | —           | Character/scene/style references. Max 7 without a reference video, max 4 with one.                  |
| `reference_video`      | string (URI)  |          | —           | .mp4/.mov, duration 3–10s, 720–2160px per side, max 200MB.                                          |
| `video_reference_type` | enum          |          | `"feature"` | `"feature"` = style/camera ref, `"base"` = edit the reference video.                                |
| `generate_audio`       | boolean       |          | `false`     | Native audio generation. **Mutually exclusive with `reference_video`.**                             |
| `keep_original_sound`  | boolean       |          | `true`      | When using a reference video, preserve its audio track.                                             |
| `multi_prompt`         | string (JSON) |          | —           | JSON array of `{"prompt", "duration"}`. Max 6 shots, min 1s each, durations must sum to `duration`. |
| `negative_prompt`      | string        |          | —           | Content to exclude (documented in README, not in schema — may be accepted but not guaranteed).      |

Local file paths for `start_image` / `end_image` / `reference_images` / `reference_video` are auto-uploaded by `run_model.py`.

## Output

A single URI to the generated MP4. Saved as `kwaivgi_kling-v3-omni-video_0.mp4`.

## Pricing

Not published on the model page. Expect it to be in the same ballpark as other Kling v3 endpoints (~$0.25–$1+ per clip depending on mode and duration). Check the playground price estimate before running, and warn the user — a 15s pro run can take 9+ minutes (the default example took 549s) and cost meaningfully more than a short draft.

Iterate in `"standard"` mode (720p) at `duration: 5`, promote to `"pro"` (1080p) only for the final.

## Examples

**Text-to-video with native audio** (1080p, 8s):

```bash
python scripts/run_model.py kwaivgi/kling-v3-omni-video \
    --input '{
      "prompt": "a golden retriever surfing a wave at sunset, cinematic slow-motion, splashing water",
      "mode": "pro",
      "duration": 8,
      "aspect_ratio": "16:9",
      "generate_audio": true
    }' \
    --output ./out/
```

**Image-to-video from a start frame:**

```bash
python scripts/run_model.py kwaivgi/kling-v3-omni-video \
    --input '{
      "prompt": "camera pushes in slowly, wind moves the curtains",
      "start_image": "./room.jpg",
      "duration": 5,
      "mode": "standard"
    }' \
    --output ./out/
```

**Reference-based (character consistency)** — keep the same person across the shot:

```bash
python scripts/run_model.py kwaivgi/kling-v3-omni-video \
    --input '{
      "prompt": "<<<image_1>>> walks into a bustling night market, neon signs reflect off puddles",
      "reference_images": ["./character.jpg"],
      "duration": 6,
      "aspect_ratio": "9:16"
    }' \
    --output ./out/
```

**Multi-shot narrative** (must sum to `duration`):

```bash
python scripts/run_model.py kwaivgi/kling-v3-omni-video \
    --input '{
      "prompt": "scene beats below",
      "duration": 10,
      "multi_prompt": "[{\"prompt\": \"<<<image_1>>> opens a heavy wooden door\", \"duration\": 4}, {\"prompt\": \"<<<image_1>>> looks around the candlelit hall in awe\", \"duration\": 6}]",
      "reference_images": ["./hero.jpg"],
      "mode": "pro"
    }' \
    --output ./out/
```

**Video edit (base)** — prompt-driven restyle of an existing clip. `duration` is ignored; output length matches the reference:

```bash
python scripts/run_model.py kwaivgi/kling-v3-omni-video \
    --input '{
      "prompt": "repaint this scene in the style of a Studio Ghibli film, soft watercolor background",
      "reference_video": "./clip.mp4",
      "video_reference_type": "base",
      "keep_original_sound": true
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Character consistency across scenes via reference images (up to 7).
- Multi-shot composition in one generation (avoids manual stitching).
- Prompt-driven video editing of an existing clip (restyle, relight, outfit swap).
- Native audio when not using a reference video.

**Gotchas:**

- `generate_audio: true` is **mutually exclusive** with `reference_video` — pick one.
- `multi_prompt` shot durations must sum exactly to `duration`, otherwise 422.
- Reference video must be 3–10s and ≤200MB; reference images must be ≥300px.
- When a reference video is provided, `reference_images` is capped at 4 (not 7).
- `pro` mode at 15s is slow (~9 minutes) and expensive — iterate in `standard`.
- `<<<image_N>>>` / `<<<video_1>>>` template refs are positional — matches the order in the input array.
