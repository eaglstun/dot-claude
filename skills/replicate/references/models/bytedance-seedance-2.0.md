# bytedance/seedance-2.0

Model page: <https://replicate.com/bytedance/seedance-2.0>

ByteDance's flagship multimodal video generator — text-to-video and image-to-video in one endpoint, up to 15 seconds, with **native synchronized audio** (dialogue, SFX, music), multimodal reference inputs (images, video, audio), and first/last-frame control. Seedance 2.0 has been the skill's implied T2V default because it hits a rare sweet spot: prompt adherence and motion coherence close to premium models like `runwayml/gen-4.5`, at a fraction of the cost, with audio included rather than bolted on. Compare:

- `runwayml/gen-4.5` — often cited higher peak fidelity, but materially pricier per clip and slower; reach for it only when the shot demands it.
- `kwaivgi/kling-v3-omni-video` — richer mode set (multi-shot, reference video editing, character-reference prompts via `<<<image_1>>>` tokens) and comparable quality; Seedance wins on speed and raw T2V prompt adherence, Kling wins on multi-shot narrative and character consistency across shots.
- `vidu/q3-pro` — direct peer on price/quality, adds 1080p and explicit start-end-frame morphs; good cross-check for a second take.
- `pixverse/pixverse-v6` — cheap/fast draft tier (~$0.05/s at 360p); iterate prompts there, finalize on Seedance.
- `lightricks/ltx-video` — fastest open-source baseline; use when latency or self-host matters more than fidelity.
- `bytedance/seedance-2.0-fast` — sibling on the same account, explicitly a "faster variant" of 2.0. Use when throughput matters; fall back to `seedance-2.0` for the final pass. (No `seedance-2.0-pro` / `-lite` exist; the 1.0 generation is superseded.)

**Honest verdict:** Seedance 2.0 remains a defensible default T2V pick — it's the only model in the skill's current lineup that bundles (a) native audio on by default, (b) up to 15s duration, (c) 7-plus aspect-ratio options including `adaptive` and `21:9`, and (d) a single unified mode for T2V + I2V + start-last-frame + reference-image/video/audio. Kling v3 Omni is the stronger pick when you need multi-shot narrative or character consistency across shots. Gen 4.5 is the stronger pick when peak fidelity outweighs cost. For everything else — the one-slug default when you don't know which model to pick — Seedance 2.0 still earns it.

## Modes (inferred from which inputs are set)

| Mode                        | How to trigger                                                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Text-to-video**           | Just a `prompt` (+ optional `aspect_ratio`). No images / reference media.                                                     |
| **Image-to-video**          | Set `image` (first frame). `aspect_ratio` is effectively taken from the image; use `"adaptive"` explicitly to be safe.        |
| **First-last-frame morph**  | Set both `image` and `last_frame_image`. Model interpolates between the two keyframes.                                        |
| **Reference-based**         | Set `reference_images` (up to 9). Refer to them in the prompt as `[Image1]`, `[Image2]`, etc. Mutually exclusive with frames. |
| **Video-referenced**        | Set `reference_videos` (up to 3, total ≤15s). Reference in prompt as `[Video1]`, `[Video2]`. For motion/style transfer.       |
| **Audio-driven / lip-sync** | Set `reference_audios` (up to 3, total ≤15s). Requires at least one reference image or video. Refer as `[Audio1]` etc.        |

## Input schema

| Field              | Type          | Required | Default  | Description                                                                                                                      |
| ------------------ | ------------- | -------- | -------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`           | string        | yes      | —        | Text prompt. Dialogue inside `"double quotes"` is spoken when `generate_audio` is true.                                          |
| `image`            | string (URI)  |          | —        | First-frame image for image-to-video. Mutually exclusive with `reference_images` / `reference_videos`.                           |
| `last_frame_image` | string (URI)  |          | —        | Last-frame image. Only valid together with `image`. Mutually exclusive with reference inputs.                                    |
| `reference_images` | array of URIs |          | `[]`     | Up to 9 images for character consistency / style / scene composition. Referenced in prompt as `[Image1]`, `[Image2]`, etc.       |
| `reference_videos` | array of URIs |          | `[]`     | Up to 3 videos, total duration ≤15s, for motion transfer / style reference / editing. Referenced as `[Video1]`, `[Video2]`, etc. |
| `reference_audios` | array of URIs |          | `[]`     | Up to 3 audio clips, total ≤15s, for audio-driven generation and lip-sync. Requires at least one reference image or video.       |
| `duration`         | integer       |          | `5`      | Seconds. Range 1–15. Set to `-1` for intelligent duration (model picks best length based on inputs).                             |
| `resolution`       | enum          |          | `"720p"` | One of `480p`, `720p`, `1080p`.                                                                                                  |
| `aspect_ratio`     | enum          |          | `"16:9"` | One of `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, `9:21`, `adaptive`. Use `adaptive` to let the model choose from inputs.      |
| `generate_audio`   | boolean       |          | `true`   | Native synchronized audio (dialogue from quoted prompt text, SFX, music). Turn off for silent video.                             |
| `seed`             | integer       |          | random   | For reproducible generation.                                                                                                     |

