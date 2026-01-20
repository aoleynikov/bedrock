# Playwright functional tests

## Prerequisites
- Docker and Docker Compose installed
- Node.js and npm installed

## Environment variables
- `ADMIN_APP_URL` (default: `http://localhost:5174`)
- `USER_APP_URL` (default: `http://localhost:5173`)
- `ADMIN_EMAIL` (default: `admin@example.com`)
- `ADMIN_PASSWORD` (default: `admin1234`)
- `BACKEND_URL` (default: `http://localhost:8000`)
- `WAIT_TIMEOUT_MS` (default: `60000`)

## Run locally
From `functional_tests`:

```bash
npm install
npm test
```

## Run with Docker Compose
From `functional_tests`:

```bash
npm install
npm run test:compose
```

`test:compose` brings the full stack up, waits for backend/admin readiness, runs Playwright, and then tears the stack down.
