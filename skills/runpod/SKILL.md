---
name: runpod
version: 1.0.0
description: >-
  Deploy local Ollama models to Runpod Serverless — either baking the GGUF into a Docker
  image or syncing models to a Runpod network volume via S3. Use when the user wants to
  host a fine-tuned Ollama model on Runpod, push a new model version, or sync local models
  to their Runpod volume.
public: true
semantic_id: "fhEOmjOzEM5DsMIabTvKS2Mq7GYnAAAF"
related_ids:
  - "TgKiPAXXGEUvsUJtdVnAAXfw9aklMAAH"
  - "WZyQmXE6omebBLj6dj7fwmcCZWKvwAAC"
topic_id: "v2:DFBB"
topic_path: "model-runners/inference-runtimes"
---

# Runpod

Two scripts in `scripts/` for getting local Ollama models onto Runpod Serverless. Pick the one that matches the path you're on.

For driving Runpod's REST/invocation API directly (create or scale an endpoint, call it, manage network volumes — instead of clicking through the console), see **`references/api.md`**.

## Pick the deploy path

| Path                       | Script                          | When to use                                                                               |
| -------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------- |
| **Bake model into image**  | `scripts/runpod-deploy.sh`      | One-off model, no Runpod volume yet, OK with ~15GB image + 1–3min cold start              |
| **Sync to network volume** | `scripts/runpod-volume-sync.sh` | Multiple models / iterating frequently — volume is shared, image stays slim, faster boots |

The two are complementary, not mutually exclusive — you can bake one model into an image for a first deploy and use the volume for everything after.

## Path 1 — bake into image (`runpod-deploy.sh`)

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

## Path 2 — sync to network volume (`runpod-volume-sync.sh`)

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

## When NOT to use this

If the model is a stock public model (vanilla Llama, Qwen, etc.), don't deploy your own — use a hosted serverless provider (Together, Groq, Replicate). These scripts only pay off for fine-tunes or quantizations you control.
