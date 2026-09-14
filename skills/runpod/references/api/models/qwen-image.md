# Qwen Image (T2I)

Part of the [Public Endpoint models index](README.md).

`model-id`: `qwen-image-t2i` — **❌ docs only, not independently verified.** Separate slugs exist for the LoRA and Edit variants mentioned in the catalog table in [`../public-endpoints.md`](../public-endpoints.md) (Qwen Image LoRA, Qwen Image Edit, Qwen Image Edit 2511 (+LoRA)) — not individually documented here, likely follow a similar `qwen-image-*` naming pattern but unconfirmed.

Pricing per docs: $0.02/image.

```json
// request
{
  "input": {
    "prompt": "A fashion-forward woman sitting at cobblestone street in Paris",
    "negative_prompt": "",
    "size": "1328*1328",
    "seed": -1,
    "enable_safety_checker": true
  }
}
// documented response (NOT independently confirmed — Flux Schnell's doc had the wrong field name for this exact shape)
{"output":{"image_url":"https://image.runpod.ai/abc123/output.png","cost":0.035267},"status":"COMPLETED"}
```

Note: `size` is a single `"WxH"` string here, not separate `width`/`height` fields like Flux — image models on this catalog don't share one input schema either.

## Sources

docs.runpod.io/public-endpoints/models/qwen-image — not live-tested.
