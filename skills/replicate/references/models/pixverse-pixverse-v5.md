# pixverse/pixverse-v5

Model page: <https://replicate.com/pixverse/pixverse-v5>

PixVerse v5 — the generation before v6. Create 5s or 8s videos with "enhanced character movement, visual effects, and exclusive 1080p-8s support. Optimized for anime characters and complex actions." Billed by **Replicate unit** (not $/second), with base units scaled by resolution and doubled for 8s clips (e.g. 1080p-8s = 80 base × 2 = 160 units). **For new work, prefer `pixverse/pixverse-v6`** — it's the flagship successor, adds native audio (`generate_audio_switch`), multi-shot composition (`generate_multi_clip_switch`), cinematic camera-control prompting, 10s and 15s durations, and uses transparent per-second pricing. The only real reasons to reach for v5 today are: (a) you need one of the **15 built-in named effects** (YMCA, Ghibli Live!, Suit Swagger, Kungfu Club, Vogue Walk, Mega Dive, etc.) — v6 dropped the `effect` enum entirely, so the anime/meme-style one-shot effects are v5-exclusive; (b) an existing workflow is pinned to v5 outputs and you don't want to re-baseline prompts. Otherwise, v6 at 360p or 540p is the cheap draft tier you want.

## Modes (inferred from which inputs are set)

| Mode                            | How to trigger                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Text-to-video**               | Just a `prompt` (+ optional `aspect_ratio`). No `image` or `last_frame_image`.                    |
| **Image-to-video**              | Set `image` (first frame). `aspect_ratio` is derived from the image.                              |
| **First-last-frame transition** | Set both `image` and `last_frame_image`. `effect` must be `"None"` — effects don't mix with this. |
| **Effect (named)**              | Set `effect` to one of the 15 named presets. Works on T2V or I2V; not with `last_frame_image`.    |

## Input schema

| Field              | Type         | Required | Default  | Description                                                                                                                            |
| ------------------ | ------------ | -------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`           | string       | yes      | —        | Text prompt for video generation.                                                                                                      |
| `image`            | string (URI) |          | —        | First-frame image. Presence switches to image-to-video mode.                                                                           |
| `last_frame_image` | string (URI) |          | —        | Last-frame image for a transition. Must be used together with `image`. Not valid with `effect`.                                        |
| `quality`          | enum         |          | `"540p"` | One of `360p`, `540p`, `720p`, `1080p`. 360p and 540p cost the same; 720p and 1080p cost more. **1080p is only valid at 8s duration.** |
| `aspect_ratio`     | enum         |          | `"16:9"` | One of `16:9`, `9:16`, `1:1`. T2V only — ignored when an image is provided.                                                            |
| `duration`         | enum         |          | `5`      | One of `5` or `8` (seconds). 8s costs 2x a 5s clip at the same resolution.                                                             |
| `effect`           | enum         |          | `"None"` | Named one-shot effect. See the full list below. Does not work with `last_frame_image`.                                                 |
| `negative_prompt`  | string       |          | `""`     | Elements to avoid in the generated video.                                                                                              |
| `seed`             | integer      |          | random   | Random seed for reproducible generation.                                                                                               |

**`effect` enum values** (v5-exclusive — v6 removed this field):

`None`, `Let's YMCA!`, `Subject 3 Fever`, `Ghibli Live!`, `Suit Swagger`, `Muscle Surge`, `360° Microwave`, `Warmth of Jesus`, `Emergency Beat`, `Anything, Robot`, `Kungfu Club`, `Mint in Box`, `Retro Anime Pop`, `Vogue Walk`, `Mega Dive`, `Evil Trigger`.

Local image paths for `image` / `last_frame_image` are auto-uploaded by `run_model.py`.

### Deltas vs. pixverse-v6

