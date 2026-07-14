# Runpod API — getting started

Enough of the Runpod public API to create, manage, and call a serverless endpoint from the command line — the step the deploy scripts currently leave to the console. Verified against docs.runpod.io (May 2026); the API moved from GraphQL to REST, so ignore older GraphQL examples.

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

## Control plane — manage endpoints

**Gotcha:** the Docker image is NOT set on the endpoint. It lives on a **template** (image, exposed `ports`, env vars, container disk). Create the template first, then create an endpoint that references it via `templateId` — the only strictly required create field.

```bash
# Create endpoint (templateId required; rest optional)
curl -X POST https://rest.runpod.io/v1/endpoints \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "templateId": "30zmvf89kd",
    "name": "ollama-mote-14b",
    "computeType": "GPU",
    "gpuTypeIds": ["NVIDIA A40"],
    "workersMin": 0,
    "workersMax": 1,
    "idleTimeout": 60,
    "containerDiskInGb": 30,
    "networkVolumeId": "agv6w2qcg7"
  }'
```

Common create fields: `gpuTypeIds` (array, see below), `workersMin`/`workersMax`, `idleTimeout` (seconds, 1–3600), `containerDiskInGb`, `networkVolumeId`, `executionTimeoutMs`, scaler (`scalerType` `QUEUE_DELAY`|`REQUEST_COUNT`, `scalerValue`). The exposed HTTP port for Ollama (`"11434/http"`) goes in the **template's** `ports`, not the endpoint body.

```bash
curl -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/endpoints              # list
curl -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/endpoints/ENDPOINT_ID  # get one

curl -X PATCH https://rest.runpod.io/v1/endpoints/ENDPOINT_ID \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"workersMax": 3}'                                                                          # scale

curl -X DELETE https://rest.runpod.io/v1/endpoints/ENDPOINT_ID \
  -H "Authorization: Bearer $RUNPOD_API_KEY"                                                      # delete
```

## Data plane — call a queue-based endpoint

For standard queue workers, every request is `{"input": {...}}` and you poll for the result.

| Path           | Method | Purpose                          |
| -------------- | ------ | -------------------------------- |
| `/runsync`     | POST   | submit and wait (≤ a few min)    |
| `/run`         | POST   | submit async, returns a job `id` |
| `/status/{id}` | GET    | poll status + `output`           |
| `/cancel/{id}` | POST   | cancel a job                     |
| `/health`      | GET    | worker/job counts                |

```bash
curl -X POST https://api.runpod.ai/v2/ENDPOINT_ID/runsync \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Hello"}}'
# -> {"id":"sync-...","status":"COMPLETED","output":{...},"delayTime":824,"executionTime":3391}
```

Status values: `IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMED_OUT`.

## Reaching Ollama's native HTTP API (raw port)

Ollama speaks its own HTTP API on `11434` — it is not a queue handler. To hit `/api/generate`, `/api/chat`, `/api/tags` directly, deploy as a **load-balancing endpoint** (bypasses the job queue, routes straight to the worker). Traffic then goes to:

```
https://ENDPOINT_ID.api.runpod.ai/<path>      # e.g. .../api/chat
```

The worker's listen port comes from the `PORT` env var. Cloudflare fronts this, so each request must finish within ~100s (else HTTP 524).

Images built by `scripts/runpod-deploy.sh` bundle an nginx proxy (`scripts/lb-entrypoint.sh`) that serves `/ping` on `$PORT` and forwards the API to Ollama, satisfying the LB health check.

> **Unverified:** the exact wiring to expose Ollama on a load-balancing worker (`$PORT` vs `PORT_HEALTH` semantics) isn't documented for Ollama specifically — confirm on first deploy. The `{pod-id}-{port}.proxy.runpod.net` pattern is **Pods only**, NOT serverless.

## Network volumes

```bash
curl -X POST https://rest.runpod.io/v1/networkvolumes \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"name": "ollama-models", "size": 50, "dataCenterId": "EU-RO-1"}'   # size GB, datacenter code
curl -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/networkvolumes  # list
```

Volumes are also reachable over an S3-compatible host per datacenter — e.g. `https://s3api-us-il-1.runpod.io` (used by `scripts/runpod-volume-sync.sh`). Match the S3 host's datacenter to the volume's `dataCenterId`.

## GPU type IDs

Referenced by full string in `gpuTypeIds`. Confirmed: `"NVIDIA A40"`, `"NVIDIA A100 80GB PCIe"`, `"NVIDIA A100-SXM4-80GB"`, `"NVIDIA L40S"`, `"NVIDIA H100 80GB HBM3"`, `"NVIDIA RTX A6000"`, `"NVIDIA GeForce RTX 4090"`, `"NVIDIA L4"`. The console GPU-types page lists the rest; there is no clearly documented REST `GET /v1/gputypes` route — use the strings directly.

## Sources

docs.runpod.io: `/api-reference/endpoints/*`, `/serverless/endpoints/send-requests`, `/serverless/endpoints/operation-reference`, `/serverless/load-balancing/*`, `/api-reference/network-volumes/*`, `/references/gpu-types`.
