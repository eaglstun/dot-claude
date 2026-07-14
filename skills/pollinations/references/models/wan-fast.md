# `wan-fast` — Wan 2.2

**Description:** Fast & cheap text/image-to-video (5s, 480P) via DashScope.
**Provider:** Alibaba Wan (served via Alibaba DashScope).
**Aliases:** `wan2.2`, `wan-2.2`.
**Tier:** paid. `0.015 pollen/sec` (video) + `0.015 pollen/sec` (audio).

## Why pick it

- **Cheapest paid video option** (3× cheaper than `p-video`, 5× cheaper than `wan`/`grok-video-pro`).
- **Supports image-to-video** — unlike `ltx-2`. Pass `--image <url>` and the first frame drives the motion.
- Optional AI-generated audio. Pairs well with quick sketches and storyboards.
- Fast turnaround relative to the full `wan` 2.6.

## Capabilities

|                  |                                                                                |
| ---------------- | ------------------------------------------------------------------------------ |
| Input modalities | text + image                                                                   |
| Output           | `video/mp4` (optionally with audio track)                                      |
| Duration         | ~5 seconds (fixed / capped — longer requests are truncated server-side)        |
| Resolution       | 480p                                                                           |
| Aspect ratio     | `16:9` or `9:16`                                                               |
| Audio            | Optional — pass `--audio`                                                      |
| Seed             | Not in the documented seed-honoring set. Don't rely on it for reproducibility. |

## Parameters that work

- `--model wan-fast`
- `--duration <n>` — effectively ~5s; longer values are ignored or capped
- `--aspect-ratio 16:9` / `9:16`
- `--audio` — include AI-generated soundtrack (**billed at an extra 0.015 pollen/sec** — audio is priced separately from video)
- `--image <url>` — first-frame reference for image-to-video
- `--enhance` — prompt rewriting
- `--negative` — best-effort
- `--output <path>`

## CLI

Text-to-video:

```bash
polli gen video "a red fox darting through autumn leaves, shallow depth of field" \
  --model wan-fast --duration 5 --aspect-ratio 16:9 --output fox.mp4
```

Image-to-video (upload a still first, then animate it):

```bash
# 1. upload a local still
FRAME_URL=$(polli upload ./portrait.jpg --json | jq -r .url)

# 2. animate
polli gen video "subject looks up, smiles gently, wind in hair" \
  --model wan-fast --image "$FRAME_URL" --duration 5 --audio --output portrait_anim.mp4
```

With audio:

```bash
polli gen video "rain pattering on a window, dim lamp light, cozy cafe interior" \
  --model wan-fast --duration 5 --audio --aspect-ratio 9:16 --output cafe.mp4
```

## HTTP

```bash
curl -sS --fail-with-body --max-time 300 -o clip.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/a%20red%20fox?model=wan-fast&duration=5&aspectRatio=16:9&audio=true"
```

Image-to-video via HTTP (`image=<url>`):

```bash
curl -sS --fail-with-body --max-time 300 -o anim.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/subject%20looks%20up?model=wan-fast&image=$FRAME_URL&duration=5"
```

## Prompt tips

- Image-to-video works best when the prompt describes **motion** that makes sense for the still: _"camera slowly pushes in"_, _"subject turns head toward camera"_, _"leaves rustle in wind"_. Scene-change prompts tend to look glitchy.
- For audio prompts, mention the sonic texture you want (_"gentle rain"_, _"crackling fireplace"_, _"upbeat synth beat"_) — the audio generation is independent of the visual and benefits from explicit cues.

## Known limits

- Hard-capped around 5 seconds. For longer clips, step up to `wan` (up to 15s, 1080p) at ~5× the cost.
- 480p only — not suitable for large-display output. Upscale externally or switch to `p-video` / `wan`.
- Audio adds meaningful cost (doubles the effective per-second price). Skip `--audio` when you'll mux music from `elevenmusic` anyway.
