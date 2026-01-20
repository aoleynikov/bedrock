#!/bin/sh
set -e

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root/backend"

COVERAGE_XML_PATH=reports/unit-coverage.xml \
COVERAGE_HTML_PATH=reports/unit-coverage/index.html \
pytest tests/unit -m unit -v --asyncio-mode=auto \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:reports/unit-coverage \
  --cov-report=xml:reports/unit-coverage.xml \
  --html=reports/unit.html \
  --self-contained-html
