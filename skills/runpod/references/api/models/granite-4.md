# IBM Granite 4.0

Part of the [Public Endpoint models index](README.md).

`model-id`: `granite-4-0-h-small` — **❌ docs only, not independently verified.**

Pricing per docs: $10.00/1M tokens.

```json
// request
{
  "input": {
    "messages": [
      {"role": "system", "content": "You are a helpful assistant. Please ensure responses are professional, accurate, and safe."},
      {"role": "user", "content": "What is Runpod?"}
    ],
    "sampling_params": {"max_tokens": 512, "temperature": 0.7, "seed": -1, "top_k": -1, "top_p": 1}
  }
}
// documented response (NOT independently confirmed)
{"output":{"choices":[{"tokens":["..."]}],"cost":0.00185,"usage":{"input":35,"output":150}},"status":"COMPLETED"}
```

Note the response shape here (`output` as an object with `choices[].tokens`) differs from Kimi's (`output` as a list with `result.choices[].message.content`) — Runpod's public text endpoints don't share one consistent schema. Confirm the actual shape before parsing.

## Sources

docs.runpod.io/public-endpoints/models/granite-4 — not live-tested.
