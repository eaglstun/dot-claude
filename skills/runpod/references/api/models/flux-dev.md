# Flux Dev

Part of the [Public Endpoint models index](README.md).

`model-id`: `black-forest-labs-flux-1-dev` — **❌ docs only, not independently verified.**

Pricing per docs: $0.02/megapixel (Flux Schnell's sibling doc claimed a per-megapixel formula that turned out to be wrong in practice — see [`flux-schnell.md`](flux-schnell.md) — so don't trust this number until re-tested).

```json
// request
{
  "input": {
    "prompt": "A serene mountain landscape at sunset, golden light filtering through clouds, photorealistic",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 28,
    "guidance": 7.5,
    "seed": 42,
    "image_format": "png"
  }
}
// documented response — Flux Schnell's doc claimed the same output.image_url shape and was WRONG (actual field was output.result); assume this one is equally suspect until verified
{"output":{"image_url":"https://image.runpod.ai/abc123/output.png","cost":0.02097152},"status":"COMPLETED"}
```

## Sources

docs.runpod.io/public-endpoints/models/flux-dev — not live-tested. See [`flux-schnell.md`](flux-schnell.md) for why this doc page's claims (response field name, pricing formula) shouldn't be taken at face value.
