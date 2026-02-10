# Data persistence

## Overview

- **Test runs**: Each integration or unit test run uses **new Docker volumes** (or no persistent volume). No data is shared between test runs. This includes **MongoDB**: each integration run gets a fresh MongoDB volume that is removed with `down -v`.
- **Environments (local, dev, staging, prod)**: All persistent app data lives under **`/data`** in the container, including **MongoDB** (at `/data/db` in the mongodb service). Volumes are mapped so that local, dev, staging, and prod each have their own backing store.

## Test runs

### Integration tests

- The integration test script uses a **unique Compose project name** per run (e.g. `bedrock_test_<timestamp>`).
- That brings up a dedicated MongoDB (and any other services) with **new volumes** for that run, including a fresh MongoDB data volume.
- After tests finish, `docker compose down -v` removes the project and **all its volumes** (including MongoDB), so the next run gets a clean state.
- File storage for the test container uses an ephemeral path; no shared volume with the host or other runs.

### Unit tests

- Unit tests run in a container that **does not mount any persistent volume** for app data.
- They do not use a real database or file storage (mocked), so each run is isolated by design.

## Environments and `/data`

Containers that need persistent data use a single root **`/data`**:

| Service   | Path in container | Purpose                          |
|-----------|-------------------|----------------------------------|
| backend, worker, beat | `/data/uploads` | Local file storage (uploaded files) |
| mongodb   | `/data/db`        | MongoDB data                     |

- **Docker Compose (local/dev)**: Named volume `app_data` at `/data` for backend, worker, and beat; `mongodb_data` at `/data/db` for MongoDB. Each environment (local, dev, staging, prod) should use its own volume names or bind mounts so data is not shared.
- **Staging / production**: Use the same layout: mount the environment’s volume(s) at `/data` (and at `/data/db` for MongoDB) so all app data, including the database, stays under `/data` and is isolated per environment.

For local development with files visible on the host, you can use a Compose override that bind-mounts a host directory at `/data`, e.g. `./data:/data`, instead of the named volume.

## Configuration

- `FILE_STORAGE_PATH`: Directory for local file storage. Use `storage/uploads` when running the app outside Docker (e.g. on the host). Use `/data/uploads` when running in Docker so storage uses the `/data` volume.
- In Compose, `FILE_STORAGE_PATH` is set to `/data/uploads` for backend, worker, and beat so they all use the same mounted volume.
