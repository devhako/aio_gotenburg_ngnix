#!/usr/bin/env bash
set -euo pipefail

# ─── CONFIG ───────────────────────────────────────────────────────────────
# Replace with your Docker Hub username/repo
REPO="devhako/aio_gotenburg_ngnix"

# Optional: name for your buildx builder
BUILDER_NAME="multi-builder"
# ──────────────────────────────────────────────────────────────────────────

# ensure timestamp in Asia/Singapore timezone
export TZ="Asia/Singapore"
TIMESTAMP=$(date +'%Y%m%d')

# enable BuildKit & Buildx
export DOCKER_CLI_EXPERIMENTAL=enabled

# create (or reuse) and bootstrap builder
docker buildx create --name "${BUILDER_NAME}" --use >/dev/null 2>&1 || true
docker buildx inspect --bootstrap

# build and push multi-arch image with both timestamp and latest tags
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${REPO}:${TIMESTAMP}" \
  -t "${REPO}:latest" \
  --push \
  .

