# `wan` — Wan 2.6

**Description:** Alibaba text/image-to-video with audio, 2–15s, up to 1080P, via DashScope.
**Provider:** Alibaba Wan (served via Alibaba DashScope).
**Aliases:** `wan2.6`, `wan-i2v`.
**Tier:** paid. `0.075 pollen/sec` (video) + `0.075 pollen/sec` (audio, always generated).

## Why pick it

- **Full-featured upgrade from `wan-fast`** — same provider family, newer architecture (2.6 vs 2.2), dramatically better resolution and duration ceiling.
- **Up to 1080p and up to 15 seconds** — the longest-runway paid option short of `nova-reel` (6–60s, but 720p only).
- **Audio is always on** — unlike `wan-fast` where `--audio` is optional. Good when you want ambient/diegetic sound without a second generation pass; costly if you don't need it.
- The `wan-i2v` alias is a tell: it's positioned primarily as an image-to-video model, and i2v quality is its strongest feature.

## Capabilities

|                  |                                                                                   |
| ---------------- | --------------------------------------------------------------------------------- |
| Input modalities | text + image                                                                      |
| Output           | `video/mp4` with embedded audio track                                             |
| Duration         | **2–15 seconds** (widest range among the standard video models)                   |
| Resolution       | Up to 1080p                                                                       |
| Aspect ratio     | `16:9` or `9:16`                                                                  |
| Audio            | **Always generated** — billed at `0.075 pollen/sec` in addition to the video cost |
| Seed             | Not in the documented seed-honoring set. Don't rely on reproducibility.           |

## Parameters that work

- `--model wan`
- `--duration <n>` — 2 to 15
- `--aspect-ratio 16:9` / `9:16`
- `--width <n>` / `--height <n>` — push up for 1080p
- `--image <url>` — first-frame reference for i2v
- `--enhance` — prompt rewriting
- `--negative <text>` — best-effort
- `--output <path>`

## Parameters that don't apply

- `--audio` — ignored; audio is always on. Doesn't matter if you pass it, but the cost is the same either way.

## CLI

Text-to-video at 1080p with audio:

```bash
polli gen video "rain-soaked Tokyo street at midnight, neon signs reflecting in puddles, person in red jacket walks toward camera" \
  --model wan --duration 8 --width 1920 --height 1080 --aspect-ratio 16:9 \
  --output tokyo_street.mp4
```

Image-to-video (the primary use case — hence `wan-i2v` alias):

```bash
FRAME_URL=$(polli upload ./still.jpg --json | jq -r .url)

polli gen video "camera slowly pushes in on the subject, gentle wind ruffles their hair, soft rain begins to fall" \
  --model wan --image "$FRAME_URL" --duration 10 --width 1920 --height 1080 \
  --output animated.mp4
```

Longer-form clip (close to the 15s cap):

```bash
polli gen video "time-lapse: sun sets over mountain range, clouds race across sky, shadows lengthen, stars begin to emerge" \
  --model wan --duration 15 --aspect-ratio 16:9 \
  --output sunset_lapse.mp4
```

## HTTP

```bash
curl -sS --fail-with-body --max-time 600 -o clip.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/rain-soaked%20Tokyo?model=wan&duration=8&aspectRatio=16:9&width=1920&height=1080"
```

Bump `--max-time` higher than for shorter models — a 15s generation can take a couple of minutes.

Image-to-video via HTTP:

```bash
curl -sS --fail-with-body --max-time 600 -o clip.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/camera%20pushes%20in?model=wan&image=$FRAME_URL&duration=10"
```

## Prompt tips

- **Describe motion in clauses, not adjectives.** _"Waves crash, spray rises, clouds drift"_ beats _"dynamic stormy ocean"_. The longer duration means the model needs a sequence of beats to animate through.
- For 15-second clips, give the model **a narrative arc**: opening state → transition → end state. _"Sun sets (start), clouds race (middle), stars emerge (end)"_. Single-action prompts look static across a 15s timeline.
- i2v works best when the prompt describes motion that **preserves the still's framing**: _"camera slowly pushes in", "subject turns head", "wind stirs the leaves"_. Scene-change prompts (_"subject walks out of frame, new location appears"_) tend to fragment.
- The always-on audio benefits from **sonic cues in the prompt**: _"rain patters on metal", "distant thunder", "footsteps on wet pavement"_. Without cues, the model guesses — often producing generic ambient beds.

## Cost awareness

At `0.075 + 0.075 = 0.15 pollen/sec` **effective cost** (video + always-on audio), `wan` is expensive:

| Duration   | Effective cost |
| ---------- | -------------- |
| 5 seconds  | 0.75 pollen    |
| 10 seconds | 1.50 pollen    |
| 15 seconds | 2.25 pollen    |

That's **10× the video-only cost of `wan-fast`** and ~4× `p-video` for the same duration. Workflow recommendation:

1. Prototype the motion on **`ltx-2`** (free, text-only) — dial in the camera language.
2. Test i2v cheaply on **`wan-fast`** (0.015/sec, 480p, 5s cap) — confirm the still + motion combo reads.
3. Only move to **`wan`** once the prompt is locked in, then spend the budget on longer durations / 1080p.

## When `wan` vs `wan-fast` vs `p-video`?

- **`wan-fast`**: cheapest i2v, capped at 5s/480p, `--audio` optional. Use for iteration, storyboards, quick drafts.
- **`p-video`**: 1080p, ~10s, no audio. Cheaper than `wan` when you don't need audio — a 10s clip is `0.36` vs `1.50` pollen.
- **`wan`**: use when you need >10s, or when embedded audio justifies the extra cost (ambient scenes, dialogue-less shorts).

## Known limits

- Audio can't be disabled — you're always paying for it even if you strip the audio track in post.
- 1080p generation is slow. Budget 60–180 seconds for a 15s/1080p request.
- Long clips (10s+) amplify any model weirdness (physics artifacts, identity drift in subjects). If fidelity matters more than duration, step down to `p-video` or chain shorter clips.
