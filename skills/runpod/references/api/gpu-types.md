# GPU type IDs

Part of the [Runpod API reference](README.md).

Referenced by full string in `gpuTypeIds`. Confirmed: `"NVIDIA A40"`, `"NVIDIA A100 80GB PCIe"`, `"NVIDIA A100-SXM4-80GB"`, `"NVIDIA L40S"`, `"NVIDIA H100 80GB HBM3"`, `"NVIDIA RTX A6000"`, `"NVIDIA GeForce RTX 4090"`, `"NVIDIA L4"`. The console GPU-types page lists the rest; there is no clearly documented **v1** REST `GET /v1/gputypes` route (confirmed: `GET /v1/gputypes` 400s with "path does not exist in the specification") — use the strings directly.

**Better sources than a web search — both confirmed live 2026-07-30, prices matched exactly between them:**

- `runpodctl gpu list` (see `../../runpodctl.md`) — exact `gpuId` string, live Pod pricing, per-datacenter stock status.
- `GET https://api.runpod.io/v2/catalog/gpus` (**API v2**, see `../../api-v2.md`) — the REST route that didn't exist in v1. Same `id`/pricing as `runpodctl gpu list`, plus the `pool` ID (e.g. `"AMPERE_24"` for `NVIDIA L4`) needed to address that GPU on a **serverless** endpoint via v2 — v1's `gpuTypeIds` array of plain name strings has no pool concept at all. Full query-param/response-schema breakdown, including per-datacenter availability, now in `../../api-v2.md`'s "GPU catalog" section — don't re-derive it here.

Verified 2026-07-30: `NVIDIA RTX A4000` ($0.17/$0.25 community/secure) and `NVIDIA RTX A6000` ($0.33/$0.53) undercut `NVIDIA L4` ($0.39 secure only) as Pods — that changes the "L4 is cheapest" claim below, which was web-search-sourced and never confirmed against a live account.

Original (2026-07-29, **superseded by the `runpodctl gpu list` numbers above** — kept for the general point, not the specific ranking) claim per web search: `"NVIDIA L4"` (~$0.69/hr) < `"NVIDIA RTX A6000"`/`"NVIDIA GeForce RTX 4090"` (~$1.10/hr serverless — note serverless pricing runs above the on-demand Pod rate for the same card, e.g. 4090 is ~$0.34–0.69/hr as a Pod). Billing is per-second while a worker is active, so with `workersMin:0` and a short `idleTimeout` the GPU choice barely matters for a smoke test either way — but for anything longer-running, check `runpodctl gpu list` rather than trusting either number here.

## Sources

docs.runpod.io: `/references/gpu-types`. GPU pricing table cross-checked live via `runpodctl gpu list` 2026-07-30 (see `../../runpodctl.md`) — prefer that over the 2026-07-29 web-search figures in this file.
