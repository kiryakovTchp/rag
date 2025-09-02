import os
import sys
from collections.abc import Generator
from pathlib import Path

import redis

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent.parent))

# Lazy imports to prevent startup failures
# from db.session import SessionLocal
# from storage.r2 import ObjectStore


# Database dependency
def get_db() -> Generator:
    """Get database session with lazy import."""
    try:
        from db.session import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        # Log the error but don't fail startup
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database connection failed: {e}")
        raise


# Redis dependency
def get_redis() -> redis.Redis:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(redis_url)


# S3 Storage dependency
def get_storage():
    """Get storage with lazy import."""
    try:
        from storage.r2 import ObjectStore
        return ObjectStore()
    except Exception as e:
        # Log the error but don't fail startup
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Storage initialization failed: {e}")
        raise
