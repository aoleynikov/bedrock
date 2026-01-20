from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    mongodb_url: str = 'mongodb://localhost:27017'
    mongodb_db_name: str = 'bedrock'
    rabbitmq_url: str = 'amqp://guest:guest@localhost:5672//'
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    worker_metrics_port: int = 8001
    cors_origins: str = 'http://localhost:5173'
    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None
    google_oauth_redirect_uri: Optional[str] = None
    oauth_state_cookie_secure: bool = False
    file_storage_type: str = 'local'  # 'local' or 's3'
    file_storage_path: str = 'storage/uploads'  # For local storage
    s3_bucket_name: Optional[str] = None  # For S3 storage
    s3_region: str = 'us-east-1'  # For S3 storage
    admin_default_email: str
    admin_default_name: str
    admin_default_password: str

    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=False,
        extra='ignore'
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',')]


settings = Settings()
