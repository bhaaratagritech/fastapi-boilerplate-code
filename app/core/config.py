from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        populate_by_name=True,
    )

    app_name: str = Field(default="fast-api-service", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    allowed_origins: str = Field(default="", alias="ALLOWED_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    auth_exempt_paths: str = Field(default="", alias="AUTH_EXEMPT_PATHS")

    jwt_secret: str = Field(default="changeme", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_audience: Optional[str] = Field(default=None, alias="JWT_AUDIENCE")
    jwt_issuer: Optional[str] = Field(default=None, alias="JWT_ISSUER")

    mysql_dsn: str = Field(alias="MYSQL_DSN")

    opensearch_host: str = Field(alias="OPENSEARCH_HOST")
    opensearch_username: str = Field(alias="OPENSEARCH_USERNAME")
    opensearch_password: str = Field(alias="OPENSEARCH_PASSWORD")

    redis_url: str = Field(alias="REDIS_URL")
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")

    aws_region: str = Field(alias="AWS_REGION")
    aws_secret_name: str = Field(alias="AWS_SECRETS_MANAGER_SECRET_NAME")

    pii_fields: str = Field(default="", alias="PII_FIELDS")

    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed_origins as a list."""
        if not self.allowed_origins.strip():
            return ["*"]
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]

    @property
    def auth_exempt_paths_list(self) -> List[str]:
        """Get auth_exempt_paths as a list."""
        if not self.auth_exempt_paths.strip():
            return []
        return [item.strip() for item in self.auth_exempt_paths.split(",") if item.strip()]

    @property
    def pii_fields_list(self) -> List[str]:
        """Get pii_fields as a list."""
        if not self.pii_fields.strip():
            return []
        return [item.strip() for item in self.pii_fields.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


