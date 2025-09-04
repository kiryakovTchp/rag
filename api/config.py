import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    cors_origins: List[str]
    admin_api_enabled: bool
    admin_api_token: Optional[str]
    rerank_enabled: bool
    embed_provider: str
    require_auth: bool
    nextauth_secret: Optional[str]
    # Auth / tokens
    jwt_secret_key: Optional[str]
    session_secret: Optional[str]

    # Connections
    database_url: Optional[str]
    redis_url: Optional[str]

    # S3 / MinIO
    s3_endpoint: Optional[str]
    s3_region: Optional[str]
    s3_bucket: Optional[str]
    s3_access_key_id: Optional[str]
    s3_secret_access_key: Optional[str]

    # Workers AI (embeddings + rerank)
    workers_ai_token: Optional[str]
    workers_ai_url: Optional[str]
    workers_ai_rerank_url: Optional[str]
    workers_ai_api_key: Optional[str]

    # Ollama
    ollama_host: Optional[str]
    ollama_embed_model: Optional[str]

    # Google / OAuth
    google_client_id: Optional[str]
    google_client_secret: Optional[str]
    google_redirect_uri: Optional[str]
    google_api_key: Optional[str]


def load_settings(env_path: Optional[Path] = None) -> Settings:
    """Load application settings from environment variables."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    return Settings(
        cors_origins=os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(","),
        admin_api_enabled=os.getenv("ADMIN_API_ENABLED", "false").lower() == "true",
        admin_api_token=os.getenv("ADMIN_API_TOKEN"),
        rerank_enabled=os.getenv("RERANK_ENABLED", "false").lower() == "true",
        embed_provider=os.getenv("EMBED_PROVIDER", "ollama"),
        require_auth=os.getenv("REQUIRE_AUTH", "true").lower() == "true",
        nextauth_secret=os.getenv("NEXTAUTH_SECRET"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
        session_secret=os.getenv("SESSION_SECRET"),
        database_url=os.getenv("DATABASE_URL"),
        redis_url=os.getenv("REDIS_URL"),
        s3_endpoint=os.getenv("S3_ENDPOINT"),
        s3_region=os.getenv("S3_REGION"),
        s3_bucket=os.getenv("S3_BUCKET"),
        s3_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
        s3_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
        workers_ai_token=os.getenv("WORKERS_AI_TOKEN"),
        workers_ai_url=os.getenv(
            "WORKERS_AI_URL",
            "https://api.cloudflare.com/client/v4/ai/run/@cf/baai/bge-m3",
        ),
        workers_ai_rerank_url=os.getenv("WORKERS_AI_RERANK_URL"),
        workers_ai_api_key=os.getenv("WORKERS_AI_API_KEY"),
        ollama_host=os.getenv("OLLAMA_HOST"),
        ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large"),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        google_redirect_uri=os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
        ),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


_settings: Optional[Settings] = None


def init_settings(env_path: Optional[Path] = None) -> Settings:
    """Initialize and cache settings object."""
    global _settings
    _settings = load_settings(env_path)
    return _settings


def get_settings() -> Settings:
    """Return cached settings; load if uninitialized."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
