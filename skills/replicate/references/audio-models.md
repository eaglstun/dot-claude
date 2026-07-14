# Audio models on Replicate

Model schemas drift; verify the model page on replicate.com before relying on exact field names or ranges. Deep-dives for each model live in `references/models/<slug>.md` — this file is a category selection guide, not a full reference.

## Selection guide

### Music / SFX generation

| Use case               | Model                           | Why                                                                             |
| ---------------------- | ------------------------------- | ------------------------------------------------------------------------------- |
| **text → music / SFX** | `stability-ai/stable-audio-2.5` | 1–190s stereo instrumental music, ambience, foley; fully-licensed training data |

### TTS / voice synthesis

| Use case                                | Model                        | Why                                                                                     |
| --------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------- |
| **Default expressive English TTS**      | `lucataco/orpheus-3b-0.1-ft` | Llama-3B LLM-native prosody, 4 preset voices, `<laugh>`/`<sigh>` tags, ~1–2 min per run |
| Multilingual / 131-voice preset menu    | `suno-ai/bark`               | 13 languages via `{lang}_speaker_{0..9}` presets, `[laughs]`/`[sighs]`/`♪...♪` tags     |
| Reference-audio voice cloning (general) | `resemble-ai/chatterbox`     | Zero-shot clone from 8–30s `audio_prompt` + emotion slider; MIT license                 |
| Non-English speech                      | `suno-ai/bark`               | 13 languages built-in — Orpheus `0.1-ft` is English-only, Chatterbox is English-first   |

### Speech-to-text / transcription

| Use case                            | Model                   | Why                                                                                                                                                         |
| ----------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| audio → transcript + speaker labels | `sabuhigr/sabuhi-model` | Whisper large-v2 + pyannote diarization — **but hard-capped at 1–2 speakers** and requires a user-supplied HF token. For new work prefer WhisperX wrappers. |

### Voice cloning / conversion

| Use case                         | Model                               | Why                                                                    |
| -------------------------------- | ----------------------------------- | ---------------------------------------------------------------------- |
| **Song cover in a preset voice** | `zsxkib/realistic-voice-cloning`    | Full AICoverGen pipeline: separate → convert → remix, 10 preset voices |
| Song cover in a custom voice     | `zsxkib/realistic-voice-cloning`    | Same model; pass `rvc_model: "CUSTOM"` + `.zip` URL                    |
| Stock-singer SVC (no training)   | `lucataco/singing_voice_conversion` | Amphion DiffWaveNetSVC, 15 fixed singers, auto-transpose               |
| Zero-shot TTS clone from clip    | `resemble-ai/chatterbox`            | `audio_prompt` + any text — not song covers, but general speech        |

### RVC pipeline (train your own voice)

| Step                   | Model                            | Output                                                |
| ---------------------- | -------------------------------- | ----------------------------------------------------- |
| **1. Build dataset**   | `zsxkib/create-rvc-dataset`      | YouTube URL → Demucs-separated vocal chunks `.zip`    |
| **2. Train RVC model** | `replicate/train-rvc-model`      | Dataset `.zip` → trained RVC `.zip` (`.pth`+`.index`) |
| **3. Run inference**   | `zsxkib/realistic-voice-cloning` | Source song + trained `.zip` URL → converted cover    |

### Pitch correction

| Use case             | Model              | Why                                                              |
| -------------------- | ------------------ | ---------------------------------------------------------------- |
| **Autotune a vocal** | `nateraw/autotune` | Classic PSOLA pitch correction, snaps to key or nearest semitone |

**Default pick when the user hasn't specified:** `lucataco/orpheus-3b-0.1-ft` with `voice: "tara"` for expressive English TTS (LLM-native prosody, `<laugh>`/`<sigh>` tags, ~1–2 min per run). Use `suno-ai/bark` when you need non-English speech or one of its 131 preset voices; use `resemble-ai/chatterbox` when the user wants to clone a specific voice from a reference audio clip. Call out that voice-cloning models (`realistic-voice-cloning`, `chatterbox` with `audio_prompt`) require consent from the person being cloned.

## Per-model schemas (common fields)

### stability-ai/stable-audio-2.5

```json
{
  "prompt": "Pop, Pop-Electronic, Ballad, Drum Machine, Bass, Lush Synthesizer Pads, Melancholic, 115 BPM",
  "duration": 90,
  "steps": 8,
  "cfg_scale": 1,
  "seed": 0
}
```

