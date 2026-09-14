# Moonshot Kimi

Part of the [Public Endpoint models index](README.md).

`model-id`: `moonshot-kimi` — **verified live 2026-07-29.** Multiple Kimi versions live behind one slug, selected via the `model` field in the request body:

- `kimi-k2.6` (default), `kimi-k2.7-code`, `kimi-k3` — K2.6/K2.7-Code: 256K context, $0.95/$4.00 per 1M in/out tokens; K3: 1M context, $3.00/$15.00 per 1M in/out tokens.
- It's a reasoning model — output includes a separate `reasoning_content` field alongside `content`, and reasoning tokens are billed as completion tokens (a one-sentence-answer test call still burned ~200 reasoning tokens).

```bash
curl -X POST https://api.runpod.ai/v2/moonshot-kimi/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{"role": "user", "content": "Hello"}],
      "sampling_params": {"max_tokens": 200, "temperature": 0.7},
      "model": "kimi-k3"
    }
  }'
# -> {"output":[{"cost":0.0039,"result":{"choices":[{"message":{"content":"...","reasoning_content":"...","role":"assistant"}}],"model":"kimi-k3","usage":{...}}}],"status":"COMPLETED"}
```

Response shape differs from a normal serverless worker: `output` is a list, and the OpenAI-style chat completion is nested at `output[0].result`, with `output[0].cost` giving the exact USD charged for that call.

## Sources

docs.runpod.io/public-endpoints/models/moonshot-kimi, verified live 2026-07-29.
