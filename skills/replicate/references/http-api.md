# Replicate HTTP API (SDK-less fallback)

Use this when the `replicate` Python SDK isn't available. The API is straightforward and everything below works with plain `curl` + `jq`.

## Authentication

All endpoints require:

```
Authorization: Bearer $REPLICATE_API_TOKEN
```

Base URL: `https://api.replicate.com/v1`

## Create a prediction (synchronous-ish)

```bash
curl -s -X POST https://api.replicate.com/v1/predictions \
    -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Prefer: wait" \
    -d '{
      "model": "bytedance/seedance-2.0",
      "input": {
        "prompt": "a sea turtle over a coral reef",
        "duration": 5
      }
    }'
```

- `model` accepts `owner/name` (latest version) or `owner/name:version_id` for a pinned version. You can also use `"version": "<version_id>"` at the top level.
- `Prefer: wait` blocks up to 60s waiting for completion. If the job isn't done in 60s, you get back the current state and should poll.
- Response body has `id`, `status`, `input`, `output` (null until done), `error`, `logs`, and `urls.get` / `urls.cancel`.

## Poll a prediction

```bash
curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
    https://api.replicate.com/v1/predictions/$ID
```

Loop until `status` is terminal:

```bash
while :; do
    resp=$(curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
        https://api.replicate.com/v1/predictions/$ID)
    status=$(echo "$resp" | jq -r '.status')
    case "$status" in
        succeeded|failed|canceled) echo "$resp"; break ;;
    esac
    sleep 3
done
```

Status values:

- `starting` — worker booting (cold start)
- `processing` — model running
- `succeeded` — done; `output` is populated
- `failed` — `error` field populated
- `canceled` — stopped by creator

## Download output files

`output` contains URLs, or a list/dict of URLs. Example for a video model:

```bash
url=$(echo "$resp" | jq -r '.output')   # or '.output[0]' if a list
curl -L -o out.mp4 "$url"
```

Most output URLs on `replicate.delivery` are pre-signed and don't require auth, but if you hit 401 add the `Authorization` header. **Files expire ~1 hour after creation — download immediately.**

## File inputs

Three ways to pass a file as an input value:

1. **HTTPS URL** — just pass the URL string. Preferred for anything already in the cloud.
2. **Data URL** — `"data:<mime>;base64,<payload>"` — only for files ≤256KB.
3. **Upload via files API**, then pass the returned URL:

```bash
curl -X POST https://api.replicate.com/v1/files \
    -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
    -F "content=@/path/to/photo.png"
# => response.urls.get is the URL to pass as input
```

## Cancel a running prediction

```bash
curl -X POST -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
    https://api.replicate.com/v1/predictions/$ID/cancel
```

## Webhooks (async without polling)

Add `"webhook": "https://yourapp.com/hook"` and optionally `"webhook_events_filter": ["completed"]` to the create request. Replicate POSTs the final prediction object to your URL.

## List predictions

```bash
curl -s -H "Authorization: Bearer $REPLICATE_API_TOKEN" \
    'https://api.replicate.com/v1/predictions?page_size=20'
```

Paginated, 100 per page max.

## Common errors

- `401` — missing/bad token.
- `402` — billing not set up.
- `422` — input schema validation failed; check field names and ranges.
- `429` — rate limited; back off.
- `403` / Cloudflare error `1010` — **your User-Agent was blocked.** `api.replicate.com` sits behind Cloudflare, which drops requests from default Python `urllib`/`urllib.request` UAs (and sometimes default `requests` UAs on older versions). Always set a UA header on side-channel schema probes or raw HTTP calls: `-H "User-Agent: my-tool/1.0"` in curl, or `headers={"User-Agent": "my-tool/1.0"}` in Python. The `replicate` SDK and browsers are fine — this only bites raw HTTP clients.

## Bare slug vs pinned version

- `POST /v1/predictions` with `"model": "owner/name"` resolves to the model's **latest official version** — works for most first-party and actively-maintained community models.
- Some older community uploads have no "latest version" alias and will **404 on the bare slug**. Known case: `andreasjansson/illusion` (pin a version hash like `:75d51a73...`). When the bare slug 404s, grab the current version id from the model page's API tab and pass either `"model": "owner/name:<id>"` or `"version": "<id>"`.