Notes: Stability's text-to-audio diffusion model for **music and sound design** (not TTS, not vocals). Generates 1–190 s of stereo instrumental audio per run — genre mockups, ambience, foley, SFX, cinematic stings. Commercially-licensed training data. Required input is `prompt` only; optional `negative_prompt` is **not exposed** — put exclusions inline (`"no drums, no vocals"`). `steps` is capped at **8** (distilled few-step sampler), `cfg_scale` default `1` is loose — bump to `3–7` for prompt-faithfulness. Prefers **comma-separated keyword prompts** (`Genre, Instrument, Mood, BPM`) over narrative sentences. Output is a **bare MP3 URI string** (stereo, 44.1 kHz assumed). **Pricing not published on the model page** — estimated ~$0.006–$0.009/run (guessed from ~6 s predict time on a high-tier GPU; verify in the playground estimator at <https://replicate.com/stability-ai/stable-audio-2.5>). **Signature gotcha: audio-conditioning is NOT exposed on the Replicate schema** despite Stability's 2.5 marketing touting continuation / inpainting — this endpoint is prompt-only (no `audio_prompt` / `init_audio` / `mask` / `seconds_start` fields). **Second gotcha: instrumental only, no lyrics / intelligible vocals** — for sung lyrics use Suno / Udio / Lyria. See [stable-audio-2.5](models/stability-ai-stable-audio-2.5.md).

### lucataco/orpheus-3b-0.1-ft

```json
{
  "text": "Wait — you brought the WRONG map? <laugh> Oh no. <sigh> Okay, I guess we are walking.",
  "voice": "tara",
  "temperature": 0.6,
  "top_p": 0.95,
  "repetition_penalty": 1.1,
  "max_new_tokens": 1200
}
```

Notes: Canopy Labs' **Orpheus 3B** (Llama-style 3B-parameter acoustic LLM), Apache 2.0, packaged as a Cog wrapper by lucataco. LLM-native prosody — phrasing, natural pauses and intonation feel much closer to a real speaker than classic encoder-decoder TTS. Four preset voices via enum `voice`: `tara` (default, female neutral American), `dan` (male mid-range), `josh` (male younger/brighter), `emma` (female alt) — **upstream Orpheus advertises more names like `leah`/`leo`/`jess`/`mia`/`zac`/`zoe`, but this `0.1-ft` checkpoint's schema enum only accepts the four above; anything else 422s**. Nine inline emotion tags using **angle-bracket syntax**: `<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`, `<sniffle>`, `<groan>`, `<yawn>`, `<gasp>`, `<uhm>` — **distinct from Bark's `[laughs]` square brackets; mixing them up reads the bracket literally or silently drops the tag**. No `seed` field (non-deterministic), no `language` field (**English-only** in practice). `max_new_tokens` defaults to `1200` (≈60–75s of speech), hard-capped at `2000` (~100–120s). `temperature` default `0.6` is already conservative — above ~0.9 the model starts to mispronounce or clip syllables. **$0.075/run on L40S** (confirmed, published on the model page), typical predict time ~77s (short utterances finish in ~10s). Output is a **bare URI string** (`.wav`), same shape as Chatterbox and stable-audio-2.5 (not a dict like Bark). See [lucataco/orpheus-3b-0.1-ft](models/lucataco-orpheus-3b-0.1-ft.md).

### suno-ai/bark

```json
{
  "prompt": "Wait — you brought the WRONG map? [laughs] Oh no.",
  "history_prompt": "en_speaker_6",
  "text_temp": 0.7,
  "waveform_temp": 0.7,
  "output_full": false
}
```

Notes: expressive TTS with bracketed nonverbal tags (`[laughs]`, `[sighs]`, `[music]`, `♪...♪`). `history_prompt` is an enum — 131 preset voices (`{lang}_speaker_{0..9}` across 13 languages, plus `announcer`). Hard ~13s cap per run; chain chunks via `output_full: true` → `prompt_npz` → `custom_history_prompt` for voice continuity. Output is a **dict** (`{audio_out, prompt_npz}`), not a bare URI. See [bark](models/suno-ai-bark.md).

### resemble-ai/chatterbox

