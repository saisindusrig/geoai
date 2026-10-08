from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+psycopg2://geoai:geoai@localhost:5432/geoai"
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT: str = ""
    S3_BUCKET: str = "geoai-files"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = ""
    # Public API URL for /files/ links (defaults to RENDER_EXTERNAL_URL on Render).
    PUBLIC_API_URL: str = ""

    GOOGLE_MAPS_API_KEY: str = ""
    CESIUM_ION_TOKEN: str = ""
    # Browser runtime receives only this explicitly restricted read credential.
    CESIUM_ION_READ_TOKEN: str = ""
    CESIUM_ION_WRITE_TOKEN: str = ""
    MAPBOX_TOKEN: str = ""

    # AI — AI_PROVIDER selects primary: nebius | ollama | openai | anthropic | mock (auto)
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Nebius Token Factory - building assistant, concept planner and optional main provider.
    NEBIUS_API_KEY: str = ""
    NEBIUS_BASE_URL: str = ""
    NEBIUS_TOKEN_FACTORY_BASE_URL: str = "https://api.tokenfactory.us-central1.nebius.com/v1"
    NEBIUS_CHAT_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT_SECONDS: int = 120

    APP_SECRET: str = "dev-secret-change-me"
    AUTH_REQUIRE_JWT: bool = False
    DEV_MOCK_USER_ROLE: str = "admin"
    ENVIRONMENT: str = "development"
    NEXT_PUBLIC_APP_URL: str = "http://localhost:3000"
    # Comma-separated extra browser origins (custom domains, staging URLs).
    CORS_ALLOWED_ORIGINS: str = ""
    # Allow https://*.netlify.app (production + preview deploys).
    CORS_ALLOW_NETLIFY: bool = True

    GENERATION_JOB_TIMEOUT_SECONDS: int = 300

    USAGE_LIMITS_ENABLED: bool = True
    RATE_LIMITING_ENABLED: bool = True
    # When true and Redis is available, design jobs enqueue to the Arq worker.
    USE_ARQ_WORKER: bool = False

    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    LOCAL_STORAGE_DIR: str = str(BACKEND_DIR / "storage")


settings = Settings()
