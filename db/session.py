import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL and DATABASE_URL.startswith(
    "postgresql"
), "Postgres required"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Register pgvector adapter
try:
    from pgvector.psycopg import register_vector

    @event.listens_for(engine, "connect")
    def _register_vector(dbapi_conn, conn_record):
        register_vector(dbapi_conn)

except ImportError:
    # pgvector not available, but we require it
    raise ImportError("pgvector is required for vector operations") from None

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