```json
{
  "prompt": "Thank you for calling Riverside Dental. Please hold while we connect you.",
  "audio_prompt": "./reference_voice.wav",
  "exaggeration": 0.5,
  "cfg_weight": 0.5,
  "temperature": 0.8,
  "seed": 0
}
```

Notes: MIT-licensed TTS with **zero-shot voice cloning** from `audio_prompt` (8–30s of clean single-speaker reference). `exaggeration` is a nonlinear emotion dial (0.25–2, nominal 0.5); push past ~1.2 and also lower `cfg_weight` to 0.3–0.4 to stay stable. No chunk length cap but long prompts drift — chunk at paragraph boundaries with the same `seed`. Output is a **bare URI string**. Every output is Perth-watermarked. See [chatterbox](models/resemble-ai-chatterbox.md).

### sabuhigr/sabuhi-model

```json
{
  "audio": "https://example.com/interview.mp3",
  "language": "en",
  "hf_token": "hf_xxx_your_token_here",
  "model": "large-v2",
  "transcription": "srt",
  "min_speakers": 1,
  "max_speakers": 2
}
```

Notes: **Whisper large-v2 + pyannote speaker diarization** in a single call — transcribes audio and labels each segment with `SPEAKER_00` / `SPEAKER_01`. Hard-capped at **1–2 speakers** (`min_speakers` / `max_speakers` are enums of `{1, 2}`) — this is a two-party interview / phone-call / podcast tool, **not** a meeting/panel transcriber. **Requires a user-supplied `hf_token`** with accepted terms for `pyannote/speaker-diarization` on Hugging Face — no token → hard fail. `language` is **required and has no auto-detect** — accepts ISO codes (`en`, `ar`, `fr`, …) or full English names (`English`, …). `model` is `large` or `large-v2` only — no `large-v3`, no distil, no faster-whisper. `translate: true` runs Whisper's X→English task. `transcription` enum (`plain text` / `srt` / `vtt`) also populates `srt_file` / `txt_file` URIs. Output is a **structured JSON dict** — `segments[]` with per-word timings and `speaker` labels, a `transcription` string that is actually **stringified Python `repr()`** (don't JSON.parse it — parse `segments` instead), plus `detected_language`, `diarization_status`, and optional `srt_file` / `txt_file` URIs. `run_model.py` walks the dict and saves any URI-valued fields. ~**$0.055/run** on L40S (~18 runs/$), ~57 s predict / ~230 s on cold start (downloads Whisper large + pyannote segmentation + speaker-embedding weights). **Positioning:** this is a 2023-era single-author Cog wrapper pinned to `large-v2` with no GitHub / license URL. For new work **prefer WhisperX-based community wrappers** — `victor-upmeet/whisperx`, `thomasmol/whisper-diarization` — which support **N speakers** (not just 1–2), newer Whisper backends, and **don't require a user HF token**. Only reach for `sabuhigr/sabuhi-model` if you have an existing workflow wired to its exact `segments` shape or you specifically want this author's pipeline. Signature gotchas: `text` in the output is often `null` (concat `segments[*].text` for a full transcript); short utterances / overlapping speech frequently get the wrong speaker label or none at all. See [sabuhigr/sabuhi-model](models/sabuhigr-sabuhi-model.md).

### zsxkib/realistic-voice-cloning

```json
{
  "song_input": "./my-track.mp3",
  "rvc_model": "Drake",
  "pitch_change": "no-change",
  "index_rate": 0.5,
  "output_format": "mp3"
}
```

Notes: RVC v2 song-cover pipeline — separates vocals, converts, remixes with instrumental. `rvc_model` is an **enum**: `Squidward`, `MrKrabs`, `Plankton`, `Drake`, `Vader`, `Trump`, `Biden`, `Obama`, `Guitar`, `Voilin` (sic — typo frozen in schema), or `CUSTOM` + `custom_rvc_model_download_url`. Distinguish `pitch_change` (AI-vocal-only gender preset) from `pitch_change_all` (whole-mix semitone shift). See [realistic-voice-cloning](models/zsxkib-realistic-voice-cloning.md).

### lucataco/singing_voice_conversion

```json
{
  "source_audio": "./vocal_stem.wav",
  "target_singer": "Taylor Swift",
  "pitch_shift_control": "Auto Shift",
  "diffusion_inference_steps": 1000
}
```

