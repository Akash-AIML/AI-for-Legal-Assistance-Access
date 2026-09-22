# ---------------------------------------------------------------------------
# Environment-driven configuration. All LLM/embedding calls use an
# OpenAI-compatible base URL, so the system works with any compatible provider.
# ---------------------------------------------------------------------------
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI-compatible provider
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    openai_audio_model: str = "whisper-1"

    # Force offline demo (deterministic embeddings + stub chat). When false,
    # the real OpenAI-compatible provider (base_url + key) is used.
    llm_offline: bool = False

    # Store / persistence
    chroma_dir: str = "./data/chroma"
    collection_name: str = "legal_docs"
    db_path: str = "./data/sessions.db"

    # Retrieval tuning
    dense_k: int = 10
    bm25_k: int = 10
    final_k: int = 5

    # Security
    jwt_secret: str = "compliance-ai-secret-key-production-change-me-32b"
    jwt_expire_minutes: int = 480
    environment: str = "development"

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        if len(v) < 32:
            raise ValueError("JWT secret must be at least 32 characters long.")
        if info.data.get("environment") == "production" and v in {
            "compliance-ai-secret-key-production-change-me-32b",
            "super-secret-key",
            "secret",
        }:
            raise ValueError("Insecure default JWT secret cannot be used in production.")
        return v

    # Optional local cross-encoder reranker (heavy; off by default)
    local_reranker: bool = False

    # Feature toggles
    enable_streaming: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()