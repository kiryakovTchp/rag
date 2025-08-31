import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from dotenv import load_dotenv
from fastapi import FastAPI

from api.routers.health import router as health_router
from api.routers.ingest import router as ingest_router
from api.routers.query import router as query_router

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI(title="PromoAI RAG API")

app.include_router(health_router, prefix="")
app.include_router(ingest_router, prefix="")
app.include_router(query_router, prefix="")

# Include admin router only if explicitly enabled
if os.getenv("ADMIN_API_ENABLED", "false").lower() == "true":
    admin_token = os.getenv("ADMIN_API_TOKEN")
    if not admin_token:
        raise ValueError("ADMIN_API_ENABLED=true requires ADMIN_API_TOKEN to be set")
    
    from api.routers.admin import router as admin_router
    app.include_router(admin_router, prefix="")
