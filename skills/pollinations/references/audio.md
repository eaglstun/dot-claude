# Audio — TTS, music, transcription

Prefer `polli`. TTS and music both go through `polli gen audio`; transcription uses `polli gen transcribe`.

## CLI (preferred)

### Text-to-speech

```bash
polli gen audio "Hello, world." --voice nova --output hello.mp3
```

Flags:

| Flag              | Purpose                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------ |
| `--voice <name>`  | Voice ID. Default: `sage`. Discover: `polli models --type audio --json \| jq '.[].voices'` |
| `--format <fmt>`  | `mp3` \| `opus` \| `aac` \| `flac` \| `wav` (default `mp3`)                                |
| `--model <name>`  | `elevenlabs` (default TTS), `elevenmusic`, `acestep`                                       |
| `--speed <n>`     | Playback speed (0.25–4.0)                                                                  |
| `--output <path>` | Save path (default `speech.mp3`)                                                           |
| `--play`          | Play via platform player after saving                                                      |

Stdin works too:

```bash
echo "today's weather looks terrible" | polli gen audio --voice callum --play
```

### Music

```bash
polli gen audio "upbeat synthwave, driving bassline, 120bpm" \
  --model elevenmusic --duration 30 --output track.mp3
```

Music-specific flags:

- `--duration <n>` — seconds (ElevenMusic)
- `--instrumental` — no vocals

`acestep` is an alternative music model that supports lyrics input.

### Transcription (speech-to-text)

```bash
polli gen transcribe meeting.m4a --output meeting.txt
```

(Backed by `whisper-large-v3` or `scribe`.)

### Voices

Core: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`, `ash`, `ballad`, `coral`, `sage`, `verse`.

ElevenLabs: `rachel`, `domi`, `bella`, `elli`, `charlotte`, `dorothy`, `sarah`, `emily`, `lily`, `matilda`, `adam`, `antoni`, `arnold`, `josh`, `sam`, `daniel`, `charlie`, `james`, `fin`, `callum`, `liam`, `george`, `brian`, `bill`.

Full, live list: `polli models --type audio --json | jq '.[].voices'`.

### Models

- `elevenlabs` — ElevenLabs v3 TTS, expressive, supports emotion & audio tags (default TTS)
- `elevenmusic` — ElevenLabs Music, studio-grade music from text
- `acestep` — ACE-Step 1.5 Turbo, fast music with lyrics (alpha)
- `whisper` — Whisper Large V3 STT (OVH, alpha)
- `scribe` — ElevenLabs Scribe v2 STT, 90+ languages, diarization

## HTTP API (fallback)

### GET `/audio/{text}` — TTS or music, returns `audio/mpeg`

```bash
curl -sS --fail-with-body -o line.mp3 \
  -H "Authorization: Bearer $POLLINATIONS_API_KEY" \
  "https://gen.pollinations.ai/audio/Hello%20world?voice=nova"
```

Query params: `voice`, `model`, `duration`.

### POST `/v1/audio/speech` — OpenAI-compat TTS

```json
{ "input": "Hello world", "voice": "nova", "model": "elevenlabs" }
```

### POST `/v1/audio/transcriptions` — STT

Multipart form. Fields: `file` (audio binary), `model` (`whisper-large-v3` | `scribe`).
