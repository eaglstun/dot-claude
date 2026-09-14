# zsxkib/realistic-voice-cloning

Model page: <https://replicate.com/zsxkib/realistic-voice-cloning>

GitHub: <https://github.com/zsxkib/AICoverGen>

RVC v2 song-cover / voice-conversion pipeline. Upload a song (or any audio file with vocals), pick a **preset AI voice** (or drop in the URL of a custom trained `.zip` RVC model), and get back a full re-sung cover — the model separates vocals from instrumentals, runs voice conversion on the vocals, applies optional reverb/pitch/volume effects, and re-mixes with the original instrumental bed. Derived from the open-source [AICoverGen](https://github.com/SociallyIneptWeeb/AICoverGen) project.

## When to pick this over other RVC endpoints

- **Pick this** when you want a turnkey "song cover in voice X" experience with a built-in bank of preset celebrity/character voices (Squidward, MrKrabs, Plankton, Drake, Vader, Trump, Biden, Obama, plus two instrument models) and automatic vocal/instrumental separation + remix. Sweet spot: quick covers in a ready-made voice, no training required.
- **Pick `lucataco/singing-voice-conversion`** if you want pure SVC (singing voice conversion) without the full AICoverGen pipeline and its preset roster — bring your own speaker embedding / model weights.
- **Pick `replicate/train-rvc-model`** (the trainer) first if none of the presets match. Train your own `.zip`, re-host it somewhere stable (Replicate output URLs expire in ~1 hour), then feed that URL back here as `custom_rvc_model_download_url` with `rvc_model: "CUSTOM"`.

## Preset voice mechanism

`rvc_model` is a **string enum** — not a URL, not a download ID. The built-in options are:

```
Squidward, MrKrabs, Plankton, Drake, Vader, Trump, Biden, Obama, Guitar, Voilin, CUSTOM
```

(Yes, `Voilin` is the actual spelling in the schema — presumably a typo for "Violin" that's now frozen.) Selecting any of the named presets loads that voice internally; no extra fields required. To use a trained model from outside the preset bank, set `rvc_model: "CUSTOM"` and supply `custom_rvc_model_download_url` pointing at a `.zip` containing the RVC `.pth` + `.index` files (e.g. the output of `replicate/train-rvc-model`, re-hosted on a stable URL). The custom model is cached by name between runs.

## Input schema

| Field                           | Type         | Required | Default       | Description                                                                                                                                                  |
| ------------------------------- | ------------ | -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `song_input`                    | string (URI) | yes      | —             | Source audio file (mp3/wav/etc.). Can be a full song with instrumentals — the model separates vocals first. Local paths are auto-uploaded by `run_model.py`. |
| `rvc_model`                     | enum         |          | `"Squidward"` | Preset voice. One of: `Squidward`, `MrKrabs`, `Plankton`, `Drake`, `Vader`, `Trump`, `Biden`, `Obama`, `Guitar`, `Voilin`, `CUSTOM`.                         |
| `custom_rvc_model_download_url` | string (URL) |          | —             | URL to a `.zip` RVC model. Used when `rvc_model: "CUSTOM"` (and overrides the preset if both are set). Cached by filename between runs.                      |
| `pitch_change`                  | enum         |          | `"no-change"` | Gender pitch-shift preset. One of `no-change`, `male-to-female`, `female-to-male`. Applied to AI vocals only (see `pitch_change_all` for the whole mix).     |
| `index_rate`                    | float        |          | `0.5`         | 0–1. How much of the target voice's accent/timbre to keep. Higher = stronger voice character, lower = closer to the source's delivery.                       |
| `filter_radius`                 | integer      |          | `3`           | 0–7. If ≥3, apply median filter to harvested pitch — smooths out pitch artifacts. Lower = rawer pitch tracking.                                              |
| `rms_mix_rate`                  | float        |          | `0.25`        | 0–1. Blend the original vocal's loudness envelope (0) vs. a fixed loudness (1).                                                                              |
| `pitch_detection_algorithm`     | enum         |          | `"rmvpe"`     | `rmvpe` (default; clearer vocals) or `mangio-crepe` (smoother, slower).                                                                                      |
| `crepe_hop_length`              | integer      |          | `128`         | Only used with `mangio-crepe`. Lower = more frequent pitch checks, better accuracy but slower + higher crack risk.                                           |
| `protect`                       | float        |          | `0.33`        | 0–0.5. How much of the source's breath and voiceless consonants to preserve. Set `0.5` to disable preservation (max AI voice takeover).                      |
| `main_vocals_volume_change`     | float (dB)   |          | `0`           | AI main-vocal gain in decibels. e.g. `3` = +3 dB, `-3` = −3 dB.                                                                                              |
| `backup_vocals_volume_change`   | float (dB)   |          | `0`           | Backup AI vocal gain in dB.                                                                                                                                  |
| `instrumental_volume_change`    | float (dB)   |          | `0`           | Instrumental / background-music gain in dB.                                                                                                                  |
| `pitch_change_all`              | float        |          | `0`           | Semitones. Shifts pitch of **everything** (instrumentals, backup vocals, AI vocals) — use for key changes. Slightly degrades quality.                        |
| `reverb_size`                   | float        |          | `0.15`        | 0–1. Reverb room size.                                                                                                                                       |
| `reverb_wetness`                | float        |          | `0.2`         | 0–1. Level of AI vocals with reverb applied.                                                                                                                 |
| `reverb_dryness`                | float        |          | `0.8`         | 0–1. Level of AI vocals without reverb.                                                                                                                      |
| `reverb_damping`                | float        |          | `0.7`         | 0–1. High-frequency absorption in the reverb.                                                                                                                |
| `output_format`                 | enum         |          | `"mp3"`       | `mp3` (small, decent) or `wav` (best, big).                                                                                                                  |

## Output

A single URI pointing to the rendered cover. Saved by `run_model.py` as `zsxkib_realistic-voice-cloning_0.mp3` (or `.wav` if you set `output_format: "wav"`).

The internal filename pattern produced by the pipeline is:

```
tmp<hash>_<source-basename> (<RvcModelName> Ver).<ext>
```

e.g. `tmp11cudxj_gangnam (Squidward Ver).mp3` — visible in the returned CDN URL but not something you need to rely on.

## Pricing and runtime

- Runs on **Nvidia T4** hardware.
- Published estimate: **~$0.033 per run** (roughly 30 runs per dollar), but varies with input length — you're billed by T4 seconds, so a 10-second clip is dramatically cheaper than a 4-minute song.
- Typical prediction time for a full song: ~2–3 minutes (vocal separation is the dominant cost).
- Confirm current pricing in the playground estimator at <https://replicate.com/zsxkib/realistic-voice-cloning> before batch runs.

## Examples

**1) Quick cover with a preset voice (Squidward singing Gangnam Style):**

```bash
python scripts/run_model.py zsxkib/realistic-voice-cloning \
    --input '{
      "song_input": "https://replicate.delivery/pbxt/JsPIizFfRy54Jk5LuXdnrNdV1JHJ6oLmPPdRuIfh3lvpoNai/gangnam.mp3",
      "rvc_model": "Squidward",
      "output_format": "mp3"
    }' \
    --output ./out/
```

**2) Pitch-shifted cover (female-to-male gender flip + drop the whole mix by 2 semitones):**

