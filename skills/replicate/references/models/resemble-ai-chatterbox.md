# resemble-ai/chatterbox

Model page: <https://replicate.com/resemble-ai/chatterbox>

**Resemble AI's Chatterbox** is an open-source (MIT) text-to-speech model with **zero-shot voice cloning** from a short reference audio clip and a single-knob **emotion exaggeration** control — the first open TTS to ship that slider. Where `suno-ai/bark` leans on bracketed tags (`[laughs]`, `[sighs]`) and a fixed set of ~131 preset voices to get expressiveness, Chatterbox gets there with a continuous `exaggeration` scalar and any reference `.wav`/`.mp3` you upload. Bark also hard-caps at ~13 s of speech per run and has a grainier, lower-sample-rate timbre; Chatterbox is natural-sounding, production-grade, has no built-in chunking cap, and clones a target speaker in a few seconds of audio. Conceptually it occupies the open-source slot that XTTS v2 held and competes head-to-head with ElevenLabs on expressivity benchmarks (Resemble's own side-by-side evals — take with salt). Pick Chatterbox when you want **natural long-form TTS in a specific cloned voice with tunable emotional intensity**; pick Bark for laughter/sighs/sung-music nonverbals or when you don't have a reference voice; pick ElevenLabs when you need ultra-low-latency production inference and are okay with a closed API. Every output is watermarked via Resemble's **Perth** perceptual watermarker — imperceptible but detectable.

## Input schema

| Field          | Type         | Required | Default | Range      | Description                                                                                                         |
| -------------- | ------------ | -------- | ------- | ---------- | ------------------------------------------------------------------------------------------------------------------- |
| `prompt`       | string       | yes      | —       | —          | Text to synthesize. No hard character cap exposed in the schema, but see gotchas — very long inputs can drift.      |
| `audio_prompt` | string (URI) |          | —       | —          | Reference voice clip for zero-shot cloning. Omit to use the built-in default voice. Local paths auto-upload.        |
| `exaggeration` | number       |          | `0.5`   | `0.25`–`2` | Emotion / expressiveness dial. `0.5` = neutral. Higher = more dramatic, animated delivery. Extreme values unstable. |
| `cfg_weight`   | number       |          | `0.5`   | `0.2`–`1`  | CFG / pace weight. Lower = faster, looser pacing; higher = slower, more deliberate, closer to the reference rhythm. |
| `temperature`  | number       |          | `0.8`   | `0.05`–`5` | Sampling temperature for the token LM. Lower = more consistent but flatter; higher = more varied but flakier.       |
| `seed`         | integer      |          | `0`     | —          | `0` = random. Set to reproduce a specific take.                                                                     |

Only `prompt` is required. The default-example run uses `cfg_weight=0.5`, `temperature=0.8`, `exaggeration=0.5` — a safe neutral baseline. There is **no** explicit `language`, `chunk_length`, or `output_format` field in the schema.

## Output

A **single URI** — unlike Bark, this is a bare string, not a dict:

```json
"https://replicate.delivery/.../output.wav"
```

Confirmed `.wav` container (24 kHz mono, based on the default example). `run_model.py` saves it as `resemble-ai_chatterbox_output_0.wav` in the `--output` directory.

## Pricing and runtime

- Pricing is **not explicitly published on the model page** as a per-run or per-dollar figure. Chatterbox runs on Replicate's hardware-tiered pricing — you pay per GPU-second on whatever tier this model is pinned to (historically T4 or L40S for a model of this size). **Guessed** ~\$0.02–\$0.05 per short run based on comparable open-source TTS models on Replicate; **confirm on the model page's "Run with an API" section** before relying on this.
- **Confirmed** typical prediction time: ~13 seconds for the default 809-character example (~64 characters/second synthesis rate, per the run log). Short utterances (<100 chars) finish in a couple of seconds.
- Run count to date: ~273,000 — mature and well-exercised.
- License: **MIT**, self-hostable. GitHub: <https://github.com/resemble-ai/chatterbox>. Watermarking (Perth) is baked in and not optional on the Replicate deployment.

## Examples

**1. Default voice, plain speech — no cloning, neutral delivery:**

