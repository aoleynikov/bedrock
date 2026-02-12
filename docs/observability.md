 # Observability Stack
 
 Bedrock ships with Prometheus, Grafana, Loki, and Promtail in `docker-compose.yml`.
 
 ## Services and ports
 - Prometheus: `http://localhost:9090`
 - Grafana: `http://localhost:3000` (admin/admin)
 - Loki: `http://localhost:3100`
 
 Promtail does not publish a host port. It tails Docker container logs and ships them to Loki.
 
 ## Configuration locations
 - Prometheus config: `prometheus/prometheus.yml`
 - Alert rules: `prometheus/alerts.yml`
 - Grafana provisioning: `grafana/provisioning/`
 - Loki config: `loki/loki.yml`
 - Promtail config: `promtail/promtail.yml`
 
 ## Troubleshooting

### "no such host" or "connection refused" for Loki in Grafana

The Logs dashboard connects to Loki via `host.docker.internal:3100`. **Loki must be running** and its port exposed to the host.

1. Start Loki (and the rest of the observability stack):

```bash
docker compose up -d loki promtail prometheus grafana
```

2. Verify Loki is running and reachable:

```bash
docker ps | grep loki
curl http://localhost:3100/ready
```

If `curl` returns "ready", Grafana should be able to connect. If you still see errors, restart Grafana after Loki is up: `docker compose restart grafana`.

## Log flow
 - App containers emit JSON logs to stdout (see `backend/src/logging/`: JSON formatter with `timestamp`, `level`, `logger`, `message`, and optional `correlation_id`, `endpoint`, `task_name`, `task_id`, etc.).
 - Correlation IDs are set per request (middleware) and per task (Celery context), and are included in log `extra` and in the JSON output.
 - Promtail scrapes Docker container logs, parses the JSON, and extracts labels: `service` (compose service name), `container`, `level`, `logger`, `correlation_id`, `endpoint`, `task_name`, `task_id`. Logs are pushed to Loki.
 - Grafana has both Prometheus and Loki datasources provisioned.
 
## Logs dashboard (browser)
Open **Grafana** → **Dashboards** → **Logs** (or go to `/d/bedrock-logs`).

Columns: **time** (Grafana), **service**, **url/task name** (endpoint for API, task_name for Celery), **message**.

- **Service filter**: Use the **Service** dropdown to filter by `backend`, `worker`, or `beat`. Default is backend + worker.
- **Filter by correlation ID**: Click a log entry, then click the correlation_id link that appears in the log details. The view filters to show only logs for that request or task. Use **Show all logs** (top of dashboard) to clear the filter.
