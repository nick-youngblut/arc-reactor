#!/usr/bin/env bash
set -euo pipefail

if [ $# -ge 2 ]; then
  IMAGE_NAME="$1"
  VERSION="$2"
else
  IMAGE_NAME="${IMAGE_NAME:-}"
  VERSION="${VERSION:-}"
fi

if [ -z "${IMAGE_NAME}" ] || [ -z "${VERSION}" ]; then
  echo "Usage: $0 <image-name> <version>" >&2
  echo "Or set IMAGE_NAME and VERSION env vars." >&2
  exit 1
fi

docker build --platform linux/amd64 -f orchestrator/Dockerfile.orchestrator \
  -t "${IMAGE_NAME}:${VERSION}" \
  .

docker tag "${IMAGE_NAME}:${VERSION}" "${IMAGE_NAME}:latest"

docker push "${IMAGE_NAME}:${VERSION}"
docker push "${IMAGE_NAME}:latest"