```bash
python scripts/run_model.py resemble-ai/chatterbox \
    --input '{
      "prompt": "Welcome to the show. Today we are talking about the long, strange history of sourdough bread.",
      "exaggeration": 0.5,
      "cfg_weight": 0.5,
      "temperature": 0.7
    }' \
    --output ./out/
```

Skip `audio_prompt` entirely to use the built-in default voice — this is the fastest path to a usable read-aloud WAV.

**2. Voice-cloned, neutral tone — clone from a reference clip:**

```bash
python scripts/run_model.py resemble-ai/chatterbox \
    --input '{
      "prompt": "Thank you for calling Riverside Dental. Please hold while we connect you to the next available assistant.",
      "audio_prompt": "./reference_voice.wav",
      "exaggeration": 0.4,
      "cfg_weight": 0.6,
      "temperature": 0.7
    }' \
    --output ./out/
```

Slightly lowered `exaggeration` and bumped `cfg_weight` for a calm, professional read. `run_model.py` auto-uploads the local `reference_voice.wav` — expect 8–20 seconds of clean, single-speaker audio for best cloning.

**3. Voice-cloned, high exaggeration — dramatic delivery:**

```bash
python scripts/run_model.py resemble-ai/chatterbox \
    --input '{
      "prompt": "You cannot be serious! After everything we have been through — YOU are the one who took the map?!",
      "audio_prompt": "./actor_reference.wav",
      "exaggeration": 1.2,
      "cfg_weight": 0.4,
      "temperature": 0.9,
      "seed": 42
    }' \
    --output ./out/
```

`exaggeration=1.2` pushes the delivery toward shouted / emotional; `cfg_weight=0.4` lets the pacing breathe. Fix `seed` so you can retake the same intense read deterministically. Creep past ~1.5 and the model starts distorting — see gotchas.

## Strengths

- **Natural long-form speech** — consistent timbre across sentences, noticeably less "TTS-flat" than Bark or older open models like XTTS.
- **Zero-shot cloning** from a few seconds of clean reference audio. No fine-tuning step, no separate speaker-embedding model.
- **Single-knob emotion control** (`exaggeration`) — one scalar replaces the tag-juggling in Bark and the style-preset menus in other TTS systems.
- **Open-source, MIT-licensed** — you can self-host via the GitHub repo for zero marginal cost, or fine-tune to a specific speaker.
- **Perth watermark** on every output — a real feature if you care about provenance / deepfake detection.

## Gotchas

- **Reference audio quality dominates clone quality.** Noisy, reverberant, or music-bedded reference clips produce noisy, reverberant clones — the model reproduces the _room_, not just the voice. Use clean, dry, single-speaker audio; 8–30 seconds is the practical sweet spot. Too short (<5 s) = weak identity; too long doesn't help.
- **`exaggeration` is nonlinear.** `0.5` is neutral, `0.7–1.0` is noticeably more animated, `1.2–1.5` is theatrical, and `>1.5` drifts into robotic / unstable / glitchy territory fast. If you push `exaggeration` high, **also lower `cfg_weight`** (try `0.3–0.4`) — the model's own tooling recommends this to keep pacing stable under heavy emotion.
- **No explicit chunking or length cap** in the schema, but practically very long prompts (many paragraphs) can drift — voice identity may soften, pacing may wander. For audiobook-length scripts, **chunk at sentence or paragraph boundaries and reuse the same `audio_prompt` + `seed`** for continuity, then concatenate the WAVs.
- **Language support is effectively English-centric.** Upstream Chatterbox is trained primarily on English; multilingual output is not advertised on the Replicate page and non-English prompts may produce heavily accented or phonetically broken results. For other languages, use Bark (13 languages built-in) or XTTS v2.
- **No `language` field, no `output_format` field, no streaming** on the Replicate endpoint — you get a WAV URL back at the end of the prediction.
- **Consent / ethics for voice cloning.** You are responsible for having permission to clone the voice in `audio_prompt`. Cloning a public figure or someone without their consent is legally and ethically fraught — and the Perth watermark means the output _will_ be detectable as synthetic. Resemble AI's own policy guidance lives at <https://www.resemble.ai/>; read it before shipping product features that let end users upload arbitrary voices.
- **Output is a bare URI string**, not a dict (unlike Bark). SDK callers can use the returned value directly as a URL; `run_model.py` handles both shapes.
- **`seed=0` means random**, not "seed with zero" — set a nonzero integer for reproducibility.
