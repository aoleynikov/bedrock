 # Environment Configuration
 
 ## Files
 - `env.example` is the canonical template.
 - `env.local` is used by Docker Compose by default.
 
 ## Usage
 ```bash
 cp env.example env.local
 docker-compose up --build
 ```
 
 To target a different file:
 ```bash
 ENV_FILE=env.local docker-compose up --build
 ```
 
 ## Key variables
 - `MONGODB_URL`, `MONGODB_DB_NAME`
 - `RABBITMQ_URL`
 - `API_HOST`, `API_PORT`
 - `WORKER_METRICS_PORT`
 - `CORS_ORIGINS`
 - `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`
 - `ADMIN_DEFAULT_EMAIL`, `ADMIN_DEFAULT_NAME`, `ADMIN_DEFAULT_PASSWORD`
- `FRONTEND_USER_PORT`, `FRONTEND_ADMIN_PORT`
- `PROMETHEUS_PORT`, `GRAFANA_PORT`, `LOKI_PORT`
- `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`
 - `FILE_STORAGE_TYPE`, `FILE_STORAGE_PATH`
 - `S3_BUCKET_NAME`, `S3_REGION`
 - `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`
 - `OAUTH_STATE_COOKIE_SECURE`
 - `VITE_API_URL`
