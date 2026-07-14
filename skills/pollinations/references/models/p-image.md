# `p-image` — Pruna p-image

**Description:** Fast text-to-image generation.
**Provider:** Pruna AI (inference optimization; same company as `p-video`, `p-image-edit`).
**Aliases:** `pruna-image`, `pruna`.
**Tier:** paid. `0.0075 pollen/image-token` (~7.5× `flux`, ~3.75× `zimage`).

## Why pick it

- Pruna's selling point is **throughput via optimization** — fast inference with an engineered model, not raw quality.
- Good middle tier between the free models (`flux`, `zimage`) and the premium tier (`seedream5`, `nanobanana-pro`, `grok-imagine-pro`).
- Part of a Pruna suite — pairs well with `p-image-edit` (editing) and `p-video` (text/image-to-video) if you're staying in one provider family.

## Capabilities

|                  |                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Input modalities | **text only** — no image reference                                                                                              |
| Output           | `image/jpeg`                                                                                                                    |
| Max resolution   | Standard (1024×1024 range)                                                                                                      |
| Seed             | **Not in the documented seed-honoring set** (`flux`, `zimage`, `seedream`, `klein`, `seedance`) — don't rely on reproducibility |
| Negative prompt  | **Not supported** (only `flux` / `zimage`)                                                                                      |
| Transparent BG   | Not supported                                                                                                                   |

## Parameters that work

- `--model p-image`
- `--width <n>` / `--height <n>`
- `--enhance`
- `--safe`
- `--output <path>`

## Parameters that don't apply

- `--image` — text-only. For edits, switch to `p-image-edit` (same provider, paid).
- `--seed` — may not be honored.
- `--negative` — not supported.
- `--transparent` — no alpha output.

## CLI

```bash
polli gen image "a cyberpunk street food vendor at midnight, steam rising from woks, neon signs" \
  --model p-image --width 1024 --height 1024 --output vendor.jpg
```

## HTTP

```bash
curl -sS --fail-with-body -o vendor.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/cyberpunk%20street%20food?model=p-image&width=1024&height=1024"
```

## Prompt tips

- Because seed isn't reliable and negative prompts don't work, **positive phrasing of what you want** is critical. Don't write _"a fox (not a dog)"_ — write what the fox looks like in detail.
- Output tends to be a bit more photographic than `flux`'s baseline — good for product / editorial / lifestyle imagery.
- If you need an image companion to `p-video`, prompt with explicit camera framing (_"wide shot", "medium close-up"_) so the still matches the video model's conventions when you later animate it.

## Cost awareness

`p-image` is ~7.5× pricier per token than `flux`. Only reach for it when:

- You're deliberately staying in the Pruna suite for consistent style
- You need `p-image-edit` downstream and want the source to match
- `flux` / `zimage` produce off-brand / off-style output for a specific domain

Otherwise: **prototype on `flux`, graduate to `p-image` only if justified.**

## Known limits

- No negative prompt, no reliable seed — iteration is noisier.
- No image input. For editing use `p-image-edit` or free alternatives like `kontext` / `klein`.
- No transparent background.
