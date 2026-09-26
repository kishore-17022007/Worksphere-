from functools import lru_cache
import secrets

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://worksphere:change-me@localhost:5432/worksphere"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    cors_origins: str = "http://localhost:3000"
    s3_bucket: str = "worksphere"
    s3_endpoint_url: str | None = None
    environment: str = "development"
    log_level: str = "INFO"
    allowed_hosts: str = "*"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if len(self.jwt_secret_key) < 32 or self.jwt_secret_key == "change-me-in-production":
            raise ValueError("JWT_SECRET_KEY must be a unique secret of at least 32 characters")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
