import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use SQLite for local development if PostgreSQL is not available
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