Notes: Amphion DiffWaveNetSVC (**not RVC**) with a fixed 15-singer roster — 6 English (Adele, Beyonce, Bruno Mars, John Mayer, Michael Jackson, Taylor Swift) + 9 Chinese (Jacky Cheung 张学友, Faye Wong 王菲, …). Pass Chinese characters verbatim. **No custom model support** — use `zsxkib/realistic-voice-cloning` if you need a voice outside the enum. Source must be vocals only (run Demucs first). Halving `diffusion_inference_steps` ≈ halves runtime. See [singing_voice_conversion](models/lucataco-singing_voice_conversion.md).

### zsxkib/create-rvc-dataset

```json
{
  "youtube_url": "https://www.youtube.com/watch?v=...",
  "audio_name": "my_target_voice"
}
```

Notes: **YouTube-only** source — no local audio upload field. Runs Demucs `htdemucs` vocal separation + silence-based chunking, outputs a single `dataset_<audio_name>.zip` with `dataset/<audio_name>/split_<i>.mp3`. Trainer wants `.wav` but is tolerant of `.mp3` in practice. Single-speaker assumption — pick videos with one dominant speaker. See [create-rvc-dataset](models/zsxkib-create-rvc-dataset.md).

### replicate/train-rvc-model

```json
{
  "dataset_zip": "https://your-bucket/dataset_my_voice.zip",
  "sample_rate": "48k",
  "version": "v2",
  "f0method": "rmvpe_gpu",
  "epoch": 20,
  "batch_size": "7"
}
```

Notes: trainer, not inference. **`batch_size` is a string, not an int** (schema quirk — keep the JSON quotes). Dataset zip must unpack to `dataset/<rvc_name>/split_<i>.wav`. Epoch guidance: 30–50 for <10 min of data, 15–25 for 10–30 min, 10–15 for 30+ min. Output URL expires in ~1 hour — **download and re-host immediately** before feeding downstream. See [train-rvc-model](models/replicate-train-rvc-model.md).

### nateraw/autotune

```json
{
  "audio_file": "./vocal_stem.wav",
  "scale": "A:min",
  "output_format": "wav"
}
```

Notes: PSOLA pitch correction — preserves timbre, changes only the note. `scale` is a 25-value enum: `closest` (snap to nearest chromatic semitone, the T-Pain sound) or `{NOTE}:{maj|min}` covering 24 keys. **Accidentals are flats only** (`Db`, `Eb`, `Gb`, `Ab`, `Bb`) — use `Db:maj` for C#/Db major. Pick the wrong key and it destructively re-maps correct notes. No strength/mix knob. CPU-only — that's why it's <1 cent per run. See [autotune](models/nateraw-autotune.md).

## RVC pipeline workflow

This is the main chain for producing a song cover in a custom-trained voice. Each step outputs a Replicate CDN URL with a **~1-hour TTL** — re-host to stable storage (S3, HF, GitHub release asset) between steps or chain them in a single session.

```text
  YouTube URL (single speaker)
       │
       ▼
  zsxkib/create-rvc-dataset     ──►  dataset_<name>.zip
       │                                (dataset/<name>/split_<i>.mp3)
       │  (re-host, then pass as `dataset_zip`)
       ▼
  replicate/train-rvc-model     ──►  trained RVC model .zip
       │                                (.pth + .index inside)
       │  (re-host, then pass as `custom_rvc_model_download_url`,
       │   with `rvc_model: "CUSTOM"`)
       ▼
  zsxkib/realistic-voice-cloning ──►  converted song cover (mp3/wav)
```

Three sequential calls:

1. **Build dataset** — `zsxkib/create-rvc-dataset` with `youtube_url` + `audio_name`. ~40s–1m, ~$0.054.
2. **Train model** — `replicate/train-rvc-model` with `dataset_zip` URL, `epoch: 20`, `batch_size: "7"` (string!). ~6 min, ~$0.32.
3. **Run inference** — `zsxkib/realistic-voice-cloning` with `song_input` + `rvc_model: "CUSTOM"` + `custom_rvc_model_download_url`. ~2–3 min/song, ~$0.033.

**Skip step 1** if you already have a clean single-speaker audio file — hand-build the dataset zip matching `dataset/<name>/split_<i>.wav` (48 kHz mono, 5–15s chunks). **Skip steps 1–2** if one of the 10 preset voices in `realistic-voice-cloning` already fits (Drake, Vader, Obama, …).

