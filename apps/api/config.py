from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    NEXT_PUBLIC_SUPABASE_URL: str = "https://imbhymzwqyfpkdnjnqan.supabase.co"
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImltYmh5bXp3cXlmcGtkbmpucWFuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MTMyMTMsImV4cCI6MjEwNTM4OTIxM30."
        "YKtMo0_jjhvOd5iZlS3U6gmjsuzlMk36-RFEgSjJPiI"
    )
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "asia-south1"
    VERTEX_AI_GEMINI_FLASH_MODEL: str = "gemini-1.5-flash"
    VERTEX_AI_GEMINI_PRO_MODEL: str = "gemini-1.5-pro"
    VERTEX_AI_EMBEDDING_MODEL: str = "text-embedding-004"


@lru_cache
def get_settings() -> Settings:
    return Settings()
