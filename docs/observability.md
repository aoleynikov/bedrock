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
 - App containers emit JSON logs to stdout.
 - Promtail reads Docker log files and forwards them to Loki.
 - Grafana reads Loki and Prometheus as data sources.
