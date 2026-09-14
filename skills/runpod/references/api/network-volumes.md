# Network volumes

Part of the [Runpod API reference](README.md).

```bash
curl -X POST https://rest.runpod.io/v1/networkvolumes \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"name": "ollama-models", "size": 50, "dataCenterId": "EU-RO-1"}'   # size GB, datacenter code
curl -H "Authorization: Bearer $RUNPOD_API_KEY" https://rest.runpod.io/v1/networkvolumes  # list
```

Volumes are also reachable over an S3-compatible host per datacenter — e.g. `https://s3api-us-il-1.runpod.io` (used by `scripts/runpod-volume-sync.sh`). Match the S3 host's datacenter to the volume's `dataCenterId`.

## Sources

docs.runpod.io: `/api-reference/network-volumes/*`.
