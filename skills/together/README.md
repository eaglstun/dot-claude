# together

Claude Code skill for direct calls to the **Together AI** OpenAI-compatible API (`https://api.together.ai/v1`) — text, vision, embeddings, image, and speech. Use it for raw model output (translation, classification, drafting, fast chat) when you want a single OpenAI-compatible endpoint without extra agent overhead.

## Setup

Set the `TOGETHER_API_KEY` environment variable — macOS/Linux: `export TOGETHER_API_KEY=...` in your shell profile (`~/.zshenv`, `~/.bashrc`, `~/.profile`); Windows PowerShell: `setx TOGETHER_API_KEY "..."`, then reopen the shell. Get a key / check credits at <https://api.together.ai/settings/billing>; calls return `Credit limit exceeded` with no balance.

Examples use `curl`, `jq`, and `grep` (plus `exiftool`/`ffmpeg` for media metadata) — standard on macOS/Linux. On Windows, run them under WSL or Git Bash, or install `jq`/`grep` first.

## Usage

`SKILL.md` is the entry point; Claude loads the reference matching the task:

| Task                                  | Reference                                                          | Status |
| ------------------------------------- | ------------------------------------------------------------------ | ------ |
| Chat / text completions (default)     | [`references/chat.md`](references/chat.md)                         | ✅     |
| Embeddings / rerank                   | [`references/embeddings.md`](references/embeddings.md)             | ✅     |
| Image generation                      | [`references/images.md`](references/images.md)                     | ✅     |
| Text-to-speech                        | [`references/tts.md`](references/tts.md)                           | ✅     |
| Vision (analyze an image)             | [`references/vision.md`](references/vision.md)                     | ✅     |
| Code interpreter (sandbox)            | [`references/code-interpreter.md`](references/code-interpreter.md) | ✅     |
| Raw non-chat completions              | [`references/completions.md`](references/completions.md)           | ✅     |
| Speech-to-text (transcribe/translate) | [`references/stt.md`](references/stt.md)                           | ✅     |
| Video generation (async)              | [`references/video.md`](references/video.md)                       | ✅     |

Streaming TTS (WebSocket) is covered inside `tts.md`. Platform/ops endpoints (files, fine-tuning, batch, dedicated endpoints, evals, clusters, deployments) are intentionally **out of scope** — see SKILL.md.

Default chat model: **`deepseek-ai/DeepSeek-V3.1`**. Gotcha: only serverless models are callable — test new ones before adding to a chain (`"choices"` = ok, `"non-serverless"` = dedicated only).

## Scripts

Each endpoint has a runnable helper in [`scripts/`](scripts/) — **pure standard library, no pip install**, key from `TOGETHER_API_KEY`. Use them for the multi-step/fiddly cases (video polling, WebSocket TTS streaming, multipart STT upload, media provenance) instead of hand-rolling `curl`:

```text
scripts/chat.py "prompt"               scripts/tts.py "text" -o out.mp3   (--stream UNTESTED)
scripts/completions.py "prompt"        scripts/stt.py audio.mp3 [--translate]
scripts/embeddings.py "a" "b"          scripts/video.py "prompt" -o out.mp4
scripts/images.py "prompt" -o out.png  scripts/tci.py "code"
scripts/vision.py "prompt" --image URL
```

Shared plumbing is in `scripts/_common.py`. See the per-endpoint reference files and SKILL.md for full flags.
