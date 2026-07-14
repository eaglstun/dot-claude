#!/usr/bin/env bash
# Create a Runpod Serverless *template* for a deployed Ollama image, then print
# the exact console steps to stand up a Load-Balancer endpoint from it.
#
# Why template-only: Runpod's REST API can create the template but CANNOT create
# a load-balancing endpoint (console UI / Flash SDK only), and Ollama's native
# HTTP API (/api/chat, /api/generate) needs a load-balancing endpoint. So this
# script automates the verified part (template create) and hands you precise
# manual steps for the rest. See references/api.md for the underlying API.
#
# Usage:
#   RUNPOD_API_KEY=... DOCKER_USER=your-dockerhub-user ./scripts/runpod-wire.sh [model-name] [image-tag-version]
#   # or pass a full image ref and skip DOCKER_USER:
#   RUNPOD_API_KEY=... IMAGE=myuser/mote-14b-q3-ft-runpod:v1 ./scripts/runpod-wire.sh
#
# Defaults:
#   model-name        = mote-14b-q3-ft
#   image-tag-version = v1   (matches runpod-deploy.sh naming: <user>/<model>-runpod:<tag>)
#
# Env overrides: TEMPLATE_NAME, CONTAINER_DISK_GB (default 30), GPU_TYPE (default "NVIDIA A40").
#
# Requirements: curl, jq, and a Runpod API key (console.runpod.io -> Settings -> API Keys).

set -euo pipefail

MODEL_NAME="${1:-mote-14b-q3-ft}"
TAG_VERSION="${2:-v1}"
RUNPOD_API_KEY="${RUNPOD_API_KEY:?Set RUNPOD_API_KEY=<your-runpod-api-key>}"

# Resolve the image: explicit IMAGE wins, else build from DOCKER_USER + deploy naming.
if [ -n "${IMAGE:-}" ]; then
  IMAGE_TAG="$IMAGE"
else
  DOCKER_USER="${DOCKER_USER:?Set DOCKER_USER=<dockerhub-user> or IMAGE=<full-image-ref>}"
  IMAGE_TAG="${DOCKER_USER}/${MODEL_NAME}-runpod:${TAG_VERSION}"
fi

command -v curl >/dev/null || { echo "curl not found in PATH" >&2; exit 1; }
command -v jq   >/dev/null || { echo "jq not found in PATH" >&2; exit 1; }

API="https://rest.runpod.io/v1"
TEMPLATE_NAME="${TEMPLATE_NAME:-${MODEL_NAME}-${TAG_VERSION}-ollama}"
CONTAINER_DISK_GB="${CONTAINER_DISK_GB:-30}"
GPU_TYPE="${GPU_TYPE:-NVIDIA A40}"

echo "[1/2] Creating serverless template '${TEMPLATE_NAME}' for image ${IMAGE_TAG}..."

REQ="$(jq -n \
  --arg name  "$TEMPLATE_NAME" \
  --arg image "$IMAGE_TAG" \
  --argjson disk "$CONTAINER_DISK_GB" \
  '{name:$name, imageName:$image, isServerless:true, containerDiskInGb:$disk,
    ports:["11434/http"], env:{OLLAMA_HOST:"0.0.0.0:11434"}}')"

RESP="$(curl -sS -X POST "$API/templates" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$REQ")"

TEMPLATE_ID="$(printf '%s' "$RESP" | jq -r '.id // empty')"

if [ -z "$TEMPLATE_ID" ]; then
  echo "Template create failed. Response:" >&2
  printf '%s\n' "$RESP" | jq . >&2 2>/dev/null || printf '%s\n' "$RESP" >&2
  exit 1
fi

echo "  template id: ${TEMPLATE_ID}"

cat <<DONE

================================================================================
 TEMPLATE CREATED

   name:      ${TEMPLATE_NAME}
   id:        ${TEMPLATE_ID}
   image:     ${IMAGE_TAG}
   port:      11434/http

 Now create the endpoint in the console (REST cannot create a Load Balancer
 endpoint, which Ollama's native HTTP API requires):

   1. https://console.runpod.io/serverless  ->  New Endpoint
   2. Endpoint Type:  Load Balancer
   3. Template:       ${TEMPLATE_NAME}   (id ${TEMPLATE_ID})
   4. GPU:            ${GPU_TYPE}
   5. Container disk: ${CONTAINER_DISK_GB} GB
   6. Idle timeout:   60s   ·   Min workers: 0   ·   Max workers: 1

 HEALTH CHECK: Load Balancer endpoints require a /ping route returning 200.
 Images built by runpod-deploy.sh now bundle an nginx proxy that serves /ping on
 \$PORT and forwards the API to Ollama, so health checks pass out of the box. A
 hand-built image running bare 'ollama serve' (no /ping) would report unhealthy.

 Once the endpoint is live, Ollama's API is reachable at:

   https://<ENDPOINT_ID>.api.runpod.ai/api/chat        (and /api/generate, /api/tags)

   curl https://<ENDPOINT_ID>.api.runpod.ai/api/chat \\
     -H "Authorization: Bearer \$RUNPOD_API_KEY" \\
     -d '{"model":"${MODEL_NAME}","messages":[{"role":"user","content":"hi"}]}'

 Paste that endpoint URL into the next chat with Claude to wire it into openclaw
 as a provider (see the openclaw-api skill).
================================================================================
DONE
