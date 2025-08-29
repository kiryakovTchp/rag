import os
from collections.abc import Generator

import redis

from db.session import SessionLocal
from storage.r2 import ObjectStore


# Database dependency
def get_db() -> Generator[SessionLocal, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis dependency
def get_redis() -> redis.Redis:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(redis_url)


# S3 Storage dependency
def get_storage() -> ObjectStore:
    return ObjectStore()
