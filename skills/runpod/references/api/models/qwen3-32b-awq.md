# Qwen3 32B AWQ

Part of the [Public Endpoint models index](README.md).

`model-id`: `qwen3-32b-awq` — **⚠️ could not verify live as of 2026-07-29.** Two separate jobs (one via `/runsync`, one via `/run`) both sat at `IN_QUEUE` for 2.5–6+ minutes straight and never progressed to `IN_PROGRESS`/`COMPLETED`; both had to be cancelled manually via `/cancel/{id}`. `GET /v2/qwen3-32b-awq/health` also returned `401 {"detail":"unauthorized access to endpoint"}` with the same key that works fine against every other endpoint (own serverless endpoints and the other public ones). Documented schema below is from `docs.runpod.io/public-endpoints/models/qwen3-32b` only — **treat as unverified, re-test before relying on it**:

```json
// request
{"input": {"prompt": "Write a Python function...", "max_tokens": 512, "temperature": 0.7}}
// documented response (NOT independently confirmed)
{"output":[{"choices":[{"tokens":["..."]}],"cost":0.0001,"usage":{"input":10,"output":100}}],"status":"COMPLETED"}
```

Docs also claim an OpenAI-compatible variant at `https://api.runpod.ai/v2/qwen3-32b-awq/openai/v1` — also unverified given the base endpoint wouldn't complete a job.

Pricing per docs: $10.00/1M tokens.

## Sources

docs.runpod.io/public-endpoints/models/qwen3-32b. Live test attempted 2026-07-29 and failed (see above) — re-test before trusting this endpoint for anything.
