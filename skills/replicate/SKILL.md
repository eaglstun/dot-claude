---
name: replicate
version: 1.0.0
public: true
description: >-
  Run any model hosted on Replicate.com — generate videos, images, audio, music, or text
  via models like seedance, veo, kling, minimax, wan, runway, flux, sdxl, whisper, or any
  other Replicate-hosted model. Use whenever the user wants to generate a video with AI,
  create AI media through Replicate, mentions replicate.com, refers to a Replicate model
  by slug (owner/name), or has REPLICATE_API_TOKEN configured.
semantic_id: "WZyQmXE6omebBLj6dj7fwmcCZWKvwAAC"
related_ids:
  - "aPwFGVu6RbetOrhRNi-Xh--qZJykcAAJ"
  - "WZbfq3SJpGK3cKauLl-tCyVu7eSoYAAC"
topic_id: "v2:DNAJ"
topic_path: "model-runners/model-hosts"
---

# Replicate

A thin, modality-agnostic wrapper around the Replicate API. Initial focus is **video generation**, but the same pattern works for image, audio, text, and any other model hosted on Replicate — the only thing that changes is which model slug and input schema you use.

## Prerequisites

Every call needs `REPLICATE_API_TOKEN`. Check it before doing anything else:

```bash
test -n "$REPLICATE_API_TOKEN" && echo "token set" || echo "MISSING"
```

If missing, stop and ask the user to generate one at https://replicate.com/account/api-tokens and export it (e.g. add to `~/.zshrc`). Do not invent a token or proceed without one — all calls will 401.

The `replicate` Python SDK is the preferred client. If not installed, try `pip install replicate` (or `uv pip install replicate`). If Python or the SDK isn't available, fall back to the HTTP API (see `references/http-api.md`).

**On the Pi 5** the system `python3` has no `replicate` and PEP 668 blocks a system-wide `pip install`; the SDK lives in a venv inside the skill dir. Invoke the script with the venv interpreter:

```bash
~/.claude/skills/replicate/.venv/bin/python scripts/run_model.py <owner/name> --input-file input.json --output ./out/
```

A plain `python scripts/run_model.py` only works on the Mac. If the venv is missing on the Pi, recreate it: `python3 -m venv ~/.claude/skills/replicate/.venv && ~/.claude/skills/replicate/.venv/bin/pip install replicate`.

## Always delegate to a subagent

Both **invoking a model** and **developing this skill** are slow, blocking operations. Video/image jobs take 30s–5min each; writing a new `references/models/<slug>.md` involves many tool calls. Running either inline blocks the TUI.

**Rule: always spawn a subagent via the `Agent` tool instead of executing the work in the main conversation.** Use `run_in_background: true` for generations so the user keeps an interactive session and gets notified on completion.

- **Invocation:** delegate the full "pick model → build input → run `scripts/run_model.py` → report saved paths" flow to an agent.
- **Development** (adding/updating a model reference, running evals, editing this skill): delegate the schema fetch, page scrape, and draft to an agent; review and apply from the main thread.

Only skip delegation for trivial, instant work (reading one file, a single `echo $REPLICATE_API_TOKEN` check).

## Core workflow

1. **Pick a model.** If the user named one, use theirs. Otherwise consult the category reference for the modality (see References below) and pick a sensible default.
2. **Build the input dict.** Each model has its own input schema — the references list common inputs, but schemas drift, so when in doubt check the model's page on replicate.com.
3. **Run it via `scripts/run_model.py`.** The script wraps `replicate.run()`, handles polling, and saves every file output to disk with a sensible extension.
4. **Report the saved file path(s) to the user.** That's the deliverable.

```bash
python scripts/run_model.py <owner/name>[:version] \
    --input '<json>' \
    --output <dir>
```

The script prints each saved path to stdout, one per line. Progress/status goes to stderr. For one-off Python use you can also call the SDK directly — the script is just the common path.

**Pass literal values only** in the Bash call: no `$VAR`, no command substitution, no `~`, no pipes or redirects, or the permission system prompts every time. For non-trivial inputs, write the JSON with the `Write` tool and pass `--input-file`. Worked examples and the full rule: `references/recipes.md`.

File outputs auto-expire after ~1 hour — save or use immediately.

## Cost & timing

Before running an expensive model (Flux Pro, Runway Gen-4.5, Veo, Kling Pro) or anything that costs more than ~$0.10/run, tell the user which model you're about to use and the expected cost — generations on Replicate cost real money.

**Video specifically:** most video jobs take **30s–5min**. `replicate.run()` polls under the hood and blocks until done — don't add your own sleep loop. Tell the user you're going to wait.

## References - load on demand

- **`references/image-models.md`** - image generation, editing, restoration/upscaling, novelty: decision tables, quick picks, per-model summaries. _Read when picking an image model._
- **`references/video-models.md`** - video generation, editing, motion transfer, lipsync, matting, colorization. _Read when picking a video model._
- **`references/audio-models.md`** - TTS, voice cloning, the RVC pipeline, pitch correction. _Read when picking an audio model._
- **`references/segmentation-models.md`** - text-prompted, auto, auto+labels. _Read when picking a segmentation model._
- **`references/models/INDEX.md`** - one-line directory of all 43 per-model deep-dives (unusual schemas, unique pricing, gotchas), grouped by modality; 3D so far is `references/models/prunaai-hunyuan3d-2.md`. _Read when a request names a model: if it has a deep-dive, read that file first and follow its example._
- **`references/loras.md`** - LoRA-aware base models, the `hf_lora`/`lora_scale`/`extra_lora` input fields, trigger-word rules, multi-LoRA stacking, the standard training workflow. _Read when the user wants a LoRA: trigger words like "in ZIKI style", a slug like `zeke/ziki-flux`, a Hugging Face or Civitai link, or stacking styles on Flux/SDXL/Wan._
- **`references/pruna-optimization.md`** - pre-optimized `prunaai/*` slugs (typically 2-5x faster than the base) plus the Cog + SmashConfig path for building a custom optimized model. _Read when latency or cost matters, or the user says "fast", "turbo", "lightning", "juiced", Pruna, or wants a cheaper Flux/SDXL/Wan._
- **`references/runtime.md`** - everything `run_model.py` does beyond `--input`/`--output`: file outputs, `.meta.json` sidecars and embedded metadata, version pinning, local-file uploads, HTTP fallback, error codes (401 / 402 / 422 / cold start). _Read when debugging a run or handling outputs specially._
- **`references/http-api.md`** - the raw HTTP API. _Read when Python or the SDK is unavailable._
- **`references/recipes.md`** - worked example invocations, the permission-friendly (no shell expansion) rules with good/bad examples, runtime quick pointers, and how to extend the skill to a new modality. _Read before composing a non-trivial invocation or adding a new category file._
