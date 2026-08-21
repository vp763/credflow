# CredFlow Backend - Configuration Management

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "CredFlow API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://credflow:credflow@localhost:5432/credflow"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    # Azure Storage (Azurite local / Azure Blob production)
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "credflow"

    # Azure Key Vault
    KEY_VAULT_URI: str = ""

    # Authentication - JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Authentication - Keycloak / Azure Entra ID
    AUTH_PROVIDER: str = "local"  # keycloak, azure, mock
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "credflow"
    KEYCLOAK_CLIENT_ID: str = "credflow-backend"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_ADMIN_USER: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: str = "admin"

    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:80"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Tally Integration
    TALLY_SYNC_MAX_PAYLOAD_MB: int = 50
    TALLY_DEFAULT_SYNC_INTERVAL_MINUTES: int = 60
    TALLY_XML_ENCODING: str = "utf-8"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Kolkata"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4

    # WhatsApp / SMS / Email Providers
    WHATSAPP_PROVIDER: str = "twilio"  # twilio, gupshup, wati, mock
    WHATSAPP_ACCOUNT_SID: str = ""
    WHATSAPP_AUTH_TOKEN: str = ""
    WHATSAPP_FROM_NUMBER: str = ""

    EMAIL_PROVIDER: str = "sendgrid"  # sendgrid, ses, smtp, mock
    SENDGRID_API_KEY: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@credflow.in"
    EMAIL_FROM_NAME: str = "CredFlow"

    SMS_PROVIDER: str = "twilio"  # twilio, msg91, mock
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # Monitoring
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_SERVICE_NAME: str = "credflow-backend"
    OTEL_RESOURCE_ATTRIBUTES: str = ""

    # Feature Flags
    FEATURE_REMINDERS_ENABLED: bool = True
    FEATURE_PAYMENTS_ENABLED: bool = True
    FEATURE_ANALYTICS_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()