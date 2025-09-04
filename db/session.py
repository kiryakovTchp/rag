import os
from contextvars import ContextVar

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL and DATABASE_URL.startswith("postgresql"), "Postgres required"

# Current tenant context for RLS policies
current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)


def set_current_tenant(tenant_id: str | None) -> None:
    """Set current tenant id for the lifetime of the request/session."""
    current_tenant.set(tenant_id)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"options": "-csearch_path=app,public"},
)

# Register pgvector adapter
try:
    from pgvector.psycopg import register_vector  # type: ignore

    @event.listens_for(engine, "connect")
    def _register_vector(dbapi_conn, conn_record):  # type: ignore[no-redef]
        # Be resilient to driver mismatch; only best-effort register
        try:
            register_vector(dbapi_conn)  # psycopg3 connection
        except Exception:
            # For psycopg2, registration isn't required for basic operations
            pass

except ImportError:
    # Optional optimization; skip if not available
    pass


@event.listens_for(engine, "begin")
def set_rls_tenant(conn):
    """Set app.current_tenant for each new transaction based on contextvar."""
    tenant_id = current_tenant.get()
    # Only set when tenant is explicitly provided to avoid overhead on public endpoints
    if tenant_id:
        # Use SET LOCAL so it applies only for the current transaction
        conn.execute(
            text("SET LOCAL app.current_tenant = :tenant_id"), {"tenant_id": tenant_id}
        )


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
