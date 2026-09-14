# arielreplicate/robust_video_matting

Model page: https://replicate.com/arielreplicate/robust_video_matting

**Robust Video Matting (RVM)** — extracts the foreground (subject) from a video without requiring a background reference. Uses a recurrent network with temporal memory, so edges stay stable frame-to-frame (unlike naive per-frame segmentation). **Trained for people** specifically; results on animals or arbitrary objects are less reliable.

## Input schema

| Field         | Type         | Required | Default          | Description                                             |
| ------------- | ------------ | -------- | ---------------- | ------------------------------------------------------- |
| `input_video` | string (URI) | ✅       | —                | Video to segment.                                       |
| `output_type` | enum         |          | `"green-screen"` | One of `green-screen`, `alpha-mask`, `foreground-mask`. |

Local video paths are auto-uploaded by `run_model.py`.

## Output types — what you get back

| Mode              | Output                                                     | Use for                                                          |
| ----------------- | ---------------------------------------------------------- | ---------------------------------------------------------------- |
| `green-screen`    | The subject composited over solid green (chroma-key ready) | Drop into editors (Premiere, Resolve, DaVinci) and key out green |
| `alpha-mask`      | Grayscale video: white = subject, black = background       | Use as an alpha channel in compositing (After Effects, ffmpeg)   |
| `foreground-mask` | The subject with alpha, background removed (RGBA)          | Direct use in compositing without a separate alpha pass          |

If you're unsure: `green-screen` is the most compatible for non-technical editors; `foreground-mask` is the cleanest for programmatic compositing.

## Output

Single URI to the processed video. Saved as `arielreplicate_robust_video_matting_0.mp4` (or `.webm` / similar depending on encoding).

## Pricing and runtime

- **~$0.034 per run** (flat, not per-second)
- **~35 seconds** typical runtime
- Runs on Nvidia L40S
- Supports HD (1920×1080) and 4K (3840×2160)

Cheap enough to be a default preprocessing step in a pipeline.

## Examples

**Default green-screen output:**

```bash
python scripts/run_model.py arielreplicate/robust_video_matting \
    --input '{"input_video": "./person_talking.mp4"}' \
    --output ./out/
```

**Alpha mask only (for use as transparency in compositing):**

```bash
python scripts/run_model.py arielreplicate/robust_video_matting \
    --input '{
      "input_video": "./person_talking.mp4",
      "output_type": "alpha-mask"
    }' \
    --output ./out/
```

**Subject with transparent background (foreground-only):**

```bash
python scripts/run_model.py arielreplicate/robust_video_matting \
    --input '{
      "input_video": "./person_talking.mp4",
      "output_type": "foreground-mask"
    }' \
    --output ./out/
```

## Typical pipelines

**Swap the background of a video:**

1. Run with `output_type: "foreground-mask"` → get `subject.mp4` with transparency.
2. Overlay onto a new background with `ffmpeg`:
   ```bash
   ffmpeg -i new_bg.mp4 -i subject.mp4 -filter_complex "[0][1]overlay" out.mp4
   ```

**Composite a person into a generated scene:**

1. Generate a background with a video model (e.g. `bytedance/seedance-2.0`).
2. Matte the person with RVM (`green-screen`).
3. Chroma-key and overlay in your editor.

## Gotchas

- **Trained on people.** Animals, cars, and arbitrary objects work sometimes but not reliably — don't expect production-quality mattes on non-human subjects.
- **Fine edges (hair, fur, fabric fringe)** can flicker on fast motion. This is an inherent limitation of video matting; consider a precision model for hero shots.
- **Input codec matters.** Weird containers/codecs may fail; re-encode to standard H.264 MP4 first if you hit issues.
- No background-reference input — if you have a static reference background available, a background-aware matting model (e.g. `pengbomb/robust-background-matting`) may give cleaner edges.
