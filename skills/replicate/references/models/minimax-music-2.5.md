# minimax/music-2.5

Model page: <https://replicate.com/minimax/music-2.5>
License: <https://www.minimax.io/platform/protocol/terms-of-service>

MiniMax's latest **full-song generator** — takes your lyrics plus a short style/mood prompt and returns a complete song with vocals, instrumentation, and arrangement. Unlike TTS or SVC models, this is **music generation from scratch** — the model writes the melody, chord progression, and backing track; the user provides only lyrics and a stylistic direction. Supports structure tags (`[Verse]`, `[Chorus]`, etc.) for section-level arrangement control. Latest version: `f2100977...` (2026-04-09 — brand new at time of writing).

## When to pick this over alternatives

- **Pick it over `stability-ai/stable-audio-2.5`** when you want **vocals with lyrics**. Stable Audio 2.5 generates instrumental music and sound; MiniMax Music-2.5 generates full songs with sung lyrics.
- **Pick it over `suno-ai/bark`** when you want actual _music_ (melody + harmony + instrumentation) instead of expressive speech with `♪...♪` tags. Bark sings approximations of short phrases; Music-2.5 writes songs.
- **Pick it over `resemble-ai/chatterbox` + autotune** when you're generating original compositions. Chatterbox+autotune sings a melody you supply; Music-2.5 writes both melody and lyrics-to-melody fit.
- **Skip it** if you need a specific named voice (clone). This model generates its own singer — no voice-cloning input surface.

## Input schema

| Field          | Type   | Required | Default  | Description                                                                                                                                                                                                                                                                                     |
| -------------- | ------ | -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lyrics`       | string | yes      | —        | Lyrics for the song, **1–3500 characters**. Separate lines with `\n`. Use structure tags `[Intro]`, `[Verse]`, `[Pre Chorus]`, `[Chorus]`, `[Interlude]`, `[Bridge]`, `[Outro]`, `[Post Chorus]`, `[Transition]`, `[Break]`, `[Hook]`, `[Build Up]`, `[Inst]`, `[Solo]` to control arrangement. |
| `prompt`       | string |          | `""`     | Style/mood description, **0–2000 characters**. Example: `"Pop, melancholic, perfect for a rainy night"`. Drives genre, instrumentation, vocal timbre, tempo.                                                                                                                                    |
| `audio_format` | enum   |          | `"mp3"`  | `mp3`, `wav`, or `pcm`. Use `wav` for downstream audio editing; `mp3` for delivery.                                                                                                                                                                                                             |
| `sample_rate`  | enum   |          | `44100`  | `16000`, `24000`, `32000`, or `44100`. Integer, not string. CD-quality default.                                                                                                                                                                                                                 |
| `bitrate`      | enum   |          | `256000` | `32000`, `64000`, `128000`, or `256000`. Integer bps. 256 kbps is transparent; 128 kbps is plenty for most uses.                                                                                                                                                                                |

## Output

**Bare URI string** — single audio file in the requested format. Saved as `minimax_music-2.5_0.{ext}` by `run_model.py`.

## Pricing and runtime

Pricing not in schema — confirm on the model page. Expect music generators to run **~$0.10–0.50/song** based on comparable models. Runtime scales with song length (which is implicit in lyrics volume); budget 30–90 s for a typical ~2-minute song.

## Examples

**Full-song generation with structure tags** — a folk-blues track with named sections:

```json
{
  "lyrics": "[Intro]\n(Fingerpicked guitar)\n\n[Verse]\nOld screen door don't close right anymore\nCreaks like my knees on a cold morning\nCoffee's on the stove, dog's on the floor\nAnother day without warning\n\n[Chorus]\nBut time don't ask permission\nAnd rivers don't run backwards, friend\nYou just hold what's left\nAnd learn to love the bend\n\n[Bridge]\n(Harmonica solo)\n\n[Outro]\nLearn to love the bend...",
  "prompt": "Acoustic folk-blues, raw and intimate, front porch recording feel, fingerpicked guitar, warm male vocals",
  "audio_format": "wav",
  "sample_rate": 44100,
  "bitrate": 256000
}
```

```bash
python scripts/run_model.py minimax/music-2.5 \
    --input-file input.json \
    --output ./out/
