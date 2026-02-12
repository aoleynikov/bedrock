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
 
## Logs dashboards (browser)

**Logs** is the default Grafana home dashboard. Open Grafana → you land on Logs, or go to `/d/bedrock-logs`.

### Main Logs (INFO+)

Shows INFO, WARNING, ERROR, CRITICAL (excludes DEBUG). Columns: **time**, **service**, **url/task name**, **message**.

- **Service filter**: Use the **Service** dropdown to filter by `backend`, `worker`, or `beat`. Default is backend + worker.
- **Filter by correlation ID**: Click a log entry to expand it. The correlation_id appears in the log line and as a clickable **All logs by correlation** link in the log details. Click it to open the correlation dashboard with that ID pre-filled.
- **All logs (incl. DEBUG) by correlation**: Link to drill into one request/task with full debug logs.

### Logs by correlation (all levels)

Shows all logs including DEBUG for a single request/task. Use when you need the full trace (e.g. LLM prompts/results).

- Open from main logs via the correlation_id link, or go to `/d/bedrock-logs-correlation` and paste a correlation ID.
