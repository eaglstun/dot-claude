# Keeping consistent characters / faces across video generations

Video models reroll the character on every call by default. Getting the same face, body, and wardrobe across shots takes deliberate conditioning. This guide covers the techniques available via Replicate, ranked from cheapest/weakest to most reliable.

## The five techniques, ranked

| Technique                 | Setup cost | Per-shot cost | Consistency  | When to use                                                                |
| ------------------------- | ---------- | ------------- | ------------ | -------------------------------------------------------------------------- |
| Seed + prompt lock        | none       | baseline      | ★☆☆☆☆        | Draft/storyboard pass only                                                 |
| Reference-image input     | none       | baseline      | ★★★☆☆        | 1–7 shots of the same character, no training budget                        |
| First-frame lock (I2V)    | 1 image    | +~$0.03       | ★★★★☆        | Hero character in a single scene; strongest for short takes                |
| Face swap on output       | none       | +~$0.03–0.05  | ★★★★☆ (face) | Character's face matters, body/wardrobe can drift                          |
| LoRA train on the subject | ~$2–4      | baseline      | ★★★★★        | Same character across many scenes/projects; worth amortizing training cost |

Mix techniques: LoRA-trained hero frame → I2V with first-frame lock → face swap as a cleanup pass is the "belt and suspenders" version.

---

## 1. Seed + prompt lock (weakest)

Same `seed`, identical character description in every prompt.

```text
"A woman, early 30s, shoulder-length auburn hair, freckles, wearing a navy
peacoat over a cream turtleneck, walking through [scene]. Cinematic, 50mm."
```

Works within a single model call sharing temporal coherence (e.g. multi-shot mode on `kwaivgi/kling-v3-video` or `pixverse/pixverse-v6` via `generate_multi_clip_switch`). Doesn't reliably work across separate calls — identity drifts even with identical seeds.

Use for storyboards or cost-capped drafts, not finals.

---

## 2. Reference-image conditioning (built-in on several models)

Several Replicate video models accept reference images that lock the character's identity. No training step, just feed images in.

### `bytedance/seedance-2.0` — up to 9 reference images

```json
{
  "prompt": "the character from the reference images, walking through a neon-lit Tokyo alley at night, handheld, 35mm",
  "image": ["./char_front.jpg", "./char_side.jpg", "./char_3q.jpg"],
  "duration": 5,
  "aspect_ratio": "16:9"
}
```

### `kwaivgi/kling-v3-omni-video` — up to 7 reference images, token syntax

```json
{
  "prompt": "<<<image_1>>> sitting at a café window, slowly stirring coffee, warm afternoon light",
  "mode": "pro",
  "reference_images": ["./char_hero.jpg", "./char_outfit.jpg"],
  "duration": 6,
  "aspect_ratio": "9:16",
  "generate_audio": true
}
```

The `<<<image_1>>>` token refers to the first reference image. Explicit tokens let you compose scenes like `<<<image_1>>> greets <<<image_2>>> at the door` for multi-character shots.

### `wan-video/wan-2.7-i2v` — first-frame-as-reference (see technique #3)

### Reference-image recipe

Give 3–7 reference images that cover:

- **1 hero frontal portrait** — clean, clear face, eyes to camera, neutral expression
- **1 three-quarter** — shows face shape from an angle
- **1 full-body** — locks proportions, wardrobe, posture
- **1–2 wardrobe details** if the outfit matters (shoes, accessories, hair from behind)
- **1 expression variety shot** — smile or talking — only if you want the model to attempt varied expressions

All references should share: same lighting character (if possible), same wardrobe, consistent hair. The model learns the _room_ and _outfit_ as much as the face — keep background simple.

---

## 3. First-frame lock (I2V pipeline)

Generate a polished hero still in an image model, then drive motion from it. The character is baked into the starting frame; the video model only has to animate it.

### Pipeline

```text
text-to-image (hero still) ──► image-to-video (motion)
   black-forest-labs/            wan-video/wan-2.7-i2v
   flux-dev-lora                 minimax/hailuo-2.3
                                 pixverse/pixverse-v6
                                 vidu/q3-pro
```

### `wan-video/wan-2.7-i2v`

```json
{
  "first_frame": "./hero_portrait.png",
  "prompt": "subtle breathing, slight head turn to camera, gentle smile, warm side lighting",
  "duration": 5,
  "resolution": "1080p"
}
```

### `minimax/hailuo-2.3`

```json
{
  "first_frame_image": "./hero_portrait.png",
  "prompt": "character steps forward, camera dollies in, subtle smile",
  "duration": 6
}
```

### First-last frame morph

`wan-2.7-i2v`, `pixverse/pixverse-v6`, and `vidu/q3-pro` accept a **second** image (`last_frame_image` / `end_image`) to lock both ends of the shot. This is the strongest consistency lever for short takes — the model interpolates _between_ two locked frames rather than drifting freely.

```json
{
  "first_frame": "./char_facing_left.png",
  "last_frame": "./char_facing_right.png",
  "prompt": "slow head turn from left to right, warm sunset light"
}
```

Per-shot cost stays normal; the hero-still generation is a one-time ~$0.03.

---

## 4. Face swap as a cleanup pass

Let the video model do what it wants with body, wardrobe, and scene — then swap the _face_ onto the output from a reference image.

### `fofr/face-swap-with-ideogram` (for stills)

```json
{
  "input_image": "./generated_character.png",
  "swap_image": "./your_reference_face.png"
}
```

