#!/usr/bin/env bash
# Build + push an Ollama model to Docker Hub for Runpod Serverless deployment.
#
# Usage:
#   DOCKER_USER=your-dockerhub-user ./scripts/runpod-deploy.sh [model-name] [image-tag-version]
#
# Defaults:
#   model-name        = mote-14b-q3-ft
#   image-tag-version = v1
#
# Requirements (on the Mac running this script):
#   - ollama (the model must exist locally: `ollama list | grep <model>`)
#   - docker
#   - You must be logged into Docker Hub:  docker login

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODEL_NAME="${1:-mote-14b-q3-ft}"
TAG_VERSION="${2:-v1}"
DOCKER_USER="${DOCKER_USER:?Set DOCKER_USER=<your-dockerhub-username>}"
IMAGE_TAG="${DOCKER_USER}/${MODEL_NAME}-runpod:${TAG_VERSION}"

command -v ollama >/dev/null || { echo "ollama not found in PATH" >&2; exit 1; }
command -v docker >/dev/null || { echo "docker not found in PATH" >&2; exit 1; }

ollama list | awk '{print $1}' | grep -qE "^${MODEL_NAME}(:|$)" || {
  echo "Ollama model '${MODEL_NAME}' not found locally. Available:" >&2
  ollama list >&2
  exit 1
}

WORK_DIR="$(mktemp -d -t runpod-deploy-XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "[1/5] Resolving GGUF blob for ${MODEL_NAME}..."
MODELFILE_RAW="$(ollama show "$MODEL_NAME" --modelfile)"
BLOB_PATH="$(printf '%s\n' "$MODELFILE_RAW" | awk '/^FROM/ {print $2; exit}')"

if [ ! -f "$BLOB_PATH" ]; then
  echo "GGUF blob not found at: $BLOB_PATH" >&2
  exit 1
fi

BLOB_SIZE_MB=$(( $(stat -f %z "$BLOB_PATH") / 1024 / 1024 ))
echo "  blob: $BLOB_PATH (${BLOB_SIZE_MB} MB)"

echo "[2/5] Copying GGUF to build context (this may take a minute)..."
cp "$BLOB_PATH" "$WORK_DIR/${MODEL_NAME}.gguf"

echo "[3/5] Generating Modelfile + Dockerfile..."
{
  echo "FROM /tmp/${MODEL_NAME}.gguf"
  printf '%s\n' "$MODELFILE_RAW" | awk '!/^FROM/'
} > "$WORK_DIR/Modelfile"

# Ship the /ping reverse-proxy entrypoint into the build context (LB-endpoint ready).
cp "$SCRIPT_DIR/lb-entrypoint.sh" "$WORK_DIR/lb-entrypoint.sh"

cat > "$WORK_DIR/Dockerfile" <<DOCKERFILE
# Multi-stage build: import model in stage 1, copy ONLY the imported blobs to
# the final image. Avoids ~15 GB of bloat from the COPY-then-import pattern.
FROM ollama/ollama:latest AS builder
COPY ${MODEL_NAME}.gguf /tmp/
COPY Modelfile /tmp/
RUN /usr/bin/ollama serve & \\
    SERVER_PID=\$! && \\
    sleep 8 && \\
    /usr/bin/ollama create ${MODEL_NAME} -f /tmp/Modelfile && \\
    kill \$SERVER_PID && \\
    sleep 2

FROM ollama/ollama:latest
COPY --from=builder /root/.ollama/models /root/.ollama/models
# nginx adds the /ping health route Runpod load-balancing endpoints require; the
# entrypoint runs ollama (11434) + the proxy ($PORT). See scripts/lb-entrypoint.sh.
RUN apt-get update && apt-get install -y --no-install-recommends nginx && rm -rf /var/lib/apt/lists/*
COPY lb-entrypoint.sh /usr/local/bin/lb-entrypoint.sh
RUN chmod +x /usr/local/bin/lb-entrypoint.sh
ENV OLLAMA_HOST=0.0.0.0:11434
EXPOSE 11434
ENTRYPOINT ["/usr/local/bin/lb-entrypoint.sh"]
DOCKERFILE

echo "[4/5] Building docker image: $IMAGE_TAG"
( cd "$WORK_DIR" && docker build --platform linux/amd64 -t "$IMAGE_TAG" . )

echo "[5/5] Pushing to Docker Hub: $IMAGE_TAG"
docker push "$IMAGE_TAG"

cat <<DONE

================================================================================
 DONE.

 Image:  ${IMAGE_TAG}

 Next: create a Runpod Serverless endpoint with this image.
   - Dashboard:   https://runpod.io/console/serverless
   - GPU:         A40 (48GB)
   - Container disk: 30GB
   - Idle timeout:   60s
   - Min workers:    0   (cold-start tolerable)
   - Max workers:    1
   - HTTP port:      11434

 Or run \`DOCKER_USER=${DOCKER_USER} scripts/runpod-wire.sh ${MODEL_NAME} ${TAG_VERSION}\`
 to create the serverless template via the API and print the console steps for
 the endpoint. Once it's live, paste its URL into the next chat with Claude and
 I'll wire it into openclaw as a provider.
================================================================================
DONE
