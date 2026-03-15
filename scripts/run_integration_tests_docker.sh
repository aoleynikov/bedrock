#!/bin/sh
# Run the backend integration test suite inside a container alongside MongoDB.
#
# Build strategy (in priority order):
#   1. rockcraft  – builds from backend/rockcraft.tests.yaml
#   2. docker build – falls back to backend/Dockerfile.integration
#
# Either way the image is run with an explicit python3 entrypoint so the
# pytest exit code is propagated correctly regardless of which init is baked in.
#
# Environment variables:
#   ENV_FILE  – path (relative to repo root) to the env file passed to the
#               test container.  Defaults to "env.local".

set -e

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
image_name="bedrock-backend-integration-tests"
env_file_path="$repo_root/${ENV_FILE:-env.local}"
compose_file="$repo_root/docker-compose.integration.yml"
project_name="bedrock_test_$(date +%s)"

cleanup() {
  docker compose -f "$compose_file" -p "$project_name" down -v
}
trap cleanup EXIT

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
    -f "$repo_root/backend/Dockerfile.integration" \
    -t "$image_name" \
    "$repo_root/backend"
fi

# ── start MongoDB ─────────────────────────────────────────────────────────────
echo "==> Starting MongoDB…"
docker compose -f "$compose_file" -p "$project_name" up -d mongodb

attempts=0
until [ "$attempts" -ge 60 ]; do
  mongo_container="$(docker compose -f "$compose_file" -p "$project_name" ps -q mongodb)"
  mongo_status="$(docker inspect -f '{{.State.Health.Status}}' "$mongo_container" 2>/dev/null || echo 'starting')"
  if [ "$mongo_status" = "healthy" ]; then
    break
  fi
  attempts=$((attempts + 1))
  sleep 2
done

if [ "$attempts" -ge 60 ]; then
  echo "ERROR: MongoDB health check timed out" >&2
  exit 1
fi

# ── run ──────────────────────────────────────────────────────────────────────
network_name="$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' "$mongo_container")"

echo "==> Running integration tests…"
docker run --rm -t \
  --entrypoint python3 \
  --network "$network_name" \
  --env-file "$env_file_path" \
  -e ENV=test \
  "$image_name" \
  -m pytest tests/integration -m integration -v --strict-markers --tb=short \
           --asyncio-mode=auto --cov=src --cov-report=term-missing \
           -o addopts=
