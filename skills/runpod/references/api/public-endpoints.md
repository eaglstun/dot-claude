# Public Endpoints — Runpod's own hosted models (no deploy needed)

Part of the [Runpod API reference](README.md). Per-model request/response schemas live in [`models/`](models/README.md) — this file is just the catalog and the shared call pattern.

For stock/public models, skip templates and endpoints entirely — Runpod hosts a catalog of pay-per-call models at fixed slugs. Same auth (`Authorization: Bearer $RUNPOD_API_KEY`), same call shape as a normal data-plane request:

```
POST https://api.runpod.ai/v2/{model-id}/runsync   # or /run to poll instead
```

Catalog as of 2026-07-29 (source: `docs.runpod.io/public-endpoints/reference` — re-check before relying on exact pricing/ids, this list changes):

| Category   | Models                                                                                                                                                                                          |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Text (3)   | IBM Granite 4.0 ($10/1M tok), Moonshot Kimi ($0.95–$3/1M in, $4–$15/1M out depending on version), Qwen3 32B AWQ ($10/1M tok, OpenAI-compatible — **⚠️ stuck IN_QUEUE on live test, see below**) |
| Image (17) | Flux Dev/Schnell/Kontext Dev, P-Image T2I/Edit, Qwen Image (+ LoRA/Edit variants), Seedream 4.0 T2I/Edit, WAN 2.6 T2I, Z-Image Turbo, Nano Banana/Pro/2 Edit — $0.0024–$0.24/image              |
| Video (16) | InfiniteTalk, Kling v2.1/v2.6, Seedance 1.5 Pro, SORA 2 (+Pro), WAN 2.1–2.6, Vidu Q3, Pruna Video — $0.02–$2.25 per clip/second                                                                 |
| Audio (2)  | Chatterbox Turbo ($0.001/s), Minimax Speech 02 HD ($0.05/1K chars)                                                                                                                              |

## Per-model docs

10 of the ~38 catalog models have a dedicated reference file so far — see **[`models/README.md`](models/README.md)** for the index (which are live-verified vs docs-only, and why the doc pages shouldn't be trusted blindly: Flux Schnell and Qwen3 32B AWQ both turned out wrong or broken when actually tested).

## Sources

docs.runpod.io: `/public-endpoints/overview`, `/public-endpoints/reference`.
