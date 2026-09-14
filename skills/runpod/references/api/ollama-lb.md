# Reaching Ollama's native HTTP API (raw port)

Part of the [Runpod API reference](README.md).

Ollama speaks its own HTTP API on `11434` — it is not a queue handler. To hit `/api/generate`, `/api/chat`, `/api/tags` directly, deploy as a **load-balancing endpoint** (bypasses the job queue, routes straight to the worker). Traffic then goes to:

```
https://ENDPOINT_ID.api.runpod.ai/<path>      # e.g. .../api/chat
```

The worker's listen port comes from the `PORT` env var. Cloudflare fronts this, so each request must finish within ~100s (else HTTP 524).

Images built by `scripts/runpod-deploy.sh` bundle an nginx proxy (`scripts/lb-entrypoint.sh`) that serves `/ping` on `$PORT` and forwards the API to Ollama, satisfying the LB health check.

This wiring is now verified against the Herd/Bardtown image
`<registry-user>/bardtown-runpod:v3`: `PORT=11434`, `PORT_HEALTH=8080`, and
`HEALTH_CHECK_PATH=/ping` produced a ready load-balancing worker whose public
`/api/tags` and `/api/chat` routes both returned successfully on 2026-08-22. A
later flashboot resume stalled before readiness, so readiness must still be
tested after lifecycle/config changes. The `{pod-id}-{port}.proxy.runpod.net`
pattern is **Pods only**, NOT serverless.

**Update (2026-07-30):** the "REST can't create a load-balancing endpoint" limitation below and in `scripts/runpod-wire.sh` may no longer be true. Runpod's newer **API v2** (`../api-v2.md`, beta) has `POST /v2/serverless` take a `"type": "LOAD_BALANCER"` field directly in the OpenAPI schema — no console step implied. Not yet tested end-to-end for this exact Ollama LB use case (only the v2 catalog/read endpoints have been exercised so far), but if it holds up on a real test, `runpod-wire.sh` could go from "template + manual console steps" to fully scripted. Check `../api-v2.md` before repeating the manual-step workaround below.

## Sources

docs.runpod.io: `/serverless/load-balancing/*`.