## Audio-specific gotchas

- **TTS length caps.** Bark hard-caps at **~13 seconds per run** — longer prompts truncate or collapse into noise. For long scripts, chunk at <13s boundaries, chain `custom_history_prompt` from the previous run's `prompt_npz` (requires `output_full: true`), and concatenate WAVs. Chatterbox has **no explicit cap** in the schema but voice identity and pacing drift on multi-paragraph inputs — chunk at paragraph boundaries and reuse the same `audio_prompt` + `seed`. Orpheus caps via **`max_new_tokens`** (default `1200` ≈ 60–75s, hard ceiling `2000` ≈ 100–120s) — much more per-run capacity than Bark, but no `prompt_npz`-style continuity token; the named `voice` enum keeps consistency across chunks since voice identity isn't a latent.
- **Reference audio quality dominates clone quality.** For `chatterbox` `audio_prompt` and for RVC training datasets: the model reproduces the _room_, not just the voice. Feed clean, dry, single-speaker audio (8–30s for zero-shot, 10–30 min for RVC training). Reverb, background music, or multiple speakers in the reference → noisy, blurred clones.
- **Source must be vocals only for SVC/autotune.** `lucataco/singing_voice_conversion` and `nateraw/autotune` both expect isolated vocal stems — feed a full mix and pitch detection breaks. Run a stem separator (`ryan5453/demucs`, `cjwbw/demucs`) first. `zsxkib/realistic-voice-cloning` is the exception: it has Demucs built in and accepts full songs.
- **Perth watermarking on Chatterbox.** Every Chatterbox output carries Resemble's perceptual watermark — imperceptible but detectable. It's baked in on the Replicate deployment and not optional. Treat this as a feature for provenance, not a problem to bypass.
- **Legal / consent framing for voice cloning.** `realistic-voice-cloning` ships with preset voices of real public figures (Trump, Biden, Obama, Drake). Replicate's ToS prohibits non-consensual voice cloning of real people. Even fictional-character presets (Squidward, Vader) carry IP exposure. For commercial use, stick to characters you own the rights to or voices you've trained from your own recordings. Always tell the user before generating a clone of a real named person, and get explicit consent before training on someone's voice in `create-rvc-dataset` / `train-rvc-model`.
- **Output-format field inconsistency.** Shapes differ across models:
  - `suno-ai/bark` → **dict** `{audio_out, prompt_npz}` (small dict — one audio URI plus a continuation token). **Only TTS model in this skill whose output is a dict rather than a bare URI** — SDK callers must index `output["audio_out"]`.
  - `resemble-ai/chatterbox` → **bare URI string**
  - `lucataco/orpheus-3b-0.1-ft` → **bare URI string** (`.wav`, same shape as Chatterbox and stable-audio — NOT a dict like Bark)
  - `stability-ai/stable-audio-2.5` → **bare URI string** (MP3, stereo; not a dict like Bark)
  - `sabuhigr/sabuhi-model` → **large structured JSON dict** — `segments[]` with per-word timings + speaker labels, plus a `transcription` string (which is actually stringified Python `repr()`, **not** JSON — parse `segments` instead), plus optional `srt_file` / `txt_file` URIs. **First audio model in this skill whose output is a real data object rather than just an audio pointer.**
  - `zsxkib/realistic-voice-cloning`, `lucataco/singing_voice_conversion`, `zsxkib/create-rvc-dataset`, `replicate/train-rvc-model`, `nateraw/autotune` → **bare URI string**

  `run_model.py` handles all three shapes transparently — it walks dicts and saves any URI-valued fields (so STT `srt_file` / `txt_file` auto-download) — but SDK callers need to index `output["audio_out"]` for Bark, parse `output["segments"]` for sabuhi-model, and use the value directly for the URI-string models.

