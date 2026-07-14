# replicate

Claude Code skill — a thin, modality-agnostic wrapper around the [Replicate](https://replicate.com) API. Run any hosted model (video, image, audio, text) by slug; the script handles auth, polling, and saving file outputs to disk.

## Setup

Set `REPLICATE_API_TOKEN` (get one at <https://replicate.com/account/api-tokens>). Client is the `replicate` Python SDK: `pip install replicate`. Generations cost real money — check pricing before running expensive models.

## Usage

```bash
python scripts/run_model.py <owner/name> --input-file input.json --output ./out/
```

Prefer `--input-file` (JSON) over inline `--input` so commands stay permission-prefix-matchable; the script prints each saved path to stdout. On the **Pi 5** the SDK lives in a venv — invoke with `~/.claude/skills/replicate/.venv/bin/python` instead.

## Picking a model

See the category guides in `references/` (image, video, audio, segmentation) and `references/models/INDEX.md` for per-model deep-dives. Cheap/fast default for tests: `black-forest-labs/flux-schnell`.
