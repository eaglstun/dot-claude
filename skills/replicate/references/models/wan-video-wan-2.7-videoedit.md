# wan-video/wan-2.7-videoedit

Model page: https://replicate.com/wan-video/wan-2.7-videoedit

Alibaba's **Wan 2.7 VideoEdit** — natural-language editing of an existing video. Unlike text-to-video (which generates from scratch), this takes a source clip and applies an instruction while preserving the underlying motion and structure. Good for the "same shot, different [background/lighting/outfit/weather/style]" pattern.

## What it's good for

- Background swap ("replace the city with a forest")
- Lighting / time-of-day shifts ("make it golden hour", "add dramatic rim light")
- Style transfer ("make it look like a watercolor", "1970s film stock")
- Clothing / appearance tweaks ("change the jacket to red leather")
- Add/remove small objects or weather effects

## What it struggles with

- Complex spatial rearrangements (moving subjects across the frame)
- Detailed facial changes (identity swaps, fine expressions)
- Physics-based modifications (realistic water, breaking glass)
- Long clips — **sweet spot is 2–5 seconds**; 2–10s is the hard range.

## Input schema

| Field             | Type         | Required | Default       | Description                                                                                               |
| ----------------- | ------------ | -------- | ------------- | --------------------------------------------------------------------------------------------------------- |
| `video`           | string (URI) | ✅       | —             | Input video (mp4/mov, 2–10s).                                                                             |
| `prompt`          | string       | ✅       | —             | Editing instructions or style description.                                                                |
| `reference_image` | string (URI) |          | —             | Optional reference image (jpg/png/bmp/webp) to guide the edit — e.g. a reference outfit or color palette. |
| `resolution`      | enum         |          | `"1080p"`     | One of `720p`, `1080p`.                                                                                   |
| `aspect_ratio`    | enum         |          | `"auto"`      | `auto`, `16:9`, `9:16`, `1:1`, `4:3`, `3:4`. `auto` keeps the input's ratio.                              |
| `duration`        | integer      |          | matches input | Seconds, range 2–10. Use to truncate a longer input.                                                      |
| `audio_setting`   | enum         |          | `"auto"`      | `auto` (model regenerates if appropriate) or `origin` (keep original audio verbatim).                     |
| `seed`            | integer      |          | random        | For reproducibility. Range: 0–2147483647.                                                                 |

Local `video` and `reference_image` paths are auto-uploaded by `run_model.py`.

## Output

Single URI to the edited video (MP4). Saved as `wan-video_wan-2.7-videoedit_0.mp4`.

## Examples

**Background swap:**

```bash
python scripts/run_model.py wan-video/wan-2.7-videoedit \
    --input '{
      "video": "./talking_head.mp4",
      "prompt": "replace the background with a sunlit beach and gentle waves, keep the subject unchanged",
      "resolution": "1080p",
      "audio_setting": "origin"
    }' \
    --output ./out/
```

**Style transfer with reference image:**

```bash
python scripts/run_model.py wan-video/wan-2.7-videoedit \
    --input '{
      "video": "./source.mp4",
      "prompt": "match the color palette and lighting of the reference",
      "reference_image": "./wes_anderson_still.jpg"
    }' \
    --output ./out/
```

**Time-of-day shift, truncated to 4s:**

```bash
python scripts/run_model.py wan-video/wan-2.7-videoedit \
    --input '{
      "video": "./daytime_street.mp4",
      "prompt": "convert the scene to golden-hour sunset with long shadows and warm tones",
      "duration": 4
    }' \
    --output ./out/
```

## Audio behavior

- `origin` — keeps the source audio exactly. Use this for talking-head edits where you don't want lip drift or audio changes.
- `auto` — lets the model re-generate audio if the edit implies it (e.g. a big environmental change). Can introduce artifacts; prefer `origin` for dialogue.

## Workflow tips

- **Keep clips short.** 2–5s edits are dramatically cleaner than 8–10s.
- **Iterate.** Because it preserves motion, you can run several passes stacking edits (swap background → then restyle → then relight) — each round is a fresh call with the previous output as the new `video`.
- **Use `reference_image`** whenever you have a concrete visual target. Describing "make it look like [famous film]" often works worse than providing a still frame from that film.
- **Preserve identity** by phrasing prompts as "change X, keep the subject unchanged" — the model responds well to explicit preservation hints.

## Not on the page

Pricing isn't shown on the model page. Check replicate.com/wan-video/wan-2.7-videoedit for current rates before running batches.
