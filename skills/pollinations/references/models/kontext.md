# `kontext` — FLUX.1 Kontext

**Description:** In-context image editing and generation.
**Provider:** Black Forest Labs (FLUX family). Same house as `flux` (Schnell) and `klein` (FLUX.2).
**Aliases:** none.
**Tier:** `0.04 pollen/image-token`. No `paid_only` flag in the API listing, but ~40× the per-token cost of `flux`.

## Why pick it

- **Purpose-built for in-context editing.** Feed it a source image plus a text instruction and it edits inside the existing composition instead of re-imagining the scene. Preserves layout, subject identity, and framing.
- **Does both t2i and img2img** in a single model — useful if you're doing a multi-step pipeline without switching models.
- **Not paid-only per the API** — accessible without paid-tier access, though the per-token cost will eat a free budget faster than `flux` / `zimage` / `klein`.
- Best editing fidelity in the free-accessible tier. `klein` is cheaper but less surgical on complex edits; `gptimage` / `nanobanana` are in the mix but paid.

## Capabilities

| | |
|---|---|
| Input modalities | **text + image** — primary use case is editing |
| Output | `image/jpeg` |
| Max resolution | ~1024×1024 range (source framing drives output) |
| Seed | **Not in the documented seed-honoring set** (`flux`, `zimage`, `seedream`, `klein`, `seedance`) — don't rely on reproducibility |
| Negative prompt | Not supported (only `flux` / `zimage`) |
| Transparent BG | Not supported |

## Parameters that work

- `--model kontext`
- `--width <n>` / `--height <n>` — usually let the source image's aspect drive this
- `--image <url>` — source image(s). `,` or `|` separated for multiple (composition / multi-reference edits)
- `--enhance` — prompt rewriting
- `--safe`
- `--output <path>`

## Parameters that don't apply

- `--seed` — not in the honoring set
- `--negative` — not supported
- `--transparent` — no alpha output

## CLI

Single-image edit:

```bash
SRC_URL=$(polli upload ./portrait.jpg --json | jq -r .url)

polli gen image "same composition, but change the sweater color to emerald green and add soft window light from the left" \
  --model kontext --image "$SRC_URL" --output portrait_edit.jpg
```

Multi-reference (style transfer):

```bash
SCENE=$(polli upload ./photo.jpg --json | jq -r .url)
STYLE=$(polli upload ./painting.jpg --json | jq -r .url)

polli gen image "reimagine the first image in the painterly style of the second" \
  --model kontext --image "$SCENE,$STYLE" --output styled.jpg
```

Pure text-to-image (works but not Kontext's strength):

```bash
polli gen image "a Victorian botanical illustration of a sunflower" \
  --model kontext --output sunflower.jpg
```

## HTTP

```bash
curl -sS --fail-with-body -o edited.jpg \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/image/change%20sweater%20to%20emerald?model=kontext&image=$SRC_URL"
```

## Prompt tips

- **Phrase edits as transformations, not rewrites.** *"Same composition, but..."*, *"keep the subject, change X"*, *"preserve the framing, add Y"*. Kontext is trained on "edit this, don't replace it" patterns.
- **Name what to preserve AND what to change.** Single-clause prompts like *"make it blue"* ask the model to guess what "it" refers to. *"Change the car's paint to metallic blue, keep the background and lighting"* reliably hits the right thing.
- For **multi-reference prompts**, the first image is usually the target (what gets edited) and later images are style / content references. Describe the role of each: *"reimagine the first image in the style of the second"*.
- **Composition moves are harder than attribute moves.** Color/texture/lighting changes → reliable. Adding or removing objects → less reliable; use `gptimage` / `nanobanana` if the edit is structural.

## When `kontext` vs `klein`?

Both are free-tier-accessible image editors in the FLUX family. Rough split:

- **`klein`** (0.01 pollen/token, 4× cheaper than `kontext`): the default choice for quick edits and t2i. Good at broad-stroke changes.
- **`kontext`** (0.04 pollen/token): reach for it when edits are **subtle or context-dependent** — maintaining subject identity across a scene change, transferring style between two specific references, localized attribute changes that require understanding "what belongs here".

Prototype on `klein` first; escalate to `kontext` if the edit isn't respecting context.

## Known limits

- No seed support → harder to iterate deterministically. Generate a few variants and pick.
- No negative prompt → specify what to preserve explicitly rather than what to avoid.
- Structural edits (adding/removing objects, geometry changes) are less reliable than attribute edits. For heavy structural work, `gptimage` / `nanobanana-pro` do better.
- Per-token cost is high for a free-accessible model — audit `polli usage` if you're iterating heavily.
