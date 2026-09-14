# Control plane — manage endpoints

Part of the [Runpod API reference](README.md).

**Gotcha:** the Docker image is NOT set on the endpoint. It lives on a **template** (image, exposed `ports`, env vars, container disk). Create the template first, then create an endpoint that references it via `templateId` — the only strictly required create field.

**Gotcha #2 (undocumented):** `POST /v1/templates` defaults to creating a **pod** template even with no `ports`/`startSsh` set — the response comes back with `startJupyter: true, startSsh: true` and `POST /v1/endpoints` against it fails with `500 "Serverless endpoints cannot use pod templates"`. The field that fixes it, `"isServerless": true`, is missing from Runpod's own published OpenAPI schema (confirmed by fetching `https://rest.runpod.io/v1/openapi.json` directly — the `TemplateCreateInput` schema just doesn't list it). Always pass it explicitly:

(This is properly documented in the newer **API v2** — same concept, renamed `"serverless": boolean` and actually present in its OpenAPI schema this time. See `../api-v2.md`.)

```bash
# Create a SERVERLESS template (isServerless:true is required but undocumented)
curl -X POST https://rest.runpod.io/v1/templates \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "name": "my-template",
    "imageName": "runpod/serverless-hello-world:latest",
    "containerDiskInGb": 5,
    "isServerless": true
  }'
```

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

Verified end-to-end (2026-07-29): `runpod/serverless-hello-world:latest` (415MB, the small `latest` tag — not the ~4.6GB `dev`/versioned tags) on an `NVIDIA L4` template, `workersMin:0`/`workersMax:1`/`idleTimeout:5`. Cold start ~9s, execution 142ms, `/health` shows 0 workers again immediately after.

**Cost gotcha (2026-07-29):** that "0 workers" reading didn't hold. Checking `/health` again ~40 minutes later on the same idle endpoint (no new requests sent, `workersMin` still `0`) showed **1 worker sitting `idle`/`ready`** — i.e. `workersMin:0` does not guarantee it stays at zero workers over time; something (possibly the `workersStandby:1` field the create response sets by default, possibly `flashboot:true` keeping a warm buffer) spun a worker back up on its own. An idle/ready GPU worker is presumably billing even with no jobs running. **Don't assume a scale-to-zero endpoint is actually costing $0 just because you saw it hit zero once** — re-check `/health` before walking away, and delete the endpoint entirely (`DELETE /v1/endpoints/{id}`) when you're done testing rather than leaving it at `workersMin:0` and trusting it to stay free.

Common create fields: `gpuTypeIds` (array, see [`gpu-types.md`](gpu-types.md)), `workersMin`/`workersMax`, `idleTimeout` (seconds, 1–3600), `containerDiskInGb`, `networkVolumeId`, `executionTimeoutMs`, scaler (`scalerType` `QUEUE_DELAY`|`REQUEST_COUNT`, `scalerValue`). The exposed HTTP port for Ollama (`"11434/http"`) goes in the **template's** `ports`, not the endpoint body.

```bash
curl -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/endpoints              # list
curl -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/endpoints/ENDPOINT_ID  # get one

curl -X PATCH https://rest.runpod.io/v1/endpoints/ENDPOINT_ID \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"workersMax": 3}'                                                                          # scale

curl -X DELETE https://rest.runpod.io/v1/endpoints/ENDPOINT_ID \
  -H "Authorization: Bearer $RUNPOD_API_KEY"                                                      # delete
```

## Sources

docs.runpod.io: `/api-reference/endpoints/*`. `isServerless` gotcha found by diffing a live `POST /v1/templates` response against `GET /v1/openapi.json` (2026-07-29) — not in any doc page as of that date.
