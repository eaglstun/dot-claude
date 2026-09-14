# Minimax Speech 02 HD

Part of the [Public Endpoint models index](README.md).

`model-id`: `minimax-speech-02-hd` — **❌ docs only, not independently verified.**

Pricing per docs: $0.05 per 1,000 characters.

```json
// request
{
  "input": {
    "prompt": "Welcome to our advanced text-to-speech system.",
    "voice_id": "Wise_Woman",
    "speed": 1,
    "volume": 1,
    "pitch": 0,
    "emotion": "happy",
    "english_normalization": false
  }
}
// documented response (NOT independently confirmed — Chatterbox Turbo's doc omitted a duplicate `result` field that showed up live, so treat this as a floor, not the full shape)
{"output":{"audio_url":"https://audio.runpod.ai/abc123/output.mp3","cost":0.0055},"status":"COMPLETED"}
```

Note the field name difference from Chatterbox Turbo: this one takes `voice_id`, Chatterbox takes `voice`.

## Sources

docs.runpod.io/public-endpoints/models/minimax-speech — not live-tested.
