#!/bin/sh
set -e

docker_compose="docker-compose -f $(cd "$(dirname "$0")/.." && pwd)/docker-compose.yml"

cleanup() {
  $docker_compose down
}

trap cleanup EXIT

$docker_compose up -d mongodb rabbitmq backend

attempts=0
until curl -sf http://localhost:8000/api/health >/dev/null; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge 60 ]; then
    echo "Backend health check failed"
    exit 1
  fi
  sleep 2
done

$docker_compose exec backend \
  env COVERAGE_XML_PATH=reports/integration-coverage.xml \
  COVERAGE_HTML_PATH=reports/integration-coverage/index.html \
  pytest tests/integration -v --asyncio-mode=auto \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html:reports/integration-coverage \
    --cov-report=xml:reports/integration-coverage.xml \
    --html=reports/integration.html \
    --self-contained-html
