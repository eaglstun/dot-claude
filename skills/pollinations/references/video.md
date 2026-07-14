# Video generation

Prefer `polli`. Video jobs are slow (seconds to minutes) — the CLI waits for you and writes the result to disk.

## CLI (preferred)

```bash
polli gen video "drone shot flying over mountains at sunrise" --model ltx-2 --duration 5 --aspect-ratio 16:9 --output clip.mp4
```

Flags:

| Flag                           | Purpose                                                             |
| ------------------------------ | ------------------------------------------------------------------- |
| `--model <name>`               | Video model (default varies — `ltx-2` is the only free-tier option) |
| `--duration <n>`               | Seconds (1–30; model caps apply)                                    |
| `--aspect-ratio <r>`           | `16:9` or `9:16`                                                    |
| `--width <n>` / `--height <n>` | Dimensions (default 1024)                                           |
| `--audio`                      | Include AI soundtrack                                               |
| `--seed <n>`                   | Reproducibility (honored by `seedance`)                             |
| `--enhance`                    | Prompt rewriting                                                    |
| `--negative <text>`            | Content to avoid                                                    |
| `--image <url>`                | Reference frame URL (image-to-video)                                |
| `--output <path>`              | Save path (default `video.mp4`)                                     |

### Models

Free tier:

- `ltx-2` — LTX-2.3, fast text-to-video with upscaler. **Default choice** unless the user specifies a paid model. Deep dive: [`models/ltx-2.md`](models/ltx-2.md).

Paid:

- `veo` — Google Veo 3.1 Fast (preview)
- `seedance` — Seedance Lite (BytePlus), better quality
- `seedance-pro` — Seedance Pro-Fast, better prompt adherence
- `wan` — Wan 2.6, text/image-to-video with always-on audio, 2–15s, up to 1080p. Deep dive: [`models/wan.md`](models/wan.md).
- `wan-fast` — Wan 2.2, 5s, 480p, cheapest paid option with image-to-video. Deep dive: [`models/wan-fast.md`](models/wan-fast.md).
- `grok-video-pro` — xAI Grok Video Pro, 720p, 1–15s
- `p-video` — Pruna, up to 1080p, best resolution/cost ratio among cheap paid tiers. Deep dive: [`models/p-video.md`](models/p-video.md).
- `nova-reel` — Amazon Bedrock Nova Reel, **6–60s (longest in the lineup)**, 720p, text+image input. Deep dive: [`models/nova-reel.md`](models/nova-reel.md).

For capabilities beyond the summary above — exact resolution ceilings, which params a model ignores, prompt patterns — see [`models/`](models/README.md).

### Embed the prompt in file metadata

After saving, write the prompt into the video so it travels with the file. Uses `exiftool` (`brew install exiftool`).

```bash
PROMPT="drone shot flying over mountains at sunrise"
polli gen video "$PROMPT" --model ltx-2 --duration 5 --output clip.mp4
exiftool -overwrite_original \
  -Comment="$PROMPT" -Description="$PROMPT" \
  -XMP-dc:Description="$PROMPT" -Software="pollinations/ltx-2" \
  clip.mp4
```

Works for MP4/MOV. Verify: `exiftool -Comment -Description clip.mp4`.

Alternative if `exiftool` isn't installed, using the already-available `ffmpeg` (writes a new file — no stream re-encode with `-c copy`):

```bash
ffmpeg -i clip.mp4 -c copy \
  -metadata comment="$PROMPT" -metadata description="$PROMPT" \
  clip.tagged.mp4 && mv clip.tagged.mp4 clip.mp4
```

### Examples

```bash
# Free-tier default
polli gen video "time-lapse of clouds rolling over a valley" --model ltx-2 --duration 5 --output clouds.mp4

# Image-to-video
polli gen video "slow push-in on the subject" --model wan --image https://example.com/still.jpg --duration 6 --audio --output push.mp4

# Vertical (short-form)
polli gen video "neon rain in Tokyo alley, POV walking" --model ltx-2 --aspect-ratio 9:16 --duration 4 --output vertical.mp4
```

## HTTP API (fallback)

Video shares the image path — pick a video model and the response flips to `video/mp4`.

```bash
curl -sS --fail-with-body --max-time 300 -o clip.mp4 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/drone%20shot%20flying%20over%20mountains?model=ltx-2&duration=5&aspectRatio=16:9"
```

Bump the curl timeout (`--max-time 300`) — generation takes a while.

Video-only params: `duration` (1–10), `aspectRatio` (`"16:9"` | `"9:16"`), `audio` (bool — `wan` always has audio regardless). Pass `image=<url>` with a video model that supports it (`wan`, `wan-fast`, `p-video`) for image-to-video.