No `negative_prompt` field. No explicit `fps` or camera-control fields — camera movement is prompt-driven only (describe it: "slow dolly-in", "orbit shot", "locked-off wide").

Local file paths for `image` / `last_frame_image` / `reference_images` / `reference_videos` / `reference_audios` are auto-uploaded by `run_model.py`.

## Output

A single URI to the generated video (MP4). Saved as `bytedance_seedance-2.0_0.mp4`.

## Pricing

Replicate does not publish per-second pricing on the model page or README (as of this reference). Use the playground price estimator before committing to a final run. As a rough calibration point, the official default example (7s, 720p, 16:9, audio on) completed in ~115s of predict time, suggesting a clip cost in the same order of magnitude as `vidu/q3-pro` at 720p ($0.15/s → ~$0.75 for 5s, ~$1.50 for 10s, ~$2.25 for 15s) — but verify this on the page before billing decisions. Audio on/off does not appear to be a separate line item on this model (unlike `pixverse/pixverse-v6`).

For high-volume iteration, draft on `pixverse/pixverse-v6` at 540p (~$0.35/5s) and promote winning prompts to Seedance 2.0 at `720p` — or use the `bytedance/seedance-2.0-fast` sibling for throughput-sensitive work.

## Examples

**Basic text-to-video** (default 5s, 720p, 16:9, audio on — the canonical "just run it" invocation):

```json
{
  "prompt": "a lone astronaut walking across a neon-lit martian plain at dusk, wide cinematic shot, slow dolly-in, dust drifting across the camera",
  "duration": 5,
  "resolution": "720p",
  "aspect_ratio": "16:9"
}
```

```bash
python scripts/run_model.py bytedance/seedance-2.0 --input-file input.json --output ./out/
```

**Image-to-video from a start frame** (animate a still, silent, 8s vertical):

```json
{
  "prompt": "camera slowly pushes in, wind moves the curtains, soft shafts of morning light",
  "image": "./room.jpg",
  "duration": 8,
  "aspect_ratio": "adaptive",
  "generate_audio": false
}
```

```bash
python scripts/run_model.py bytedance/seedance-2.0 --input-file input.json --output ./out/
```

**Longer clip with native audio and dialogue** (15s, 1080p, quoted dialogue is spoken):

```json
{
  "prompt": "close-up on a grizzled detective leaning against a rain-streaked alley wall, neon reflections in the puddles. He exhales, looks into the camera and says, \"I told you we'd find him here.\" Distant thunder, a car horn, jazz bleeding from a doorway down the block.",
  "duration": 15,
  "resolution": "1080p",
  "aspect_ratio": "21:9",
  "generate_audio": true
}
```

```bash
python scripts/run_model.py bytedance/seedance-2.0 --input-file input.json --output ./out/
```

## Strengths / gotchas

**Good at:**

- Prompt adherence and motion coherence — subjects stay on-model and physics-plausible through 10s+ clips better than most non-premium peers.
- Native synchronized audio on by default — dialogue (from `"quoted text"` in the prompt), SFX, and ambient music in one pass, no second-stage audio model needed.
- Intelligent duration (`duration: -1`) when you don't want to commit to a length up front.
- Wide aspect-ratio menu including `21:9` / `9:21` cinematic and `adaptive` — unusual in this tier.
- Multimodal reference inputs in a single model: images, videos, and audio clips, with positional tokens (`[Image1]`, `[Video1]`, `[Audio1]`) in the prompt.
- First-last-frame morphs via `image` + `last_frame_image`.

**Gotchas:**

- Text rendering inside the frame (signs, titles, on-screen captions) is unreliable — not a strength; prefer `pixverse/pixverse-v6` or post-overlay if readable text matters.
- `image` / `last_frame_image` are **mutually exclusive** with `reference_images` / `reference_videos` — pick frame-driven mode **or** reference-driven mode, not both.
- `reference_audios` **requires** at least one reference image or video — audio alone won't work.
- `reference_videos` and `reference_audios` each cap at total duration ≤15s combined; exceeding it will 422.
- `duration` max is 15s; don't expect longer continuous shots. For longer narratives, use `kwaivgi/kling-v3-omni-video` multi-shot or stitch multiple Seedance clips.
- Camera control is prompt-driven only — no explicit pan/orbit/zoom parameters. Be descriptive ("slow crane up", "handheld tracking shot").
- `aspect_ratio` is only honored cleanly in text-to-video; with an `image` input, prefer `"adaptive"` to avoid surprise letterboxing.
- Predict time is non-trivial (≈15–20s per second of output at 720p in the default example); warn the user on 15s / 1080p runs.
- Dialogue is extracted from `"double-quoted"` spans in the prompt — if you don't want spoken lines, don't quote, or set `generate_audio: false`.
- Peak fidelity on complex human faces / hands still trails `runwayml/gen-4.5`; for hero shots where face quality matters most, cross-check against Gen 4.5.
