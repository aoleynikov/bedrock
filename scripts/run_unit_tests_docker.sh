#!/bin/sh
set -e

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
image_name="bedrock-backend-unit-tests"

docker build -f "$repo_root/backend/Dockerfile.tests" -t "$image_name" "$repo_root/backend"
docker run --rm -t "$image_name"
