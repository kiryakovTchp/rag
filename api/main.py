from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import init_settings
from api.metrics import metrics_endpoint
from api.middleware.auth import auth_middleware
from api.routers.answer import router as answer_router
from api.routers.auth import router as auth_router
from api.routers.chunks import router as chunks_router
from api.routers.feedback import router as feedback_router
from api.routers.health import router as health_router
from api.routers.ingest import router as ingest_router
from api.routers.oauth import router as oauth_router
from api.routers.query import router as query_router
from api.websocket import router as websocket_router

# OpenTelemetry temporarily disabled for stability
# from api.tracing import (
#     setup_tracing, instrument_fastapi, instrument_redis,
#     instrument_sqlalchemy, instrument_logging, metrics_middleware
# )

settings = init_settings()

app = FastAPI(title="PromoAI RAG API")

# OpenTelemetry temporarily disabled for stability
# setup_tracing()
# instrument_fastapi(app)
# instrument_redis()
# instrument_sqlalchemy()
# instrument_logging()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (required for OAuth state)
try:
    import os

    from starlette.middleware.sessions import SessionMiddleware  # type: ignore

    session_secret = os.getenv("SESSION_SECRET") or (
        settings.nextauth_secret or "dev_session_secret"
    )
    app.add_middleware(SessionMiddleware, secret_key=session_secret)
except Exception:
    # Non-fatal in environments without sessions or missing dependency
    pass

# Add auth middleware to store user in request.state
app.middleware("http")(auth_middleware)

# Add rate limiting middleware (temporarily disabled for testing)
# app.middleware("http")(rate_limit_middleware)

# Add metrics middleware
# app.middleware("http")(metrics_middleware)  # OpenTelemetry temporarily disabled

app.include_router(health_router, prefix="")
app.include_router(ingest_router, prefix="")
app.include_router(query_router, prefix="")
app.include_router(answer_router, prefix="")
app.include_router(websocket_router, prefix="")
app.include_router(auth_router, prefix="")
app.include_router(feedback_router, prefix="")
app.include_router(oauth_router, prefix="")
app.include_router(chunks_router, prefix="")

# Add metrics endpoint
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

# Include admin router only if explicitly enabled
if settings.admin_api_enabled:
    admin_token = settings.admin_api_token
    if not admin_token:
        raise ValueError("ADMIN_API_ENABLED=true requires ADMIN_API_TOKEN to be set")

    from api.routers.admin import router as admin_router

    app.include_router(admin_router, prefix="")
