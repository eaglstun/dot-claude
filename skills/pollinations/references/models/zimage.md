# `zimage` — Z-Image Turbo

**Description:** Fast 6B Flux-family model with built-in 2× upscaling.
**Provider:** Z-Image (community fine-tune of FLUX architecture, 6B parameters).
**Aliases:** `z-image`, `z-image-turbo`.
**Tier:** free. `0.002 pollen/image-token` (2× `flux`, still cheap).

## Why pick it

- **Default model** on the Pollinations `/image/` endpoint when no model is specified — not an accident.
- Built-in **2× upscaling** — the output is already higher resolution than what `flux` produces at the same request size. Good for posters, prints, or larger displays.
- Like `flux`, supports `negative_prompt` and `seed` reliably.
- Costs 2× `flux` — still negligible for the quality bump.

## Capabilities

|                  |                                                    |
| ---------------- | -------------------------------------------------- |
| Input modalities | **text only** — no image reference / editing       |
| Output           | `image/jpeg`, upscaled 2× from the base generation |
| Max resolution   | 1024×1024 request → effectively 2048×2048 output   |
| Seed             | Honored — reproducible                             |
| Negative prompt  | Supported                                          |
| Transparent BG   | Not supported                                      |

## Parameters that work

- `--model zimage`
- `--width <n>` / `--height <n>`
- `--seed <n>` — `-1` for random
- `--negative <text>`
- `--enhance`
- `--safe`
- `--output <path>`

## Parameters that don't apply

- `--image` — text-only model
- `--transparent` — JPEG output

## CLI

```bash
polli gen image "a bustling Tokyo street at night, neon reflections on wet pavement, 35mm film" \
  --model zimage --width 1024 --height 1024 --seed 7 --output tokyo.jpg
```

Portrait orientation for social:

```bash
polli gen image "minimalist travel poster, Mount Fuji at dawn, muted palette, Swiss typography" \
  --model zimage --width 768 --height 1344 --output poster.jpg
```

## HTTP

```bash
curl -sS --fail-with-body -o tokyo.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/Tokyo%20street%20at%20night?model=zimage&width=1024&height=1024"
```

Note: `zimage` is also the server default — omitting `?model=` gets you `zimage`.

## Prompt tips

- Because output is upscaled, **detail-heavy prompts pay off**: textures, micro-expressions, fabric weave, lens characteristics. Vague prompts just upscale blurry results.
- For text/poster-style work, specify typography explicitly (_"Swiss typography", "bold serif title"_) — zimage handles typography better than flux but worse than GPT Image.
- If the 2× upscale introduces artifacts (happens on low-frequency subjects like clear sky / gradients), fall back to `flux` at a higher request resolution.

## When `flux` vs `zimage`?

- **Fast iteration / large batches:** `flux` (cheaper, still great quality).
- **Final delivery / large display / print:** `zimage` (upscaled output is ready to use).
- **Reproducibility:** both honor seed equally well.

## Known limits

- No image input → no img2img / editing. Use `kontext`, `klein`, or `nanobanana` for edit workflows.
- No transparent background.
- Generation is fast but the upscaler adds a beat — if you care about raw latency, `flux` is snappier.
