# pollinations

Claude Code skill for generating images, videos, text-to-speech audio, music, and chat/text completions through the **Pollinations.AI** API — one unified provider for all four modalities. Prefers the local `polli` CLI (keychain auth, friendly error/balance hints, writes binaries straight to disk) and falls back to the HTTP API when the CLI can't express what's needed.

## CLI at a glance

```bash
polli gen image "a cat in space" --model flux --output cat.png
polli gen video "drone over mountains" --model ltx-2 --duration 5 --output clip.mp4
polli gen audio "hello world" --voice nova --output hello.mp3
polli models --type image     # list models   ·   polli usage   # pollen balance
```

## Docs

`SKILL.md` is the entry point; load the reference matching the task:

| Task | Doc |
| --- | --- |
| Image generation / editing | [`references/image.md`](references/image.md) |
| Video generation | [`references/video.md`](references/video.md) |
| TTS, music, transcription | [`references/audio.md`](references/audio.md) |
| Text / chat (incl. vision) | [`references/text.md`](references/text.md) |
| Auth, uploads, errors · per-model deep dives | [`references/other.md`](references/other.md) · [`references/models/`](references/models/README.md) |

Helper scripts live under `scripts/`; generated media has the model + prompt embedded in the file before the path is reported.
