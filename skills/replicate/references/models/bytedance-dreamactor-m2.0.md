# bytedance/dreamactor-m2.0

Model page: https://replicate.com/bytedance/dreamactor-m2.0

Motion / expression transfer: give it a **single image** of any subject (human, cartoon, animal, non-human character) plus a **driving video**, and it re-animates the subject with the driving video's motion, facial expressions, and lip movements. Learns directly from raw pixels — no skeletal pose estimation — so it works on non-humanoid characters.

## When to use

- Bring a still portrait, illustration, or character to life with a performance from another clip (acting, dance, dialogue).
- Retarget a driving performance onto a different character.
- Pseudo lip-sync: if the driving video is someone speaking, the subject's mouth follows.

For pure audio-driven lipsync (no driving video) use `heygen/lipsync-speed` or `zsxkib/multitalk` instead — this model needs a video reference, not an audio track.

## Input schema

| Field              | Type         | Required | Default  | Description                                                                                                            |
| ------------------ | ------------ | -------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| `image`            | string (URI) | ✅       | —        | Subject image. JPEG/JPG/PNG. Max 4.7 MB. Resolution 480×480 to 1920×1080.                                              |
| `video`            | string (URI) | ✅       | —        | Driving video (supplies motion + expression + lip movement). MP4/MOV/WebM. Max 30s. Resolution 200×200 to 2048×1440.   |
| `cut_first_second` | boolean      |          | `true`   | Crops the first second of output (removes a 1-second transition at the start). Leave `true` unless you need full length. |

Local paths for `image` / `video` are auto-uploaded by `run_model.py`.

## Output

A single URI to the generated MP4. Saved as `bytedance_dreamactor-m2.0_0.mp4`.

## Pricing

Not published on the model page. Runtime for the default 30s driving clip is ~3.5 minutes (default example: 214s). Check the playground price estimate before running, and warn the user.

## Examples

**Animate a portrait with a driving performance:**

```bash
python scripts/run_model.py bytedance/dreamactor-m2.0 \
    --input '{
      "image": "./portrait.jpg",
      "video": "./actor_performance.mp4"
    }' \
    --output ./out/
```

**Animate a cartoon with dance motion, keep the full output length:**

```bash
python scripts/run_model.py bytedance/dreamactor-m2.0 \
    --input '{
      "image": "./cartoon.png",
      "video": "./dance.mp4",
      "cut_first_second": false
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Non-humanoid subjects (animals, cartoons, props) — no pose-estimation assumption.
- Facial expression + lip transfer from the driving video.
- Temporal consistency (trained on raw pixels, less flicker than skeleton-based models).

**Gotchas:**

- Both `image` and `video` are required — no text-only mode.
- Driving video is capped at **30 seconds**; pre-trim if longer.
- Subject image must be 480×480 or larger — tiny thumbnails will fail.
- A multi-character subject image works but requires careful alignment with the driving video's framing; single clearly-posed subjects are more reliable.
- Output starts with a 1-second transition; `cut_first_second: true` (the default) removes it.
- For audio-only lipsync (no driving video) use a different model — this one requires video motion.
