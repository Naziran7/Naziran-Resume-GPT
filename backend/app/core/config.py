import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "NaziranGPT"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development" # development, production, test
    
    # Security
    # In production, this MUST be a long random string
    SECRET_KEY: str = Field(default="supersecretkeyforlocaldevelopmentonlychangeinprod1234567890!")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for convenience in MVP
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Postgres Database Config
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "nazirangpt"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None

    @property
    def sync_database_uri(self) -> str:
        if self.DATABASE_URL:
            # Handle standard postgresql:// vs postgresql+psycopg2:// if needed
            uri = self.DATABASE_URL
            if uri.startswith("postgres://"):
                uri = uri.replace("postgres://", "postgresql://", 1)
            return uri
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def async_database_uri(self) -> str:
        sync_uri = self.sync_database_uri
        # Convert postgresql:// or postgresql+psycopg2:// to postgresql+asyncpg://
        if sync_uri.startswith("postgresql://"):
            return sync_uri.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif sync_uri.startswith("postgresql+psycopg2://"):
            return sync_uri.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        return sync_uri

    # Redis Config (for background task rate limiting, cache, celery in future)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Sentry DSN
    SENTRY_DSN: Optional[str] = None

    # Google Gemini API Key
    GEMINI_API_KEY: Optional[str] = None

    # Resend Email API Key
    RESEND_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
