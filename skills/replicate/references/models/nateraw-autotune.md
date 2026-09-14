# nateraw/autotune

Model page: <https://replicate.com/nateraw/autotune>

Classic **pitch-correction autotune** — take a vocal audio clip and snap the notes onto a target scale or to the nearest chromatic semitone, producing either subtle polish or the cartoon "T-Pain" effect depending on the source material and chosen scale. Under the hood it's a traditional DSP pipeline (no neural net): `librosa.pyin` for pitch detection (returning voiced/unvoiced flags + NaNs on silence) and the `psola` Python library (Pitch Synchronous OverLap Add) for the actual frequency-domain shift. Because it's PSOLA — not a vocoder — the singer's **timbre and identity are preserved**; only the fundamental frequency of each voiced frame is moved.

## When to pick this over related audio models

- **Pick autotune** when you want the _same singer_ on-key. This model changes the _notes_, not the voice.
- **Pick `zsxkib/realistic-voice-cloning` (AICoverGen / RVC)** when you want a _different singer's voice_ on the same melody — voice conversion, not pitch correction.
- **Pick `lucataco/singing_voice_conversion` / other SVC models** when you want wholesale singer-identity replacement with melody preserved.
- **Pick a DAW plugin (Melodyne, Antares Auto-Tune, Waves Tune)** when you need per-note manual tuning, formant preservation controls, or time correction — this model has no such knobs, only a key.

## Input schema

| Field           | Type         | Required | Default     | Description                                                                                                                              |
| --------------- | ------------ | -------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `audio_file`    | string (URI) | Yes      | —           | Audio input file. Local paths are auto-uploaded by `run_model.py`. Should be a vocal stem (no backing music) for best results.           |
| `scale`         | enum         |          | `"closest"` | Target key/scale to snap notes to. `"closest"` = nearest chromatic semitone (no key context). Otherwise `{NOTE}:{maj\|min}` — see below. |
| `output_format` | enum         |          | `"wav"`     | One of `"wav"`, `"mp3"`.                                                                                                                 |

### `scale` enum (25 values)

`closest` plus 24 major/minor keys covering all 12 pitch classes:

| Majors                                                  | Minors                                                  |
| ------------------------------------------------------- | ------------------------------------------------------- |
| `C:maj`, `Db:maj`, `D:maj`, `Eb:maj`, `E:maj`, `F:maj`  | `C:min`, `Db:min`, `D:min`, `Eb:min`, `E:min`, `F:min`  |
| `Gb:maj`, `G:maj`, `Ab:maj`, `A:maj`, `Bb:maj`, `B:maj` | `Gb:min`, `G:min`, `Ab:min`, `A:min`, `Bb:min`, `B:min` |

Accidentals are flats only (`Db`, `Eb`, `Gb`, `Ab`, `Bb`) — anything outside this exact enum will 422. Use `Db:maj` for C#/Db major, `Eb:min` for D#/Eb minor, etc.

**Semantics:**

- `"closest"` — for each voiced frame, snap the detected f0 to the **nearest chromatic semitone** (12-TET). No key context; every semitone is a legal target. This is the "T-Pain / heavy chromatic" mode and sounds most robotic, because passing tones get pinned too.
- `"C:maj"` etc. — snap each frame to the nearest note **in that key's diatonic scale** (7 legal targets per octave instead of 12). Notes outside the key get pulled to the closest scale tone. Much more musical when the key matches the song, but **brutal if the key is wrong** — it will destructively re-map out-of-key notes onto the scale.

There is **no strength / amount / retune-speed parameter.** The snap is binary (frame-level hard snap via PSOLA). If you want subtlety, use `"closest"` on an already-mostly-in-tune vocal, or tune the source first and only pass occasional problem notes.

## Output

A single URI to a pitch-corrected audio file (`.wav` or `.mp3`, matching `output_format`). Saved by `run_model.py` as `nateraw_autotune_0.wav` (or `.mp3`).

Example output URL pattern: `.../tmp<hash><original_stem>_pitch_corrected.wav`.

## Pricing and runtime

