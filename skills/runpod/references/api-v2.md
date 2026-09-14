# Runpod API v2 (beta)

A second, newer control-plane REST API — coexists with the v1 API in `references/api/`, does not replace it (both were live and returning consistent account state when checked 2026-07-30). **Currently in beta per Runpod's own docs — behavior may still change.**

**Domain gotcha:** there are now three different Runpod base URLs in play, easy to confuse:

| API                                    | Base URL                                 | Domain                                  |
| -------------------------------------- | ---------------------------------------- | --------------------------------------- |
| v1 control plane                       | `https://rest.runpod.io/v1`              | `rest.runpod.io`                        |
| **v2 control plane (this file)**       | `https://api.runpod.io/v2`               | `api.runpod.io`                         |
| Data plane (job invocation, unchanged) | `https://api.runpod.ai/v2/{endpoint_id}` | `api.runpod.ai` — note **.ai**, not .io |

Same Bearer key works across all three (confirmed live 2026-07-30). OpenAPI spec: `https://api.runpod.io/v2/openapi.json` — pulled directly and inspected for this file rather than trusting the doc pages' prose, since Runpod's own model doc pages have already been caught wrong twice this session (see `api/models/flux-schnell.md`, `api/models/qwen3-32b-awq.md`).

## What's actually different from v1

- **Responses are wrapped, not bare arrays.** `GET /v2/pods` → `{"pods": [...]}`, not v1's bare `[...]`. Applies across the board (`{"gpus": [...]}`, etc.) — don't reuse v1 parsing code unchanged.
- **`isServerless` → `serverless`, and it's finally documented.** `POST /v2/templates` takes `"serverless": boolean` (default `false`) right there in the OpenAPI schema — the same real distinction as v1's undocumented `isServerless` (see `api/control-plane.md`), just no longer a gotcha you have to discover by trial and error.
- **Serverless endpoints can embed the image directly — no template required.** `POST /v2/serverless` takes `image`, `env`, `ports`, `disk`, etc. straight on the request body (shared `ContainerConfig`, also used by pods and templates). Templates still exist for reuse/Hub sharing, but they're no longer a mandatory intermediate step the way v1 requires `templateId`.
- **⭐ Load-balancing endpoints can now be created via REST.** This is the big one: v1's `api/ollama-lb.md` and `scripts/runpod-wire.sh` both note that Runpod's v1 REST API cannot create a load-balancing endpoint — console or Flash SDK only, hence `runpod-wire.sh` stopping at the template and handing off manual steps. **v2 removes that gap:** `POST /v2/serverless` takes a required `"type": "QUEUE" | "LOAD_BALANCER"` field. Not yet tested end-to-end against the Ollama LB use case in this skill, but if it holds up, `runpod-wire.sh` could go fully scripted. Worth a follow-up test before rewriting that script.
  - `LOAD_BALANCER` type requires the `REQUEST_COUNT` scaler (`QUEUE_DELAY` is queue-only) — enforced in the schema (`oneOf` discriminated union on `scaling.type`).
- **GPUs addressed by name for pods, by pool for serverless.** `GET /v2/catalog/gpus` returns entries with both a plain `id` (e.g. `"NVIDIA L4"`, same string as v1's `gpuTypeIds` and `runpodctl gpu list`'s `gpuId`) **and** a `pool` (e.g. `"AMPERE_24"`, or `null` if not poolable). Pods (`CreatePodRequest.gpu.id`) use the plain `id` string, same as v1. Serverless (`CreateEndpointRequest.gpu.pools`) uses an **array of pool IDs**, not the plain name — a real structural difference, not just a rename. Multiple GPU models can share one pool (e.g. `NVIDIA A40` and `NVIDIA RTX A6000` are both `AMPERE_48`).
- **CPU pods and AMD GPUs are first-class**, not an afterthought — `TemplateCategory` enum is `CPU | NVIDIA | AMD`, and `CreatePodRequest` requires exactly one of `gpu`/`cpu`.
- **Per-resource billing endpoints** (`GET /v2/billing/{pods,serverless,endpoints,clusters,networkvolumes}`) — nothing equivalent documented in v1's `references/api/`.
- **Registry management is a real resource**, not just a template field — `GET/POST /v2/registries` (+ `/registries/delegations`) for container-registry credentials, matching `runpodctl registry`.

## Resources (29 paths total, from the OpenAPI spec)

```
GET/POST   /v2/pods                              GET/PATCH/DELETE /v2/pods/{id}
POST       /v2/pods/{id}/action                   GET              /v2/pods/{id}/logs
GET/POST   /v2/serverless                         GET/PATCH/DELETE /v2/serverless/{id}
GET        /v2/serverless/{id}/releases           GET              /v2/serverless/{id}/workers
GET        /v2/serverless/{id}/workers/{workerId}/logs
GET/POST   /v2/templates                          GET/PATCH/DELETE /v2/templates/{id}
GET/POST   /v2/network-volumes                    GET/PATCH/DELETE /v2/network-volumes/{id}
GET/POST   /v2/registries                         GET/DELETE       /v2/registries/{id}
GET/POST   /v2/registries/delegations             DELETE           /v2/registries/delegations/{id}
GET        /v2/catalog/{cpus,gpus,datacenters}[/{id}]
GET        /v2/billing[/{pods,serverless,endpoints,clusters,networkvolumes}]
```

## GPU catalog (`GET /v2/catalog/gpus`)

The richest GPU listing across v1/v2/`runpodctl` — no v1 equivalent exists at all (see `api/gpu-types.md`). Confirmed live against this account 2026-07-30, including every query param below (not just read from docs — each was hit individually and the errors read verbatim off the wire).

