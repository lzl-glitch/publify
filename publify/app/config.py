"""Application configuration using environment variables."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Publify"
    app_env: str = "development"
    secret_key: str
    base_url: str = "http://localhost:8000"

    # Database
    database_url: str = "sqlite:///./publify.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qiniu Cloud Storage
    qiniu_access_key: str = ""
    qiniu_secret_key: str = ""
    qiniu_bucket: str = ""
    qiniu_domain: str = ""

    # Xiaohongshu OAuth
    xiaohongshu_client_id: str = ""
    xiaohongshu_client_secret: str = ""
    xiaohongshu_redirect_uri: str = ""
    xiaohongshu_auth_url: str = "https://open.xiaohongshu.com/oauth/authorize"
    xiaohongshu_token_url: str = "https://open.xiaohongshu.com/oauth/access_token"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Session
    session_expire_days: int = 7

    # Rate Limiting
    rate_limit_enabled: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
