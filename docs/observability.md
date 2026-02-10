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
 
 ## Log flow
 - App containers emit JSON logs to stdout (see `backend/src/logging/`: JSON formatter with `timestamp`, `level`, `logger`, `message`, and optional `correlation_id`, `endpoint`, `task_name`, `task_id`, etc.).
 - Correlation IDs are set per request (middleware) and per task (Celery context), and are included in log `extra` and in the JSON output.
 - Promtail scrapes Docker container logs, parses the JSON, and extracts labels: `service` (compose service name), `container`, `level`, `logger`, `correlation_id`, `endpoint`, `task_name`, `task_id`. Logs are pushed to Loki.
 - Grafana has both Prometheus and Loki datasources provisioned.
 
 ## Logs dashboard (browser)
 Open **Grafana** → **Dashboards** → **Logs** (or go to `/d/bedrock-logs`).
 
 - **Log stream by service**: Use the **Service** dropdown to filter by `backend`, `worker`, or `beat`. You can select one or multiple services. The top panel shows the log stream for the selected service(s).
 - **Logs for correlation ID (all services)**: Enter a **Correlation ID** in the text box (e.g. from the `X-Correlation-ID` response header or from a log line). The bottom panel shows all log entries with that `correlation_id` across every service, so you can trace a request or task end-to-end.
 
 To get a correlation ID from a request: send `X-Correlation-ID` with any value, or omit it and read the generated ID from the response header `X-Correlation-ID`.
