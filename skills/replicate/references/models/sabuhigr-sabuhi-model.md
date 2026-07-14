# sabuhigr/sabuhi-model

Model page: <https://replicate.com/sabuhigr/sabuhi-model>

A community Whisper wrapper by user `sabuhigr` that combines **OpenAI Whisper large / large-v2 transcription** with **channel separation** and **pyannote-based speaker diarization** in a single prediction. The model takes an audio URL, runs Whisper for word-level timing, then overlays speaker labels (`SPEAKER_00`, `SPEAKER_01`) onto the transcript segments. It is explicitly bounded to 1–2 speakers — enum-restricted on both `min_speakers` and `max_speakers` — so it is aimed at mono vs stereo two-party audio (phone calls, interviews, podcasts with a host + guest), not meetings or panels.

## When to pick this over alternatives

- **Pick dedicated WhisperX wrappers** like `victor-upmeet/whisperx` or `thomasmol/whisper-diarization` first — they support N-speaker diarization, newer Whisper backends (faster-whisper, large-v3), and have vastly more runs / battle-testing. This model is older (2023-era) and pinned to `large` / `large-v2`.
- **Pick `openai/whisper` on Replicate** if you only need plain transcription without speaker labels — it is cheaper, faster, and officially maintained.
- **Pick this model** only if you have a very specific 1–2 speaker workflow and already have a `sabuhigr` pipeline wired up, or if you want the exact `segments` shape it emits. It's essentially a single-author checkpoint — fine for what it does but not a default recommendation.
- **Requires a Hugging Face token** (`hf_token`) for the pyannote diarization pipeline. That is a hard blocker if you don't have one; pick a wrapper that bundles its own diarization instead.

## Input schema