| Area                     | v5                                    | v6                                                                    |
| ------------------------ | ------------------------------------- | --------------------------------------------------------------------- |
| Durations                | `5`, `8`                              | `5`, `8`, `10`, `15`                                                  |
| Named effect presets     | 15-item `effect` enum                 | Removed — no `effect` field                                           |
| Native audio             | Not supported                         | `generate_audio_switch: bool`                                         |
| Multi-shot composition   | Not supported                         | `generate_multi_clip_switch: bool`                                    |
| Billing                  | **Unit-based** (1080p-8s = 160 units) | **Per-second** tiered by resolution + audio                           |
| 1080p availability       | Only at 8s                            | Any duration                                                          |
| Camera-control prompting | Generic — describe it in `prompt`     | Marketed as "precise camera control"; still prompt-driven but trained |
| POV / first-person mode  | Not a trained mode                    | Noted as a v6 strength                                                |
| In-frame text rendering  | Unreliable                            | Improved                                                              |

## Output

A single URI to the generated video (MP4). Saved as `pixverse_pixverse-v5_0.mp4`.

## Pricing

Billed in **Replicate units**, not $/second. The logs from a real run surface the math:

```text
Base units for 1080p: 80
Duration multiplier (8s = 2x): 2
Calculation: 80 × 2 = 160
Total units: 160
```

The resolution → base-units scale is roughly `1080p: 80`, with 720p / 540p / 360p consuming progressively fewer units (360p and 540p are billed at the same tier per Replicate's note). An 8s clip is 2x a 5s clip at the same resolution. For the authoritative $/unit rate see the "Run time and cost" footer on <https://replicate.com/pixverse/pixverse-v5> — the rate is the same used across pixverse-v3.5 / v4 / v4.5 / v5. Per-clip cost at 5s/540p is typically under a quarter; 8s/1080p is the priciest v5 combo. **v6's per-second pricing at 540p ($0.07/s → $0.35 for 5s) is competitive with v5's cheap tier**, so v5 is not meaningfully cheaper as a draft tier — reach for v6 for drafts, and only drop to v5 when you specifically want a named `effect`.

## Examples

**Text-to-video with a named effect** (v5-exclusive use case):

```json
{
  "prompt": "A young woman in a bright yellow sundress on a sunlit rooftop",
  "effect": "Let's YMCA!",
  "quality": "540p",
  "duration": 5,
  "aspect_ratio": "9:16"
}
```

```bash
python scripts/run_model.py pixverse/pixverse-v5 --input-file input.json --output ./out/
```

**Image-to-video at max quality** (1080p requires 8s):

```json
{
  "prompt": "camera slowly pushes in, wind rustles the leaves, dust motes drift through a beam of light",
  "image": "./photo.jpg",
  "quality": "1080p",
  "duration": 8
}
```

```bash
python scripts/run_model.py pixverse/pixverse-v5 --input-file input.json --output ./out/
```

**First-last-frame transition** (morph between two keyframes — `effect` must stay `"None"`):

```json
{
  "prompt": "smooth morph from day to night over the valley",
  "image": "./day.jpg",
  "last_frame_image": "./night.jpg",
  "quality": "720p",
  "duration": 5
}
```

```bash
python scripts/run_model.py pixverse/pixverse-v5 --input-file input.json --output ./out/
```

## Strengths / gotchas

**Good at:**

- The 15 named `effect` presets — anime-adjacent one-shot gags (YMCA, Vogue Walk, Kungfu Club, Retro Anime Pop, Ghibli Live!). v6 has no equivalent.
- Anime / stylized character motion — the model card calls this out explicitly.
- First-last-frame transitions at 5s or 8s.
- 1080p-8s output — was the v5 launch headline.

**Gotchas:**

- `duration` is **exactly `5` or `8`** — no 10s or 15s option (that's v6). Passing anything else 422s.
- `quality: "1080p"` is **only valid with `duration: 8`**. 1080p at 5s will reject.
- `aspect_ratio` is only `16:9` / `9:16` / `1:1`.
- `effect` and `last_frame_image` are **mutually exclusive** — pick one mode.
- No `generate_audio_switch` — v5 output is silent. Add audio in post, or use v6.
- No `generate_multi_clip_switch` — single-shot only. Stitch multi-shots externally, or use v6.
- No POV / first-person-camera trained mode (v6 added this).
- In-frame text rendering is unreliable — v6 improved this.
- Billing is unit-based, not $/second — harder to budget at a glance than v6's explicit tier table. Check the model page footer for the current $/unit rate.
- For any workflow where you'd otherwise pick v6 without thinking: just pick v6. v5 is the effects-library fallback, not a cheap-draft alternative.
