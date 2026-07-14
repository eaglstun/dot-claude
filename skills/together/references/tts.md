# Together — text-to-speech

> **Script:** `scripts/tts.py "text" -o out.mp3` (REST) or `--stream` for the WebSocket below.

Endpoint: `POST https://api.together.ai/v1/audio/speech`. Returns raw audio bytes — pipe to a file with `--output`.

```bash
curl -sS https://api.together.ai/v1/audio/speech \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hexgrad/Kokoro-82M",
    "input": "The quick brown fox jumps over the lazy dog.",
    "voice": "af_bella",
    "response_format": "mp3"
  }' --output out.mp3
```

## Models

| Model                          | $/M chars | Notes                                                                       |
| ------------------------------ | --------- | --------------------------------------------------------------------------- |
| `hexgrad/Kokoro-82M`           | $4        | **Default** — cheap, 50+ voices, supports voice-mixing via `voice1+voice2`  |
| `canopylabs/orpheus-3b-0.1-ft` | $15       | Better prosody; voices: tara, leah, jess, leo, dan, mia, zac, zoe           |
| Cartesia Sonic 2 variants      | $65       | Highest quality, 100+ named voices ("friendly sidekick", "meditation lady") |

## Parameters

- `model` (required)
- `input` (required) — text to speak
- `voice` (required) — see per-model voice lists above
- `response_format` — `"mp3"` (default), `"wav"`, `"raw"` (PCM), `"mulaw"`
- `sample_rate` — optional int (Hz)

## Cost reference

A typical paragraph (~500 chars) costs ~$0.002 on Kokoro, ~$0.0075 on Orpheus, ~$0.03 on Cartesia.

## Real-time / streaming TTS (WebSocket) — ⚠️ untested

> The `scripts/tts.py --stream` client and the example below are written from the protocol spec but have **not** been run against a live key. Verify before relying on them.

For low-latency playback, stream audio over a WebSocket — you get base64 PCM chunks as they're generated instead of one blob at the end. Best for live/interactive use; for "render a file" just use the REST call above.

- Connect: `wss://api.together.ai/v1/audio/speech/websocket`
- Auth: `Authorization: Bearer $TOGETHER_API_KEY` header on the upgrade request
- Query params (optional): `model` (`hexgrad/Kokoro-82M` default, or `cartesia/sonic-english`), `voice` (default `tara`), `language` (ISO 639-1), `max_partial_length` (default 250)
- Audio format: **raw PCM s16le, mono, 24000 Hz** (base64 inside each delta event — no container, so wrap in WAV headers if you want a playable file)

### Protocol

Client → server (JSON):

| `type`                     | Purpose                                      |
| -------------------------- | -------------------------------------------- |
| `input_text_buffer.append` | Send text (`{"type":..., "text":"..."}`)     |
| `input_text_buffer.commit` | Flush buffered partial text now (don't wait) |
| `input_text_buffer.clear`  | Drop buffered text                           |
| `tts_session.updated`      | Change voice / `extra_params` mid-session    |
| `context.cancel`           | Cancel a `context_id`                        |

Server → client (JSON): `session.created` (on connect) → `conversation.item.input_text.received` (ack) → repeated `conversation.item.audio_output.delta` (`.delta` = base64 PCM chunk) → `conversation.item.audio_output.done`. Errors arrive as `conversation.item.tts.failed` with an `error` object.

Buffered partial text is spoken when the model decides it's complete, when it exceeds `max_partial_length`, or when you send `input_text_buffer.commit`.

### Minimal example (Python)

```python
import asyncio, base64, json, websockets

async def stream_tts(text, out="stream.pcm"):
    url = "wss://api.together.ai/v1/audio/speech/websocket?model=hexgrad/Kokoro-82M&voice=tara"
    headers = {"Authorization": f"Bearer {__import__('os').environ['TOGETHER_API_KEY']}"}
    async with websockets.connect(url, additional_headers=headers) as ws:
        await ws.send(json.dumps({"type": "input_text_buffer.append", "text": text}))
        await ws.send(json.dumps({"type": "input_text_buffer.commit"}))
        with open(out, "wb") as f:
            async for raw in ws:
                msg = json.loads(raw)
                if msg["type"] == "conversation.item.audio_output.delta":
                    f.write(base64.b64decode(msg["delta"]))   # raw PCM s16le @24kHz
                elif msg["type"] == "conversation.item.audio_output.done":
                    break

asyncio.run(stream_tts("Hello from the stream."))
# play/convert:  ffmpeg -f s16le -ar 24000 -ac 1 -i stream.pcm stream.wav
```

(`additional_headers` is `websockets` ≥12; older versions use `extra_headers`.)
