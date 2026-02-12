#!/bin/sh
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
  echo 'Dependencies health check failed'
  exit 1
fi

docker build -f "$repo_root/backend/Dockerfile.integration" -t "$image_name" "$repo_root/backend"
network_name="$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' "$mongo_container")"
docker run --rm -t --network "$network_name" --env-file "$env_file_path" "$image_name"
