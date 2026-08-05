"""
Centralized configuration.

Every setting the app needs is declared here ONCE, typed, with a sane
default where possible. Nothing outside this file should call os.getenv()
directly — that keeps config discoverable and testable.

Values are loaded from environment variables / a .env file at process
startup (see .env.example for the full list).
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    PROJECT_NAME: str = "AI Book Translation Platform"
    ENVIRONMENT: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Security (used from Phase 2 onward) ---
    SECRET_KEY: str = "change-me-in-.env"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@db:5432/book_platform"
    )

    # --- Redis / Celery (used from Phase 5 onward) ---
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # --- Storage (used from Phase 3 onward) ---
    # "local" writes to LOCAL_STORAGE_PATH on disk — zero setup, used by
    # default so the project runs without any cloud credentials. Switch
    # to "s3" once AWS_* credentials below are filled in.
    STORAGE_BACKEND: str = "local"  # s3 | azure_blob | local
    LOCAL_STORAGE_PATH: str = "/app/storage"
    S3_BUCKET_NAME: str = "book-platform-storage"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"

    # --- Upload validation (Phase 3) ---
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_UPLOAD_EXTENSIONS: str = "pdf,epub,docx,txt"

    # --- Chunking (Phase 5) ---
    # Kept well under most translation-model context windows so a chunk +
    # system prompt + the model's own output still fits comfortably —
    # this is deliberately conservative, not the max the API could take.
    CHUNK_MAX_TOKENS: int = 1200
    # tiktoken encoding used for token counting. "cl100k_base" is what
    # GPT-4-class models use; close enough for GPT-5.5 for sizing purposes
    # even before an exact encoding is published for it.
    CHUNK_TOKENIZER_ENCODING: str = "cl100k_base"
 
    # --- Translation (Phase 6) ---
    # Which TranslationProvider to use — "openai" or "indictrans2". See
    # services/translation/provider_factory.py. Swappable without touching
    # business logic, per the AI-provider-abstraction requirement.
    TRANSLATION_PROVIDER: str = "openai"
    OPENAI_MODEL: str = "gpt-5.5"
    # IndicTrans2 is served as a separate inference endpoint rather than
    # loaded in-process — embedding transformers/torch in this API image
    # would bloat it enormously for a model most requests won't use.
    INDICTRANS2_ENDPOINT_URL: str = ""
 
    TRANSLATION_MAX_RETRIES: int = 3
    TRANSLATION_RETRY_BACKOFF_SECONDS: int = 5
 
    # --- Cost protection (Phase 6 / production addendum) ---
    # A hard ceiling on chunks-per-job is the single most effective guard
    # against one user accidentally (or deliberately) generating a huge
    # AI bill from one oversized upload.
    MAX_CHUNKS_PER_TRANSLATION_JOB: int = 500
    # Second layer of protection: even small books can't be spammed
    # endlessly — caps jobs per user per day regardless of book size.
    MAX_TRANSLATION_JOBS_PER_USER_PER_DAY: int = 10
    # Rough cost estimate shown to the user before they confirm — not
    # billed anywhere, purely informational. Adjust to your actual
    # provider's real per-1K-token pricing.
    ESTIMATED_COST_PER_1K_TOKENS_USD: float = 0.01
 
    @field_validator("ALLOWED_UPLOAD_EXTENSIONS", mode="before")
    @classmethod
    def split_extensions(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [ext.strip().lower() for ext in v.split(",") if ext.strip()]
        return v

    # def get_allowed_upload_extensions(self) -> List[str]:
    #    if not self.ALLOWED_UPLOAD_EXTENSIONS:
    #       return []

    #    raw_value = self.ALLOWED_UPLOAD_EXTENSIONS.strip()
    #    if raw_value.startswith("[") and raw_value.endswith("]"):
    #         raw_value = raw_value[1:-1]
    #         return [
    #         item.strip().strip("\"'").lower()
    #         for item in raw_value.split(",")
    #         if item.strip()
    #     ]

    # --- AI providers (used from Phase 6 onward) ---
    OPENAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    AZURE_SPEECH_KEY: str = ""

    # --- CORS ---
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200", 
        "http://localhost:8080"
        ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, v):
        # Allows CORS_ORIGINS to be supplied as a comma-separated string
        # in the .env file, e.g. CORS_ORIGINS=http://a.com,http://b.com
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # def get_cors_origins(self) -> List[str]:
    #     if not self.CORS_ORIGINS:
    #         return []

    #     raw_value = self.CORS_ORIGINS.strip()
    #     if raw_value.startswith("[") and raw_value.endswith("]"):
    #         raw_value = raw_value[1:-1]

    #     return [origin.strip().strip("\"'") for origin in raw_value.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is parsed only once per process."""
    return Settings()


settings = get_settings()