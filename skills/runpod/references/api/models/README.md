# Public Endpoint models — index

Part of the [Runpod API reference](../README.md). Overview of the catalog and the common call pattern lives in [`../public-endpoints.md`](../public-endpoints.md); this folder has one file per model with its exact request/response schema.

| Model                                 | File                                         | Category | Verified live?                         |
| ------------------------------------- | -------------------------------------------- | -------- | -------------------------------------- |
| Moonshot Kimi (K2.6 / K2.7-Code / K3) | [`kimi.md`](kimi.md)                         | Text     | ✅ 2026-07-29                          |
| Flux Schnell                          | [`flux-schnell.md`](flux-schnell.md)         | Image    | ✅ 2026-07-29                          |
| Chatterbox Turbo                      | [`chatterbox-turbo.md`](chatterbox-turbo.md) | Audio    | ✅ 2026-07-29                          |
| Qwen3 32B AWQ                         | [`qwen3-32b-awq.md`](qwen3-32b-awq.md)       | Text     | ⚠️ broken — stuck `IN_QUEUE`, see file |
| IBM Granite 4.0                       | [`granite-4.md`](granite-4.md)               | Text     | ❌ docs only                           |
| Flux Dev                              | [`flux-dev.md`](flux-dev.md)                 | Image    | ❌ docs only                           |
| Qwen Image (T2I)                      | [`qwen-image.md`](qwen-image.md)             | Image    | ❌ docs only                           |
| Kling v2.1 I2V Pro                    | [`kling-v2-1.md`](kling-v2-1.md)             | Video    | ❌ docs only                           |
| SORA 2 I2V                            | [`sora-2.md`](sora-2.md)                     | Video    | ❌ docs only                           |
| Minimax Speech 02 HD                  | [`minimax-speech.md`](minimax-speech.md)     | Audio    | ❌ docs only                           |

"Docs only" means the schema below came from `docs.runpod.io/public-endpoints/models/*` and has not been called — Flux Schnell and Qwen3 32B AWQ both turned out to have real discrepancies (wrong response field, wrong price, or outright non-functional) vs their doc pages, so treat any "docs only" entry as a starting point, not ground truth. Re-verify before depending on one, especially the response shape and exact price.

This is 10 of the ~38 models in the full catalog (see the summary table in [`../public-endpoints.md`](../public-endpoints.md) for the rest) — the ones covered here were picked for spread across categories, not because they're the only ones worth using.
