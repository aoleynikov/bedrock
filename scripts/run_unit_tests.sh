#!/bin/sh
set -e

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root/backend"

venv_path="$repo_root/backend/.venv"
if [ ! -d "$venv_path" ]; then
  python3 -m venv "$venv_path"
fi

. "$venv_path/bin/activate"

if ! python -m pytest --version >/dev/null 2>&1; then
  if ! python -m pip install -r requirements.txt; then
    python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
  fi
fi

COVERAGE_XML_PATH=reports/unit-coverage.xml \
COVERAGE_HTML_PATH=reports/unit-coverage/index.html \
python -m pytest tests/unit -m unit -v --asyncio-mode=auto \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:reports/unit-coverage \
  --cov-report=xml:reports/unit-coverage.xml \
  --html=reports/unit.html \
  --self-contained-html
