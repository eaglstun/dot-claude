# Runpod API v1 reference — index

Enough of the Runpod public API to create, manage, and call a serverless endpoint from the command line — the step the deploy scripts currently leave to the console. Verified against docs.runpod.io (May 2026); the API moved from GraphQL to REST, so ignore older GraphQL examples.

**This is v1.** There's also a newer, beta **API v2** at a different base URL (`https://api.runpod.io/v2`) — see `../api-v2.md`. v2 fixes real gaps (a documented GPU-catalog route, REST-creatable load-balancing endpoints) but is still beta; both coexist for now.

Two distinct planes, **same Bearer key**:

| Plane                | Base URL                                 | Use                                                             |
| -------------------- | ---------------------------------------- | --------------------------------------------------------------- |
| Control (management) | `https://rest.runpod.io/v1`              | create/list/update/delete endpoints, templates, network volumes |
| Data (invocation)    | `https://api.runpod.ai/v2/{endpoint_id}` | submit jobs to a deployed endpoint                              |

## Auth

Create a key in the console under **Settings → API Keys** (console.runpod.io). Every request on both planes uses:

```
Authorization: Bearer $RUNPOD_API_KEY
Content-Type: application/json
```

## Files in this folder

| File                                         | Covers                                                                               |
| -------------------------------------------- | ------------------------------------------------------------------------------------ |
| [`control-plane.md`](control-plane.md)       | Creating/managing templates and endpoints — including the `isServerless` gotcha      |
| [`data-plane.md`](data-plane.md)             | Calling a queue-based endpoint (`/runsync`, `/run`, `/status`, `/cancel`, `/health`) |
| [`ollama-lb.md`](ollama-lb.md)               | Reaching Ollama's native HTTP API through a load-balancing endpoint                  |
| [`network-volumes.md`](network-volumes.md)   | Creating/listing network volumes, the S3-compatible side                             |
| [`gpu-types.md`](gpu-types.md)               | Valid `gpuTypeIds` strings and rough serverless pricing                              |
| [`public-endpoints.md`](public-endpoints.md) | Runpod's own hosted models — catalog + call pattern, no deploy needed                |
| [`models/`](models/README.md)                | One file per model with its exact request/response schema (Kimi, Flux, Qwen3, etc.)  |
