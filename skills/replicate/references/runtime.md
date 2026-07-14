# Replicate — runtime reference

Behavior of `scripts/run_model.py` and HTTP-API fallbacks. Read when actually running into one of these situations — not for routine generation.

## File output handling

Replicate delivers file outputs as HTTPS URLs on `replicate.delivery`. The script downloads them and saves locally.

- **Files auto-expire after ~1 hour.** Save or use immediately.
- Models return **one of**: a single FileOutput, a list of FileOutputs, a dict with file values (including dicts whose values are nested lists, like `meta/sam-2`'s `individual_masks`), or (for LLMs) a streaming iterator of text. The script recursively walks dict/list structures and saves every file-like leaf.
- For LLMs / text output the script writes a `.txt` and also prints to stdout.
- Extensions are inferred from the URL path. If a model returns an unusual format, pass `--basename` or post-rename the file.

## Output metadata

Every run writes a **sidecar** `<basename>.meta.json` alongside the output(s) — one per run — capturing `model`, `version` (resolved hash), `prediction_id`, timestamps, `runtime_seconds`, the full `inputs` dict (pre-upload, so local paths show as the original path strings), and the list of saved output filenames. Read it to answer "what prompt/seed/inputs produced this file?" even months later.

On top of the sidecar, metadata is **embedded into the output file itself** where the format supports it — so it survives copies / re-uploads:

- **PNG** — `Software` / `Source` / `Comment` tEXt chunks via Pillow
- **JPG / WebP** — EXIF `UserComment` (0x9286) and `ImageDescription` (0x010E) via Pillow
- **MP4 / WebM / MOV / MKV** — `comment` + `title` metadata via `ffmpeg -codec copy` (no re-encode; skipped silently if `ffmpeg` isn't on PATH)
- **WAV / MP3** — ID3 `TXXX:prompt` / `TXXX:model` via `mutagen` (skipped silently if mutagen isn't installed)
- **Anything else** (.bin, .txt, .glb, .zip, streaming LLM output, etc.) — sidecar only

The embedded blob is a compact `{"model", "prompt", "seed", "tool"}` — only fields a viewer wants inline. The sidecar always has the full inputs. Embedding failures log a `[metadata] ...` warning to stderr and never fail the run.

Pass `--no-metadata` to disable both sidecar and embedding.

Pass `--no-sidecar` to keep embedding but skip the `.meta.json` sidecar. Use this when you want the prompt traveling inside each output file (so it survives renames, moves, copies) but don't want extra JSON files cluttering your output directories. This is the right default for iterative / exploratory work where the embedded EXIF/PNG-tEXt blob is sufficient.

## Version pinning

`run_model.py` accepts either a bare slug (`owner/name`) or a pinned ref (`owner/name:abcd1234...`). When you pass a bare slug, the script resolves the current latest-version hash via `models.get()` and pins to it before calling `predictions.create`. This avoids the **404 on bare-slug** that several older community models return (e.g. `andreasjansson/illusion`, `bytedance/bagel`, `fofr/latent-consistency-model`, `jagilley/controlnet-scribble`, `lucataco/flux-dev-multi-lora`, `fermatresearch/magic-image-refiner`, `meta/sam-2`). The resolved hash is printed to stderr (`[resolve] owner/name -> :abcd12345678...`) and stored in the sidecar's `version` field.

To pin explicitly (e.g. for long-running batches where you don't want a mid-batch version change), pass the full ref: `python scripts/run_model.py owner/name:<hash> --input ...`.

## Passing local files as input

If any input value is a local file path (e.g. for image-to-video), the script detects it and passes an open file handle to the SDK, which uploads it. URLs (`http://`, `https://`, `data:`) are passed through untouched. Remote URLs are more efficient — prefer them for files already in the cloud.

## HTTP-only fallback

If the Python SDK isn't available, use the HTTP API directly. See `references/http-api.md` for endpoint shapes, the `Prefer: wait` synchronous mode, polling loops, file uploads, and download handling.

## When things fail

- **401 Unauthorized** — token missing or wrong. Re-check `echo $REPLICATE_API_TOKEN`.
- **402 Payment Required** — account needs billing set up at replicate.com/account/billing.
- **422 Validation** — input schema mismatch. Re-read the model page; field names change between versions.
- **Model failed mid-run** — the script prints the prediction ID; fetch its logs with:
  ```bash
  curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
      https://api.replicate.com/v1/predictions/<id> | jq '.error, .logs'
  ```
- **Cold start slowness** — first run of an idle model can take 1–3 extra minutes while it warm-boots. Normal; wait.
