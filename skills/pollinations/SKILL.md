---
name: pollinations
version: 1.0.0
public: true
description: >-
  Generate images, videos, text-to-speech audio, music, and chat/text completions using
  the Pollinations.AI API. Use when the user asks to create/generate an image, video clip,
  voiceover, speech, or music, or wants to call an LLM through Pollinations.
semantic_id: "aPwFGVu6RbetOrhRNi-Xh--qZJykcAAJ"
related_ids:
  - "Tn5GDFfVCQUZbJD0QgYWxT-aY7ikUAAK"
  - "IG2DMNG5pVX7shlyN68mrTVpZ3riUAAP"
topic_id: "v2:DNGP"
topic_path: "model-runners/model-hosts"
---

# Pollinations.AI

Single unified provider for text, image, video, and audio.

**Prefer the `polli` CLI when it's available** (`command -v polli`) — it handles auth from the local keychain, surfaces friendly error messages (especially 402 balance hints), and writes binaries directly to disk.

**If `polli` isn't installed, use the bundled HTTP fallback [`scripts/pollinate.py`](scripts/pollinate.py)** — pure-stdlib Python (no pip deps), same media coverage and prompt-metadata embedding, key from `$POLLINATIONS_API_KEY`. See [When the CLI isn't enough](#when-the-cli-isnt-enough). Drop to raw HTTP/SDK calls only when neither tool expresses what you need (embedding in code, tool-calling chat, etc.).

## Pick a doc

Load only the doc you need — keep this skill file lean.

| Task                                             | Doc                                     |
| ------------------------------------------------ | --------------------------------------- |
| Image generation / editing                       | [`references/image.md`](references/image.md)         |
| Video generation                                 | [`references/video.md`](references/video.md)         |
| TTS, music, transcription                        | [`references/audio.md`](references/audio.md)         |
| Text / chat (incl. vision)                       | [`references/text.md`](references/text.md)           |
| Auth, keys, usage, uploads, BYOP, errors         | [`references/other.md`](references/other.md)         |
| Per-model deep dives (caps, quirks, prompt tips) | [`references/models/`](references/models/README.md)  |
| Full API reference (all endpoints, every param)  | [`references/reference.md`](references/reference.md) |
| Canonical upstream snapshot                      | [`references/llm.txt`](references/llm.txt)           |

## CLI at a glance

```bash
polli gen image "a cat in space" --model flux --output cat.png
polli gen video "drone over mountains" --model ltx-2 --duration 5 --output clip.mp4
polli gen audio "hello world" --voice nova --output hello.mp3
polli gen text "summarize this" < notes.md
polli gen chat --model openai-large       # interactive
polli models --type image                  # list models (free + paid)
polli usage                                # pollen balance
polli auth login / status / logout
polli upload ./frame.png                   # → public URL on media.pollinations.ai
```

Every command supports `--json` for machine-readable output.

## Workflow for artifacts

1. Pick a descriptive filename in the cwd (`sunset_beach.jpg`, not `output.jpg`).
2. Run the CLI with `--output <path>` so bytes land on disk, never in the context.
3. **For images and videos, write the prompt into the file's metadata** so it travels with the file. Use `exiftool` (install via `brew install exiftool` if missing):

   ```bash
   exiftool -overwrite_original \
     -Comment="$PROMPT" -Description="$PROMPT" -UserComment="$PROMPT" \
     -XMP-dc:Description="$PROMPT" -Software="pollinations/$MODEL" \
     <file>
   ```

   Works for JPG/PNG/WebP and MP4/MOV. Record at minimum the prompt; include the model and seed when you have them. Verify with `exiftool -Comment -Description <file>`.

4. Report the saved path back to the user — the harness displays images/audio/video inline.
5. On `402` (insufficient balance): the chosen model is paid. Retry with a free-tier model (`flux`/`zimage` for image, `ltx-2` for video, `elevenlabs`/`elevenmusic` for audio, `openai`/`mistral`/`grok` etc. for text).

## Auth

The CLI reads its key from the local keychain once you run `polli auth login`. For HTTP fallback, set `$POLLINATIONS_API_KEY` (checked by the env — if missing, ask the user to export it). Get keys at <https://enter.pollinations.ai>.

## When the CLI isn't enough

### `scripts/pollinate.py` — drop-in fallback when `polli` is absent

Pure-stdlib Python wrapper over the HTTP API. Same behavior the workflow expects: saves
to disk, embeds the prompt into image/video metadata (via `exiftool`, or `ffmpeg` for
video), friendly 402 hints. Needs `$POLLINATIONS_API_KEY` for generation (model listing
is open). Run `scripts/pollinate.py -h` for all flags.

```bash
scripts/pollinate.py image "a cat in space" -o cat.jpg --model flux --width 1024 --height 1024
scripts/pollinate.py video "drone over mountains" -o clip.mp4 --model ltx-2 --duration 5 --aspect-ratio 16:9
scripts/pollinate.py audio "Hello world" -o hello.mp3 --voice nova
scripts/pollinate.py text  "summarize this" --model openai            # → stdout, or -o out.txt
scripts/pollinate.py models --type image                              # no key needed
```

### Raw HTTP / SDK

For anything the script doesn't cover (tool-calling chat, embedding in code), call the API directly:

- Base URL: `https://gen.pollinations.ai`
- OpenAI-compat under `/v1/*` — set `base_url="https://gen.pollinations.ai/v1"` in any OpenAI SDK
- Image and video share the same path (`/image/{prompt}`) — picking a video model flips the response from `image/jpeg` to `video/mp4`
- A non-default `User-Agent` header is required (the API is behind Cloudflare, which 403s the default `python-urllib` UA)

The per-medium docs above show both the CLI form and the HTTP fallback side-by-side.
