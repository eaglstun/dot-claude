# suno-ai/bark

Model page: <https://replicate.com/suno-ai/bark>

Bark is Suno's **text-to-audio** generative model — not a pure TTS system. From a text prompt it produces realistic multilingual speech plus non-speech audio: laughter, sighs, gasps, crying, crowd noise, and short snippets of singing or hummed music. Effects are triggered inline by bracketed or symbolic tags in the prompt (`[laughter]`, `[laughs]`, `[sighs]`, `[music]`, `[gasps]`, `[clears throat]`, `—` for hesitation, `...` for pauses, capital-lettering for emphasis, `♪ ... ♪` around sung lyrics).

## When to pick Bark over alternatives

- **Pick it over ElevenLabs / OpenAI TTS / Cartesia** when you want expressive character voice with real laughter, sighs, and emotional nonverbals mid-sentence — not just clean read-aloud speech. Also pick Bark when you want multilingual speech (13 languages in the preset list) from a single model with no extra setup.
- **Pick it over MusicGen / Riffusion** only for _short_ incidental music, humming, or sung phrases embedded in speech — Bark is not a general music generator.
- **Pick clean TTS (ElevenLabs, OpenAI `tts-1`/`gpt-4o-mini-tts`, Cartesia Sonic) instead** when you need reliable, low-variance, long-form narration — Bark is creative but inconsistent and hard-capped at ~13 seconds per run.
- **Pick dedicated music models (MusicGen, Stable Audio, Lyria)** for anything longer than a bar or two of music.

## Input schema

| Field                   | Type         | Required | Default                                                                                                                       | Description                                                                                                                                                            |
| ----------------------- | ------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`                | string       | ✅       | `"Hello, my name is Suno. And, uh — and I like pizza. [laughs] But I also have other interests such as playing tic tac toe."` | Text to vocalize. Embed tags like `[laughs]`, `[sighs]`, `[music]`, `♪...♪` to trigger nonverbal effects. Keep under ~13 seconds of speech (~35–40 words for English). |
| `history_prompt`        | enum         |          | —                                                                                                                             | Voice preset. One of the ~130 `{lang}_speaker_{0..9}` presets plus `announcer` (see full list below). Controls speaker identity, language, and accent.                 |
| `custom_history_prompt` | string (URI) |          | —                                                                                                                             | URL to a `.npz` file from a prior Bark run (`prompt_npz` output) to reuse that exact voice. **Overrides `history_prompt` if both are set.**                            |
| `text_temp`             | number       |          | `0.7`                                                                                                                         | Temperature for the text→semantic stage. `1.0` = more diverse / unpredictable, `0.0` = conservative. Lower = more faithful to prompt phrasing.                         |
| `waveform_temp`         | number       |          | `0.7`                                                                                                                         | Temperature for the semantic→waveform stage. Same scale. Lower = less timbral variation across runs.                                                                   |
| `output_full`           | boolean      |          | `false`                                                                                                                       | If `true`, also return the generation's full `.npz` history file (in `prompt_npz`) so you can feed it back in as `custom_history_prompt` to continue/clone the voice.  |

Local `.npz` paths for `custom_history_prompt` are auto-uploaded by `run_model.py`.

### Voice presets (`history_prompt` enum)

`announcer`, plus `{lang}_speaker_0` … `{lang}_speaker_9` for each of these languages:

| Code | Language | Code | Language   |
| ---- | -------- | ---- | ---------- |
| `en` | English  | `ja` | Japanese   |
| `de` | German   | `ko` | Korean     |
| `es` | Spanish  | `pl` | Polish     |
| `fr` | French   | `pt` | Portuguese |
| `hi` | Hindi    | `ru` | Russian    |
| `it` | Italian  | `tr` | Turkish    |
|      |          | `zh` | Chinese    |

Total: 131 presets (13 languages × 10 speakers + `announcer`). **Don't invent preset names** — anything outside this enum returns 422. To hear voices, check the Bark speaker library at <https://suno-ai.notion.site/8b8e8749ed514b0cbf3f699013548683>.

## Output

An object, not a bare URI:

```json
{
  "audio_out": "https://replicate.delivery/.../audio.wav",
  "prompt_npz": "https://replicate.delivery/.../prompt.npz" // only if output_full=true
}
```

- `audio_out` — a 24 kHz mono WAV, always present.
- `prompt_npz` — the full semantic/coarse/fine history arrays as a NumPy zip, only set when `output_full: true`. Reuse it by passing the URL back as `custom_history_prompt` for voice continuity across multiple <13s chunks.

`run_model.py` saves each URI in the dict to disk; expect files like `suno-ai_bark_audio_out_0.wav` (and `suno-ai_bark_prompt_npz_0.npz` if `output_full` was on).

## Pricing and runtime

- **~$0.040 per run** (~25 runs per $1) on Nvidia **T4** hardware, per the model page.
- Typical prediction time: under 3 minutes but **highly variable with input length**. The default example ran in ~45 seconds.
- Open-source — you can self-host via the GitHub Cog image at <https://github.com/chenxwh/bark> for zero marginal cost.

## Examples

**1. Plain speech with a named voice preset:**

```bash
python scripts/run_model.py suno-ai/bark \
    --input '{
      "prompt": "Welcome to the show. Today we are talking about the long, strange history of sourdough bread.",
      "history_prompt": "en_speaker_6",
      "text_temp": 0.6,
      "waveform_temp": 0.6
    }' \
    --output ./out/