For **video**, face-swap the hero still _before_ running I2V rather than post-hoc on every frame. Video face-swap has its own tools (outside the scope of Replicate's most common flows) — the Replicate-native pattern is:

1. Generate hero still (any image model)
2. Face swap the reference face onto the hero still
3. Run I2V from the swapped still

This preserves your reference face through the I2V step because modern video models respect the first-frame face strongly.

---

## 5. LoRA training — the durable option

A Flux Dev LoRA trained on 10–20 photos of your character will produce that character in any scene, any wardrobe, any lighting, across dozens of generations. Worth the setup if you're making more than ~5 shots of the same character.

### Dataset

- **10–20 images** (more ≠ better past ~25; quality dominates)
- **Varied angles**: frontal, 3/4, profile, full body, from behind
- **Varied expressions**: neutral, smile, talking, eyes closed
- **Varied lighting**: daylight, golden hour, indoor warm, neutral flash
- **Varied wardrobe** if the LoRA should generalize; **consistent wardrobe** if you want the outfit baked in
- **Plain backgrounds** when possible — the LoRA absorbs whatever backgrounds you feed it
- **No group shots** — one subject per image
- **Real photographs** beat AI renders for realism

### Training

Replicate's Flux LoRA trainers accept a zip of images + a caption file. After training you get a LoRA slug (`your-username/your-character-lora`) you plug into any LoRA-aware base model.

### Inference

```json
{
  "prompt": "ZIKI standing on a misty dock at dawn, wearing a black raincoat, cinematic",
  "hf_lora": "your-username/your-character-lora",
  "lora_scale": 1.0,
  "aspect_ratio": "16:9"
}
```

**Trigger word matters.** Every LoRA has an activation token (`ZIKI`, `sks person`, or whatever you set at training). Without it in the prompt, identity collapses.

### Pipeline with LoRA

```text
Flux Dev LoRA ──► hero still ──► I2V model ──► final clip
  (your char)       (scene 1)     (wan/hailuo/etc.)
                ──► hero still ──►
                    (scene 2)
                ──► hero still ──►
                    (scene 3)
```

This is the most reliable end-to-end: LoRA locks the face, per-scene stills lock wardrobe/lighting/pose, I2V only handles motion.

---

## Recommended workflows by use case

### "Short clip, one scene, one character"

1. Write a detailed character description
2. Generate 3–5 hero stills in `flux-dev-lora` (no LoRA, just description + seed)
3. Pick best one, run `wan-video/wan-2.7-i2v` with that as `first_frame`

Cost: ~$0.10–0.30 total.

### "Multi-shot narrative, same character, one project"

1. Generate hero still pack (3–7 images from different angles) in Flux Dev
2. Use `kwaivgi/kling-v3-omni-video` or `bytedance/seedance-2.0` reference-image mode with 3–5 of the stills
3. One call per scene, same references, vary the prompt

Cost: ~$0.30–0.50 per scene.

### "Same character across many projects / recurring"

1. Collect 15–20 real photos (or generate a consistent pack with method above)
2. Train a Flux Dev LoRA (~$2–4 one-time)
3. Use LoRA for all future hero stills; I2V with first-frame lock

Cost: ~$3 setup, then ~$0.10–0.40 per shot forever.

### "Real person (you or a consented subject)"

Same as LoRA path, with real photos. Always get explicit consent before training on someone. Replicate's ToS prohibits non-consensual cloning.

### "Motion/performance transfer (puppeteering a character)"

`bytedance/dreamactor-m2.0` takes one character image + one driving video, and retargets the driving performance onto the character. Best for "make this portrait act out this clip" workflows — single shot, up to 30s.

```json
{
  "image": "./my_character.png",
  "video": "./driving_performance.mp4"
}
```

---

## Common failure modes and fixes

| Symptom                                   | Likely cause                                  | Fix                                                              |
| ----------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------- |
| Face morphs between shots                 | No reference; relying on prompt only          | Add reference images or train a LoRA                             |
| Face stable, outfit drifts                | Wardrobe under-described                      | Add wardrobe-specific reference images or bake into LoRA dataset |
| Face stable early, drifts by end of clip  | Long clip, model loses identity lock          | Shorten duration, or use first + last frame morph                |
| Character looks "close but not right"     | References are too varied / different rooms   | Use cleaner, more consistent references                          |
| LoRA makes everyone look like the subject | Trigger word missing or `lora_scale` too high | Add trigger word; drop `lora_scale` to 0.7–0.9                   |
| Motion looks stiff when face is perfect   | I2V is over-respecting first frame            | Increase motion cues in prompt ("walks forward", "turns head")   |
| Side/profile shots fail                   | Only frontal references provided              | Add 3/4 and profile references, or include in LoRA dataset       |

---

## Cross-shot continuity checklist

Before rendering a final pass, verify:

- [ ] Same seed across shots when using models that support it (locks style tendencies)
- [ ] Identical character description text in every prompt (name, age, hair, wardrobe)
- [ ] References are the same across calls when using reference-image mode
- [ ] Lighting language is consistent ("golden hour", "warm practicals") or explicitly different by shot
- [ ] Aspect ratio is locked across shots unless you want obvious cuts
- [ ] One hero still per scene is the "ground truth" frame — generate it first, drive motion from it

---

## What doesn't work (yet)

- **Pixel-exact face identity across 10+ seconds** without first+last frame locks — modern models drift.
- **Consistent fine detail** (tattoos, freckles, asymmetric jewelry) — LoRAs help, pure prompting won't.
- **Same character across very different body types / ages** in one project — LoRA the youngest, prompt aging upward, or train separate LoRAs.
- **Character + complex choreography** — motion/expression transfer (`dreamactor-m2.0`) is your best bet; pure T2V will improvise.

When in doubt: generate the hero still separately, then drive motion from it. Locking the starting frame is the single biggest consistency win available in 2026.
