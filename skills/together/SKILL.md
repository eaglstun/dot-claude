---
name: together
version: 1.0.0
public: true
description: >-
  Direct calls to Together AI's OpenAI-compatible API for text completions, vision,
  embeddings, and image/speech generation. Models include Qwen3-235B, MiniMax-M2, Llama
  3.3 70B, DeepSeek, and Black Forest Labs FLUX. Use for raw LLM output (translation,
  classification, drafting, fast chat) when you want a single OpenAI-compatible endpoint
  without extra agent overhead.
semantic_id: "KGVGsr_7sxHB-AhzVBwGrTRxpdj3wAAF"
related_ids:
  - "IG2DMNG5pVX7shlyN68mrTVpZ3riUAAP"
  - "IMIDkDGrganQkIHDFZ-GDwQ031MnwAAJ"
topic_id: "v2:DLDM"
topic_path: "model-runners/ai-aggregators"
---

# Together AI Skill

OpenAI-compatible Together AI API — chat, completions, embeddings, vision, image / speech / video generation, speech-to-text, and a code sandbox. Base URL `https://api.together.ai/v1` (video uses `/v2`). Auth via `TOGETHER_API_KEY` — key setup, billing, and tool deps in `references/setup.md`.

This file is an index. Load the one reference for your task — each is self-contained.

## Index — load on demand

Each task has a reference (raw API + `curl`) and a ready-to-run script (`scripts/`, pure stdlib, key from env). Default to chat if unsure.

| Task                                  | Reference                        | Script                                   |
| ------------------------------------- | -------------------------------- | ---------------------------------------- |
| Chat completions (default)            | `references/chat.md`             | `scripts/chat.py "prompt"`               |
| Raw non-chat completion (base models) | `references/completions.md`      | `scripts/completions.py "prompt"`        |
| Embeddings / rerank                   | `references/embeddings.md`       | `scripts/embeddings.py "a" "b"`          |
| Image generation                      | `references/images.md`           | `scripts/images.py "prompt" -o f.png`    |
| Vision (analyze an image)             | `references/vision.md`           | `scripts/vision.py "prompt" --image URL` |
| Text-to-speech                        | `references/tts.md`              | `scripts/tts.py "text" -o f.mp3` ¹       |
| Speech-to-text (transcribe/translate) | `references/stt.md`              | `scripts/stt.py audio.mp3 [--translate]` |
| Video generation (async)              | `references/video.md`            | `scripts/video.py "prompt" -o f.mp4`     |
| Code sandbox (TCI)                    | `references/code-interpreter.md` | `scripts/tci.py "code"`                  |

¹ `tts.py --stream` (WebSocket) is untested — see `references/tts.md`.

## Cross-cutting docs (read when relevant)

- **`references/serverless.md`** — default model + the serverless-vs-dedicated gotcha. Read before adding any new model to a chain (many models are dedicated-only and fail).
- **`references/provenance.md`** — REQUIRED metadata-embed rule for any generated image/audio/video. The scripts do it automatically; do it by hand if you call the API with `curl`.
- **`references/setup.md`** — `TOGETHER_API_KEY` setup (macOS/Linux/Windows), billing, and the `curl`/`jq`/`exiftool` tool deps.

## Scope & script notes

This skill is for getting **model output**, not platform ops. Out of scope (use Together's CLI/SDK directly): files, fine-tuning, batch, dedicated endpoints, evals, clusters, deployments, queue. If your assigned model already handles the task, just use it.

When calling a script, pass **literal args only** (no `$VAR`, `$(...)`, pipes, or redirects) so the call stays prefix-matchable for the permission system; use `--input-file` / `--code-file` / `--messages-file` for complex inputs. Shared plumbing lives in `scripts/_common.py`.
