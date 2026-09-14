# fofr/flux-bad-70s-food

Model page: <https://replicate.com/fofr/flux-bad-70s-food>

**Novelty Flux LoRA: 1970s-cookbook-photography aesthetic.** A `flux-dev` LoRA by [fofr](https://replicate.com/fofr) trained on photos of unappetizing 1970s food — aspics, gelatin salads, molded tuna, beige casseroles, weirdly-plated meat loaf, hot-dog-wrapped-in-cheese-wrapped-in-bacon horrors — rendered in the distinctive low-fi commercial food-photography look of that era: harsh direct on-camera flash, blown highlights on sauces, yellowed color cast, overexposed meat, garnish-on-doily staging, slightly-out-of-focus product-catalog framing. The model description is a single sentence: "Flux dev lora trained on photos of 1970s food." There is no README.

**This is explicitly a fun / meme / shitpost LoRA, not a serious food-photography tool.** It produces intentionally _bad_ food photos. If you want an appetizing image of food, this is the wrong endpoint.

## When to pick it over alternatives

- **Pick over `aramintak/flux-film-foto`** when you want a _specific_ historical look (1970s commercial food photography with its unique flash-harsh/color-shifted/gross-garnish aesthetic), not a general neutral film emulation. Film-foto gives you "photographed on film"; this gives you "photographed for a 1974 Jell-O pamphlet."
- **Pick over `levelsio/lomography`** for era-specificity. Lomo is toy-camera analog look (light leaks, saturated vignettes, cross-processed color) — adjacent but different decade and different visual language. This LoRA is specifically the _commercial-photo-studio-with-bad-taste_ vibe.
- **Pick over generic Flux + prompt `"1970s cookbook photo"`** when you want the aesthetic reliably. Vanilla Flux with the right prompt gets 60–70% of the way there — this LoRA nails the specific color cast, flash-harshness, and "this food looks wrong" staging that plain prompting under-specifies.
- **Sweet spot:** meme content, aesthetic shitposts, album art, parody-cookbook covers, retro-editorial illustrations, "what if [modern food] were in a 1974 church-group cookbook" projects, "weird food Twitter" content.
- **Don't pick it for:** actual food photography, menu shots, recipe-blog images, food-delivery app content, or anything where you want the food to look _good_. The whole point is that it looks bad.

## Input schema

This is the stock Replicate `flux-lora-trainer` inference template — every Flux-dev LoRA knob is exposed.

| Field                    | Type         | Required | Default  | Description                                                                                                                                                                                   |
| ------------------------ | ------------ | -------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                 | string       | yes      | —        | Text prompt. **Include the phrase `"bad 70s food"` (or close variants like `"1970s food"`) to activate the trained style** — see Gotchas. The default example is `"A photo of bad 70s food"`. |
| `image`                  | string (URI) |          | —        | Input image for img2img / stylization. If omitted, runs in pure txt2img mode. Local paths are auto-uploaded by `run_model.py`.                                                                |
| `mask`                   | string (URI) |          | —        | Inpainting mask. White = regenerate, black = preserve. Requires `image`. Disables `aspect_ratio` / `width` / `height`.                                                                        |
| `aspect_ratio`           | enum         |          | `"1:1"`  | Standard Flux ratios (`1:1`, `16:9`, `9:16`, `3:2`, `2:3`, `4:3`, `3:4`, `4:5`, `5:4`, `21:9`, `9:21`) or `"custom"` to use `width`/`height`. Default example uses `"3:2"`.                   |
| `height`                 | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest multiple of 16. Incompatible with `go_fast`.                                                                             |
| `width`                  | integer      |          | —        | 256–1440. Only used when `aspect_ratio="custom"`. Rounded to nearest multiple of 16. Incompatible with `go_fast`.                                                                             |
| `prompt_strength`        | number       |          | `0.8`    | img2img tuning knob. 0.0 = preserve input, 1.0 = full destruction. `0.75–0.9` is the sweet spot for restyling a real food photo into the bad-70s look.                                        |
| `model`                  | enum         |          | `"dev"`  | `"dev"` (28 steps, best quality) or `"schnell"` (4 steps, fast/cheap).                                                                                                                        |
| `num_outputs`            | integer      |          | `1`      | 1–4.                                                                                                                                                                                          |
| `num_inference_steps`    | integer      |          | `28`     | 1–50. 28 for `dev`, 4 for `schnell`.                                                                                                                                                          |
| `guidance_scale`         | number       |          | `3`      | 0–10. Flux likes low values; 2.5–3.5 band. Default example used `3.5`. Higher = more prompt-literal, less photographic.                                                                       |
| `seed`                   | integer      |          | random   | Set for reproducibility.                                                                                                                                                                      |
| `output_format`          | enum         |          | `"webp"` | `"webp"`, `"jpg"`, or `"png"`.                                                                                                                                                                |
| `output_quality`         | integer      |          | `80`     | 0–100. Ignored for PNG.                                                                                                                                                                       |
| `disable_safety_checker` | boolean      |          | `false`  | Disable NSFW filter.                                                                                                                                                                          |
| `go_fast`                | boolean      |          | `false`  | fp8-quantized fast path. Faster/cheaper, slight quality loss. Incompatible with custom `width`/`height`. **Silently multiplies `lora_scale` by 1.5x — see Gotchas.**                          |
| `megapixels`             | enum         |          | `"1"`    | `"1"` (~1MP) or `"0.25"` (~0.25MP). Ignored when `width`/`height` set or `image` provided.                                                                                                    |
| `lora_scale`             | number       |          | `1`      | -1 to 3. **Effect-strength knob.** 0 = none, 1 = trained strength, >1 = exaggerated. With `go_fast` Replicate auto-applies a 1.5x multiplier.                                                 |
| `replicate_weights`      | string       |          | —        | Override the main LoRA. Almost never useful here — the whole point of this endpoint is its baked-in weights.                                                                                  |
| `extra_lora`             | string       |          | —        | Stack a second LoRA on top (Replicate slug, HuggingFace URL, CivitAI URL, or `.safetensors` URL).                                                                                             |
| `extra_lora_scale`       | number       |          | `1`      | -1 to 3. Strength of the stacked LoRA.                                                                                                                                                        |

## Output

An **array of URI strings** (length = `num_outputs`). With the default `num_outputs: 1` you get a one-element list. `run_model.py` saves them as `fofr_flux-bad-70s-food_0.<ext>` (and `_1.<ext>`, `_2.<ext>`, ... when `num_outputs > 1`). Extension follows `output_format` — default `.webp`.

## Pricing

**~$0.018 per run** on Nvidia H100 — roughly **55 runs per $1**. Predictions typically complete in **~13 seconds** at default settings. Cheap enough for bulk meme generation; fast enough for interactive iteration.

## Examples

**1. Specific canonical-bad-70s dish** (tuna salad molded in a fish shape — the platonic ideal of aspic horror). Note the activation phrase `"bad 70s food"` in the prompt:

```bash
python scripts/run_model.py fofr/flux-bad-70s-food \
    --input '{
      "prompt": "A photo of bad 70s food, a tuna salad molded in the shape of a fish, set on a lace doily, served on a harvest-gold plate, surrounded by parsley sprigs and olive slices for eyes, harsh on-camera flash, yellowed color cast",
      "aspect_ratio": "3:2",
      "guidance_scale": 3.5,
      "lora_scale": 1.0,
      "num_inference_steps": 28,
      "output_format": "webp"
    }' \
    --output ./out/
```

**2. Modern food given the treatment** (a 2020s dish dragged back into 1974 — works because the LoRA re-renders lighting, plating, and color):

```bash
python scripts/run_model.py fofr/flux-bad-70s-food \
    --input '{
      "prompt": "A photo of bad 70s food: an avocado toast with poached egg, plated on orange melamine, harsh direct flash, overexposed egg yolk, wilted parsley garnish, faded color, 1970s cookbook photography",
      "aspect_ratio": "4:5",
      "lora_scale": 1.1,
      "guidance_scale": 3.0,
      "num_inference_steps": 28,
      "seed": 70
    }' \
    --output ./out/
```

**3. Scene with the aesthetic** (wider frame — a 1970s dinner-party table, everything wrong):

```bash
python scripts/run_model.py fofr/flux-bad-70s-food \
    --input '{
      "prompt": "Wide shot of a 1970s suburban dinner party table, bad 70s food everywhere: lime gelatin salad with suspended vegetables, a ham studded with pineapple rings and maraschino cherries, deviled eggs with paprika, brown casserole in a pyrex dish, olive-green tablecloth, harsh flash photography",
      "aspect_ratio": "16:9",
      "lora_scale": 1.0,
      "guidance_scale": 3.5,
      "num_inference_steps": 30,
      "num_outputs": 2,
      "output_format": "jpg",
      "output_quality": 90
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- The exact flash-harsh, yellowed-color-cast, blown-highlight, doily-and-parsley aesthetic of 1970s commercial food photography — nails it more reliably than plain Flux with a prompt describing the look.
- Aspics, gelatin salads, molded things, weird casseroles — the LoRA has strong priors for the _horror category_ of 1970s food, not just the photo style.
- Scene compositions (dinner tables, potlucks, holiday spreads), not just single-dish shots.
- Cheap (~$0.018) and fast (~13s) — viable for batch meme generation.
- Stacks with other LoRAs via `extra_lora` — e.g. combine with a named-character face LoRA for "what if [celebrity] were on a 1974 cookbook cover."

**Gotchas:**

- **Activation phrase required.** The default example uses `"A photo of bad 70s food"` — there is no `TOK` token here (fofr-trained LoRAs typically use natural-language captions, not the default trainer's `TOK` placeholder). **Include the phrase `"bad 70s food"` or `"1970s food"` somewhere in your prompt** or the LoRA barely activates and you get plain Flux food. No README confirms the exact trigger string, so `"bad 70s food"` from the default example is the safest canonical form; variants like `"1970s cookbook photo"`, `"1970s food photography"` also activate it to varying degrees.
- **This LoRA over-applies — it hits like a truck, not a whisper.** Unlike subtle film-tint LoRAs, this one commits hard to the aesthetic: your input food will look genuinely unappetizing, with blown flash highlights, off-color tones, and uncanny plating. At `lora_scale: 1.0` it's already aggressive. Drop to `0.6–0.8` if you want the vibe without full grossness; bump to `1.1–1.3` if you want maximum cursed-cookbook energy. Above ~1.5 things get abstract and lose food-identity.
- **`go_fast: true` silently multiplies `lora_scale` by 1.5.** At default `lora_scale: 1.0` + `go_fast: true` you're effectively running at 1.5, which pushes into over-cooked territory. Compensate by setting `lora_scale: 0.65–0.7` when `go_fast` is on, or leave `go_fast: false` for predictable scaling.
- **`prompt_strength` is the img2img knob** (only relevant when `image` is provided). 0.6–0.7 lets the input's composition show through with a 70s tint; 0.8–0.9 lets the LoRA rewrite the image aggressively. Above 0.9 you've effectively switched back to txt2img.
- **Face / identity preservation is poor.** Like all Flux-dev LoRAs, this will not reliably preserve facial identity in portraits. If your prompt includes a person eating the food, the person will be generic. For named-subject integration, stack an identity LoRA via `extra_lora` and accept that the food-style LoRA may compete with it for attention.
- **Intentionally bad output.** This is worth repeating: the LoRA was trained on unappetizing food and it produces unappetizing food. Do not reach for this when you want food that looks delicious — use a food-styling-focused model or plain Flux with an appetite-appeal prompt instead.
- **Max resolution 1440 on either axis** (Flux-dev limit). For larger outputs, chain into a dedicated upscaler.
- **Output is an array**, not a single string — index `[0]` when wiring the response.
- **No README / no GitHub link.** The model description is one sentence; the schema and default example are the source of truth. fofr's broader work: <https://replicate.com/fofr>.
- **Low run count (~1,000 runs lifetime as of 2026).** This is a genuine niche/meme LoRA, not a battle-tested production model. Expect occasional weirdness; seed-sweep for good takes.
