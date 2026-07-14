#!/usr/bin/env bash
# Run a deployed Ollama image as an on-demand Runpod GPU **Pod** and print the
# proxy URL that speaks Ollama's native HTTP API. Unlike serverless, a pod runs
# the plain image as-is (no queue handler, no LB /ping needed) and exposes port
# 11434 directly at https://<pod-id>-11434.proxy.runpod.net. See references/api.md.
#
# Usage:
#   RUNPOD_API_KEY=... DOCKER_USER=your-dockerhub-user ./scripts/runpod-pod.sh [model-name] [image-tag-version]
#   # or pass a full image ref and skip DOCKER_USER:
#   RUNPOD_API_KEY=... IMAGE=myuser/mote-14b-q3-ft-runpod:v1 ./scripts/runpod-pod.sh
#
# Defaults:
#   model-name        = mote-14b-q3-ft
#   image-tag-version = v1   (matches runpod-deploy.sh naming: <user>/<model>-runpod:<tag>)
#
# Env overrides: POD_NAME, GPU_TYPE (default "NVIDIA A40"), GPU_COUNT (1),
#                CONTAINER_DISK_GB (30), CLOUD_TYPE (SECURE|COMMUNITY, default SECURE).
#
# Requirements: curl, jq, and a Runpod API key (console.runpod.io -> Settings -> API Keys).

set -euo pipefail

MODEL_NAME="${1:-mote-14b-q3-ft}"
TAG_VERSION="${2:-v1}"
RUNPOD_API_KEY="${RUNPOD_API_KEY:?Set RUNPOD_API_KEY=<your-runpod-api-key>}"

if [ -n "${IMAGE:-}" ]; then
  IMAGE_TAG="$IMAGE"
else
  DOCKER_USER="${DOCKER_USER:?Set DOCKER_USER=<dockerhub-user> or IMAGE=<full-image-ref>}"
  IMAGE_TAG="${DOCKER_USER}/${MODEL_NAME}-runpod:${TAG_VERSION}"
fi

command -v curl >/dev/null || { echo "curl not found in PATH" >&2; exit 1; }
command -v jq   >/dev/null || { echo "jq not found in PATH" >&2; exit 1; }

API="https://rest.runpod.io/v1"
POD_NAME="${POD_NAME:-${MODEL_NAME}-${TAG_VERSION}}"
GPU_TYPE="${GPU_TYPE:-NVIDIA A40}"
GPU_COUNT="${GPU_COUNT:-1}"
CONTAINER_DISK_GB="${CONTAINER_DISK_GB:-30}"
CLOUD_TYPE="${CLOUD_TYPE:-SECURE}"

echo "[1/2] Creating ${CLOUD_TYPE} GPU pod '${POD_NAME}' (${GPU_COUNT}x ${GPU_TYPE}) from ${IMAGE_TAG}..."

REQ="$(jq -n \
  --arg name  "$POD_NAME" \
  --arg image "$IMAGE_TAG" \
  --arg gpu   "$GPU_TYPE" \
  --arg cloud "$CLOUD_TYPE" \
  --argjson gpus "$GPU_COUNT" \
  --argjson disk "$CONTAINER_DISK_GB" \
  '{name:$name, imageName:$image, gpuTypeIds:[$gpu], gpuCount:$gpus,
    cloudType:$cloud, interruptible:false, ports:["11434/http"],
    containerDiskInGb:$disk, env:{OLLAMA_HOST:"0.0.0.0:11434"}}')"

RESP="$(curl -sS -X POST "$API/pods" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$REQ")"

POD_ID="$(printf '%s' "$RESP" | jq -r '.id // empty')"

if [ -z "$POD_ID" ]; then
  echo "Pod create failed. Response:" >&2
  printf '%s\n' "$RESP" | jq . >&2 2>/dev/null || printf '%s\n' "$RESP" >&2
  exit 1
fi

PROXY="https://${POD_ID}-11434.proxy.runpod.net"

cat <<DONE

================================================================================
 POD CREATED

   name:   ${POD_NAME}
   id:     ${POD_ID}
   image:  ${IMAGE_TAG}

 Ollama API (HTTPS, once the pod is RUNNING and the model has loaded):

   ${PROXY}/api/tags
   ${PROXY}/api/chat

   curl ${PROXY}/api/chat \\
     -d '{"model":"${MODEL_NAME}","messages":[{"role":"user","content":"hi"}]}'

 !! SECURITY: the proxy URL is PUBLIC and UNAUTHENTICATED (the pod id is the only
    obscurity), and Ollama has no built-in auth. Anyone with the URL can use the
    model. Don't share it; stop the pod when idle. Add app-level auth if exposing.

 Manage:
   status:  curl -H "Authorization: Bearer \$RUNPOD_API_KEY" ${API}/pods/${POD_ID}
   stop:    curl -X POST -H "Authorization: Bearer \$RUNPOD_API_KEY" ${API}/pods/${POD_ID}/stop
   start:   curl -X POST -H "Authorization: Bearer \$RUNPOD_API_KEY" ${API}/pods/${POD_ID}/start
   delete:  curl -X DELETE -H "Authorization: Bearer \$RUNPOD_API_KEY" ${API}/pods/${POD_ID}

 Note: HTTPS only; Cloudflare caps each request at ~100s. Paste the proxy URL
 into the next chat with Claude to wire it into openclaw (see openclaw-api skill).
================================================================================
DONE
