# lucataco/orpheus-3b-0.1-ft

Model page: <https://replicate.com/lucataco/orpheus-3b-0.1-ft>

**Orpheus 3B TTS** is Canopy Labs' open-source, **Llama-style 3B-parameter text-to-speech** model, released in 2025 under Apache 2.0, packaged here as a Cog wrapper by lucataco. Because the acoustic model is an LLM, prosody and phrasing come out noticeably more natural than older autoregressive-TTS checkpoints, and sampling controls (`temperature`, `top_p`, `repetition_penalty`) are exposed exactly the way you'd tune a text LM. Orpheus ships with **four named preset voices** (`tara`, `dan`, `josh`, `emma`) and supports inline **nonverbal/emotion tags** written with angle brackets — `<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`, `<sniffle>`, `<groan>`, `<yawn>`, `<gasp>`, `<uhm>`.

Against the other two TTS models already documented in this skill:

- **vs `suno-ai/bark`**: both support inline nonverbal tags for laughter / sighs / gasps. Orpheus is newer (2025 vs 2023), has a much more natural LLM-based prosody, and has no ~13-second hard cap — you get up to ~2000 tokens of audio per run (roughly 1–2 minutes of speech). Bark has 131 voice presets across 13 languages; Orpheus gives you 4 English presets. Bark costs ~\$0.040/run on T4; Orpheus costs ~\$0.075/run on L40S (published), so Orpheus is actually **more** expensive per run but produces longer, cleaner audio per dollar of speech-seconds.
- **vs `resemble-ai/chatterbox`**: Chatterbox's headline feature is **zero-shot voice cloning** from a reference audio clip plus a continuous `exaggeration` slider. This Orpheus checkpoint (`0.1-ft`) has **no reference-audio input** — voice identity is selected by name from the four-preset enum, not cloned. If you need a specific target voice, use Chatterbox; if you need named preset voices + emotion tags + LLM-grade naturalness, use Orpheus.
- **Sweet spot:** natural-sounding, medium-length English TTS with inline emotion tags and no reference audio to wrangle. Pick Orpheus when Bark's 13-second cap and grainy timbre hurt and Chatterbox's reference-audio dependency is overkill.

## Input schema

| Field                | Type    | Required | Default  | Range        | Description                                                                                                                                                               |
| -------------------- | ------- | -------- | -------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `text`               | string  | yes      | —        | —            | Text to convert to speech. Embed emotion tags inline as `<laugh>`, `<sigh>`, etc. (see list below). No schema-level character cap — the hard cap is `max_new_tokens`.     |
| `voice`              | enum    |          | `"tara"` | see below    | One of `"tara"`, `"dan"`, `"josh"`, `"emma"`. These are the only valid values — anything else 422s.                                                                       |
| `temperature`        | number  |          | `0.6`    | `0.1`–`1.5`  | Sampling temperature for the audio-token LM. Default `0.6` is already lower than typical text LM temperatures — Orpheus is sensitive and drifts above ~`0.9`.             |
| `top_p`              | number  |          | `0.95`   | `0.1`–`1`    | Nucleus sampling cutoff. Default `0.95` is the recommended value; dropping to `0.8` tightens delivery, raising to `1.0` lets more variance in.                            |
| `repetition_penalty` | number  |          | `1.1`    | `1`–`2`      | LM-style repetition penalty on the audio token stream. `1.1` is the default; raise to `1.2–1.3` if you hear looping / stuck phonemes, lower to `1.0` to disable.          |
| `max_new_tokens`     | integer |          | `1200`   | `100`–`2000` | Upper bound on generated audio tokens. `1200` tokens is roughly ~60–75 seconds of speech in practice; `2000` is the hard ceiling. Set tight for short clips to save time. |

There is **no** `seed` field in this schema — runs of identical input are non-deterministic. There is **no** `language` field either; this checkpoint is **English-only** in practice (see gotchas).

### Voice preset enum

| Value  | Notes                                                                               |
| ------ | ----------------------------------------------------------------------------------- |
| `tara` | Default. Female, neutral American English. Used in the model's own default example. |
| `dan`  | Male, mid-range American English.                                                   |
| `josh` | Male, slightly younger / brighter than `dan`.                                       |
| `emma` | Female, alternative to `tara` — slightly different timbre / pacing.                 |

Canopy Labs' upstream training release documents more voice names (`leah`, `leo`, `jess`, `mia`, `zac`, `zoe`), but **this specific `0.1-ft` Replicate checkpoint only exposes the four above** — passing any other name 422s.

### Emotion / nonverbal tags

Documented as working on the Replicate model page:

`<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`, `<sniffle>`, `<groan>`, `<yawn>`, `<gasp>`, `<uhm>`

Note the **angle-bracket syntax** — this is different from Bark's `[laughs]` square brackets. Tags are probabilistic (like Bark's): the model _usually_ fires the gesture, but may skip or soften it. Retry with a slightly higher `temperature` if a tag misses.

## Output

A **single URI** — a bare string, not a dict (same shape as Chatterbox, unlike Bark):

```json
"https://replicate.delivery/.../output.wav"
```

Confirmed `.wav` container from the default example output. `run_model.py` saves it as `lucataco_orpheus-3b-0.1-ft_0.wav` in the `--output` directory.

## Pricing and runtime

