from fastapi import FastAPI

from api.routers.health import router as health_router
from api.routers.ingest import router as ingest_router

app = FastAPI(title="PromoAI RAG API")

app.include_router(health_router, prefix="")
app.include_router(ingest_router, prefix="")
