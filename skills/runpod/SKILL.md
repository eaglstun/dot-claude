---
name: runpod
description: Deploy models to Runpod Serverless using cached Hugging Face models, Docker images, or network volumes; operate endpoints and track billing. Use when the user wants to host a fine-tuned model on Runpod, reduce cold starts, push a model version, or manage model storage and endpoint configuration.
metadata:
  version: 1.1.0
  public: 'true'
  semantic_id: fhEOmjOzEM5DsMIabTvKS2Mq7GYnAAAF
  related_ids: '["TgKiPAXXGEUvsUJtdVnAAXfw9aklMAAH","WZyQmXE6omebBLj6dj7fwmcCZWKvwAAC"]'
  topic_id: v2:DFBB
  topic_path: model-runners/inference-runtimes
---

# Runpod

This skill covers three ways to make model weights available to Runpod Serverless: Runpod's host-local cached models, weights baked into a Docker image, and a user-managed network volume. Pick the path before changing endpoint or image configuration; these mechanisms have different ownership, billing, and cold-start behavior.

For **Runpod cached models**, read **`references/cached-models.md`** before configuring the endpoint or worker. Cached models are not ordinary network-volume files even though both appear below `/runpod-volume/` inside the worker.

For driving Runpod's REST/invocation API directly (create or scale an endpoint, call it, manage network volumes — instead of clicking through the console), see **`references/api/`** (start at `references/api/README.md`). Prefer the official CLI over hand-rolled `curl` when it covers the task — see **`references/runpodctl.md`** (already installed and authenticated on this machine).

Runpod also has a second, newer **API v2** (beta, `https://api.runpod.io/v2` — a different base URL from both v1's `rest.runpod.io/v1` and the data-plane's `api.runpod.ai`) — see **`references/api-v2.md`**. Notably, it can create **load-balancing endpoints via REST**, which v1 cannot (v1 needs a manual console step — see `api/ollama-lb.md`). Worth checking before assuming the v1 limitation still applies.

Runpod also hosts a catalog of ready-to-call **Public Endpoints** (Kimi K3, Qwen3, Flux, WAN, etc.) — no deploy, no GPU rental, pay per call. See `references/api/public-endpoints.md` before reaching for the scripts below if the model is a stock/public one.

**Reading spend: use `runpodctl billing serverless`, and nothing else.** Verified 2026-08-05 by getting it wrong two different ways first. It is the only authoritative source — per endpoint, per day, with dollars _and_ billed milliseconds, which together give the true active rate:

```bash
runpodctl billing serverless        # [{amount, timeBilledMs, endpointId, time}, …]
```

Worked example from that day: one endpoint billed **$0.3706 across 33.7 minutes** (`$0.66/hr` while active), another **$0.83 across 43 min** (`$1.16/hr`, pricier tier), whole account **$1.50 for the day**. The hourly rate applies only to minutes a worker is actually up — which is the entire point of scale-to-zero, and the reason an hourly figure alone tells you nothing.

Three things that look like evidence and are not:

- **Worker counts overlap.** `/v2/<id>/health` returns `{idle, initializing, ready, running, throttled, unhealthy}` and counts one machine in several buckets. Summing them is meaningless: two endpoints reported `idle:1, ready:1, running:1` and `idle:1, ready:1` — an apparent **five workers against a hard ceiling of three** (`workersMax` 2 and 1) when the truth was one. `workersMax` is the ceiling and RunPod enforces it.
- **Balance deltas are lumpy — short samples are worthless.** Settlement is batched, not continuous. The _same_ 90-second `clientBalance` diff gave `$0.00/hr` on one attempt and `$2.29/hr` on the next, neither being the real rate. That method produced a false all-clear and a false alarm within ten minutes. Do not use it.
- **`currentSpendPerHr` is roughly the right RATE while workers are active** (`0.69` vs a billing-derived `0.66`), but it lingers after they stop and says nothing about the day's total. It is not "what I am spending now."

**Never raise a cost alarm off the health endpoint, the spend field, or a short balance diff.** Pull the billing history first.

**Pick `idleTimeout` for the traffic shape, not for tidiness.** 60s minimises idle spend and suits a trickle. 300s suits a spike: everyone arriving inside the window skips a 1–3 minute cold start, and cold starts are what make a public demo look broken in front of an audience.

**Clean up test endpoints when done — don't trust `workersMin:0` to actually keep costing $0.** Verified 2026-07-29: a serverless endpoint that showed `/health` → 0 workers immediately after a test job still had **1 worker sitting `idle`/`ready`** ~40 minutes later with no new requests and `workersMin` still `0`. Scale-to-zero is not something to leave unattended and assume — after any exploratory test, either `DELETE /v1/endpoints/{id}` (and the template, `DELETE /v1/templates/{id}`, if nothing else needs it) or re-check `/health` right before walking away. Details in `references/api/control-plane.md`.

## Pick the deploy path

| Path                       | Tool / configuration            | When to use                                                                                              |
| -------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Runpod cached model**    | Endpoint **Model** field        | Model is on Hugging Face; smallest image and fastest weight availability; one cached model per endpoint  |
| **Bake model into image**  | `scripts/runpod-deploy.sh`      | Private/local-only or tightly coupled artifact; OK with ~15GB image and slower image pulls               |
| **Sync to network volume** | `scripts/runpod-volume-sync.sh` | Multiple models or frequent iteration under your own storage layout; shared volume but slower than cache |

