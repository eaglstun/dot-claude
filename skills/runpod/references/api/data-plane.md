# Data plane — call a queue-based endpoint

Part of the [Runpod API reference](README.md).

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

**Gotcha:** `/runsync` doesn't always block until completion — it has an internal wait cap. On a slow cold start (verified 2026-07-29 against a stuck endpoint, see the Qwen3 32B AWQ entry in [`public-endpoints.md`](public-endpoints.md)) it can return with `{"status":"IN_QUEUE"}` immediately instead of the final result. Always be ready to fall back to polling `/status/{id}` even when you called `/runsync`.

`zsh` gotcha when scripting a poll loop: don't name a variable `status` — it's a read-only special variable in zsh and assignment silently fails the whole script (`read-only variable: status`). Use `jstatus` or similar.

## Sources

docs.runpod.io: `/serverless/endpoints/send-requests`, `/serverless/endpoints/operation-reference`.
