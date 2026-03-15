# syntax=docker/dockerfile:1
#
# WHY THIS FILE IS NOT REPLACED BY A ROCKCRAFT CONFIG
# ─────────────────────────────────────────────────────
# Playwright requires a heavily pre-configured base image that ships three
# browser engines (Chromium, Firefox, WebKit) plus all their system-level
# dependencies: hundreds of apt packages, fonts, audio/video codecs, and
# sandboxing utilities.  Microsoft maintains this officially as:
#
#   mcr.microsoft.com/playwright:v1.58.1-jammy
#
# Rockcraft has no Playwright plugin and no mechanism to declare browser
# binaries as parts.  Reproducing the full dependency tree manually in a
# rockcraft.yaml would require hundreds of stage-packages entries and brittle
# override-build scripts, and would need to be kept in sync with every
# Playwright release.
#
# For the other services in this project (backend, frontends) rockcraft is
# the canonical build tool.  For the functional-test runner, this Dockerfile
# remains the source of truth and should stay on the official Playwright base.

FROM mcr.microsoft.com/playwright:v1.58.1-jammy

WORKDIR /tests

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
