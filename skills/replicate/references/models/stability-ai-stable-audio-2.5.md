# stability-ai/stable-audio-2.5

Model page: <https://replicate.com/stability-ai/stable-audio-2.5>

Stability AI's **Stable Audio 2.5** is a text-to-audio diffusion model for **music and sound design** — not a TTS. From a single text prompt it generates up to **~3 minutes (190 s)** of stereo audio: full-structure instrumental tracks, genre mockups, ambience beds, foley, sound effects, and cinematic hits. The 2.5 generation is Stability's "enterprise" commercial release, trained on **fully-licensed data** so output is safe for commercial use. Upstream, the model supports audio-conditioned **continuation and inpainting** (extend a clip, fill a gap) — but see the gotchas: **that capability is not exposed on this Replicate endpoint**, which is prompt-only.

## When to pick Stable Audio 2.5 over alternatives

- **Pick it over `suno-ai/bark`** for anything longer than a bar or two of music, or any real sound-design / SFX work. Bark is a TTS with bracketed `[music]` / `♪...♪` hacks capped at ~13 s — a different tool. Stable Audio does 1 s to 190 s, with coherent structure, in stereo, at full resolution.
- **Pick it over `resemble-ai/chatterbox` / TTS models** whenever you want music or SFX instead of speech. Stable Audio does **not** generate lyrics or intelligible vocals — it is an **instrumental / SFX** model. If you want sung lyrics, use a vocal-music model (Suno, Udio, or a MusicGen+vocal pipeline).
- **Pick it over MusicGen / Riffusion** when you need longer clips with genuine song structure (intro / build / drop / outro), stereo output, or commercial-licensed training provenance. MusicGen tops out at ~30 s of mono by default; Stable Audio 2.5 goes to ~3 min stereo.
- **Pick vocal-music models (Suno, Udio, Lyria) instead** when you need real sung lyrics or a song with a top-line melody + words — Stable Audio is instrumental-only.
- **Sweet spot:** genre-tagged instrumental backings (~60–180 s), ambience and foley beds, SFX one-shots, trailer stings, production cues for video where you need royalty-safe music fast.

## Input schema

| Field       | Type    | Required | Default | Range   | Description                                                                                                                                                 |
| ----------- | ------- | -------- | ------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`    | string  | yes      | —       | —       | Text prompt describing the desired audio. Genre / mood / instrument / tempo keywords work far better than sentences — see prompt-format notes below.        |
| `duration`  | integer |          | `190`   | `1–190` | Length of generated audio, in seconds. `190` ≈ 3 min 10 s is the hard cap.                                                                                  |
| `steps`     | integer |          | `8`     | `4–8`   | Diffusion steps. Capped at 8 — the model is distilled for few-step sampling, so raising steps beyond 8 is not available. Drop to 4 for faster, lower-fi.    |
| `cfg_scale` | number  |          | `1`     | `1–25`  | Classifier-free guidance. `1` (the default) is very loose; `3–7` is the usual "more prompt-faithful" range; `>10` tends to over-cook / saturate. Start low. |
| `seed`      | integer |          | random  | —       | Random seed for reproducible runs. Leave blank for random. Reported back in the prediction logs (`Using seed: ...`) so you can capture and replay.          |

Only `prompt` is required. Notable gaps vs. the upstream Stable Audio 2.5 research release: **no `audio_prompt` / `init_audio` / `seconds_start` / `mask` / `negative_prompt` fields on this Replicate endpoint.** Continuation, inpainting, and audio-conditioned generation that Stability markets for 2.5 are **not wired up here** — the Replicate cog is prompt-only. If you need audio-to-audio, self-host via `stable-audio-tools` or use a different endpoint.

## Output

A **single URI** to an MP3 file — bare string, not a dict:

```json
"https://replicate.delivery/.../tmp_neuxeuk.mp3"
```

- Container: **MP3** (confirmed from the default-example output filename `tmp_neuxeuk.mp3`).
- Channels: **stereo** (Stable Audio 2.5 is a stereo model upstream).
- Sample rate: **44.1 kHz** upstream (not re-confirmed by this Replicate endpoint — assume 44.1 kHz stereo until proven otherwise).
- `run_model.py` saves it as `stability-ai_stable-audio-2.5_0.mp3` in the `--output` directory.

## Pricing and runtime

- **Pricing not published on the model page** as a per-run headline number. Replicate bills by GPU-second on the hardware this model is pinned to.
- **Confirmed** from the default example: a 90-second, 8-step generation completed in **5.8 s** of predict time (`"Generated audio in 5.8sec"`). That's ~15× realtime — extremely fast.
- **Estimated** cost per run: the cog runs on a high-tier GPU (behavior is consistent with L40S at ~\$0.000975/s or an A100 80GB at ~\$0.0014/s, per <https://replicate.com/pricing>). At ~6 s per run that's **roughly \$0.006–\$0.009 per generation** — call it ~\$0.01 to be safe. **Guessed, not confirmed** — verify in the "Run with an API" price estimator on the model page before running a batch.
- **Run count:** ~43,000 as of April 2026 — a well-exercised endpoint.
- **License:** the cog's LICENSE (<https://github.com/zsxkib/cog-stability-stable-audio-2.5/blob/main/LICENSE>) governs the wrapper; the underlying **Stable Audio 2.5 model is Stability's commercial-licensed release** ("commercially safe models, trained with advanced techniques on fully licensed datasets," per Stability's own page). Upstream tooling: <https://github.com/Stability-AI/stable-audio-tools>. Confirm the Stability license grant covers your use case (self-serve / on-platform is fine; bulk redistribution and enterprise-volume use may need a Stability agreement).

## Examples

**1. Basic text-to-music prompt — 90 s instrumental backing:**

```bash
python scripts/run_model.py stability-ai/stable-audio-2.5 \
    --input '{
      "prompt": "Pop, Pop-Electronic, Ballad, Billboard, Drum Machine, Bass, Lush Synthesizer Pads, Synthesizer Arp, Synth Bass, Vocal Sample Chops, Percussion, Honest, Heart-Felt, Melancholic, Vibe, Cool, Modern, Atmospheric, well-arranged composition, 115 BPM",
      "duration": 90,
      "steps": 8,
      "cfg_scale": 1
    }' \
    --output ./out/