```

**Minimal invocation** — just lyrics and a style hint, default audio format:

```json
{
  "lyrics": "[Verse]\nCity lights are fading, neon signs go dim\n\n[Chorus]\nWe're driving through the night, on a whim",
  "prompt": "Synthwave, 80s nostalgia, driving beat, female vocals"
}
```

**Instrumental-only** — empty lyrics with `[Inst]` tags:

```json
{
  "lyrics": "[Intro]\n[Inst]\n[Solo]\n[Outro]",
  "prompt": "Uplifting orchestral cinematic score, strings and brass crescendo, 90 seconds"
}
```

## Structure tags — the arrangement control surface

Tags are the only way to shape the song structure. The model respects them as section breakpoints and varies instrumentation/melody accordingly. Typical use:

```text
[Intro]              ← short instrumental opener
(directions can go here in parens — often used for "fingerpicked guitar", "drum buildup")

[Verse]              ← lyrics for verse 1

[Pre Chorus]         ← optional lift into chorus
[Chorus]             ← hook
[Verse]              ← verse 2
[Chorus]             ← repeat hook
[Bridge]             ← contrast section (can be instrumental: [Bridge]\n(Harmonica solo))
[Chorus]             ← final chorus (sometimes elevated, varies by model)
[Outro]              ← fade / tag
```

Parenthetical direction lines inside sections (e.g. `(Guitar fades to crickets)`) are treated as instrumentation cues, not sung lyrics.

## Strengths / gotchas

**Good at:**

- Genre adherence via `prompt` — the model picks up explicit genre words ("synthwave", "folk-blues", "bossa nova") and produces convincing stylistic output
- Structure-tag honoring — sections actually transition, instrumentation varies across `[Verse]` / `[Chorus]` / `[Bridge]`
- Vocal-lyric alignment — phrasing and syllable stress usually match sung lines reasonably well
- Short-to-medium-length songs (under ~3 minutes)

**Gotchas:**

- **Lyrics cap is 3500 characters.** That's roughly 2.5–3 minutes of sung content depending on pacing. Plan verses/choruses accordingly; split very long songs into multiple generations.
- **Prompt matters more than it looks.** `"pop song"` gets you generic pop; `"indie dream-pop with shoegaze guitars, airy female vocals, 2010s Real Estate feel"` gets you something specific. Invest in the prompt.
- **No seed field.** Results aren't reproducible across identical calls — budget 2–4 attempts to land a keeper. Keep good seeds by saving outputs immediately.
- **Structure tags are suggestions, not guarantees.** The model usually respects them but occasionally merges or skips sections on very short inputs.
- **No voice cloning.** The singer is chosen by the model from its learned distribution — you can steer with prompt ("warm male baritone", "young female soprano") but not upload a reference.
- **Parenthetical cues work but don't overdo them.** A line like `(harmonica solo)` inside `[Bridge]` is a useful hint; stacking five direction lines in a row confuses the model.
- **Bitrate/sample-rate are integers, not strings.** `256000` not `"256000"`. Same for `44100`.
- **Quality variance between seeds is high.** Unlike text generation where seed changes are cosmetic, a bad music seed can produce muddy instrumentation or off-key vocals. Generate 3 and pick the winner.
- **Replicate TTL applies.** The output URL expires in ~1 hour — download the file immediately.
- **Version pin:** `minimax/music-2.5:f2100977b6ce90322ab00443b76d48f079435c1d903c4805517f89d2b8cc9c5a`. Pin because this model is brand new (2026-04) and may see rapid iteration.
- **Licensing.** Output falls under MiniMax's platform TOS (see license link above). For commercial use, confirm rights — some music-gen providers restrict commercial distribution of generated songs.
