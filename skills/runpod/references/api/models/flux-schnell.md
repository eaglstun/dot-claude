# Flux Schnell

Part of the [Public Endpoint models index](README.md).

`model-id`: `black-forest-labs-flux-1-schnell` — **verified live 2026-07-29** with a 256×256 test image. Two real discrepancies vs the published doc page:

- **Response shape:** actual response is `{"output":{"cost":...,"result":"https://...jpeg"}}` — a bare URL string at `output.result`, not `output.image_url` as documented.
- **Pricing:** doc claims "$0.0024/megapixel" (would be ~$0.00016 for a 256×256 image); actual charge was a flat **$0.003** regardless. Treat the per-megapixel formula as unverified/wrong until re-tested at a larger size.

```bash
curl -X POST https://api.runpod.ai/v2/black-forest-labs-flux-1-schnell/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "a small red circle on white background", "width": 256, "height": 256, "num_inference_steps": 4, "seed": 1}}'
# -> {"delayTime":4624,"executionTime":12317,"output":{"cost":0.003,"result":"https://image.runpod.ai/.../result.jpeg"},"status":"COMPLETED"}
```

## Sources

docs.runpod.io/public-endpoints/models/flux-schnell, verified live 2026-07-29 (response shape and pricing both found to differ from the doc page).
