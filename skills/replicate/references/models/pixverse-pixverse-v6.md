# pixverse/pixverse-v6

Model page: <https://replicate.com/pixverse/pixverse-v6>

PixVerse's flagship v6 video generator — cheap, fast text-to-video and image-to-video with optional native audio, multi-shot sequences, and first-last-frame transitions. Billed per second of output, starting at $0.05/s (360p, no audio). Positioned as a high-volume draft / iteration model: use it to lock in shot composition and prompt wording before promoting a final pass to something like `bytedance/seedance-2.0` (the skill's current default T2V — higher fidelity, higher $/clip) or `kwaivgi/kling-v3-omni-video` (premium multi-mode with character-reference support). Improvements over v5.6 emphasize cinematic camera control, character emotion, dynamic physics, native in-frame text rendering, and first-person POV; schema also gains `generate_multi_clip_switch` for cinematic multi-shot composition. For short throwaway drafts, v6 at 360p/5s is roughly an order of magnitude cheaper than the premium tier.

## Modes (inferred from which inputs are set)

| Mode                            | How to trigger                                                                                           |
| ------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Text-to-video**               | Just a `prompt` (+ optional `aspect_ratio`). No `image` or `last_frame_image`.                           |
| **Image-to-video**              | Set `image` (first frame). `aspect_ratio` is ignored — derived from the image.                           |
| **First-last-frame transition** | Set both `image` and `last_frame_image`. The model interpolates a motion path between the two keyframes. |
| **Multi-shot**                  | Set `generate_multi_clip_switch: true`. T2V or I2V only — not valid with `last_frame_image`.             |
| **With audio**                  | Set `generate_audio_switch: true` on any mode. Adds BGM, SFX, and dialogue. Pricier per second.          |

## Input schema

| Field                        | Type         | Required | Default  | Description                                                                                                                          |
| ---------------------------- | ------------ | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `prompt`                     | string       | ✅       | —        | Text prompt for video generation.                                                                                                    |
| `image`                      | string (URI) |          | —        | First-frame image. Presence switches to image-to-video mode.                                                                         |
| `last_frame_image`           | string (URI) |          | —        | Last-frame image for transition mode. Must be used together with `image`.                                                            |
| `quality`                    | enum         |          | `"540p"` | One of `360p`, `540p`, `720p`, `1080p`. Higher tiers cost more per second.                                                           |
| `aspect_ratio`               | enum         |          | `"16:9"` | One of `16:9`, `9:16`, `1:1`. Only used for text-to-video — ignored when `image` or `last_frame_image` is provided.                  |
| `duration`                   | integer      |          | `5`      | One of `5`, `8`, `10`, `15` seconds. Not a free range — pick one of the enum values.                                                 |
| `negative_prompt`            | string       |          | `""`     | Elements to avoid in the generated video.                                                                                            |
| `seed`                       | integer      |          | random   | Random seed for reproducible generation.                                                                                             |
| `generate_audio_switch`      | boolean      |          | `false`  | Enable AI-generated audio (BGM, SFX, character dialogue). Raises the per-second rate (see Pricing).                                  |
| `generate_multi_clip_switch` | boolean      |          | `false`  | Enable multi-shot generation for cinematic sequences with scene transitions. Text-to-video and image-to-video only (no transitions). |

Local image paths for `image` / `last_frame_image` are auto-uploaded by `run_model.py`.

## Output

A single URI to the generated video (MP4). Saved as `pixverse_pixverse-v6_0.mp4`.

## Pricing

Billed **per second of output video**, by resolution, with a surcharge when audio is on:

| Resolution | No audio | With audio | 5s (no audio / audio) | 15s (no audio / audio) |
| ---------- | -------- | ---------- | --------------------- | ---------------------- |
| 360p       | $0.05/s  | $0.07/s    | $0.25 / $0.35         | $0.75 / $1.05          |
| 540p       | $0.07/s  | $0.09/s    | $0.35 / $0.45         | $1.05 / $1.35          |
| 720p       | $0.09/s  | $0.12/s    | $0.45 / $0.60         | $1.35 / $1.80          |
| 1080p      | $0.18/s  | $0.23/s    | $0.90 / $1.15         | $2.70 / $3.45          |

Iterate on prompt wording at `quality: "360p"` or `"540p"` with audio off — under $0.50 per draft — then promote the winning prompt to `"1080p"` with audio for the final.

## Examples

**Text-to-video draft** (cheapest tier, 5s, 540p, no audio):

```json
{
  "prompt": "a lone astronaut walking across a neon-lit martian plain at dusk, wide cinematic shot, slow dolly-in",
  "quality": "540p",
  "duration": 5,
  "aspect_ratio": "16:9"
}
```

```bash
python scripts/run_model.py pixverse/pixverse-v6 --input-file input.json --output ./out/
```

**Image-to-video with audio** (animate a still, 720p, 8s, native SFX):

```json
{
  "prompt": "camera slowly pushes in, wind rustles the leaves, ambient forest audio",
  "image": "./photo.jpg",
  "quality": "720p",
  "duration": 8,
  "generate_audio_switch": true
}
```

```bash
python scripts/run_model.py pixverse/pixverse-v6 --input-file input.json --output ./out/
```

**Multi-shot cinematic** (T2V, 15s at 1080p, native audio, multi-clip):

```json
{
  "prompt": "Shot 1: extreme close-up of a mechanical watch movement, gears turning, warm golden light. Shot 2: a woman's wrist as she fastens the watch, slow deliberate motion. Shot 3: her face at golden hour on a misty mountain ridge, calm confident smile. Shot 4: she turns her wrist, watch face catches a sunbeam. Shot 5: aerial pull-back reveals her at the summit, cinematic orchestral swell.",
  "quality": "1080p",
  "duration": 15,
  "aspect_ratio": "16:9",
  "generate_audio_switch": true,
  "generate_multi_clip_switch": true
}
```

```bash
python scripts/run_model.py pixverse/pixverse-v6 --input-file input.json --output ./out/
```

## Strengths / gotchas

**Good at:**

- Cheap drafts — sub-$0.50 iteration loop at 540p is the main reason to reach for this over v5.6 or premium models.
- Native in-frame text rendering (new in v6) — signs, titles, UI overlays render more reliably than most competitors.
- Cinematic camera moves (dolly, crane, orbit) when described explicitly in the prompt.
- Multi-shot composition in a single call (`generate_multi_clip_switch`) — avoids manual stitching of 3–5 shots.
- First-last-frame transitions for morph effects.

**Gotchas:**

- `duration` is a **fixed enum** (`5`, `8`, `10`, `15`) — not a free integer. Other values 422.
- `aspect_ratio` is only `16:9` / `9:16` / `1:1` — no `4:3` or `3:4`.
- `generate_multi_clip_switch` is **not valid with `last_frame_image`** — the transition mode is single-shot only.
- In image-to-video, camera motion defaults to a slow push/drift — be explicit in the prompt if you want something else (pan, orbit, locked-off).
- `quality: "1080p"` with audio and 15s duration is the priciest combo (~$3.45/clip); reserve it for final passes.
- Audio generation uses the generic `generate_audio_switch` boolean — no fine-grained control over music style, dialogue language, or SFX mix.
- Prompt adherence is decent but not as tight as Kling v3 or Seedance 2.0 — for precise subject/action control, draft here and finalize there.
- The default `quality` is `540p`, not `720p` — double-check before assuming HD output.
