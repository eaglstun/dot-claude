# `klein` — FLUX.2 Klein 4B

**Description:** Fast image generation and editing.
**Provider:** Black Forest Labs (FLUX 2 family). _Klein_ = German for "small" — this is the 4B-parameter member of FLUX.2.
**Aliases:** `flux-klein`.
**Tier:** `0.01 pollen/image-token`. No `paid_only` flag — free-tier accessible, though 10× the per-token cost of `flux` (Schnell).

## Why pick it

- **Default free-tier image editor.** Only free-accessible image model besides `kontext` that takes `image` input. Cheaper than `kontext` (4× less per token) and faster.
- **Does both t2i and img2img well** — the 4B param size keeps it fast while the FLUX.2 architecture handles editing fidelity better than stretching `flux` with img2img tricks.
- **Seed honored.** One of the few image models where seed actually produces reproducible output (the official list: `flux`, `zimage`, `seedream`, `klein`, `seedance`).
- Newer FLUX generation than `flux` (Schnell) — FLUX.2 vs FLUX.1.

## Capabilities

|                  |                                                 |
| ---------------- | ----------------------------------------------- |
| Input modalities | **text + image** — supports editing and img2img |
| Output           | `image/jpeg`                                    |
| Max resolution   | ~1024×1024 range                                |
| Seed             | **Honored** — reproducible output               |
| Negative prompt  | Not supported (only `flux` / `zimage`)          |
| Transparent BG   | Not supported                                   |

## Parameters that work

- `--model klein`
- `--width <n>` / `--height <n>`
- `--seed <n>` — `-1` for random; honored
- `--image <url>` — source image(s) for editing / img2img. `,` or `|` separated for multiple
- `--enhance`
- `--safe`
- `--output <path>`

## Parameters that don't apply

- `--negative` — not supported
- `--transparent` — no alpha output

## CLI

Text-to-image:

```bash
polli gen image "a Scandinavian interior with large windows, morning light, mid-century furniture, plants" \
  --model klein --width 1344 --height 768 --seed 42 --output interior.jpg
```

Image editing:

```bash
SRC_URL=$(polli upload ./room.jpg --json | jq -r .url)

polli gen image "same room, but redecorate in maximalist 1970s style with warm earth tones and patterned wallpaper" \
  --model klein --image "$SRC_URL" --output room_70s.jpg
```

Img2img style transfer:

```bash
polli gen image "convert this photo into a watercolor painting with soft edges and muted palette" \
  --model klein --image "$SRC_URL" --seed 7 --output watercolor.jpg
```

## HTTP

```bash
curl -sS --fail-with-body -o out.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/Scandinavian%20interior?model=klein&width=1344&height=768&seed=42"
```

Editing via HTTP:

```bash
curl -sS --fail-with-body -o edit.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/redecorate%201970s?model=klein&image=$SRC_URL"
```

## Prompt tips

- **Leverage the seed.** Unlike most image editors, klein actually reproduces. When iterating, lock the seed and vary the prompt — you see the effect of your prompt changes cleanly.
- **For edits, keep the structure cue explicit.** _"same composition, but..."_ or _"preserve the framing, change X"_. Klein handles this but won't infer it from single-clause prompts.
- Klein is FLUX.2 — it handles **text rendering in images** noticeably better than FLUX.1 (`flux`/`zimage`). Still not a replacement for `gptimage`, but posters / signs / UI mockups with legible text land more often.
- **Aspect ratios:** FLUX.2 respects non-square outputs well. Landscape 1344×768 or portrait 768×1344 both produce coherent results (FLUX.1 sometimes stretches subjects).

## When `klein` vs `flux` / `zimage` / `kontext`?

- **`flux`** (0.001/token): cheapest. Default for **text-only** generation at large batch size.
- **`zimage`** (0.002/token): server default, 2× upscaled. Default for **final delivery** of text-only work.
- **`klein`** (0.01/token, **this model**): default when you need **image editing / img2img** on the free tier. Also a strong text-to-image choice when FLUX.2's typography or aspect handling matters.
- **`kontext`** (0.04/token): escalate to when klein's edits don't preserve context well enough — subtle, localized, identity-preserving changes.

Rough rule: **prototype on `flux`, edit on `klein`, escalate to `kontext` for fussy edits.**

## Known limits

- No negative prompt — spell out what to preserve instead of what to avoid.
- Structural edits (adding/removing objects) less reliable than attribute/style edits. For heavy structural work, step up to `gptimage`, `nanobanana`, or `kontext`.
- No transparent background — use `gptimage` / `gptimage-large`.
- 10× `flux` per token: not a concern for single images, but noticeable at batch scale. Use `flux` if you don't need editing.
