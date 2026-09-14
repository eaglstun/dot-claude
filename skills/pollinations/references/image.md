# Image generation

Prefer the CLI (`polli`) — it handles auth, filenames, and errors. Fall back to the HTTP API only when you need something the CLI doesn't expose or you're embedding in code.

## CLI (preferred)

```bash
polli gen image "beautiful sunset over ocean" --output sunset.jpg
```

Common flags:

| Flag                           | Purpose                                                          |
| ------------------------------ | ---------------------------------------------------------------- |
| `--model <name>`               | Image model (default: `zimage`). See `polli models --type image` |
| `--width <n>` / `--height <n>` | Dimensions (default 1024)                                        |
| `--seed <n>`                   | Reproducibility. `-1` for random                                 |
| `--enhance`                    | AI rewrites the prompt before generation                         |
| `--negative <text>`            | Content to avoid (flux/zimage only)                              |
| `--safe`                       | NSFW safety filter                                               |
| `--transparent`                | Transparent PNG (gptimage/gptimage-large)                        |
| `--image <url>`                | Reference image for img2img / editing. Repeatable                |
| `--output <path>`              | Save path (default `image.png`)                                  |
| `--json`                       | Machine-readable result metadata                                 |

### Models

Free tier:

- `flux` — Flux Schnell, fast, high quality. Deep dive: [`models/flux.md`](models/flux.md).
- `zimage` — Z-Image Turbo, 6B Flux with 2× upscaling (server default). Deep dive: [`models/zimage.md`](models/zimage.md).
- `kontext` — FLUX.1 Kontext, in-context editing (image input). Deep dive: [`models/kontext.md`](models/kontext.md).
- `klein` — FLUX.2 Klein 4B, fast editing + t2i with seed support (image input). Deep dive: [`models/klein.md`](models/klein.md).
- `gptimage` — GPT Image 1 Mini (image input)
- `gptimage-large` — GPT Image 1.5 (image input)
- `wan-image`, `qwen-image`

Paid:

- `nanobanana`, `nanobanana-2`, `nanobanana-pro` (Gemini image)
- `seedream5` — ByteDance ARK with web search + reasoning. Deep dive: [`models/seedream5.md`](models/seedream5.md).
- `wan-image-pro` (4K, thinking mode)
- `grok-imagine`, `grok-imagine-pro`
- `p-image` — Pruna, fast paid text-to-image. Deep dive: [`models/p-image.md`](models/p-image.md).
- `p-image-edit`
- `nova-canvas` (Bedrock)

For capabilities beyond the summary above — which params a model ignores, prompt patterns, cost tradeoffs — see [`models/`](models/README.md).

If a call returns 402 (insufficient balance), the chosen model is paid — retry with `flux` or `zimage`.

### Embed the prompt in file metadata

After saving, write the prompt into the image so it travels with the file. Uses `exiftool` (`brew install exiftool`).

```bash
PROMPT="a cat in space"
polli gen image "$PROMPT" --model flux --output cat.png
exiftool -overwrite_original \
  -Comment="$PROMPT" -Description="$PROMPT" -UserComment="$PROMPT" \
  -XMP-dc:Description="$PROMPT" -Software="pollinations/flux" \
  cat.png
```

Works for JPG/PNG/WebP. Verify: `exiftool -Comment -Description cat.png`.

### Examples

```bash
# Basic
polli gen image "a cat in space" --model flux --output cat.png

# With size + seed for reproducibility
polli gen image "cyberpunk street at night, neon" --width 1280 --height 720 --seed 42 --output street.png

# Image-to-image / editing (reference image)
polli gen image "same scene, but at dawn" --model kontext --image https://example.com/src.jpg --output dawn.png

# Transparent background
polli gen image "isolated red apple on transparent" --model gptimage --transparent --output apple.png
```

## HTTP API (fallback)

Base URL: `https://gen.pollinations.ai`. All generation calls need `Authorization: Bearer $POLLINATIONS_API_KEY` (or `?key=...`).

### GET `/image/{prompt}` — binary response

Returns `image/jpeg` (or `video/mp4` if you pass a video model).

```bash
curl -sS --fail-with-body -o sunset.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/beautiful%20sunset%20over%20ocean?model=flux&width=1024&height=1024"
```

Query params: `model`, `width`, `height`, `seed`, `enhance`, `negative_prompt`, `safe`, `quality` (low|medium|high|hd for gptimage), `image` (URL, `|` or `,` separated), `transparent`, `reasoning` (nanobanana variants).

### POST `/v1/images/generations` — OpenAI-compatible

Works with any OpenAI SDK: `base_url="https://gen.pollinations.ai/v1"`.

```python
from openai import OpenAI
client = OpenAI(base_url="https://gen.pollinations.ai/v1", api_key=os.environ["POLLINATIONS_API_KEY"])
r = client.images.generate(model="flux", prompt="a cat in space", size="1024x1024")
print(r.data[0].url)
```

Body: `prompt` (required), `model` (default `flux`), `size` (`WIDTHxHEIGHT`), `response_format` (`url` | `b64_json`), `quality`, `seed`, `nologo`, `enhance`, `safe`.

### POST `/v1/images/edits` — OpenAI-compatible edits

JSON or multipart. Body: `prompt`, `image` (source URL or array; or multipart file field), `model` (default `flux`).
