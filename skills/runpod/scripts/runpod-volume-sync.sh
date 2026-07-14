#!/usr/bin/env bash
# Sync ollama models from Mac → Runpod network volume via S3.
# Volume must already exist in the matching datacenter.
#
# Usage:
#   ./scripts/runpod-volume-sync.sh                              # sync everything (~116 GB)
#   ./scripts/runpod-volume-sync.sh mote-14b-q3-ft               # sync one model
#   ./scripts/runpod-volume-sync.sh mote-14b-q3-ft margot-1.7b-q8-ft   # sync several
#
# Env overrides:
#   PROFILE=runpod         (aws cli profile to use)
#   ENDPOINT=https://s3api-us-il-1.runpod.io
#   BUCKET=smq48f3agd
#
# Selective mode reads each manifest and uploads only its referenced blobs +
# the manifest itself. Skips unrelated 100+ GB of models you don't need.

set -euo pipefail

PROFILE="${PROFILE:-runpod}"
ENDPOINT="${ENDPOINT:-https://s3api-us-il-1.runpod.io}"
BUCKET="${BUCKET:-smq48f3agd}"
OLLAMA_DIR="${HOME}/.ollama/models"

command -v aws >/dev/null || { echo "awscli not installed" >&2; exit 1; }
command -v jq  >/dev/null || { echo "jq not installed (brew install jq)" >&2; exit 1; }
[ -d "$OLLAMA_DIR" ] || { echo "Ollama models dir not found: $OLLAMA_DIR" >&2; exit 1; }

S3="aws s3 --profile $PROFILE --endpoint-url $ENDPOINT"

if [ "$#" -eq 0 ]; then
  echo "[*] No models named — full mirror of $OLLAMA_DIR (~$(du -sh $OLLAMA_DIR | cut -f1))"
  read -p "Continue? [y/N] " yn
  [[ "$yn" =~ ^[yY]$ ]] || exit 0
  $S3 sync "$OLLAMA_DIR/" "s3://$BUCKET/models/" --no-progress
  exit 0
fi

# Selective sync: walk each named model's manifest to collect blob digests
declare -a INCLUDES
TOTAL_BYTES=0

for name in "$@"; do
  # split name:tag (default tag = latest)
  if [[ "$name" == *:* ]]; then
    base="${name%:*}"; tag="${name##*:}"
  else
    base="$name"; tag="latest"
  fi

  # try canonical paths
  manifest=""
  for candidate in \
      "$OLLAMA_DIR/manifests/registry.ollama.ai/library/${base}/${tag}" \
      "$OLLAMA_DIR/manifests/hf.co/${base}/${tag}" \
      "$OLLAMA_DIR/manifests/${base}/${tag}"; do
    [ -f "$candidate" ] && { manifest="$candidate"; break; }
  done

  if [ -z "$manifest" ]; then
    echo "manifest not found for ${base}:${tag}" >&2
    echo "available local manifests:" >&2
    find "$OLLAMA_DIR/manifests" -type f | sed "s|$OLLAMA_DIR/manifests/||" >&2
    exit 1
  fi

  echo "[*] $base:$tag"
  rel_manifest="${manifest#$OLLAMA_DIR/}"
  INCLUDES+=( "$rel_manifest" )

  # collect all sha256 digests referenced anywhere in the manifest JSON
  while IFS= read -r digest; do
    [ -z "$digest" ] && continue
    blob_name="sha256-${digest#sha256:}"
    blob_path="blobs/${blob_name}"
    abs="$OLLAMA_DIR/$blob_path"
    if [ -f "$abs" ]; then
      sz=$(stat -f%z "$abs")
      TOTAL_BYTES=$((TOTAL_BYTES + sz))
      INCLUDES+=( "$blob_path" )
      echo "    + $blob_path  ($((sz / 1024 / 1024)) MB)"
    else
      echo "    ! missing blob $abs" >&2
      exit 1
    fi
  done < <(jq -r '.. | .digest? // empty' "$manifest")
done

echo
echo "[*] Total transfer: $((TOTAL_BYTES / 1024 / 1024)) MB ($((TOTAL_BYTES / 1024 / 1024 / 1024)) GB)"

# de-dup includes (multiple models may share the same template/system blob)
INCLUDES=($(printf '%s\n' "${INCLUDES[@]}" | sort -u))

# Build --exclude '*' --include <each> for sync
ARGS=( --exclude '*' )
for inc in "${INCLUDES[@]}"; do
  ARGS+=( --include "$inc" )
done

echo "[*] Uploading to s3://$BUCKET/models/..."
$S3 sync "${ARGS[@]}" "$OLLAMA_DIR/" "s3://$BUCKET/models/"

echo
echo "Done. Verify on Runpod:"
echo "  $S3 ls s3://$BUCKET/models/manifests/registry.ollama.ai/library/"
