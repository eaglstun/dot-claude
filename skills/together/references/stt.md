# Together — speech-to-text (transcription & translation)

> **Script:** `scripts/stt.py audio.mp3 [--translate]` wraps both endpoints (handles multipart).

The inverse of `tts.md` — turn audio into text. Two OpenAI-compatible endpoints, both `multipart/form-data`:

- Transcribe (keep original language): `POST https://api.together.ai/v1/audio/transcriptions`
- Translate to English: `POST https://api.together.ai/v1/audio/translations`

The only difference is the output language: **transcription** returns text in the spoken language; **translation** always returns English. Request fields and response shapes are otherwise identical.

## Transcribe

```bash
curl -sS https://api.together.ai/v1/audio/transcriptions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F "file=@audio.mp3" \
  -F "model=openai/whisper-large-v3" \
  | jq -r '.text'
```

You can pass a public HTTPS URL instead of uploading bytes:

```bash
curl -sS https://api.together.ai/v1/audio/transcriptions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F "file=https://example.com/clip.mp3" \
  -F "model=openai/whisper-large-v3"
```

## Translate foreign audio → English

```bash
curl -sS https://api.together.ai/v1/audio/translations \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -F "file=@spanish.mp3" \
  -F "model=openai/whisper-large-v3" \
  | jq -r '.text'
```

## Request fields (form fields)

| Field                         | Notes                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------ |
| `file`                        | **Required.** Audio upload (≤500 MB) or public HTTPS URL (≤1 GB). Max 4 hours. |
| `model`                       | Default `openai/whisper-large-v3` (see models below)                           |
| `language`                    | ISO 639-1 code, or `auto` to detect. Defaults to `en`                          |
| `prompt`                      | Bias text to nudge decoding (Whisper models only)                              |
| `response_format`             | `json` (default) or `verbose_json`                                             |
| `temperature`                 | Float 0.0–1.0 (default 0)                                                      |
| `timestamp_granularities`     | `segment` and/or `word` — **`verbose_json` only**                              |
| `diarize`                     | Boolean — label speakers (transcription)                                       |
| `min_speakers`/`max_speakers` | Integer hints to improve diarization                                           |

Supported audio formats: `.wav .mp3 .m4a .webm .flac .ogg .opus .aac`.

## Response shapes

**`json`** (default) — just the text:

```json
{ "text": "Hello, world!" }
```

**`verbose_json`** — text plus metadata, timestamps, and (if requested) per-speaker segments:

```json
{
  "language": "english",
  "duration": 3.5,
  "text": "Hello, world!",
  "segments": [ ... ],
  "words": [ ... ],
  "speaker_segments": [ ... ]
}
```

## Models

| Model slug                    | $/audio-min | Notes                         |
| ----------------------------- | ----------- | ----------------------------- |
| `openai/whisper-large-v3`     | $0.0015     | **Default** — broad, accurate |
| `nvidia/parakeet-tdt-0.6b-v3` | $0.0015     | Fast alternative              |

## Notes

- Billed per minute of audio, not per token.
- `prompt`, word-level timestamps, and diarization are the knobs worth reaching for; everything else is fine at defaults.
