# luma/reframe-video

Model page: <https://replicate.com/luma/reframe-video>

Luma's **aspect-ratio reframing** model — takes a video shot in one aspect ratio and rebuilds it in another (16:9 → 9:16, 4:3 → 21:9, etc.) without simple cropping or letterboxing. It uses generative outpainting to extend the frame naturally, preserving the subject and motion while filling in the sides or top/bottom with plausible continuation of the scene. Latest version: `7a27619c...` (2025-11-07). ~47k runs — one of Luma's most-used models on Replicate.

## When to pick this over alternatives

- **Pick it over `ffmpeg crop` / `ffmpeg pad`** when the source has subject motion near the edges and you can't afford to crop, or when you need to go from narrow to wide (9:16 → 16:9) and plain padding would leave ugly black bars.
- **Pick it over `wan-video/wan-2.7-videoedit`** for pure aspect-ratio changes — Wan's video editor is prompt-driven style/content modification, not purpose-built outpainting. Luma's reframe is faster for the aspect-ratio-only use case.
- **Pick it over regenerating** (T2V re-roll) when you want to preserve the original performance/motion exactly and only change the frame shape around the action.
- **Skip it** if you only need a simple static crop — ffmpeg is free and instant. Reframe is for the cases where the crop loses something important or the target aspect is _wider_ than the source.

## Input schema

| Field             | Type         | Required | Default  | Description                                                                                                                                |
| ----------------- | ------------ | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `video`           | string (URI) | yes\*    | —        | Source video. **Schema says max 10 s** (contradicts the top-of-page 30 s claim — assume 10 s is correct).                                  |
| `aspect_ratio`    | enum         |          | `"16:9"` | Target aspect ratio: `1:1`, `3:4`, `4:3`, `9:16`, `16:9`, `9:21`, `21:9`.                                                                  |
| `prompt`          | string       |          | —        | Optional guidance for the outpainted regions (e.g. "a clean podcast studio background"). Helps steer what fills the extension.             |
| `x_start`         | integer      |          | —        | Left boundary (pixels) where the source will be placed inside the output frame. Paired with `x_end` to set resized width.                  |
| `x_end`           | integer      |          | —        | Right boundary (pixels). Distance from `x_start` = resized source width.                                                                   |
| `y_start`         | integer      |          | —        | Top boundary (pixels).                                                                                                                     |
| `y_end`           | integer      |          | —        | Bottom boundary (pixels). Distance from `y_start` = resized source height.                                                                 |
| `grid_position_x` | integer      |          | —        | Horizontal pixel position of the source inside the target frame. Alternative to `x_start`/`x_end` when you just want to shift, not resize. |
| `grid_position_y` | integer      |          | —        | Vertical pixel position of the source inside the target frame.                                                                             |
| `video_url`       | string       |          | —        | **Deprecated.** Use `video`.                                                                                                               |

\* `video` isn't listed as formally required in the schema but the call fails without it — `video_url` is accepted as the legacy fallback.

### Placement controls

You've got two ways to control where the source sits inside the new frame:

- **Bounds mode** (`x_start` / `x_end` / `y_start` / `y_end`): specify the exact pixel rectangle inside the target frame where the resized source should land. The model outpaints everything else. Gives fine-grained control for asymmetric layouts (e.g. "put the subject on the left third, outpaint a right-side panel").
- **Grid mode** (`grid_position_x` / `grid_position_y`): just shift the source to a position in the target frame without resizing. Simpler, works for common cases.

Omit both sets for default centered placement.

## Output

**Bare URI string** — single `.mp4` at **720p** (output resolution is not configurable). Saved as `luma_reframe-video_0.mp4` by `run_model.py`.

## Pricing and runtime

Pricing not in schema — confirm on the model page. Expect premium (Luma-official). Default example (9:16 reframe of a podcast clip) predicted in **~69 s**. Budget ~1–3× real-time on typical inputs.

## Examples

**16:9 → 9:16 (landscape → vertical)** — the canonical podcast-to-shorts use case:

```json
{
  "video": "./podcast_landscape.mp4",
  "aspect_ratio": "9:16",
  "prompt": "a woman standing in a podcast studio, soft warm lighting, clean backdrop"
}
```

```bash
python scripts/run_model.py luma/reframe-video \
    --input-file input.json \
    --output ./out/
```

**9:16 → 16:9 with bounds** — phone clip into a wide canvas, placing the source on the left third:

```json
{
  "video": "./phone_clip.mp4",
  "aspect_ratio": "16:9",
  "prompt": "continuation of the background environment, natural extension",
  "x_start": 0,
  "x_end": 427,
  "y_start": 0,
  "y_end": 720
}
```

**Square → wide (1:1 → 21:9)** — cinematic letterbox effect without bars:

```json
{
  "video": "./square_clip.mp4",
  "aspect_ratio": "21:9",
  "prompt": "cinematic scene continuation, film grain, warm cinematography"
}
```

## Strengths / gotchas

**Good at:**

- Vertical-to-horizontal and horizontal-to-vertical conversions where simple crops would cut off the subject
- Outpainting plausible background extensions (walls, sky, interior continuations)
- Preserving source motion exactly — no re-rendering of the subject, only the generated outer regions

**Gotchas:**

- **10 s hard cap.** The schema field description says max 10 seconds, even though the top-line description says 30. Treat 10 s as the real limit — longer inputs silently truncate or fail.
- **720p-only output.** No resolution knob. If you need 1080p or 4K, run `topazlabs/video-upscale` as a post-process.
- **Outpainted regions aren't frame-perfect consistent.** Over time the generated side panels can shift or shimmer — worse on cluttered backgrounds, fine with plain walls/sky. Keep it short (≤6 s) if flicker matters.
- **Provide a prompt when extending into ambiguous space.** Without a prompt, Luma guesses what should fill the outpaint; results get weird on abstract or confusing backgrounds. Even one sentence ("podcast studio, warm lighting") dramatically improves coherence.
- **`bounds` vs `grid` modes are mutually exclusive in practice.** Passing both confuses the placement — pick one path.
- **Deprecated `video_url`.** Still works; use `video` in new code.
- **Subjects near edges get recomposed awkwardly.** If the source already has important action at the very edge of frame, reframe will sometimes extend that motion implausibly. Pre-trim so the subject sits centrally.
- **Not a resolution upscaler.** If your source is already lower than 720p, output will be 720p-upscaled but muddy. Upscale first (`topazlabs/video-upscale`) if the source is <720p.
- **Version pin:** `luma/reframe-video:7a27619ccb64e4f1942e9a53e503142be08d505587313afa1da037b631a6760e` — pin for reproducibility since Luma rotates bare-slug targets on updates.
