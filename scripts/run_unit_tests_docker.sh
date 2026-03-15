#!/bin/sh
# Run the backend unit test suite inside a container.
#
# Build strategy (in priority order):
#   1. rockcraft  – builds from backend/rockcraft.tests.yaml, produces a
#                   hardened OCI image identical to the production rock.
#   2. docker build – falls back to backend/Dockerfile.tests when rockcraft
#                     is not installed.
#
# Either way the image is run with an explicit python3 entrypoint so the
# pytest exit code is propagated correctly regardless of which init (pebble
# vs none) is baked in.

set -e

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
image_name="bedrock-backend-unit-tests"

# ── build ────────────────────────────────────────────────────────────────────
if command -v rockcraft > /dev/null 2>&1; then
  echo "==> Building test image with rockcraft…"
  (
    cd "$repo_root/backend"
    rockcraft pack --rockfile rockcraft.tests.yaml
  )
  rock_file="$(ls "$repo_root/backend/bedrock-backend-tests_"*.rock 2>/dev/null | head -1)"
  if [ -z "$rock_file" ]; then
    echo "ERROR: rockcraft pack produced no .rock file" >&2
    exit 1
  fi
  rockcraft.skopeo copy "oci-archive:$rock_file" "docker-daemon:$image_name:latest"
else
  echo "==> rockcraft not found – building test image with docker build…"
  docker build \
    -f "$repo_root/backend/Dockerfile.tests" \
    -t "$image_name" \
    "$repo_root/backend"
fi

# ── run ──────────────────────────────────────────────────────────────────────
echo "==> Running unit tests…"
docker run --rm -t \
  --entrypoint python3 \
  "$image_name" \
  -m pytest tests/unit -m unit -v --strict-markers --tb=short \
           --asyncio-mode=auto --cov=src --cov-report=term-missing \
           -o addopts=