The paths are complementary, not mutually exclusive. Keep application code in the image while Runpod supplies a cached Hugging Face model, or bake one model first and use a volume for later iterations.

For repeated LoRA rounds over a shared Ollama base, read **`references/adapter-only-ollama.md`** before uploading a newly fused multi-gigabyte model. It covers cloud-side base pulls, MLX-LM conversion, small manifest/blob syncs, and the behavioral equivalence check required when the serving base uses a different quantization.

## Path 1 — Runpod cached model

Runpod can place a public, gated, or private Hugging Face repository into a host-local cache before starting a worker. Configure the repository identifier in the endpoint's **Model** field; Hugging Face deployments configure this automatically. Official Runpod workers such as vLLM generally consume the field or `MODEL_NAME` directly. A custom worker must resolve and load the mounted snapshot itself.

For this skill's Ollama images, cached-model support is **not automatic**: Ollama does not consume a Hugging Face cache directory merely because `MODEL_NAME` is set. The entrypoint must resolve the snapshot, find the intended GGUF and Modelfile, and import or serve them without downloading. Read `references/cached-models.md` for the mount layout, offline-mode guidance, limitations, and source links.

## Path 2 — bake into image (`runpod-deploy.sh`)

Builds a Docker image with the GGUF blob and Modelfile already imported (multi-stage to avoid ~15 GB of layer bloat) and pushes to Docker Hub.

```bash
DOCKER_USER=<your-dockerhub-user> ./scripts/runpod-deploy.sh [model-name] [tag-version]
# defaults: model-name = mote-14b-q3-ft, tag = v1
```

**Prerequisites:** `ollama` + `docker` on PATH; the named model exists locally (`ollama list | grep <name>`); `docker login` already done.

**Output:** image at `${DOCKER_USER}/${MODEL_NAME}-runpod:${TAG_VERSION}`.

**Recommended Runpod endpoint config** (printed by the script on success):

- GPU: A40 (48GB)
- Container disk: 30GB
- Idle timeout: 60s · Min workers: 0 · Max workers: 1
- HTTP port: 11434

## Path 3 — sync to network volume (`runpod-volume-sync.sh`)

Mirrors selected models from `~/.ollama/models` to the Runpod S3-compatible bucket backing your network volume. Selective mode walks each manifest and uploads only its referenced blobs (skips the unrelated 100+ GB on disk).

```bash
./scripts/runpod-volume-sync.sh                                    # full mirror (~116 GB — confirms first)
./scripts/runpod-volume-sync.sh mote-14b-q3-ft                     # one model
./scripts/runpod-volume-sync.sh mote-14b-q3-ft margot-1.7b-q8-ft   # several
```

**Prerequisites:** `awscli` + `jq` installed; AWS profile `runpod` configured (`aws configure --profile runpod`) with Runpod's S3 credentials; the destination volume already exists in the matching datacenter.

**Env overrides:**

| Var        | Default                           | Meaning                                |
| ---------- | --------------------------------- | -------------------------------------- |
| `PROFILE`  | `runpod`                          | aws cli profile                        |
| `ENDPOINT` | `https://s3api-us-il-1.runpod.io` | Runpod S3 endpoint (datacenter-scoped) |
| `BUCKET`   | `smq48f3agd`                      | Bucket id for the network volume       |

Verify after upload:

```bash
aws s3 --profile runpod --endpoint-url https://s3api-us-il-1.runpod.io \
  ls s3://smq48f3agd/models/manifests/registry.ollama.ai/library/
```

## Serve the deployed image — pod vs serverless

The image from `runpod-deploy.sh` runs `ollama serve` on 11434 plus an nginx `/ping` proxy (`scripts/lb-entrypoint.sh`), so it works either way:

| Path           | Script                                 | Gives you                                                                                                                                      | Trade-off                                                                      |
| -------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **GPU Pod**    | `scripts/runpod-pod.sh [model] [tag]`  | Creates the pod via REST and prints `https://<pod-id>-11434.proxy.runpod.net/api/chat`                                                         | Always-on billing; proxy URL is **public + unauthenticated** (script warns)    |
| **Serverless** | `scripts/runpod-wire.sh [model] [tag]` | Creates the serverless **template** via REST, then prints console steps for the load-balancer endpoint + `https://<id>.api.runpod.ai/api/chat` | Scale-to-zero, but REST can't create the LB endpoint (one manual console step) |

`runpod-pod.sh` is the fully-scripted path; `runpod-wire.sh` stops at the template because Runpod's REST API cannot create a load-balancing endpoint (console / Flash SDK only). Either way, once the URL is live paste it into the next chat so Claude can wire it into openclaw as a provider (done by hand against the openclaw config — see the openclaw-api skill).

## When NOT to deploy weights yourself

If a compatible stock model already exists in Runpod's **Public Endpoints** catalog, check `references/api/public-endpoints.md` before creating an endpoint. Use cached models when a Hugging Face-hosted model needs your own worker or endpoint configuration. The bake and volume scripts mainly pay off for private/local artifacts, custom quantizations, or storage layouts you control.
