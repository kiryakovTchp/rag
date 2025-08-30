#!/bin/bash
set -euo pipefail

echo "🔍 Checking Sprint-2 wireup..."

# 1) Check for SQLite traces (forbidden)
echo "1. Checking for SQLite traces..."
if git grep -nE 'sqlite|aiosqlite|:memory:|check_same_thread|StaticPool' -- api/ services/ workers/ db/ storage/ 2>/dev/null; then
    echo "❌ SQLite traces found in production code"
    exit 1
fi
echo "✅ No SQLite traces found"

# 2) Check pgvector extension
echo "2. Checking pgvector extension..."
if ! psql -U postgres -d postgres -tAc "\dx" | grep -qE '^\s*vector\s'; then
    echo "❌ pgvector extension missing"
    exit 1
fi
echo "✅ pgvector extension found"

# 3) Check vector(1024) column type
echo "3. Checking embeddings.vector column type..."
if ! psql -U postgres -d postgres -tAc "\d+ embeddings" | grep -q "vector(1024)"; then
    echo "❌ embeddings.vector is not vector(1024)"
    exit 1
fi
echo "✅ embeddings.vector is vector(1024)"

# 4) Check ivfflat index with vector_cosine_ops
echo "4. Checking ivfflat index..."
if ! psql -U postgres -d postgres -tAc "\d+ embeddings" | grep -q "USING ivfflat"; then
    echo "❌ ivfflat index missing"
    exit 1
fi

if ! psql -U postgres -d postgres -tAc "\d+ embeddings" | grep -q "vector_cosine_ops"; then
    echo "❌ ivfflat without vector_cosine_ops"
    exit 1
fi
echo "✅ ivfflat index with vector_cosine_ops found"

# 5) Check PostgreSQL connection
echo "5. Checking PostgreSQL connection..."
python3 -c "
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg://postgres:postgres@localhost:5432/postgres')
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        version = result.scalar()
        if 'PostgreSQL' in version:
            print('✅ PostgreSQL connection: OK')
        else:
            print('❌ Not PostgreSQL')
            exit(1)
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    exit(1)
"

# 6) Check Redis connection
echo "6. Checking Redis connection..."
python3 -c "
import redis
import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    r = redis.from_url(REDIS_URL)
    r.ping()
    print('✅ Redis connection: OK')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
"

# 7) Check S3/MinIO connection
echo "7. Checking S3/MinIO connection..."
python3 -c "
import boto3
import os

S3_ENDPOINT = os.getenv('S3_ENDPOINT', 'http://localhost:9000')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY_ID', 'minio')
S3_SECRET_KEY = os.getenv('S3_SECRET_ACCESS_KEY', 'minio123')
S3_BUCKET = os.getenv('S3_BUCKET', 'promoai')

try:
    s3 = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY
    )
    s3.head_bucket(Bucket=S3_BUCKET)
    print('✅ S3/MinIO connection: OK')
except Exception as e:
    print(f'❌ S3/MinIO connection failed: {e}')
    exit(1)
"

# 8) Check Celery tasks
echo "8. Checking Celery tasks..."
python3 -c "
try:
    from workers.tasks.parse import parse_document
    print('✅ parse_document task: OK')
except Exception as e:
    print(f'❌ parse_document task: {e}')
    exit(1)
"

python3 -c "
try:
    from workers.tasks.chunk import chunk_document
    print('✅ chunk_document task: OK')
except Exception as e:
    print(f'❌ chunk_document task: {e}')
    exit(1)
"

python3 -c "
try:
    from workers.tasks.embed import embed_document
    print('✅ embed_document task: OK')
except Exception as e:
    print(f'❌ embed_document task: {e}')
    exit(1)
"

# 9) Check embedding services
echo "9. Checking embedding services..."
python3 -c "
try:
    from services.embed.provider import EmbeddingProvider
    from services.index.pgvector import PGVectorIndex
    print('✅ Embedding services: OK')
except Exception as e:
    print(f'❌ Embedding services: {e}')
    exit(1)
"

# 10) Check WorkersAIEmbedder (should fail without token)
echo "10. Checking WorkersAIEmbedder..."
python3 -c "
try:
    from services.embed.workers_ai import WorkersAIEmbedder
    embedder = WorkersAIEmbedder()
    print('❌ WorkersAIEmbedder should fail without token')
    exit(1)
except ValueError as e:
    if 'WORKERS_AI_TOKEN' in str(e):
        print('✅ WorkersAIEmbedder: properly configured (requires token)')
    else:
        print(f'❌ WorkersAIEmbedder: {e}')
        exit(1)
except Exception as e:
    print(f'❌ WorkersAIEmbedder: {e}')
    exit(1)
"

echo "✅ Sprint-2 wireup check passed!"