```bash
python scripts/run_model.py zsxkib/realistic-voice-cloning \
    --input '{
      "song_input": "./my-track.mp3",
      "rvc_model": "Drake",
      "pitch_change": "female-to-male",
      "pitch_change_all": -2,
      "index_rate": 0.7,
      "protect": 0.2,
      "output_format": "wav"
    }' \
    --output ./out/
```

**3) Custom trained RVC model (output of `replicate/train-rvc-model`, re-hosted stably):**

```bash
python scripts/run_model.py zsxkib/realistic-voice-cloning \
    --input '{
      "song_input": "./source.wav",
      "rvc_model": "CUSTOM",
      "custom_rvc_model_download_url": "https://your-bucket.s3.amazonaws.com/my-voice.zip",
      "index_rate": 0.6,
      "pitch_detection_algorithm": "rmvpe",
      "main_vocals_volume_change": 2,
      "reverb_wetness": 0.15,
      "output_format": "wav"
    }' \
    --output ./out/
```

## Strengths / gotchas

**Good at:**

- One-call "song cover" pipeline — vocal separation, conversion, and instrumental remix all handled internally.
- Large bank of preset voices (cartoon characters, musicians, named public figures) with no training step.
- Accepts custom RVC `.zip` models via URL — drop-in compatible with `replicate/train-rvc-model` output.
- Fine-grained mix controls (per-stem volume, reverb, pitch) built in — no post-processing DAW pass needed for most use cases.

**Gotchas:**

- **Preset voice spelling is case- and typo-sensitive.** Use `Voilin` (not `Violin`), `MrKrabs` (no space), `CUSTOM` (uppercase). The enum rejects anything else with a 422.
- **Output URL TTL is ~1 hour** — download immediately if you want to keep the result. For custom `rvc_model` zips, re-host to stable storage before passing the URL (training outputs from `replicate/train-rvc-model` also expire).
- **`pitch_change` vs `pitch_change_all`** are different: `pitch_change` is an enum gender preset that only affects the AI vocals; `pitch_change_all` is a semitone offset applied to the entire mixdown (instrumental + vocals) for key changes. Combining them is valid.
- **`rmvpe` vs `mangio-crepe`:** `rmvpe` (default) is the faster + clearer choice for most vocals. Switch to `mangio-crepe` only if you hear pitch instability on sustained notes — and expect 2–3× longer runs. `crepe_hop_length` only applies to the latter.
- **`protect`** at `0.5` fully disables consonant/breath preservation — the AI voice takes over even voiceless sounds, which can sound "plasticky" on raw source vocals but may help on clean studio material. Lower values (0.2–0.33) keep more of the source's natural articulation.
- **Audio length:** no hard cap documented, but T4 prediction time scales roughly linearly with input duration and long files (>5 min) risk timeout or high cost. Pre-trim to the section you need.
- **Quality depends heavily on clean vocals.** The built-in separator handles most songs, but mono/lo-fi sources or heavy processing (auto-tune, distortion) on the input vocal bleed into the result.
- **Ethics / legal:** voice cloning is sensitive. The preset list includes named public figures (Trump, Biden, Obama, Drake). Do **not** use outputs to impersonate real people, commit fraud, generate political disinformation, or infringe copyright / publicity rights. Replicate's terms of service prohibit non-consensual voice cloning of real individuals. For commercial use, stick to fictional/character voices or voices you own the rights to (e.g. a model trained on your own recordings via `replicate/train-rvc-model`).