- **Confirmed \$0.075 per run** (~13 runs per \$1) on Nvidia **L40S** hardware, per the Replicate model page.
- Predictions **typically complete in ~77 seconds** per the model page, though this scales heavily with `max_new_tokens` — the default-example short utterance finished in ~9.6 seconds.
- Run count to date: ~34,800. License: **Apache 2.0**. Upstream training code / weights: Canopy Labs on Hugging Face; Cog wrapper GitHub: <https://github.com/lucataco/cog-orpheus-3b-0.1-ft>.

## Examples

**1. Default voice, plain speech:**

```bash
python scripts/run_model.py lucataco/orpheus-3b-0.1-ft \
    --input '{
      "text": "Welcome to the show. Today we are talking about the long, strange history of sourdough bread.",
      "voice": "tara",
      "temperature": 0.6,
      "top_p": 0.95
    }' \
    --output ./out/
```

`tara` is the default-recommended voice and what the upstream team tests most heavily — start here before exploring the other three.

**2. Expressive speech with inline emotion tags:**

```bash
python scripts/run_model.py lucataco/orpheus-3b-0.1-ft \
    --input '{
      "text": "Wait — you brought the WRONG map? <laugh> Oh no. <sigh> Okay, I guess we are walking. <cough> Sorry, I have a cold. <uhm> Let me think.",
      "voice": "tara",
      "temperature": 0.7,
      "top_p": 0.95,
      "repetition_penalty": 1.1,
      "max_new_tokens": 1500
    }' \
    --output ./out/
```

Angle-bracket tags (`<laugh>`, `<sigh>`, `<cough>`, `<uhm>`) — _not_ Bark-style `[laughs]`. `temperature` bumped to `0.7` to give the tags more room to fire; still conservative enough to avoid LLM drift.

**3. Different preset for a different character:**

```bash
python scripts/run_model.py lucataco/orpheus-3b-0.1-ft \
    --input '{
      "text": "Detective Cole here. I have been working this case for six weeks, and I am telling you, something does not add up.",
      "voice": "dan",
      "temperature": 0.5,
      "top_p": 0.9,
      "max_new_tokens": 800
    }' \
    --output ./out/
```

`dan` for a lower, more authoritative read. Lowered `temperature` and `top_p` for a tighter, less improvisational delivery — useful for narration / detective-monologue cadence where you don't want surprise inflections. `max_new_tokens: 800` caps wall-clock time since the text is short.

## Strengths

- **LLM-native prosody** — because the acoustic model is a Llama-style 3B, sentence-level phrasing, natural pauses, and intonation feel much closer to a real speaker than classic encoder-decoder TTS.
- **Inline emotion tags** that don't require a separate style input — just type `<laugh>` inline.
- **Longer per-run output than Bark** (~1–2 minutes vs ~13 seconds) with no chunking gymnastics.
- **Four named preset voices** — no reference-audio upload required, unlike Chatterbox.
- **Apache 2.0 license** on the weights — self-hostable via the Cog image for zero marginal cost.
- Fast for a 3B LM on L40S — the default short-sentence example finishes in under 10 seconds.

## Gotchas

- **Only four voices** (`tara`, `dan`, `josh`, `emma`) in this `0.1-ft` checkpoint. The upstream Orpheus release advertises more names (`leah`, `leo`, `jess`, `mia`, `zac`, `zoe`) — those are **not** exposed here and will 422. For a wider named-voice menu, use Bark (131 presets) or self-host the upstream Orpheus repo.
- **English-only, effectively.** There's no `language` field and the fine-tune is English-centric. Non-English text will be read with heavy anglophone phonetics or outright mispronounced. For multilingual TTS use Bark.
- **No `seed` field** — runs are non-deterministic. If you need reproducibility, generate multiple takes and pick; there is no way to lock a specific rendering in this schema.
- **Temperature drifts fast.** Default `0.6` is tuned conservatively for a reason — above ~`0.9` the model starts to mispronounce words, clip syllables, or halt mid-sentence. If you need liveliness, bump `temperature` to `0.7–0.8` _and_ keep `top_p` at `0.95`; don't raise both aggressively.
- **Emotion tags are probabilistic.** `<laugh>` usually produces laughter but can come out as a breath, a giggle, or nothing. Reliable in practice: `<laugh>`, `<chuckle>`, `<sigh>`, `<uhm>`. Less reliable: `<cough>`, `<yawn>`, `<gasp>`, `<sniffle>`, `<groan>` — retry or slightly increase `temperature` if a tag misses.
- **Bracket syntax matters.** Orpheus uses **angle brackets** (`<laugh>`), not Bark's **square brackets** (`[laughs]`). Mixing them up means the brackets read aloud literally or get silently ignored.
- **`max_new_tokens` is the real length cap.** `2000` is the hard ceiling and corresponds to roughly 100–120 seconds of speech. For audiobook-length scripts, chunk at sentence/paragraph boundaries and concatenate — there's no `prompt_npz`-style voice-continuity handle like Bark has, but because voice is an enum keyword (not a latent), the same `voice` setting will stay reasonably consistent across chunks.
- **Repetition penalty is worth tuning.** If you hear a phoneme loop or a stuck "uh-uh-uh" at chunk boundaries, bump `repetition_penalty` from `1.1` to `1.2`. Going above `1.3` starts to flatten prosody.
- **Output is a bare URI string**, not a dict. SDK callers can use the returned value directly as a URL.
- **Pricier per run than Bark** (\$0.075 vs \$0.040) but delivers much longer, cleaner audio per run — compare on dollars-per-second-of-speech, not dollars-per-call.