**Query params** (all optional):

| Param            | Type    | Notes                                                                                                                                                                             |
| ---------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `include`        | array   | Only documented value: `AVAILABILITY`. Adds `availability` + `dataCenters` to every GPU object.                                                                                   |
| `product`        | array   | One or more of `POD`, `CLUSTER`, `SERVERLESS`. **Requires `include=AVAILABILITY`** — 422s otherwise with an enum-validation error, not the plain 400 the other gated params give. |
| `count`          | integer | GPU count to price for; default 1, min 1. **Requires `include=AVAILABILITY`.**                                                                                                    |
| `cloud`          | string  | `SECURE` (default) or `COMMUNITY`. **Requires `include=AVAILABILITY`.**                                                                                                           |
| `minCudaVersion` | string  | `"major"` or `"major.minor"`, e.g. `"12.1"`. **Requires `include=AVAILABILITY`.**                                                                                                 |

⚠️ **Correction to the doc page's wording:** docs.runpod.io only calls out `product` as gated behind `include=AVAILABILITY`. Live testing shows `cloud`, `count`, and `minCudaVersion` are _equally_ gated — each 400s on its own with `"<param> filters are valid only with include=AVAILABILITY"` if you pass it alone. In practice: always pass `include=AVAILABILITY` if you're using any other filter param.

**Response** — `{"gpus": [GpuType, ...]}`. Each `GpuType`:

```
id            string   e.g. "NVIDIA GeForce RTX 4090" — same string as v1 gpuTypeIds / runpodctl gpuId
name          string   short display name, e.g. "RTX 4090"
pool          string|null   serverless pool ID (e.g. "ADA_24"), or null if not poolable
manufacturer  enum     NVIDIA | AMD | UNKNOWN
memory        integer  VRAM in GB
secure        boolean  available on secure cloud
community     boolean  available on community cloud
price         object   {secure: float, community: float} $/hr
maxCount      object   {secure: int, community: int} — max GPUs of this type per pod/worker
availability  enum     NONE | LOW | MEDIUM | HIGH — only present with include=AVAILABILITY
dataCenters   array    only present with include=AVAILABILITY — [{id, name, availability}, ...] per datacenter
```

Confirmed live: base call (no `include`) returns the same 8 fields as always (`id`/`name`/`pool`/`manufacturer`/`memory`/`secure`/`community`/`price`/`maxCount`) — `availability`/`dataCenters` are additive, not a schema change. With `include=AVAILABILITY` and no `product` filter, every datacenter came back `"availability":"NONE"` for the GPU checked (`AMD Instinct MI300X OAM`) — that's a stock reading, not a broken query; a live-stock GPU (`NVIDIA GeForce RTX 4090` with `product=SERVERLESS`) also came back `"NONE"` at check time, so treat `NONE` as "no live line-item," not proof the query is misconfigured.

```bash
curl -H "Authorization: Bearer $RUNPOD_API_KEY" \
  "https://api.runpod.io/v2/catalog/gpus?include=AVAILABILITY&product=SERVERLESS&cloud=COMMUNITY&count=4&minCudaVersion=12.1"
```

Pool IDs seen for the GPUs this skill already references: `NVIDIA L4` → `AMPERE_24`, `NVIDIA A40` & `NVIDIA RTX A6000` → `AMPERE_48` (shared pool), `NVIDIA GeForce RTX 4090` → `ADA_24`, `NVIDIA RTX A4000` → `AMPERE_16`, `NVIDIA L40`/`L40S` → `ADA_48_PRO`.

Rate limiting (from response headers, confirmed present on every call): three windows tracked independently — minute (180/min), hour (7200/hr), day (86400/day) — via `RateLimit`/`RateLimit-Policy` response headers, e.g. `ratelimit: "minute";r=175;t=43, "hour";r=7195;t=1903, "day";r=86392;t=55903` (`r`=remaining, `t`=seconds till window reset). Not yet seen a 429 in practice — just noting the budget exists.

## Verified live (2026-07-30)

```bash
curl -H "Authorization: Bearer $RUNPOD_API_KEY" https://api.runpod.io/v2/pods
# -> {"pods":[]}   — wrapped, confirmed different from v1's bare `[]`
```

Cross-checked GPU catalog pricing against `runpodctl gpu list` (references/runpodctl.md) — prices matched exactly; community availability for a given GPU fluctuated between the two calls (stock changes live, not a bug).

## What's not yet verified

- Actually creating a template/endpoint/pod through v2 end-to-end (only read/catalog endpoints were exercised so far — no spend without asking first, same policy as the Public Endpoints model docs).
- Whether a `LOAD_BALANCER`-type endpoint created via v2 actually works for reaching Ollama's native HTTP API the way `api/ollama-lb.md` describes for the console-created version.
- Whether v1 and v2 objects are literally the same underlying rows (strong circumstantial evidence: both showed the same empty state on this account) versus something that merely looks that way.

## Sources

`https://api.runpod.io/v2/openapi.json` (fetched and parsed directly, 2026-07-30) — preferred over `docs.runpod.io/api-reference-v2/*` prose, which was thin and didn't cover the v1 differences at all. Exception: `docs.runpod.io/api-reference-v2/catalog/list-gpu-types` (pulled 2026-07-30) filled in the query-param semantics well — cross-checked live against this account and corrected in the GPU catalog section above where its wording undersold which params need `include=AVAILABILITY`. Live calls against `/v2/catalog/gpus` and `/v2/pods` on this account, 2026-07-30.