```

This is the default-example prompt — a good baseline to confirm the endpoint works. Note the **comma-separated keyword style**: genre, subgenre, instruments, mood, descriptors, BPM. This format (not free-text sentences) is what Stable Audio was trained on and it handles it markedly better than narrative prompts.

**2. Sound-effects prompt — short foley / cinematic hit:**

```bash
python scripts/run_model.py stability-ai/stable-audio-2.5 \
    --input '{
      "prompt": "Cinematic impact, deep sub boom, metallic shimmer tail, reversed riser, dark trailer hit, dense reverb, 48000 Hz production quality",
      "duration": 6,
      "steps": 8,
      "cfg_scale": 3,
      "seed": 7
    }' \
    --output ./out/
```

Short durations (1–10 s) are the right range for SFX one-shots. Bump `cfg_scale` to `3–5` when you need the prompt's specific descriptors (e.g. "reversed riser") to actually land — the default `1` can drift toward generic ambience.

**3. Longer-form ambience bed — near the duration cap:**

```bash
python scripts/run_model.py stability-ai/stable-audio-2.5 \
    --input '{
      "prompt": "Ambient, Drone, Cinematic, slow evolving pads, distant field recording, rain on glass, tape hiss, warm analog, meditative, no drums, no percussion, A minor, 60 BPM",
      "duration": 180,
      "steps": 8,
      "cfg_scale": 2
    }' \
    --output ./out/
```

At 180 s (~3 min) you're near the hard cap. Include "no drums / no percussion" style negatives inline in the prompt — **there is no separate `negative_prompt` field** on this endpoint, unlike most image models. Key signatures (`A minor`) and tempo tags tend to be respected for tonal / pad material, less so for genre pop material.

> **Audio-to-audio / continuation:** not available on this Replicate endpoint. If that's the job, use `stable-audio-tools` upstream (<https://github.com/Stability-AI/stable-audio-tools>) or pick a different endpoint with `init_audio` support.

## Strengths / gotchas

**Good at:**

- Genre-tagged instrumental music with coherent structure at **60–180 s** length — the sweet spot.
- Stereo, near-production-quality output at ~15× realtime (a 90 s clip in ~6 s of GPU time).
- Sound design and SFX one-shots via short `duration` values — foley, cinematic hits, ambience.
- **Commercially-licensed training data** — the enterprise selling point over MusicGen / Riffusion / other open-source music models trained on scraped data.
- Responds well to **comma-separated keyword prompts** with `Genre, Instrument, Mood, Descriptor, BPM` structure.

**Gotchas:**

- **Prompt-only on Replicate, despite the page marketing continuation / inpainting.** The OpenAPI schema exposes only `prompt`, `duration`, `steps`, `cfg_scale`, `seed`. There is **no `audio_prompt` / `init_audio` / `audio_url` / `mask` / `seconds_start` field** — you cannot extend a clip or fill a gap via this endpoint. If you need those features, self-host `stable-audio-tools`.
- **No `negative_prompt` field.** Put exclusions inline in the main prompt (`"no drums, no vocals, no percussion"`) — the model respects these to a reasonable degree.
- **Instrumental only — no lyrics, no intelligible vocals.** You may get "vocal sample chops" or wordless "oohs/ahhs" when the prompt asks for them, but full sung lyrics are out of scope. For songs with lyrics use Suno / Udio / Lyria.
- **Prompt format matters a lot.** Comma-separated `Genre, Subgenre, Instruments, Mood, BPM` style (see the default example) outperforms narrative sentences like _"write me a sad pop song about ..."_. Stable Audio was trained with tag-style metadata; lean into that.
- **`cfg_scale=1` default is deliberately loose.** If the model is ignoring specific instruments / moods in your prompt, bump to `3–7`. Past `~10` it over-saturates and can produce distorted, clipping output.
- **`steps` is capped at 8.** This model is distilled for few-step sampling; higher step counts that work on other diffusion models are unavailable here. `4` is viable for quick previews.
- **190 s hard cap.** Anything longer requires generating multiple clips and crossfading — since continuation isn't exposed, seamless joins are not possible from this endpoint alone.
- **Sample rate / channel count not confirmed in Replicate logs** — upstream is 44.1 kHz stereo; assume the same until you inspect a real output file with `ffprobe`.
- **Output is a bare URI string** (not a dict like `suno-ai/bark`). `run_model.py` handles both shapes — saves as `stability-ai_stable-audio-2.5_0.mp3`.
- **Seed is logged, not returned.** When `seed` is left blank the model picks one and reports it in the prediction logs (`Using seed: 1025718006`) — parse the logs to capture it for replay, since it's not exposed in the response payload.
- **License is dual-layered.** Cog wrapper: see <https://github.com/zsxkib/cog-stability-stable-audio-2.5/blob/main/LICENSE>. Underlying model: Stability's commercial license. For high-volume or redistributed commercial use, check with Stability directly before you build product around it.
