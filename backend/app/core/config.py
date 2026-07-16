from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Anthropic
    anthropic_api_key: str = ""
    claude_model_fast: str = "claude-haiku-4-5-20251001"
    claude_model_smart: str = "claude-sonnet-5"

    # Auth
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Token encryption (for stored OAuth tokens)
    token_encryption_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://dad:dad@db:5432/dad"

    # Redis / arq
    redis_url: str = "redis://redis:6379/0"

    # Job execution backend: "arq" (Redis + worker) or "inline" (in-process background tasks,
    # no Redis/worker — used for free/serverless deploys).
    job_mode: str = "arq"

    # Brute-force rate limiting on auth endpoints (disabled in tests).
    rate_limit_enabled: bool = True

    # Storage: "local" (filesystem, ephemeral on free hosts) or "supabase" (durable object storage)
    storage_backend: str = "local"
    upload_dir: str = "/data/uploads"
    # Supabase Storage (used when storage_backend == "supabase")
    supabase_url: str = ""  # e.g. https://<project-ref>.supabase.co
    supabase_service_role_key: str = ""  # secret — server-side only
    supabase_storage_bucket: str = "dad-files"

    # Web Push (VAPID). If keys are empty, push is disabled (in-app notifications still work).
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@dad.app"

    # Email OAuth (Phase 4)
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    ms_client_id: str = ""
    ms_client_secret: str = ""

    # Used to build OAuth redirect URIs and the post-connect redirect back to the SPA.
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
