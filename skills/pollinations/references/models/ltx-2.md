# `ltx-2` — LTX-2.3

**Description:** Fast text-to-video generation with built-in upscaler.
**Provider:** Lightricks (LTX-Video family).
**Aliases:** `ltx2`, `ltx-2.3`, `ltxvideo`, `ltx-video`.

## Why pick it

- **Cheapest video model by a wide margin.** `0.005 pollen/sec` — ~3× cheaper than `wan-fast`, 16× cheaper than `nova-reel`, 30× cheaper than `veo`.
- **Effectively the default free-tier choice.** Both `ltx-2` and `nova-reel` lack the `paid_only` flag in the API listing, but `nova-reel`'s cost-per-second would burn a free-tier pollen budget in a few clips — `ltx-2` is the only one practical for sustained free-tier use.
- Fastest round-trip of the video models — good for iteration.
- Includes an upscaler step so output holds up at larger display sizes despite the small base model.

## Capabilities

|                  |                                                                                                                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Input modalities | **text only** — no image input / i2v                                                                                                                                                                         |
| Output           | `video/mp4`                                                                                                                                                                                                  |
| Duration         | Up to ~10 seconds                                                                                                                                                                                            |
| Aspect ratio     | `16:9` or `9:16`                                                                                                                                                                                             |
| Audio            | No native audio output                                                                                                                                                                                       |
| Seed             | Not in the documented seed-honoring set (`flux`, `zimage`, `seedream`, `klein`, `seedance`). Pass `--seed` anyway if you want — it may still influence sampling, but don't expect bit-exact reproducibility. |

## Parameters that work

- `--model ltx-2`
- `--duration <n>` — seconds
- `--aspect-ratio 16:9` / `9:16`
- `--width` / `--height`
- `--enhance` — LLM rewrites the prompt before generation
- `--negative` — content to avoid (best-effort; this param is documented for flux/zimage primarily)
- `--output <path>`

## Parameters that don't apply

- `--image` — text-only model, image reference is ignored
- `--audio` — no audio output

## CLI

```bash
polli gen video "time-lapse of cumulus clouds rolling over a mountain valley at sunset" \
  --model ltx-2 --duration 6 --aspect-ratio 16:9 --output clouds.mp4
```

Vertical / short-form:

```bash
polli gen video "first-person POV walking through a neon-lit Tokyo alley at night, rain" \
  --model ltx-2 --aspect-ratio 9:16 --duration 5 --output vertical.mp4
```

## HTTP

```bash
curl -sS --fail-with-body --max-time 300 -o clip.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/time-lapse%20of%20clouds?model=ltx-2&duration=6&aspectRatio=16:9"
```

## Prompt tips

- Describe motion explicitly (verbs: "drifting", "pushing in", "panning left"). Static prompts often produce static or flickery results.
- Short, concrete prompts beat long ones. One subject + one action + lighting is usually enough.
- For establishing shots, specify camera language: _"aerial drone shot"_, _"handheld close-up"_, _"slow dolly forward"_.

## Known limits

- No image-to-video — for i2v, switch to `wan-fast`, `wan`, `p-video`, `seedance`, etc.
- No diegetic audio; if the user wants sound, generate separately via `elevenmusic` / `elevenlabs` and mux with `ffmpeg`.
- Short clips only. For 15–60s output use `wan` (≤15s) or `nova-reel` (6–60s).
