# Fine-tuning a LoRA on a person's face (Flux Dev)

A companion to `character-consistency-guide.md`. That guide covers all five consistency techniques; this one goes deep on the most durable option: training a Flux Dev LoRA on a specific face.

**The trainer:** `ostris/flux-dev-lora-trainer` on Replicate. Training takes ~20–40 minutes and costs ~$2–5. Output is a model slug you can pass as `hf_lora` into any Flux-Dev-LoRA-aware endpoint.

**When to train:** you'll use the same face in 5+ generations, across varied scenes/wardrobes/lighting. Below that threshold, reference-image conditioning on Seedance/Kling is cheaper and good enough.

**Consent first:** if this isn't your own face, get explicit written consent from the subject. Replicate's ToS prohibits non-consensual cloning. This guide assumes you have consent (or it's you).

---

## 1. Build the dataset

Dataset quality is 80% of final LoRA quality. A great 15-image set beats a mediocre 40-image set every time.

### Image count

- **15–25 images** is the sweet spot for a face LoRA
- 10 works if they're excellent and varied
- Past ~30, you hit diminishing returns and start risking overfit to incidental details
- **Do not pad the set with mediocre shots.** Fewer, sharper images win.

### What to include

| Shot type                  | Count  | Why                                                               |
| -------------------------- | ------ | ----------------------------------------------------------------- |
| Frontal, neutral           | 3–5    | Anchors identity                                                  |
| Three-quarter (both sides) | 4–6    | Teaches face shape, cheekbones, jaw line                          |
| Profile                    | 2–3    | Nose, brow, chin silhouette                                       |
| Slight up / down angle     | 2–3    | Prevents "always shot from eye level" bake-in                     |
| Expression variety         | 3–5    | Neutral, slight smile, laughing, eyes closed — mouth/eye range    |
| Full-body or 3/4 body      | 2–4    | Proportions, posture (skip if you only need face)                 |
| Varied lighting            | spread | Daylight, golden hour, indoor warm, flat/cloudy — don't all match |

### What to avoid

- **Sunglasses / face-covering hats / masks** — the model will learn to generate them
- **Heavy filters or beauty-smoothing** — bakes in artificial texture
- **Group shots** — even if you crop, contamination risk is high
- **Low-res / blurry / heavy compression** — the model reproduces the blur
- **Strong uniform backgrounds** (same studio wall in every shot) — LoRA learns the room
- **All-identical wardrobe** — unless you specifically want the outfit baked in
- **Heavy makeup variance** — pick a "representative" look; massive makeup differences confuse the model
- **AI-generated or upscaled images** — use real photographs; synthetic data creates a feedback loop that exaggerates artifacts

### Preprocessing

- Crop to center on the face, but keep **some headroom and shoulders** — full-face close-ups cause "floating head" artifacts
- **Square crops preferred** (1024×1024); the trainer bucket-resizes but square is cleanest
- Strip EXIF if privacy matters
- Don't manually color-correct to make shots match — variety is a feature
- Zip all images into `dataset.zip`. No subfolders needed; no captions file required (captions are optional — see below)

---

## 2. Pick a trigger word

The trigger word is the activation token you put in every prompt to invoke the LoRA. Without it, the LoRA often stays dormant.

### Rules

- **Unique, not a real word.** `TOK`, `ZIKI`, `sks`, `ohwx`, `myface42` — anything the base model hasn't seen semantically. Avoid `"john"` or `"person"` — they collide with base-model knowledge.
- **Short is fine.** 3–6 characters is typical. Tokenizer doesn't care.
- **All-caps optional but conventional** — helps humans spot it in prompts.
- **Don't use names of real celebrities** — Flux has strong priors and you'll fight them instead of learning from scratch.

Pick one and use it in every training/inference prompt. Changing the trigger word later means retraining.

---

## 3. Captioning (optional but recommended)

Flux LoRA trainers support captions — a `.txt` file matching each image filename in the zip.

### Two schools of thought

**No captions (auto-caption mode):** the trainer uses a vision-language model to auto-caption each image. Easiest, produces good results, slightly less controllable.

**Manual captions:** write a short caption per image, always starting with the trigger word. Gives tighter control and usually better generalization to varied scenes.

### Manual caption template

Every caption starts with the trigger word, then describes **what's not the face**. The goal: teach the model to treat the face as the constant and everything else as variable.

```text
TOK a photo of a person, wearing a navy blazer, standing outdoors, golden hour lighting
TOK a photo of a person, wearing a white t-shirt, sitting at a cafe, soft window light
TOK a portrait of a person, red background, studio lighting
```

**Critical rule:** don't describe the face itself (no "green eyes, freckles, sharp jaw"). The LoRA should learn identity implicitly; captioning it makes the model treat it as something prompt-controllable and identity drifts.

### Zip layout for captioned training

```
dataset.zip
├── 001.jpg
├── 001.txt
├── 002.jpg
├── 002.txt
└── ...
```

Filenames must match exactly (extension aside). Txt files are plain UTF-8.

---

## 4. Training run

### Hyperparameters for face LoRAs

| Parameter       | Default   | Face-LoRA recommendation           | Why                                                                               |
| --------------- | --------- | ---------------------------------- | --------------------------------------------------------------------------------- |
| `steps`         | 1000      | **1000–1500**                      | Faces are information-dense — 1000 is usually enough with 15–25 images            |
| `lora_rank`     | 16        | **16 or 32**                       | 16 is fine for most faces; 32 if you need finer detail (freckles, scars, tattoos) |
| `learning_rate` | 4e-4      | **default**                        | Don't tune unless you see specific failure modes                                  |
| `optimizer`     | adamw8bit | **default**                        | Don't change                                                                      |
| `trigger_word`  | —         | **your chosen token**              | Required                                                                          |
| `autocaption`   | true      | **false** if using manual captions | Set to `true` if you didn't write captions                                        |
| `resolution`    | 512       | **1024** if budget allows          | Higher resolution = sharper face detail but ~2× longer/cost                       |
| `batch_size`    | 1         | **default**                        | Don't tune                                                                        |

### The Replicate call

```json
{
  "input_images": "https://your-bucket/dataset.zip",
  "trigger_word": "TOK",
  "steps": 1000,
  "lora_rank": 16,
  "resolution": 1024,
  "autocaption": false,
  "hf_repo_id": "your-hf-username/your-character-lora"
}
```

- `input_images`: must be a URL. Host the zip on S3, Hugging Face, or a GitHub release.
- `hf_repo_id`: optional but recommended — pushes the trained weights to HF for easy future inference. You'll need `HF_TOKEN` set on your Replicate account.
- Output is a Replicate model slug (`your-username/your-character-lora`) you can pass to any Flux-Dev-LoRA model.

### Runtime and cost

- 1000 steps @ 1024 resolution: ~25–35 minutes, ~$2.50–4
- 1500 steps @ 1024: ~40–50 minutes, ~$4–6
- 500 steps @ 512 (draft/test): ~10 min, ~$1 — use this to sanity-check dataset before committing to a full run

---

## 5. Validate the LoRA

Before trusting it on a final project, run a validation prompt set. Use `black-forest-labs/flux-dev-lora` with `lora_scale: 1.0`.

### The 5-prompt acid test

```text
1. TOK a photo of a person looking at the camera, neutral expression
2. TOK a photo of a person smiling, outdoor park, soft daylight
3. TOK a photo of a person in profile, studio lighting, black background
4. TOK a photo of a person wearing a red sweater, sitting at a desk
5. TOK a close-up portrait of a person, dramatic rim lighting
```

Render 2–4 outputs per prompt. What you're looking for:

- **Identity holds** across all five with obvious family resemblance to the dataset
- **Not rigidly one image** — each output should feel like a different photo of the same person, not a reprint of dataset image #1
- **Wardrobe / background / lighting actually changes** when you change the prompt — if everyone's wearing the same shirt from your training data, you've overfit
- **Face still recognizable at 3/4 and profile** — if only frontal works, your dataset was too frontal-heavy

### Lora_scale sweep

If identity feels off, sweep `lora_scale` at `0.7`, `0.85`, `1.0`, `1.15`:

- **< 0.8:** identity fades, becomes generic
- **0.9–1.1:** sweet spot
- **> 1.2:** over-applied, skin looks plastic, facial features exaggerated, poses become rigid

If the sweet spot is < 0.8 or > 1.2, the LoRA is under- or over-trained and you should retrain with different step count.

---

## 6. Common failure modes

| Symptom                                              | Diagnosis                                   | Fix                                                        |
| ---------------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------- |
| Everyone in the output looks like your subject       | `lora_scale` too high                       | Drop to 0.9, then 0.8                                      |
| Subject looks generic, not like them                 | Trigger word missing, or undertrained       | Check prompt; retrain with 1500 steps                      |
| Subject always faces camera, can't do profile        | Dataset too frontal-heavy                   | Retrain with more 3/4 and profile shots                    |
| Subject always wears one specific outfit             | Dataset had too-similar wardrobe            | Vary wardrobe or caption the wardrobe explicitly per-image |
| Output looks plastic / over-sharpened                | Overtrained                                 | Retrain with fewer steps (700–900) or lower `lora_rank`    |
| Weird artifacts on skin / double eyes                | Low-quality or inconsistent dataset         | Cull bad images, retrain                                   |
| Background always looks like dataset room            | Same background in too many training images | Diversify backgrounds or caption them out                  |
| Subject is recognizable close up but not at distance | Dataset all close-ups                       | Add full-body and mid-distance shots                       |
| Can't generate subject in unusual poses / angles     | Overfit to narrow pose range                | Add pose variety; drop `lora_scale` to 0.8                 |
| Face identity slowly drifts in long video clips      | LoRA on I2V isn't enough alone              | Use LoRA for hero still only → first-frame lock in video   |

---

## 7. Iteration loop

Good LoRAs often come from a second pass:

1. Train v1 on real photos
2. Generate 50–100 images with v1 across varied prompts (poses, lighting, wardrobe)
3. Hand-curate 20–30 of the best outputs — the ones where identity holds and variety is high
4. Train v2 using **real photos + curated synthetic outputs**. This often sharpens identity while broadening pose/scene coverage.
5. Validate v2 against the same 5-prompt acid test and compare

Don't train v2 on purely synthetic data — feedback loop will exaggerate any artifacts v1 introduced.

---

## 8. Using the LoRA downstream

### Flux Dev (images)

```json
{
  "prompt": "TOK standing on a misty dock at dawn, wearing a black raincoat, cinematic, 35mm",
  "hf_lora": "your-username/your-character-lora",
  "lora_scale": 1.0,
  "aspect_ratio": "16:9",
  "output_format": "png"
}
```

Model: `black-forest-labs/flux-dev-lora`.

### Stacked with a style LoRA

```json
{
  "prompt": "TOK portrait, illustrated in MSMRB style, dramatic lighting",
  "hf_lora": "your-username/your-character-lora",
  "lora_scale": 1.0,
  "extra_lora": "jakedahn/flux-midsummer-blues",
  "extra_lora_scale": 0.95
}
```

Model: `lucataco/flux-dev-multi-lora`. Start both scales near 1.0; if the style dominates, lower `extra_lora_scale` first.

### Feeding into video

LoRAs don't apply directly to most video models. The pattern is:

1. Generate a hero still with Flux Dev + your LoRA (`lora_scale: 1.0`)
2. Feed that still as `first_frame` / `first_frame_image` / `image` to your I2V model of choice
3. Let the video model handle motion; the face is locked in the starting frame

See `character-consistency-guide.md` for the full video pipeline.

---

## 9. Ethics and consent checklist

Before training on anyone's face, including your own:

- [ ] Subject (or you) has given explicit informed consent for this specific use
- [ ] You control access to the trained LoRA (don't publish it publicly without consent)
- [ ] You'll delete training data and weights if the subject withdraws consent
- [ ] Output won't be used to depict the subject doing things they didn't do, especially in contexts that could cause harm (NSFW, political, defamatory, criminal)
- [ ] If the subject is a minor, **don't train** — full stop

Replicate's ToS and most jurisdictions' biometric laws treat face models as sensitive personal data. Treat training weights like a password: valuable, revocable, and not to be shared.

---

## Quick reference: a good first-run config

```json
{
  "input_images": "https://your-bucket/dataset.zip",
  "trigger_word": "TOK",
  "steps": 1000,
  "lora_rank": 16,
  "resolution": 1024,
  "autocaption": true
}
```

- 20 photos, varied angles, expressions, and lighting
- Consented subject
- Budget: ~$3 and 30 minutes
- Expect: a usable face LoRA that clears the 5-prompt acid test at `lora_scale: 1.0`

If the result isn't there, the fix is almost always **in the dataset**, not the hyperparameters.
