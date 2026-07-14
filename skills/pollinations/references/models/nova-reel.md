# `nova-reel` — Amazon Nova Reel

**Description:** Bedrock Video Generation, 6–60s, 720p.
**Provider:** Amazon (Bedrock Nova family; same family as `nova-canvas` for image).
**Aliases:** `amazon-nova-reel`.
**Tier:** `0.08 pollen/sec`. **Does not carry the `paid_only` flag** in the API model listing — in principle accessible to free-tier accounts, though each second is 16× the cost of `ltx-2` (`0.005/sec`), so it burns pollen quickly.

## Why pick it

- **Longest clips in the Pollinations lineup.** Up to 60 seconds — nothing else comes close. The next-longest option (`wan`) caps at 15 seconds.
- **Image-to-video** support. Text + image input modalities.
- 720p is the ceiling — lower than `wan` / `p-video` (1080p), higher than `wan-fast` (480p).
- Bedrock-grade inference pipeline: consistent, generally "safe/professional" output tone.

## Capabilities

|                  |                                                                         |
| ---------------- | ----------------------------------------------------------------------- |
| Input modalities | text + image                                                            |
| Output           | `video/mp4`                                                             |
| Duration         | **6–60 seconds**                                                        |
| Resolution       | 720p max                                                                |
| Aspect ratio     | `16:9` or `9:16`                                                        |
| Audio            | No native audio output                                                  |
| Seed             | Not in the documented seed-honoring set. Don't rely on reproducibility. |

## Parameters that work

- `--model nova-reel`
- `--duration <n>` — 6 to 60
- `--aspect-ratio 16:9` / `9:16`
- `--width <n>` / `--height <n>` — cap at 720p equivalent
- `--image <url>` — first-frame reference
- `--enhance` — prompt rewriting
- `--negative <text>` — best-effort
- `--output <path>`

## Parameters that don't apply

- `--audio` — no audio generation. For sound, mux from `elevenmusic` / `elevenlabs` with `ffmpeg`.

## CLI

60-second showcase:

```bash
polli gen video "cinematic establishing shot: aerial drone flies over a misty mountain valley at sunrise, slowly descends toward a lone cabin by a lake, smoke rising from chimney, birds crossing frame" \
  --model nova-reel --duration 60 --aspect-ratio 16:9 \
  --output valley_sunrise.mp4
```

Minimum duration (6s):

```bash
polli gen video "slow dolly forward through a quiet forest, morning light filtering through leaves, dust motes drifting" \
  --model nova-reel --duration 6 --aspect-ratio 16:9 \
  --output forest.mp4
```

Image-to-video for brand / narrative:

```bash
FRAME_URL=$(polli upload ./hero_shot.jpg --json | jq -r .url)

polli gen video "camera orbits the subject once, then pulls back to reveal the full environment, golden hour lighting shifts subtly" \
  --model nova-reel --image "$FRAME_URL" --duration 15 --aspect-ratio 16:9 \
  --output hero.mp4
```

## HTTP

```bash
curl -sS --fail-with-body --max-time 900 -o clip.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/cinematic%20establishing%20shot?model=nova-reel&duration=30&aspectRatio=16:9"
```

Bump `--max-time` aggressively for long clips. A 60s request can take several minutes to return.

## Prompt tips

- **Treat long durations as narrative.** A 60s clip with a static prompt will look repetitive or wander. Give the model an **arc with beats**: _"opens on X, transitions through Y, resolves on Z"_. Nova Reel handles multi-beat camera language (dollies, orbits, pulls) better than most.
- **Cinematic / commercial language is Nova Reel's comfort zone.** Specify shot type (_"wide establishing", "medium tracking", "close-up insert"_), camera motion, and lighting beat. The output tends toward polished / brand-safe — use it for product reels, showreels, establishing shots, not for edgy/experimental looks.
- For i2v, describe the camera's journey starting from the still's framing. The model preserves the source composition well at the opening and evolves from there.
- Prompts focused on **single sustained actions** (a person walking, water flowing) work better than **rapid scene changes** at long durations. For cuts, generate multiple shorter clips and edit externally.

## Cost awareness

At `0.08 pollen/sec`:

| Duration             | Cost        |
| -------------------- | ----------- |
| 6 seconds (minimum)  | 0.48 pollen |
| 15 seconds           | 1.20 pollen |
| 30 seconds           | 2.40 pollen |
| 60 seconds (maximum) | 4.80 pollen |

A 60s Nova Reel clip costs about the same as a full 15s `wan` clip (`0.15 pollen/sec` including audio). So if you need **duration over audio**, Nova Reel is the better spend; if you need **audio**, go with `wan` at shorter lengths.

Workflow: prototype on a **6s clip** at lower resolution to confirm the motion and composition work, then commit the budget to the full-length version.

## When `nova-reel` vs others?

- **`nova-reel`**: the only choice for >15s clips. Best for establishing shots, showreels, narrative beats that need real runtime. No audio.
- **`wan`**: 2–15s with always-on audio, up to 1080p. Choose when audio matters and 15s is enough.
- **`p-video`**: up to ~10s, 1080p, no audio. Cheapest per-second for 1080p if you don't need length or audio.
- **`wan-fast`**: cheap iteration tier, 5s / 480p.
- **`ltx-2`**: free-tier, text-only, short.

## Known limits

- No audio — expect to mux separately for finished output.
- 720p ceiling — not a 1080p-finishing model. If you need print-quality resolution, switch to `wan` or `p-video` at shorter durations.
- Longer generations amplify physics/continuity artifacts. A 60s clip with a single subject often drifts in appearance partway through — factor this into the prompt (favor camera-motion stories over character-continuity stories).
