# minimax/video-01-director

Model page: <https://replicate.com/minimax/video-01-director>

MiniMax Video-01 with an explicit **"director" mode** — the prompt parser recognises bracketed camera-movement directives like `[Push in]`, `[Pan left]`, `[Zoom out]`, `[Tilt up]`, and executes them as deterministic camera control rather than leaving it to natural-language interpretation. Think of it as storyboard-style direction: you write scene description in plain English and annotate camera ops inside square brackets.

**When to reach for this over siblings in the skill:**

- `minimax/hailuo-2.3` — current default for text/image-to-video. Better overall motion and prompt following, but camera control is purely linguistic ("the camera pushes in slowly…") and therefore fuzzier.
- `kwaivgi/kling-v3-omni-video` — supports multi-shot composition via `multi_prompt`, but has no named camera-op vocabulary.
- `bytedance/seedance-2.0` — top-tier fidelity and audio, no director syntax.
- **`minimax/video-01-director`** — pick this when you need a specific, repeatable camera move (bullet-time orbit, vertigo pull-out, rising crane) and don't want to roll the dice on prose interpretation.

Fixed output: **720p, 25fps, up to 6s**. Single clip, no audio.

## Input schema

| Field               | Type         | Required | Default | Description                                                                                                                   |
| ------------------- | ------------ | -------- | ------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `prompt`            | string       | yes      | —       | Scene description. Embed camera directives in square brackets (see Director tags). Up to 3 combined movements per prompt.     |
| `first_frame_image` | string (URI) |          | —       | Optional start frame. Presence switches to image-to-video (I2V-01-Director). Output aspect ratio is inherited from the image. |
| `prompt_optimizer`  | boolean      |          | `true`  | MiniMax server-side prompt rewriting. Leave on unless you want your exact wording preserved verbatim.                         |

Local file paths for `first_frame_image` are auto-uploaded by `run_model.py`.

There is **no** `duration`, `aspect_ratio`, `resolution`, or `seed` field — this endpoint intentionally exposes a minimal surface. Aspect ratio comes from the first frame image (I2V) or defaults to 16:9 (T2V).

### Supported director tags

Wrap tags in `[ ]`. Combine up to **three** movements with commas inside one bracket group: `[Truck left, Pan right, Zoom in]`.

| Axis       | Tags                                                           |
| ---------- | -------------------------------------------------------------- |
| Horizontal | `[Truck left]`, `[Truck right]`, `[Pan left]`, `[Pan right]`   |
| Vertical   | `[Pedestal up]`, `[Pedestal down]`, `[Tilt up]`, `[Tilt down]` |
| Depth      | `[Push in]`, `[Pull out]`, `[Zoom in]`, `[Zoom out]`           |
| Special    | `[Tracking shot]`, `[Shake]`, `[Static shot]`                  |

**Truck vs Pan**: truck translates the camera body left/right; pan rotates it in place. **Pedestal vs Tilt**: pedestal translates the camera body up/down; tilt rotates it. **Push/Pull vs Zoom**: push/pull dollies the camera physically through space; zoom changes focal length with the camera stationary. These distinctions matter — the model respects them.

For sequential moves across the shot, place separate bracket groups at different points in the prompt text (e.g. `[Push in] hero opens the door [Pan right] revealing the ballroom`).

## Output

A single URI pointing to an MP4. `run_model.py` saves it as `minimax_video-01-director_0.mp4`.

## Pricing

Not published on the model page or on the generic Replicate pricing page at time of writing. The base `minimax/video-01` endpoint (same underlying model, no director parser) historically ran around **$0.50 per generation** — expect director mode to be priced the same or within a few cents. Check the playground estimate before bulk runs. (Guessed — confirm in the playground.)

## Examples

**Text-to-video with combined director tags** (bullet-time orbit):

```bash
python scripts/run_model.py minimax/video-01-director \
    --input '{
      "prompt": "[Push in, Pan left] a lone samurai standing in a bamboo grove at dawn, mist curling around his feet, bullet-time effect",
      "prompt_optimizer": true
    }' \
    --output ./out/
```

**Image-to-video with a first frame** (vertigo pull-out on a portrait):

```bash
python scripts/run_model.py minimax/video-01-director \
    --input '{
      "prompt": "[Pull out, Zoom in] subject remains fixed in the center, background rushes away, dolly-zoom effect",
      "first_frame_image": "./portrait.jpg"
    }' \
    --output ./out/
```

**Sequential moves across the shot:**

```bash
python scripts/run_model.py minimax/video-01-director \
    --input '{
      "prompt": "[Static shot] a small wooden door in a stone wall, then it creaks open [Push in] revealing a candlelit hall [Tilt up] showing a vaulted ceiling painted with constellations",
      "prompt_optimizer": false
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- Reproducible, named camera moves — the single biggest reason to pick this model.
- Pairing a specific directive with a first-frame image for controlled product/portrait shots.
- Combining up to 3 movements simultaneously via comma syntax inside one bracket group.

**Gotchas:**

- **Tag syntax is strict.** The parser expects the exact vocabulary above. `[zoom]` alone won't match — it needs a direction (`[Zoom in]` or `[Zoom out]`). Typos or unknown verbs are silently ignored and fall back to natural-language interpretation.
- **Bracketed words elsewhere in the prompt are at risk.** If you write `[dramatic]` or `[slow-mo]` thinking it's emphasis, the parser may attempt to match it as a directive and fail. Keep bracket groups reserved for director tags only.
- **Disambiguation:** a bare word like "pan" in narrative prose (e.g. "a frying pan on the stove") is treated as text, not a camera op. Only `[Pan left]` / `[Pan right]` inside brackets are directives. Similarly, "truck" in prose ≠ `[Truck left]`.
- **Three-movement cap.** Four or more combined moves in one bracket group degrade quality — split them into two bracket groups at different points in the prompt.
- **6-second hard ceiling, no `duration` knob.** If you need longer, run multiple clips and stitch, or use `kwaivgi/kling-v3-omni-video` / `vidu/q3-pro`.
- **No audio.** Pair with a TTS or music model if you need a soundtrack.
- **No `seed` parameter** — runs are not deterministic across calls even with identical inputs.
- **`prompt_optimizer: true`** (the default) may rewrite your prompt and occasionally strip or reformat director tags. If a tag is being ignored, try `prompt_optimizer: false`.
