# lucataco/singing_voice_conversion

Model page: <https://replicate.com/lucataco/singing_voice_conversion>

**SVC (Singing Voice Conversion) — Amphion DiffWaveNetSVC.** Takes a source singing (or speaking) clip and re-sings it in the voice of one of 15 built-in target singers. Unlike RVC/SoVITS, this model ships a **fixed roster** — there is no way to plug in your own trained voice model; the target is chosen from an enum. Built on top of [Amphion](https://github.com/open-mmlab/Amphion)'s `vocalist_l1_contentvec+whisper` checkpoint with a BigVGAN vocoder.

## Positioning

- vs `replicate/train-rvc-model` — that's the _trainer_ that produces a custom `.pth` voice model; this is an _inference_ model with a closed set of voices, no training required.
- vs `zsxkib/realistic-voice-cloning` — that model _does_ take a custom RVC model URL and is more flexible for arbitrary target voices; use it when you need a voice the Amphion roster doesn't cover.
- **Sweet spot:** quick karaoke-style covers and demos where one of the 15 stock voices is acceptable. Zero setup, no training pipeline, just a source audio URL.

Source: <https://github.com/lucataco/cog-singing-voice-conversion>

## Input schema

| Field                       | Type         | Required | Default          | Description                                                                                          |
| --------------------------- | ------------ | -------- | ---------------- | ---------------------------------------------------------------------------------------------------- |
| `source_audio`              | string (URI) | yes      | —                | Input singing/speech clip to convert.                                                                |
| `target_singer`             | enum         |          | `"Taylor Swift"` | One of 15 fixed singers (see below).                                                                 |
| `pitch_shift_control`       | enum         |          | `"Auto Shift"`   | `"Auto Shift"` matches source's median F0 to target's; `"Key Shift"` uses `key_shift_mode` manually. |
| `key_shift_mode`            | integer      |          | `0`              | Semitones to shift. Range `-6` to `+6`. Only applied when `pitch_shift_control = "Key Shift"`.       |
| `diffusion_inference_steps` | integer      |          | `1000`           | Denoising steps. Range `0`–`1000`. Lower = faster, lossier.                                          |

### `target_singer` enum

English: `Adele`, `Beyonce`, `Bruno Mars`, `John Mayer`, `Michael Jackson`, `Taylor Swift`.

Chinese: `Jacky Cheung 张学友`, `Jian Li 李健`, `Feng Wang 汪峰`, `Faye Wong 王菲`, `Yijie Shi 石倚洁`, `Tsai Chin 蔡琴`, `Ying Na 那英`, `Eason Chan 陈奕迅`, `David Tao 陶喆`.

Pass the full string verbatim, including the Chinese characters where present.

## Output

Single URI to a **WAV** file (BigVGAN vocoder output, 24 kHz). `run_model.py` saves it as `lucataco_singing_voice_conversion_0.wav`.

## Pricing and runtime

- **~$0.11 per run** (~9 runs/$1); varies with audio length and `diffusion_inference_steps`.
- **~113 seconds** typical runtime (default 1000 steps on L40S).
- Runs on Nvidia L40S.

Halving `diffusion_inference_steps` to ~500 roughly halves predict time with modest quality loss; going below ~200 starts to show audible degradation.

## Examples

**Default — Adele source, Taylor Swift target, auto-transpose:**

```bash
python scripts/run_model.py lucataco/singing_voice_conversion \
    --input '{
      "source_audio": "https://example.com/adele_clip.wav",
      "target_singer": "Taylor Swift"
    }' \
    --output ./out/
```

**Manual pitch shift (up a perfect fourth, +5 semitones) for a higher-range target:**

```bash
python scripts/run_model.py lucataco/singing_voice_conversion \
    --input '{
      "source_audio": "./male_vocal.wav",
      "target_singer": "Faye Wong 王菲",
      "pitch_shift_control": "Key Shift",
      "key_shift_mode": 5
    }' \
    --output ./out/
```

**Fast preview — fewer diffusion steps:**

```bash
python scripts/run_model.py lucataco/singing_voice_conversion \
    --input '{
      "source_audio": "./demo.wav",
      "target_singer": "Bruno Mars",
      "diffusion_inference_steps": 200
    }' \
    --output ./out/
```

## Strengths

- **Zero-setup.** No training, no `.pth` files, no index files — pick a name from the enum and go.
- **Auto-transpose** handles the common SVC headache of key mismatch: if source's median F0 is far from the target singer's comfort range, it retunes automatically (logs show e.g. `source f0 median = 372.9, target f0 median = 286.9, factor = 0.77`).
- **BigVGAN vocoder** gives cleaner, less "vocoder-y" output than the HiFiGAN variants common in open-source SVC.
- Diffusion backbone → smoother pitch transitions than flow-based RVC on sustained notes.

## Gotchas

- **Fixed voice roster.** You cannot supply a custom RVC/SoVITS model here. If you need a voice not in the enum, use `zsxkib/realistic-voice-cloning` (with a trained RVC model) or another custom-model SVC instead.
- **No F0 method knob.** Unlike RVC (`rmvpe`/`harvest`/`crepe`/`pm`/`dio`), pitch extraction is baked in — you can't switch algorithms when a source confuses the tracker. Noisy/polyphonic sources will show pitch-tracking artifacts with no mitigation knob.
- **No "protect" value.** There's no consonant/breath preservation slider (RVC users expect `protect` at ~0.33 to keep breathiness). Expect the target voice to be applied uniformly, which can flatten plosives and sibilants.
- **Source must be vocals only.** Feed instrumental-removed stems, not full mixes. Run a stem separator (`cjwbw/demucs`, `ryan5453/demucs`) first.
- **Auto Shift is usually right** — only reach for `Key Shift` when the source/target gender or range gap is extreme and Auto Shift sounds off.
- **Output is 24 kHz WAV.** If you need 44.1/48 kHz for mastering, upsample downstream; don't expect CD-quality masters from this model.
- **`diffusion_inference_steps = 0`** will technically accept but produce noise; keep it ≥ ~100 in practice.
- **Runtime scales roughly linearly with source length** after a ~15s fixed overhead (model init + feature extraction). Budget ~2× audio duration at default steps on L40S.
- **Output URLs expire** ~1 hour after generation (standard Replicate behavior) — download immediately if you want to keep the result.

## Legal/ethical note

The target singers are real, named public figures. Generating a "Michael Jackson singing X" clip and publishing it can create rights-of-publicity and copyright exposure regardless of the tool used. This is a research/demo model — treat outputs accordingly and don't pass them off as genuine recordings.
