# Bedrock

Production-ready full stack boilerplate with FastAPI, MongoDB, RabbitMQ, Celery, and two React apps.

## Stack
- Backend: FastAPI (Python 3.11+)
- Database: MongoDB 7
- Queue: RabbitMQ 3 + Celery
- Frontend: React 18 + Vite (user and admin)
- Infrastructure: Docker Compose

## Services and Ports
- User app: http://localhost:5173
- Admin app: http://localhost:5174
- API: http://localhost:8000 (docs at `/docs`)
- RabbitMQ management: http://localhost:15672 (guest/guest)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Loki: http://localhost:3100

## Quick Start
```bash
docker-compose up --build
```

## Environment
- Use `env.example` as a template and copy it to `env.local` for local development
- Target a specific env file with `ENV_FILE=env.local docker-compose up`

## Tests
```bash
./scripts/run_unit_tests.sh
./scripts/run_integration_tests.sh
```
```bash
cd functional_tests
# Docker-only Playwright workflow is documented here:
cat README.md
```

## Documentation
- `docs/README.md`

## Useful Paths
- API routes: `backend/src/routes/`
- Services: `backend/src/services/`
- Repositories: `backend/src/repositories/`
- User app: `frontend-user/`
- Admin app: `frontend-admin/`
