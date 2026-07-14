# runwayml/gen-4.5

Model page: https://replicate.com/runwayml/gen-4.5

Runway's **Gen-4.5** — the premium, flagship tier for video generation on Replicate. Text-to-video by default, image-to-video when you supply a first frame. Ranked **#1 on the Artificial Analysis Text-to-Video Benchmark** (1247 Elo as of Nov 30, 2025). Reach for this when you need top-shelf physics, coherence, and visual fidelity and you're willing to pay for it.

## When to pick Gen-4.5

- Hero shots for marketing or ads
- Anything with liquids, fabric, hair, or fine physical detail
- Multi-element scenes where consistency across objects matters
- Work where the output will be scrutinized closely (close-ups, slow motion)

For drafts, iteration, or bulk generation, **don't start here** — use something like `prunaai/p-video` (draft mode) or `bytedance/seedance-2.0` and only upgrade to Gen-4.5 for the finals.

## Input schema

| Field          | Type         | Required | Default  | Description                                                                 |
| -------------- | ------------ | -------- | -------- | --------------------------------------------------------------------------- |
| `prompt`       | string       | ✅       | —        | Text prompt for video generation.                                           |
| `image`        | string (URI) |          | —        | Optional first frame. When provided, the model runs in image-to-video mode. |
| `duration`     | enum         |          | `5`      | One of `5` or `10` (seconds). Only these two values.                        |
| `aspect_ratio` | enum         |          | `"16:9"` | One of `16:9`, `9:16`, `4:3`, `3:4`, `1:1`, `21:9`.                         |
| `seed`         | integer      |          | random   | For reproducibility.                                                        |

Local `image` path is auto-uploaded by `run_model.py`.

## Output

Single URI to the generated video (MP4). Saved as `runwayml_gen-4.5_0.mp4`.

## Pricing

Not listed on the model page. Historical tier for Runway video on Replicate is **~$0.50–$1.50 per clip** depending on duration and aspect ratio — confirm on replicate.com/runwayml/gen-4.5 before running batches. A 10s generation is noticeably more expensive than a 5s one.

## Strengths

- **Realistic physics** — weight, momentum, liquids, cloth simulation
- **Character expressions** — subtle facial performances beyond most competitors
- **Multi-element scenes** — multiple characters/objects stay coherent across frames
- **Style range** — photorealistic, cinematic, and non-photorealistic aesthetics all handled well
- **Temporal consistency** — less flicker and morphing than the generation below it

## Known limitations

Documented by Runway on the page:

- **Causal reasoning** — effects may precede causes (e.g. splash before the object hits water)
- **Object permanence** — items can disappear and reappear unexpectedly, especially when occluded
- **Success bias** — actions tend to resolve successfully even when the prompt implies failure

Prompt around these with explicit "failure" language if you need it (e.g. "the ball misses the net and bounces back").

## Examples

**Text-to-video:**

```bash
python scripts/run_model.py runwayml/gen-4.5 \
    --input '{
      "prompt": "a single drop of water falls onto a still pool, high-speed macro shot, crown splash with droplets frozen mid-air, photorealistic, cinematic lighting",
      "duration": 5,
      "aspect_ratio": "16:9"
    }' \
    --output ./out/
```

**Image-to-video (animate a hero still):**

```bash
python scripts/run_model.py runwayml/gen-4.5 \
    --input '{
      "prompt": "subject slowly turns toward the camera, soft hair movement in the breeze, shallow depth of field",
      "image": "./portrait.jpg",
      "duration": 5
    }' \
    --output ./out/
```

**Cinematic 21:9 extended clip:**

```bash
python scripts/run_model.py runwayml/gen-4.5 \
    --input '{
      "prompt": "aerial dolly over a snow-covered mountain range at dawn, soft volumetric light breaking through clouds, anamorphic lens, cinematic color grade",
      "duration": 10,
      "aspect_ratio": "21:9"
    }' \
    --output ./out/
```

**Vertical for social (with reproducibility):**

```bash
python scripts/run_model.py runwayml/gen-4.5 \
    --input '{
      "prompt": "a dancer spinning in a neon-lit alley, rain droplets catching the light, slow-motion, 1/8 shutter look",
      "duration": 5,
      "aspect_ratio": "9:16",
      "seed": 42
    }' \
    --output ./out/
```

## Prompting tips

- **Be specific about camera.** "Slow dolly-in", "handheld tracking shot", "static wide", "drone pullback" — Gen-4.5 responds well to cinematography language.
- **Name the look.** "Anamorphic", "Kodak film stock", "Fujifilm", "volumetric light", "practical lighting" land better than vague "cinematic".
- **Break physics queries into concrete cause-and-effect** — "the domino falls, hitting the next one, which topples" rather than "dominoes fall" — this partially works around the causal-reasoning limitation.
- **For image-to-video**, describe motion only; the image already conveys the scene. Prompts that redescribe the still often introduce drift.

## Gotchas

- **`duration` only accepts 5 or 10.** Not arbitrary integers — the schema is an enum.
- **No audio.** Gen-4.5 outputs silent video. For matched audio, generate separately (e.g. with a music or SFX model) and mux with ffmpeg.
- **Cost adds up fast** — at a rough $1/clip, iteration is expensive. Prototype on cheaper models, then run Gen-4.5 once for the final take.
- **Large aspect ratios** (`21:9`, `1:1`) still top out at the same internal resolution budget — don't expect 21:9 to deliver higher per-frame fidelity than 16:9.
