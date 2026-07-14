# luma/modify-video

Model page: <https://replicate.com/luma/modify-video>

Luma's **video style-transfer / prompt-based editing** model — feed in an existing clip and a prompt (plus an optional modified first frame), get back a re-rendered video that keeps the source motion but changes style, look, environment, or subject per the prompt. Three fidelity bands × three intensity levels give nine `mode` presets spanning "subtle polish" to "reimagine completely". Latest version: `de2d85dc...` (2025-11-07).

## When to pick this over alternatives

- **Pick it over `wan-video/wan-2.7-videoedit`** when you want a stronger stylistic departure — Wan's editor is tuned for subtle background swaps / relights and tends to fight prompts that ask for dramatic look changes. Luma's `reimagine_*` tier is purpose-built for "turn this live-action into anime" style moves.
- **Pick it over `kwaivgi/kling-v3-omni-video` in video-edit mode** when you have a modified **first frame** that shows what you want (Luma explicitly accepts a hand-edited first frame as a style anchor; Kling doesn't).
- **Skip it** when you need to preserve lip sync on a talking head (use `heygen/lipsync-speed`), when you need pixel-accurate foreground-only edits (use `arielreplicate/robust_video_matting` + compositing), or when your clip is longer than 30 seconds or bigger than 100 MB (hard limits).

## Input schema

| Field             | Type         | Required | Default      | Description                                                                                                                   |
| ----------------- | ------------ | -------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `video`           | string (URI) | yes      | —            | Source clip. **Max 100 MB, max 30 seconds.** Local paths are auto-uploaded by `run_model.py`.                                 |
| `prompt`          | string       | yes      | —            | Text guidance for the modification. Describe the _target_ look, not the source.                                               |
| `mode`            | enum         |          | `"adhere_1"` | How far the output can drift from the source. Nine values — see table below.                                                  |
| `first_frame`     | string (URI) |          | —            | Optional hand-modified first frame. The model uses it as a style anchor — powerful when a prompt alone isn't specific enough. |
| `video_url`       | string       |          | —            | **Deprecated.** Use `video`.                                                                                                  |
| `first_frame_url` | string       |          | —            | **Deprecated.** Use `first_frame`.                                                                                            |

### `mode` enum — nine presets

| Band      | Values                                      | Use when                                                                                          |
| --------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Adhere    | `adhere_1`, `adhere_2`, `adhere_3`          | Subtle enhancement — relight, grade, minor polish. Source stays recognisable beat-for-beat.       |
| Flex      | `flex_1`, `flex_2`, `flex_3`                | Style change while keeping recognizable subjects, framing, motion. The most useful middle ground. |
| Reimagine | `reimagine_1`, `reimagine_2`, `reimagine_3` | Dramatic transformation — medium/style swap (live-action → anime, film → painterly).              |

The numeric suffix within a band is intensity — `_1` lightest, `_3` strongest. Default `adhere_1` is the safest starting point; the default-example showcase uses `flex_1` for an "anime Ferrari" conversion.

## Output

**Bare URI string** — single `.mp4`. Saved as `luma_modify-video_0.mp4` by `run_model.py`.

## Pricing and runtime

Pricing not listed in schema — confirm on the model page. Expect premium tier (this is a Luma-official model). Default example took **~184 s** for a short clip; budget ~2–4× the source duration for processing, more for `reimagine_*` modes.

## Examples

**Anime-style restyle of a short car shot** — the default showcase. The `first_frame` is a still that's been hand-edited (or run through an image model) to establish the target look; Luma extends that look across the rest of the clip:

```json
{
  "video": "./ferrari_drive.mp4",
  "prompt": "make it anime",
  "mode": "flex_1",
  "first_frame": "./ferrari_drive_anime_frame0.png"
}
```

```bash
python scripts/run_model.py luma/modify-video \
    --input-file input.json \
    --output ./out/
```

**Subtle grade / relight** — no first-frame anchor, just a prompt:

```json
{
  "video": "./interview.mp4",
  "prompt": "warmer golden hour lighting, softer skin tones, shallow film-like depth of field",
  "mode": "adhere_2"
}
```

**Dramatic medium swap** — convert live-action to an illustrated look at the strongest setting:

```json
{
  "video": "./skateboard_run.mp4",
  "prompt": "ink and watercolor illustration, Studio Ghibli palette, paper grain",
  "mode": "reimagine_3"
}
```

## Strengths / gotchas

**Good at:**

- Full-clip style transfer with coherent motion (the model keeps source motion intact even in `reimagine` modes)
- Taking a hand-modified first frame as a style anchor — by far the most controllable pattern
- Subtle grades and relights via `adhere_*` without degrading subjects

**Gotchas:**

- **Hard limits: 100 MB / 30 s.** Clips above either will fail. Pre-compress (`ffmpeg -crf 28`) or trim before submitting.
- **Long wall time.** Default-example ran ~3 minutes for a short clip. Budget accordingly — this is not a fast-iteration model.
- **Mode choice is the single biggest quality lever.** Start on `adhere_1`, then push to `flex_1` / `flex_2`, then `reimagine_*`. Skipping straight to `reimagine_3` without a first frame often garbles the subject.
- **First-frame images dominate style when supplied.** If the first-frame's look disagrees with the prompt, the image wins. Align the two or drop the first frame entirely.
- **Deprecated URL fields.** `video_url` and `first_frame_url` still work but are marked deprecated — use `video` / `first_frame` in new calls. Local paths are fine; `run_model.py` uploads them.
- **Not a lipsync tool.** For talking heads keep lip motion via `heygen/lipsync-speed` or `wan-video/wan-2.7-videoedit` with `audio_setting: "origin"` — Luma can drift the mouth under aggressive `reimagine_*`.
- **No explicit seed.** Results aren't reproducible across identical calls — budget 2–3 attempts to land a keeper.
- **Pinned version safe.** Latest version id is `de2d85dcc392377a811cf6cda8f2b2b862548954363551b9cf27383ba04aed94` — pin it if you need byte-reproducible behavior, since Luma updates will rotate the bare slug target.
