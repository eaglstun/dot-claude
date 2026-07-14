# `flux` — Flux Schnell

**Description:** Fast high-quality image generation.
**Provider:** Black Forest Labs (FLUX family). "Schnell" is their fastest, Apache-licensed variant.
**Aliases:** none.
**Tier:** free. `0.001 pollen/image-token`.

## Why pick it

- **Cheapest image model on Pollinations.** About half the price of `zimage`.
- Strong baseline quality across subjects — portraits, landscapes, product shots, illustration.
- Supports `negative_prompt` and `seed` (only `flux` and `zimage` honor these reliably).
- Fastest generation time in the free tier.

## Capabilities

|                  |                                                                       |
| ---------------- | --------------------------------------------------------------------- |
| Input modalities | **text only** — no image reference / editing                          |
| Output           | `image/jpeg`                                                          |
| Max resolution   | 1024×1024 is the sweet spot; larger works but quality drift increases |
| Seed             | Honored — use for reproducibility                                     |
| Negative prompt  | Supported                                                             |
| Transparent BG   | Not supported (use `gptimage` / `gptimage-large`)                     |

## Parameters that work

- `--model flux`
- `--width <n>` / `--height <n>`
- `--seed <n>` — `-1` for random
- `--negative <text>` — content to avoid
- `--enhance` — AI rewrites the prompt first
- `--safe` — NSFW filter
- `--output <path>`

## Parameters that don't apply

- `--image` — text-only, no img2img. Use `kontext`, `klein`, `gptimage`, or `nanobanana` for editing.
- `--transparent` — JPEG output, no alpha. Use `gptimage` / `gptimage-large`.

## CLI

```bash
polli gen image "a lone red fox on a snowy hilltop at golden hour, cinematic" \
  --model flux --width 1024 --height 1024 --seed 42 --output fox.jpg
```

With negative prompt:

```bash
polli gen image "portrait of a sailor in 1920s Boston, oil painting style" \
  --model flux --negative "modern clothing, cars, smartphones" --output sailor.jpg
```

## HTTP

```bash
curl -sS --fail-with-body -o fox.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/a%20lone%20red%20fox?model=flux&width=1024&height=1024&seed=42"
```

OpenAI-compat:

```python
client = OpenAI(base_url="https://gen.pollinations.ai/v1", api_key=...)
r = client.images.generate(model="flux", prompt="a lone red fox", size="1024x1024")
```

## Prompt tips

- **Concrete subjects + lighting + medium** outperform long paragraphs. `"red fox on a snowy hill, golden hour, cinematic"` beats `"please create an image of a fox..."`.
- `flux` handles style tags well (_"oil painting"_, _"isometric", "line art", "3D render"_). Lead with the style if it matters more than the subject.
- If composition is drifting, bump seed with `--seed -1` and regenerate a few times rather than re-prompting.
- For posters / text-in-image: flux is okay but not great. Use `gptimage` / `gptimage-large` / `nanobanana-pro` when legible text is critical.

## Default choice rule

Unless the user specifies otherwise, **start with `flux`** for any text-to-image task. Fall through to:

- `zimage` if you need slightly more detail / 2× upscaled output
- `kontext` / `klein` for editing existing images (both free)
- `gptimage` for text-in-image or transparent PNG
- paid models (`nanobanana-pro`, `seedream5`) only when quality demands it