| Field                               | Type         | Required | Default      | Notes                                                                                                    |
| ----------------------------------- | ------------ | -------- | ------------ | -------------------------------------------------------------------------------------------------------- |
| `audio`                             | string (URI) | yes      | —            | Audio file URL. Local paths are auto-uploaded by `run_model.py`. WAV / MP3 / common formats.             |
| `hf_token`                          | string       | yes      | —            | Your Hugging Face access token with access accepted for `pyannote/speaker-diarization`. No token → fail. |
| `language`                          | enum         | yes      | —            | Spoken language. Accepts ISO code (`en`, `ar`, `fr`, …) or full name (`English`, `Arabic`). See below.   |
| `model`                             | enum         |          | `large-v2`   | Whisper model. One of `large`, `large-v2`. No `large-v3`, no distil, no `tiny`/`base`/`small`/`medium`.  |
| `transcription`                     | enum         |          | `plain text` | Output format. One of `plain text`, `srt`, `vtt`. Non-plain formats also populate `srt_file`/`txt_file`. |
| `translate`                         | boolean      |          | `false`      | If `true`, translate to English (Whisper's X→en task).                                                   |
| `temperature`                       | number       |          | `0`          | Sampling temperature.                                                                                    |
| `patience`                          | number       |          | —            | Beam-search patience (arXiv 2204.05424). Default `1.0` ≡ conventional beam search.                       |
| `suppress_tokens`                   | string       |          | `"-1"`       | Comma-separated token ids to suppress. `"-1"` suppresses most special chars except common punctuation.  |
| `initial_prompt`                    | string       |          | —            | Seed text for the first decoding window (domain terms, names).                                           |
| `condition_on_previous_text`        | boolean      |          | `true`       | Feed previous output as prompt. Disable to avoid failure loops at the cost of cross-window consistency.  |
| `temperature_increment_on_fallback` | number       |          | `0.2`        | Fallback temperature step when decoding fails the thresholds.                                            |
| `compression_ratio_threshold`       | number       |          | `2.4`        | gzip ratio above which a segment is treated as failed.                                                   |
| `logprob_threshold`                 | number       |          | `-1.0`       | Average log-prob below which a segment is treated as failed.                                             |
| `no_speech_threshold`               | number       |          | `0.6`        | If `<\|nospeech\|>` probability exceeds this AND `logprob_threshold` failed, mark as silence.            |
| `min_speakers`                      | enum int     |          | `1`          | `1` or `2` only. Set `2` for stereo / two-party audio.                                                   |
| `max_speakers`                      | enum int     |          | `1`          | `1` or `2` only. Hard-capped at 2 — this is not a multi-speaker meeting model.                           |

`language` enum accepts both short ISO codes (98 of them — `en`, `es`, `fr`, `de`, `ja`, `zh`, `ar`, `ru`, `hi`, …) and full English names (`English`, `Spanish`, …). There is **no "auto-detect" option** — the field is required, pick one. Unlike OpenAI Whisper's own schema, you cannot pass `None` for detection.

## Output

A JSON object (not a bare URI):

```json
{
  "text": null,
  "segments": [
    {
      "start": 0.06,
      "end": 3.98,
      "text": " تقع القاهرة على جوانب جزر نهر النيل في شمال مصر",
      "speaker": "SPEAKER_00",
      "words": [
        { "word": "تقع", "start": 0.06, "end": 0.422, "score": 0.884 },
        { "word": "القاهرة", "start": 0.442, "end": 1.025, "score": 0.899, "speaker": "SPEAKER_00" }
      ]
    }
  ],
  "transcription": "<stringified Python list of segments>",
  "translation": null,
  "detected_language": "arabic",
  "diarization_status": true,
  "srt_file": "https://replicate.delivery/.../out.srt",
  "txt_file": "https://replicate.delivery/.../out.txt"
}
```

- `segments` — the structured list with per-segment `start` / `end` / `text` / `speaker` and per-word timings with confidence `score`. This is the useful field.
- `transcription` — the same data, but stringified via Python `repr()`, not real JSON. Parse `segments` instead if you need to programmatically consume it.
- `translation` — populated when `translate: true`.
- `detected_language` — what the audio was classified as (lowercased English name).
- `diarization_status` — boolean; `true` if pyannote succeeded.
- `srt_file` / `txt_file` — only populated when `transcription` is `srt` or `vtt` (or when a TXT export is emitted). URIs to downloadable subtitle files.

`run_model.py` walks the dict and saves any URI-valued fields to disk — expect filenames like `sabuhigr_sabuhi-model_srt_file_0.srt` and `sabuhigr_sabuhi-model_txt_file_0.txt`.

## Pricing and runtime

- **~$0.055 per run** (~18 runs per $1) on Nvidia **L40S** hardware, per the model page.
- Typical prediction time: around 57 seconds, but dominated by one-time HuggingFace weight downloads (Whisper large + pyannote segmentation + speaker-embedding) on cold start — the reference run in the default example took ~56 s predict / ~231 s total wall. Expect long cold-starts.
- **GitHub / license:** no GitHub URL is published on the model page. It is a personal Cog image.

## Examples

**1. Single-speaker mono interview, English SRT output:**

```bash
python scripts/run_model.py sabuhigr/sabuhi-model \
    --input '{
      "audio": "https://example.com/interview.mp3",
      "language": "en",
      "hf_token": "hf_xxx_your_token_here",
      "model": "large-v2",
      "transcription": "srt",
      "min_speakers": 1,
      "max_speakers": 1
    }' \
    --output ./out/
```

Saves `sabuhigr_sabuhi-model_srt_file_0.srt` and `sabuhigr_sabuhi-model_txt_file_0.txt` to `./out/`.

**2. Two-speaker Arabic call with diarization and domain-term priming:**

```bash
python scripts/run_model.py sabuhigr/sabuhi-model \
    --input '{
      "audio": "https://example.com/call-stereo.wav",
      "language": "Arabic",
      "hf_token": "hf_xxx_your_token_here",
      "model": "large-v2",
      "min_speakers": 2,
      "max_speakers": 2,
      "initial_prompt": "القاهرة، نهر النيل، مصر",
      "condition_on_previous_text": true
    }' \
    --output ./out/
```

Use `initial_prompt` to seed proper nouns / domain vocabulary — improves recall on named entities significantly with Whisper.

**3. Translate foreign-language audio to English, VTT subtitles:**

```bash
python scripts/run_model.py sabuhigr/sabuhi-model \
    --input '{
      "audio": "https://example.com/spanish-podcast.mp3",
      "language": "es",
      "hf_token": "hf_xxx_your_token_here",
      "translate": true,
      "transcription": "vtt",
      "min_speakers": 2,
      "max_speakers": 2,
      "temperature": 0.0
    }' \
    --output ./out/
```

`translate: true` runs Whisper's X→English translation task; the translated text shows up in segments and in the VTT file.

## Strengths / gotchas

**Good at:**

- One-shot transcription + word-level timing + speaker labels for 1–2 speaker audio.
- Multilingual coverage (98 languages via Whisper large-v2), Arabic / Hindi / RTL scripts included.
- Native SRT / VTT export without a separate formatting step.
- `initial_prompt` and `condition_on_previous_text` knobs for domain vocabulary.

**Gotchas:**

- **Requires `hf_token`** with accepted terms for `pyannote/speaker-diarization` on Hugging Face. No token → hard fail. This is the single biggest friction point and the main reason to prefer a wrapper that bundles diarization.
- **Hard-capped at 2 speakers.** `min_speakers` / `max_speakers` are enums of `{1, 2}`. You cannot pass `3`, `4`, `null`, or leave diarization open-ended. For meetings, panels, group calls — use WhisperX or a different model.
- **Only `large` / `large-v2` Whisper.** No `large-v3`, no faster-whisper, no distil variants. Lower accuracy on recent benchmarks than newer wrappers, and no smaller/cheaper tier.
- **`language` is required and has no auto-detect.** You must pick one before submission even if you don't know what the audio is. Workaround: run `openai/whisper` first for language ID, then route to this model.
- **`transcription` field is stringified Python**, not JSON — it's the `repr()` of the segment list with single quotes. Do NOT `JSON.parse` it; use the structured `segments` array instead.
- **`text` is often `null`.** The usable aggregated transcript lives inside `segments[*].text`; concatenate them yourself if you want a single string.
- **Older model, personal author.** Created 2023-06; no GitHub repo linked; no active maintenance signals. For production, a more popular WhisperX wrapper will have more real-world fixes applied.
- **Cold-start is heavy.** First run on a new replica downloads Whisper-large (~1.3 GB) plus pyannote segmentation + speaker-embedding models. Expect the ~231 s total time seen in the default example on cold containers; warm runs are much faster.
- **No seed / determinism field**; set `temperature: 0` and live with pyannote's stochasticity on speaker clustering.
- **Diarization quality is pyannote-bounded.** Short utterances (<1 s) and overlapping speech frequently get the wrong `SPEAKER_XX` label or no label at all — the default example actually shows the first word lacking a speaker assignment.
