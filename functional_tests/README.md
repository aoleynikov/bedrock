# Playwright functional tests

## Prerequisites
- Docker and Docker Compose installed

## Environment variables
- `ADMIN_APP_URL` (default: `http://localhost:5174`)
- `USER_APP_URL` (default: `http://localhost:5173`)
- `ADMIN_EMAIL` (default: `admin@example.com`)
- `ADMIN_PASSWORD` (default: `admin1234`)
- `BACKEND_URL` (default: `http://localhost:8000`)
- `WAIT_TIMEOUT_MS` (default: `60000`)

## Quick start (Docker-only)
From `functional_tests`:

```bash
VITE_API_URL=http://bedrock_backend:8000 PW_COVERAGE=true docker-compose -f ../docker-compose.yml up -d --build
```

Run the suite in Docker:
```bash
docker build -t bedrock-functional-tests . && docker run --rm --network bedrock_bedrock_network -e ADMIN_APP_URL=http://bedrock_frontend_admin:5174 -e USER_APP_URL=http://bedrock_frontend_user:5173 -e BACKEND_URL=http://bedrock_backend:8000 -e PW_COVERAGE=true -v "$PWD/coverage-report:/tests/coverage-report" -v "$PWD/coverage:/tests/coverage" bedrock-functional-tests npm run test:coverage
```

Reports are written to `functional_tests/coverage-report/`.

If you started the stack for testing, you can stop it:
```bash
docker-compose -f ../docker-compose.yml down
```

## Coverage
Coverage requires the frontend apps to be started with `PW_COVERAGE=true`.

Run against an existing stack:
```bash
PW_COVERAGE=true npm run test:coverage
```

Reports are written to `functional_tests/coverage-report/`.

## Run in Docker (Playwright image)
This keeps the stack running and runs tests from a container on the same network.
No local Node.js, Playwright, or browser installs are required.
Ensure the frontends are running with `VITE_API_URL=http://bedrock_backend:8000`.

Build the image from `functional_tests`:
```bash
docker build -t bedrock-functional-tests .
```

Run the suite against the running stack:
```bash
docker run --rm \
  --network bedrock_bedrock_network \
  -e ADMIN_APP_URL=http://bedrock_frontend_admin:5174 \
  -e USER_APP_URL=http://bedrock_frontend_user:5173 \
  -e BACKEND_URL=http://bedrock_backend:8000 \
  -e PW_COVERAGE=true \
  -v "$PWD/coverage-report:/tests/coverage-report" \
  -v "$PWD/coverage:/tests/coverage" \
  bedrock-functional-tests \
  npm run test:coverage
```

## Optional local run (requires Node.js + Playwright)
From `functional_tests`:

```bash
npm install
npx playwright install
npm test
```