```

`en_speaker_6` and `en_speaker_9` are the usually-recommended "clean narrator" English voices.

**2. Expressive speech with nonverbal tags and a musical flourish:**

```bash
python scripts/run_model.py suno-ai/bark \
    --input '{
      "prompt": "Wait — you brought the WRONG map? [laughs] Oh no. [sighs] Okay. ♪ Guess we are going the long way home ♪ [laughter]",
      "history_prompt": "en_speaker_3",
      "text_temp": 0.8,
      "waveform_temp": 0.7,
      "output_full": true
    }' \
    --output ./out/
```

Note `output_full: true` — this also saves the `.npz` so you can continue the same voice in a follow-up generation via `custom_history_prompt`.

**3. A specific non-English language voice:**

```bash
python scripts/run_model.py suno-ai/bark \
    --input '{
      "prompt": "Bonjour, bienvenue à notre podcast hebdomadaire sur les mystères de Paris.",
      "history_prompt": "fr_speaker_1"
    }' \
    --output ./out/
```

The `history_prompt` prefix (`fr_`, `de_`, `ja_` …) is what selects the language — the text should match; mixing a French prompt with `en_speaker_*` produces a heavy-accented mess.

## Strengths / gotchas

**Good at:**

- Emotional, character-voice speech with laughter, sighs, gasps, crying mid-sentence.
- Short musical phrases, humming, sung lyrics inside speech (via `♪ ... ♪`).
- 13-language coverage out of the box with consistent voice IDs.
- Voice continuity across segments by round-tripping `output_full: true` → `prompt_npz` → `custom_history_prompt`.

**Gotchas:**

- **Hard ~13-second cap per generation.** Anything longer will truncate, trail off, or collapse into noise. For long scripts: split into <13s chunks, run each with the same `history_prompt` _and_ chain `custom_history_prompt` from the previous chunk's `prompt_npz` for voice continuity, then concatenate the WAVs.
- **Bracketed tags are probabilistic, not guaranteed.** `[laughter]` might yield an actual laugh, a giggle, a snort, a chuckle — or sometimes nothing at all. Retry with a different seed / slightly higher `text_temp` if a tag doesn't fire. Reliable-ish tags in practice: `[laughs]`, `[laughter]`, `[sighs]`, `[music]`, `♪`. Less reliable: `[gasps]`, `[clears throat]`, `[MAN]`, `[WOMAN]`.
- **No seed input** in this schema — reruns of the same input will differ. If you need reproducibility, capture the `prompt_npz` and re-feed it.
- **Voice preset is an enum.** Don't invent names like `en_narrator_1` — the 131 presets listed above are the only valid values (anything else 422s). Custom voices require an `.npz` file via `custom_history_prompt`.
- **Language is implicit in the preset.** Pick `de_speaker_*` for German text, `ja_speaker_*` for Japanese, etc. There is no separate `language` field.
- **`custom_history_prompt` overrides `history_prompt`.** If both are set, only the custom npz is used — a silent override, not an error.
- **Output is a dict**, not a single URI (unlike most image/video models in this skill). When using the `replicate` Python SDK directly, index into `output["audio_out"]`; `run_model.py` handles the dict-iteration for you.
- **Temperatures are separate for the two stages.** If prompts come out wrong but timbre is fine, lower `text_temp`. If phonetics drift or timbre warbles, lower `waveform_temp`.
- **GitHub:** <https://github.com/chenxwh/bark> (Cog wrapper) and upstream <https://github.com/suno-ai/bark>. Upstream license is MIT; the model weights are under a non-commercial-ish license in practice — check before commercial deployment.
