# `seedream5` — Seedream 5.0 Lite

**Description:** ByteDance ARK image model with **web search and reasoning** built into the generation pipeline.
**Provider:** ByteDance (ARK / Seedream family).
**Aliases:** none.
**Tier:** paid. `0.0525 pollen/image-token` — expensive; premium tier.

## Why pick it

- **Unique feature set:** the model can invoke web search and a reasoning pass during generation. Effectively gives you a model that can ground visuals in current references rather than purely training data.
- **Accepts image input** — so it's useful for editing / img2img workflows, not just text-to-image.
- Seed is honored (aliased as `seedream` in the seed-honoring set).
- Best quality in the Pollinations image lineup for conceptually-complex prompts (e.g. _"a kitchen gadget inspired by the 2024 Nobel Prize in Chemistry"_ — the search step helps the model anchor the concept).

## Capabilities

|                  |                                                               |
| ---------------- | ------------------------------------------------------------- |
| Input modalities | **text + image** — editing and img2img supported              |
| Output           | `image/jpeg`                                                  |
| Max resolution   | Typical high-res (1024×1024 and up)                           |
| Seed             | Honored                                                       |
| Web search       | Built into generation — real-time grounding on current topics |
| Reasoning        | Built-in chain-of-thought pass over the prompt                |
| Negative prompt  | Not documented as supported                                   |
| Transparent BG   | Not supported                                                 |

## Parameters that work

- `--model seedream5`
- `--width <n>` / `--height <n>`
- `--seed <n>` — honored
- `--image <url>` — source image(s) for editing / img2img
- `--enhance`
- `--safe`
- `--output <path>`

## Parameters that may not apply

- `--negative` — not documented
- `--transparent` — not supported

## CLI

Text-to-image with a reference-heavy concept:

```bash
polli gen image "a product shot of a kitchen gadget inspired by this year's Nobel Prize in Chemistry, editorial photography, soft studio light" \
  --model seedream5 --width 1024 --height 1024 --seed 11 --output gadget.jpg
```

Image-to-image editing:

```bash
SRC_URL=$(polli upload ./base.jpg --json | jq -r .url)

polli gen image "same composition, but transform into a 1980s Polaroid aesthetic with soft grain" \
  --model seedream5 --image "$SRC_URL" --output polaroid.jpg
```

## HTTP

```bash
curl -sS --fail-with-body -o gadget.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/kitchen%20gadget?model=seedream5&width=1024&height=1024&seed=11"
```

## Prompt tips

- **Lean into the web-search capability** for prompts that depend on current real-world references (events, trends, named people in the news, new product categories). `flux` and `zimage` will hallucinate; `seedream5` will actually look up.
- For the reasoning pass to help, give the model a **problem to solve** in the prompt: _"design a poster that answers X"_, _"illustrate the contrast between Y and Z"_. Simple nouns don't activate reasoning.
- For img2img, phrase edits as **transformations** (_"same composition, transform to X style"_) rather than wholesale rewrites — preserves the source structure.

## Cost awareness

At 0.0525 pollen/token, `seedream5` is **~52× pricier per token than `flux`** and **~7× pricier than `p-image`**. Reach for it when:

- The prompt requires current-world knowledge (web search pays for itself)
- Conceptually complex / multi-reference prompts where reasoning helps
- High-stakes final delivery where the extra quality is visible

For exploratory work, **always prototype on `flux` or `zimage` first.** Only promote to `seedream5` once the prompt is dialed in.

## Known limits

- Expensive — burns balance quickly on iteration.
- Slower than free-tier models (the search + reasoning passes add latency).
- No transparent background.
- For pure text-in-image work, `gptimage-large` or `nanobanana-pro` are often better fits.
