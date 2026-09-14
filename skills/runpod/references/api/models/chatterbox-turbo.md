# Chatterbox Turbo

Part of the [Public Endpoint models index](README.md).

`model-id`: `chatterbox-turbo` — **verified live 2026-07-29.** Request schema (`prompt`/`voice`/`format`) matches the docs. Two notes:

- **Slow cold start:** 52.5s `delayTime` on this test call — noticeably slower than Kimi (~9s) or Flux (~5s). Budget for it if calling synchronously.
- Response includes the URL under **both** `output.audio_url` and `output.result` (duplicate, same value) — the doc page only mentions `audio_url`.

```bash
curl -X POST https://api.runpod.ai/v2/chatterbox-turbo/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Hi", "voice": "lucy", "format": "wav"}}'
# -> {"delayTime":52530,"output":{"audio_url":"https://...wav","cost":0.00088,"result":"https://...wav"},"status":"COMPLETED"}
```

## Sources

docs.runpod.io/public-endpoints/models/chatterbox-turbo, verified live 2026-07-29.