- **Sample-rate variance.** Bark and Chatterbox and `lucataco/singing_voice_conversion` all output 24 kHz mono WAV. RVC training (`replicate/train-rvc-model`) uses `sample_rate: "40k"` or `"48k"`. `realistic-voice-cloning` output is mp3/wav at song-native rates. `nateraw/autotune` preserves input rate. If you're mastering for music, upsample the 24 kHz outputs downstream — don't expect CD-quality masters from TTS/SVC models.
- **Output URL TTL ~1 hour.** Every Replicate CDN URL expires. For multi-step pipelines (especially RVC: dataset → train → inference), **download and re-host** between steps or run them back-to-back in one session.
- **Schema-quirk enums.** Several audio models fail with 422 on close-but-wrong preset names — `Voilin` (not `Violin`), `MrKrabs` (no space), `CUSTOM` (uppercase) in `realistic-voice-cloning`; `Db:maj` (flats only, no `C#:maj`) in `autotune`; `en_speaker_6` (not `en_narrator_6`) in Bark. Don't invent preset names — verify against the model page's enum list.

## Cost awareness

Audio models span a wide price range per call (confirm on replicate.com/\<model\>):

- `nateraw/autotune` — ~$0.007/run (CPU)
- `stability-ai/stable-audio-2.5` — ~$0.006–$0.009/run **(guessed — pricing not published on model page; verify in playground estimator)**. ~6 s predict time for a 90 s clip on a high-tier GPU.
- `suno-ai/bark` — ~$0.04/run (T4)
- `zsxkib/realistic-voice-cloning` — ~$0.033/run (T4, scales with song length)
- `resemble-ai/chatterbox` — ~$0.02–$0.05/run (hardware-tiered; confirm)
- `lucataco/orpheus-3b-0.1-ft` — **$0.075/run** (L40S, published; typical predict ~77 s; short utterances ~10 s)
- `zsxkib/create-rvc-dataset` — ~$0.054/run (L40S, scales with video length)
- `lucataco/singing_voice_conversion` — ~$0.11/run (L40S, 1000 diffusion steps)
- `replicate/train-rvc-model` — ~$0.32/run (L40S, ~6 min)
- `sabuhigr/sabuhi-model` — ~$0.055/run (L40S, ~57 s predict; cold start ~230 s while pyannote + Whisper-large weights download)

A full RVC pipeline (dataset → train → cover) runs ~$0.40–$0.50 end-to-end. Call out cost before training runs or batch SVC jobs; the cheap inference models don't need a heads-up.

## Quick picks

- **Music / SFX (text → audio):** `stability-ai/stable-audio-2.5` — 1–190 s stereo instrumental music, ambience, or SFX from a text prompt. Instrumental only (no lyrics). Prompt-only on Replicate — no `audio_prompt` / continuation even though Stability markets it upstream.
- **Default English TTS (expressive):** `lucataco/orpheus-3b-0.1-ft` with `voice: "tara"` — LLM-native prosody, inline angle-bracket emotion tags (`<laugh>`, `<sigh>`), ~1–2 min of speech per run, $0.075/run. Use when you want natural-sounding English narration and don't need a cloned voice.
- **Multilingual / 131-voice TTS:** `suno-ai/bark` with a chosen `history_prompt` and square-bracket tags (`[laughs]`, `[sighs]`, `♪...♪`) — 13 languages, 131 presets, ~13 s/run cap so chunk long scripts.
- **Reference-audio voice clone (general speech):** `resemble-ai/chatterbox` with `audio_prompt` — zero-shot clone from 8–30s clean reference; best when the target voice is specified by an audio sample rather than a preset name.
- **Cheap default narration (no preset hunting):** `resemble-ai/chatterbox` with default voice (no `audio_prompt`) — a few cents per run. Reach for Orpheus when you want more expressive delivery on the same material.
- **Song cover in a preset celebrity voice:** `zsxkib/realistic-voice-cloning` with `rvc_model: "Drake"` (or Vader, Obama, …).
- **Song cover in a stock studio singer (no training):** `lucataco/singing_voice_conversion` with `target_singer: "Taylor Swift"`.
- **Custom voice from a long audio source:** full RVC pipeline — `create-rvc-dataset` → `train-rvc-model` → `realistic-voice-cloning` with `rvc_model: "CUSTOM"`.
- **Autotune a vocal:** `nateraw/autotune` with `scale: "closest"` (T-Pain) or the song's actual key.
- **Transcription + diarization (1–2 speakers):** `sabuhigr/sabuhi-model` — Whisper large-v2 + pyannote. Requires a user HF token and is hard-capped at 1–2 speakers. For >2 speakers, newer Whisper backends, or no HF-token requirement, prefer WhisperX wrappers like `victor-upmeet/whisperx` or `thomasmol/whisper-diarization`.
