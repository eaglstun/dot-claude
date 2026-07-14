# zsxkib/create-rvc-dataset

Model page: <https://replicate.com/zsxkib/create-rvc-dataset>

GitHub: <https://github.com/zsxkib/voice-cloning-create-dataset>

**RVC v2 dataset builder** — the **upstream** step in the RVC voice-cloning pipeline. Point it at a **YouTube URL** and it downloads the audio, runs **vocal/instrumental source separation** (Demucs `htdemucs`), trims silence, splits the isolated vocal track into short clips, and hands back a **single zip** ready to drop into `replicate/train-rvc-model`. In other words: `YouTube URL → clean vocal chunks → trainable RVC dataset` in one call.

## Pipeline position

```text
  YouTube URL
       │
       ▼
  zsxkib/create-rvc-dataset   ──►  dataset_<audio_name>.zip
       │                             (dataset/<audio_name>/split_<i>.mp3)
       │  (pass zip URL as `dataset_zip`)
       ▼
  replicate/train-rvc-model   ──►  trained RVC .zip model
       │
       │  (pass URL as `custom_rvc_model_download_url`, `rvc_model: "CUSTOM"`)
       ▼
  zsxkib/realistic-voice-cloning (or other RVC inference)
       │
       ▼
  voice-converted audio / song cover
```

## Input schema

| Field         | Type   | Required | Default           | Description                                                                                                                                                |
| ------------- | ------ | -------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `youtube_url` | string | yes      | —                 | URL to the YouTube video to extract audio from. This is the only source input — **there is no direct audio-file upload field on this model**.              |
| `audio_name`  | string |          | `"rvc_v2_voices"` | Dataset name. Controls the internal folder (`dataset/<audio_name>/`) and the final zip filename (`dataset_<audio_name>.zip`). Freeform; keep it slug-safe. |

**Only YouTube is supported as a source.** There is no `audio_file` / URI input. If you already have a clean audio file (podcast, voice memo, studio take), skip this model and either upload to YouTube first or build the dataset yourself (see "Preparing a dataset" in `replicate/train-rvc-model.md`) — the expected layout is `dataset/<name>/split_<i>.wav` (note: the trainer expects `.wav`; this tool produces `.mp3` — see gotchas).

## Output

A **single URI** pointing to a zip archive (not a dict / not multiple files).

- Filename pattern: `dataset_<audio_name>.zip` (e.g. `dataset_andrew_huberman.zip`).
- Unzipped structure:

  ```text
  dataset/
  └── <audio_name>/
      ├── split_0.mp3
      ├── split_1.mp3
      ├── split_2.mp3
      └── ...
  ```

- Each `split_<i>.mp3` is a short isolated-vocal chunk (after Demucs separation and silence-based splitting).
- Saved by `run_model.py` as `zsxkib_create-rvc-dataset_0.zip`.

## Pricing and runtime

- Runs on **Nvidia L40S** hardware.
- Playground estimate: **~$0.054 per run** (~18 runs per $1) — varies with video length because billing is per-second on L40S.
- Typical prediction time: **~40s–1m** for a short clip (the Demucs separation stage dominates; longer YouTube videos scale roughly linearly).
- Confirm current pricing at <https://replicate.com/zsxkib/create-rvc-dataset> before batch runs.

## Examples

**1) Default — build a dataset from a YouTube video:**

```bash
python scripts/run_model.py zsxkib/create-rvc-dataset \
    --input '{
      "youtube_url": "https://www.youtube.com/watch?v=4b6bwcWK6GE",
      "audio_name": "andrew_huberman"
    }' \
    --output ./out/
```

**2) Minimal invocation (default `audio_name`):**

```bash
python scripts/run_model.py zsxkib/create-rvc-dataset \
    --input '{
      "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }' \
    --output ./out/
```

**3) Full RVC pipeline — dataset → train → cover (three sequential calls):**

```bash
# Step 1: build the dataset from YouTube
python scripts/run_model.py zsxkib/create-rvc-dataset \
    --input '{"youtube_url": "https://www.youtube.com/watch?v=XXXXXXX", "audio_name": "my_target_voice"}' \
    --output ./out/
# -> note the returned zip URL, then re-host it to stable storage (Replicate URLs expire ~1h)

# Step 2: train an RVC model on it
python scripts/run_model.py replicate/train-rvc-model \
    --input '{"dataset_zip": "https://your-bucket/dataset_my_target_voice.zip", "epoch": 20, "batch_size": "7"}' \
    --output ./out/

# Step 3: use the trained model for a song cover
python scripts/run_model.py zsxkib/realistic-voice-cloning \
    --input '{"song_input": "./source.mp3", "rvc_model": "CUSTOM", "custom_rvc_model_download_url": "https://your-bucket/trained.zip"}' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- One-call "turn a YouTube video into a trainable voice dataset" — handles download, vocal isolation (Demucs `htdemucs`), silence trimming, and chunking in a single step.
- Completely hands-off; only two inputs (URL + name).
- Output zip folder layout matches what `replicate/train-rvc-model` expects (`dataset/<name>/split_<i>.<ext>`), so the two models chain cleanly.

**Gotchas:**

- **YouTube-only source.** No `audio_file` / URI upload field exists. If your source is a local file, upload it to YouTube (unlisted) first, or skip this tool and hand-roll the dataset zip.
- **Output is `.mp3`, trainer expects `.wav`.** The zip contains `split_<i>.mp3` files, but `replicate/train-rvc-model`'s documented layout lists `split_<i>.wav`. In practice the trainer's ingestion is tolerant of either (the trainer re-encodes internally), but if you hit a format-related error, unzip, convert to 44.1kHz/48kHz mono WAV with `ffmpeg`, and re-zip with the same structure.
- **No user-tunable chunk length / silence threshold / sample rate.** The splitter's parameters are fixed internally (typical RVC target is ~5–10s clips; actual chunk length is whatever the silence-based splitter produces). If you need deterministic chunking, pre-process locally.
- **Source-separation quality is the ceiling.** Demucs does well on studio music and clean podcast audio but degrades on: loud overlapping speakers, heavy background noise (crowds, traffic), bandwidth-limited source (phone recordings), or music with prominent backing vocals. Garbage vocals in → garbage RVC model out.
- **Output URL TTL ~1 hour.** Download the zip immediately — or re-host to stable storage (S3, HF, GitHub release asset) — before feeding into the trainer, especially if there will be any gap between steps.
- **Video length drives cost and time** (L40S per-second billing). A 3–4 minute song produces plenty of 5–10s chunks; 30+ minute videos inflate runtime without proportional dataset quality gains. 10–30 minutes of clean target vocals is the typical RVC sweet spot — trim to the best single-speaker sections.
- **Single-speaker assumption.** The tool doesn't diarize: if the video contains multiple speakers or duets, you'll get mixed-speaker chunks and your trained RVC model will blend voices. Pick source videos with one dominant speaker throughout.
- **Legal / ethical:** YouTube ingestion doesn't grant usage rights. Downloading audio from YouTube may violate YouTube's Terms of Service and copyright law depending on the source. Voice-cloning output of real people without consent is prohibited by Replicate's ToS and is legally risky (right of publicity, defamation, deepfake statutes). Only use this with content you own or have explicit rights to clone.
