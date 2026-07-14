# fofr/face-swap-with-ideogram

Model page: https://replicate.com/fofr/face-swap-with-ideogram

**Not a classical face-swap.** This is a pipeline that uses **Ideogram's character-reference feature** to re-generate the target image with the character's identity substituted in. The result is a new Ideogram generation, not pixel-level grafting of one face onto another — so lighting, pose, and background all match the target scene naturally (but the target image is re-rendered, not preserved).

## The pipeline

```
  character_image           target_image
        │                        │
        │                        ▼
        │               [optional: Claude describes the target → prompt]
        │                        │
        ▼                        ▼
  Ideogram (character mode) — generates new image with character's identity
                │
                ▼
  [optional: Nano Banana cleanup pass fills missing elements]
                │
                ▼
              Output
```

Two notable design choices:

1. **Prompt is optional** — if omitted, the model internally calls Claude to caption the `target_image` and uses that as the Ideogram prompt.
2. **Optional cleanup** via Google's Nano Banana for post-fixing missing elements (logos, background objects, etc.).

## When to use this vs. a traditional face-swapper

- **Use this** when you want the result to look like a _new Ideogram image in the style of the target_ with a specific person's identity — e.g., "put this person into an ad mockup", "make this character appear in a travel poster".
- **Use a classical face-swap model** (`xlabs-ai/flux-ip-adapter` + face embeds, `fofr/face-to-many`, `lucataco/faceswap`, etc.) when you need to _preserve the target image pixel-for-pixel_ and only change the face region.

## Input schema

| Field             | Type         | Required | Default | Description                                                                                   |
| ----------------- | ------------ | -------- | ------- | --------------------------------------------------------------------------------------------- |
| `character_image` | string (URI) | ✅       | —       | Reference image of the character whose face/identity to use.                                  |
| `target_image`    | string (URI) | ✅       | —       | Target scene/composition. The output will re-render this scene with the character's identity. |
| `prompt`          | string       |          | auto    | Optional. If omitted, Claude analyzes `target_image` to generate a prompt.                    |
| `cleanup`         | boolean      |          | `false` | Run a final Nano Banana pass to add any missing elements that Ideogram left out.              |

Local file paths for `character_image` and `target_image` are auto-uploaded by `run_model.py`.

## Output

Single URI to the generated image. Saved as `fofr_face-swap-with-ideogram_0.png` (or whatever extension Ideogram returns).

## Examples

**Minimal (auto-prompt via Claude):**

```bash
python scripts/run_model.py fofr/face-swap-with-ideogram \
    --input '{
      "character_image": "./person_headshot.jpg",
      "target_image": "./target_scene.jpg"
    }' \
    --output ./out/
```

**Explicit prompt for more control:**

```bash
python scripts/run_model.py fofr/face-swap-with-ideogram \
    --input '{
      "character_image": "./person_headshot.jpg",
      "target_image": "./beach_poster.jpg",
      "prompt": "A vintage 1960s travel poster style illustration of a person standing on a tropical beach at sunset, bold typography reading VISIT BALI"
    }' \
    --output ./out/
```

**With cleanup pass to catch missing props:**

```bash
python scripts/run_model.py fofr/face-swap-with-ideogram \
    --input '{
      "character_image": "./person.jpg",
      "target_image": "./complex_scene.jpg",
      "cleanup": true
    }' \
    --output ./out/
```

## Tips

- **Good character image:** clear, well-lit, face-forward, neutral expression. Ideogram's character-reference keys off a clean identity signal.
- **Explicit prompts help with style.** Since Ideogram is strong at typography and illustration styles, a manually written prompt beats the auto-caption when you want a _specific_ look (comic cover, movie poster, magazine spread).
- **Cleanup is worth trying** when the target has distinctive props or text — Ideogram may drop them; Nano Banana can add them back.
- **Identity fidelity** won't be photo-perfect because it's generated, not grafted. Expect "recognizably the same person" rather than "identical."

## Gotchas

- **Output is a new image, not edited target.** If you need to preserve the exact target pixels/composition outside the face region, this is the wrong model.
- **Face-only identity.** Hair, body, and clothing in the output come from the Ideogram generation, not the character image.
- **Auto-prompt quality varies.** If the target is abstract or unusual, Claude's caption may miss nuance — writing your own prompt is usually better for non-trivial cases.
- **Multi-step pipeline = multi-cost.** You pay for Ideogram + Claude (when auto-prompting) + Nano Banana (when `cleanup: true`). No explicit pricing on the page; each sub-step bills separately under the hood.
