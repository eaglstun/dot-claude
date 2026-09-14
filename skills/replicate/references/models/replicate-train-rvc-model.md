# replicate/train-rvc-model

Model page: https://replicate.com/replicate/train-rvc-model

**This is a trainer, not an inference model.** It takes a zip of audio samples and produces a trained RVC (Retrieval-based Voice Conversion) model you can then plug into a separate RVC inference model for voice conversion.

## Pipeline overview

```
  raw voice recordings
         │
   [split into chunks, wrap in zip with expected layout]
         │
         ▼
  replicate/train-rvc-model  ──►  URL to a trained .zip model
         │
         │  (pass URL as custom_rvc_model_download_url)
         ▼
  downstream RVC inference model (e.g. zsxkib / hvigil-studio / community forks)
         │
         ▼
  converted audio
```

## Required dataset layout

The `dataset_zip` must unpack to this exact structure:

```
dataset/
└── <rvc_name>/
    ├── split_0.wav
    ├── split_1.wav
    ├── split_2.wav
    └── ...
```

`<rvc_name>` is your model name (freeform, no spaces). Samples are individual WAV chunks (typically 5–15s each) of a single speaker. Aim for 10–30 minutes of clean speech total. Remove silence, music, and other speakers first.

## Input schema

| Field         | Type                  | Required | Default       | Description                                                                                                                |
| ------------- | --------------------- | -------- | ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `dataset_zip` | string (URI)          | ✅       | —             | Zip of training data. Must contain `dataset/<rvc_name>/split_<i>.wav`.                                                     |
| `sample_rate` | enum                  |          | `"48k"`       | One of `"40k"`, `"48k"`. Match your source recordings.                                                                     |
| `version`     | enum                  |          | `"v2"`        | One of `"v1"`, `"v2"`. v2 recommended.                                                                                     |
| `f0method`    | enum                  |          | `"rmvpe_gpu"` | Pitch-extraction algorithm. One of `pm`, `dio`, `harvest`, `rmvpe`, `rmvpe_gpu`. `rmvpe_gpu` is fastest + highest-quality. |
| `epoch`       | integer               |          | `10`          | Number of passes over the dataset. More = better fit but diminishing returns past ~20–30.                                  |
| `batch_size`  | **string** (not int!) |          | `"7"`         | Samples per optimization step. Quirk of this model — pass as a string in JSON.                                             |

## Output

A single URI pointing to a zip containing the trained model artifacts. Saved by `run_model.py` as `replicate_train-rvc-model_0.zip`.

## Pricing and runtime

- **~$0.32 per training run** (approximate)
- **~6 minutes** typical runtime (varies with dataset size and epoch count)
- Runs on Nvidia L40S

## Example

```bash
python scripts/run_model.py replicate/train-rvc-model \
    --input '{
      "dataset_zip": "https://example.com/my-voice-dataset.zip",
      "sample_rate": "48k",
      "version": "v2",
      "f0method": "rmvpe_gpu",
      "epoch": 20,
      "batch_size": "7"
    }' \
    --output ./out/
```

Local zip (auto-uploaded by `run_model.py`):

```bash
python scripts/run_model.py replicate/train-rvc-model \
    --input '{
      "dataset_zip": "./my-voice-dataset.zip",
      "epoch": 20,
      "batch_size": "7"
    }' \
    --output ./out/
```

## Using the trained model downstream

The output URL is what you feed into an RVC _inference_ model. The conventional field name on inference models is `custom_rvc_model_download_url` with `rvc_model` set to `CUSTOM`:

```json
{
  "rvc_model": "CUSTOM",
  "custom_rvc_model_download_url": "<output URL from training>",
  "song_input": "https://example.com/source.mp3",
  ...
}
```

**Critical gotcha:** Replicate output URLs expire ~1 hour after generation. For a trained voice you want to reuse, **download the zip immediately and re-host it** somewhere stable (S3, Hugging Face, GitHub release asset, etc.) — then pass that stable URL to the inference model instead.

## Preparing a dataset

Not every trainer user has clean WAV chunks ready. A typical prep flow:

1. Collect ~10–30 min of single-speaker audio (podcast, voice notes, studio takes).
2. Denoise / remove background music (e.g. with an audio separation model like `cjwbw/rvc-voice-clone` prep or `spleeter`).
3. Split into 5–15s chunks with silence trimmed. `ffmpeg -f segment` works, or `pydub` for programmatic splitting.
4. Convert all to 48kHz mono WAV.
5. Organize as `dataset/<name>/split_N.wav` and zip.

## Legal/ethical note

Voice cloning can enable impersonation. Only train on voices you have explicit rights to use. Replicate's ToS prohibits training on a specific person's voice without their consent.

## Choosing batch_size and epoch

- **Small dataset (<10 min)**: `epoch: 30-50`, `batch_size: "4"` — overfitting less harmful when data is thin.
- **Medium (10-30 min)**: `epoch: 15-25`, `batch_size: "7"` (default).
- **Large (30+ min)**: `epoch: 10-15`, `batch_size: "10"-"14"` — bigger batches converge faster on more data.

Remember `batch_size` is a **string** here due to a schema quirk — keep the quotes in JSON.
