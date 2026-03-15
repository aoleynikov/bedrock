# syntax=docker/dockerfile:1
# Canonical OCI image definition: backend/rockcraft.yaml
# This Dockerfile is the docker-compose fallback; rockcraft is preferred for
# production image builds.

# ── build stage: compile C extensions ──────────────────────────────────────
FROM python:3.11-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

RUN python3 -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# ── runtime stage ───────────────────────────────────────────────────────────
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libffi8 \
        libssl3 \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /venv /venv

ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY src/ ./src/

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
