# `p-video` — Pruna p-video

**Description:** Text/image-to-video generation up to 1080p.
**Provider:** Pruna AI (optimization-focused inference).
**Aliases:** `pruna-video`.
**Tier:** paid. `0.036 pollen/sec`.

## Why pick it

- **Highest resolution among the cheap paid video models** — up to 1080p, versus 480p for `wan-fast`.
- **Supports image-to-video** — `--image <url>` drives the first frame.
- Solid middle ground between the 480p `wan-fast` and the premium `wan` / `veo` / `seedance-pro` tier.
- Reasonable cost for 1080p: ~2.5× `wan-fast`, but ~2× cheaper than `wan`, `grok-video-pro`, and `nova-reel`.

## Capabilities

|                  |                                                                     |
| ---------------- | ------------------------------------------------------------------- |
| Input modalities | text + image                                                        |
| Output           | `video/mp4`                                                         |
| Duration         | Up to ~10 seconds (typical)                                         |
| Resolution       | Up to 1080p                                                         |
| Aspect ratio     | `16:9` or `9:16`                                                    |
| Audio            | No native audio                                                     |
| Seed             | Not in the documented seed-honoring set. Treat as non-reproducible. |

## Parameters that work

- `--model p-video`
- `--duration <n>` — seconds (1–10)
- `--aspect-ratio 16:9` / `9:16`
- `--width` / `--height` — bump for 1080p output
- `--image <url>` — first-frame reference
- `--enhance` — prompt rewriting
- `--negative` — best-effort
- `--output <path>`

## Parameters that don't apply

- `--audio` — no audio generation

## CLI

Text-to-video at 1080p:

```bash
polli gen video "aerial drone shot flying over fog-covered Redwood forest at dawn, cinematic" \
  --model p-video --duration 6 --width 1920 --height 1080 --aspect-ratio 16:9 \
  --output redwoods.mp4
```

Image-to-video:

```bash
FRAME_URL=$(polli upload ./product.jpg --json | jq -r .url)

polli gen video "camera slowly orbits product, soft studio lighting rotates with it" \
  --model p-video --image "$FRAME_URL" --duration 6 --width 1920 --height 1080 \
  --output product_rotate.mp4
```

## HTTP

```bash
curl -sS --fail-with-body --max-time 300 -o clip.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/aerial%20drone%20shot?model=p-video&duration=6&width=1920&height=1080&aspectRatio=16:9"
```

## Prompt tips

- 1080p rewards **cinematic language**: specify lens (_"35mm", "anamorphic"_), motion (_"slow push-in", "whip pan"_), and lighting (_"golden hour", "chiaroscuro", "practicals only"_). The extra resolution surfaces detail that vague prompts waste.
- For product / marketing clips, describe camera motion first, subject second, background third. Pruna handles deliberate camera work well.
- Image-to-video works best when the still already has clear composition — `p-video` preserves framing rather than re-composing.

## Cost awareness

At 0.036 pollen/sec a 10-second clip runs ~0.36 pollen per attempt. If the user is iterating, prototype at `ltx-2` first (30× cheaper, text-only but fast) and only move to `p-video` once the prompt is dialed in.

## Known limits

- No audio — mux separately with `elevenmusic` / `elevenlabs` + `ffmpeg`.
- Requires balance — will 402 on free-tier accounts. Fall back to `ltx-2` if budget is the constraint.
- Longer clips than ~10s aren't reliable — switch to `wan` (≤15s) or `nova-reel` (6–60s) for extended takes.
