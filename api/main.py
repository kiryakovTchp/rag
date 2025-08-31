import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.routers.health import router as health_router
from api.routers.ingest import router as ingest_router
from api.routers.query import router as query_router
from api.routers.answer import router as answer_router
from api.routers.websocket import router as websocket_router
from api.routers.feedback import router as feedback_router
from api.websocket import router as websocket_router
from api.metrics import metrics_endpoint

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI(title="PromoAI RAG API")

# Configure CORS
frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="")
app.include_router(ingest_router, prefix="")
app.include_router(query_router, prefix="")
app.include_router(answer_router, prefix="")
app.include_router(websocket_router, prefix="")
app.include_router(feedback_router, prefix="")
app.include_router(websocket_router, prefix="")

# Add metrics endpoint
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

# Include admin router only if explicitly enabled
if os.getenv("ADMIN_API_ENABLED", "false").lower() == "true":
    admin_token = os.getenv("ADMIN_API_TOKEN")
    if not admin_token:
        raise ValueError("ADMIN_API_ENABLED=true requires ADMIN_API_TOKEN to be set")
    
    from api.routers.admin import router as admin_router
    app.include_router(admin_router, prefix="")