- **~$0.0070 per run** (~142 runs per $1) per the model page.
- **~70 seconds typical**, but scales with clip length — a 4-second clip in the default example completed in ~4 seconds.
- Runs on **CPU**, not GPU — which is why it's so cheap. No batching advantage from GPU parallelism here; each run is a straight-line PSOLA pass.

## Examples

**1. Subtle correction in the song's actual key** (best-practice path — gives musical, mostly-transparent polish):

```json
{
  "audio_file": "https://example.com/vocal_stem_in_Amin.wav",
  "scale": "A:min",
  "output_format": "wav"
}
```

```bash
python scripts/run_model.py nateraw/autotune --input-file input.json --output ./out/
```

**2. Heavy T-Pain chromatic effect** (`"closest"` = snap every note to the nearest semitone, regardless of key — the canonical robotic autotune sound):

```json
{
  "audio_file": "./my_vocal.wav",
  "scale": "closest",
  "output_format": "mp3"
}
```

```bash
python scripts/run_model.py nateraw/autotune --input-file input.json --output ./out/
```

**3. Creative "wrong key" effect** (deliberately pick a scale that _doesn't_ match the melody — pulls the vocal into an unexpected modal feel; e.g. a major-key melody forced into the relative minor, or a totally unrelated key for a sound-design / glitch use):

```json
{
  "audio_file": "https://example.com/cheerful_major_key_vocal.wav",
  "scale": "Eb:min",
  "output_format": "wav"
}
```

```bash
python scripts/run_model.py nateraw/autotune --input-file input.json --output ./out/
```

## Strengths / gotchas

**Good at:**

- Fast, cheap, no-frills autotune on a vocal stem — CPU-only means <1 cent a run.
- Preserving the singer's voice/timbre (PSOLA, not a vocoder or neural model).
- Producing the classic T-Pain effect when paired with `"closest"` on a non-melismatic vocal.
- Leaving unvoiced segments (breath, consonants, silence) alone — `librosa.pyin` returns NaN for unvoiced frames and PSOLA passes them through unmodified.

**Gotchas:**

- **Pick the right key or it will wreck the melody.** If the song is in A minor and you pass `"C:maj"`, every note that isn't a C-major scale tone (the ♭6, ♭7 of A minor, say) gets mapped to the nearest C-major note — turning a correctly-sung phrase into an out-of-tune-sounding mess. When in doubt, use `"closest"`; it's key-agnostic and only snaps to the nearest semitone.
- **No strength parameter.** Snap is hard / binary per frame. The way to get "subtle" autotune is to start with an already-clean vocal — or to pre-blend the wet output with the dry original in a DAW afterwards. This model doesn't expose a mix / retune-speed knob.
- **Expects a dry vocal stem.** Background music, harmonies, or reverb tails confuse `pyin` pitch detection → mis-detected f0 → wild shifts. Isolate the lead vocal first (e.g. with `ryan5453/demucs` or a similar stem-splitter) before running autotune.
- **Monophonic only.** `pyin` tracks a single f0. Harmony stacks, choirs, and overlapping voices will produce unpredictable results — run each voice separately.
- **Relative pitch shifts, no absolute re-tuning.** Out-of-range / extremely off notes can still be pulled far from the original pitch — watch for octave errors on breathy or noisy frames (pyin sometimes flips octaves on low-amplitude voiced segments).
- **Accidentals are flats only in the enum** (`Db`, `Eb`, `Gb`, `Ab`, `Bb`). There is no `C#:maj` — use `Db:maj` (enharmonic equivalent).
- **No `seed` input and no randomness** — the pipeline is deterministic, so reruns of the same input are bit-identical.
- **Output filename hint:** the Replicate URL ends in `_pitch_corrected.wav`/`.mp3`. `run_model.py` renames to `nateraw_autotune_0.<ext>`, but if you download manually note the source filename is embedded.
- **GitHub / source:** <https://github.com/nateraw/replicate-examples/tree/main/autotune> — Cog image; open-source, self-hostable. Depends on `psola`, `librosa`, and `soundfile`.
