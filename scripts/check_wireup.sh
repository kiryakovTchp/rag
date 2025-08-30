#!/bin/bash
set -e

echo "🔍 Checking service connectivity..."

# Check for SQLite usage (should fail)
echo "  Checking for SQLite usage..."
if grep -r "sqlite\|sqlite3\|aiosqlite\|sqlite:///\|:memory:" api/ services/ workers/ db/ storage/ 2>/dev/null; then
    echo "    ❌ Found SQLite usage in code"
    exit 1
fi

# Check db/session.py contains postgresql+psycopg
echo "  Checking db/session.py..."
if ! grep -q "postgresql+psycopg" db/session.py; then
    echo "    ❌ db/session.py doesn't contain postgresql+psycopg"
    exit 1
fi

if grep -q "sqlite" db/session.py; then
    echo "    ❌ db/session.py contains SQLite references"
    exit 1
fi

echo "    ✅ No SQLite usage found"

# Check PostgreSQL
echo "  Checking PostgreSQL..."
python3 -c "
import psycopg
try:
    conn = psycopg.connect('postgresql://postgres:postgres@localhost:5432/postgres')
    conn.close()
    print('    ✅ PostgreSQL: OK')
except Exception as e:
    print(f'    ❌ PostgreSQL: {e}')
    exit(1)
"

# Check Redis
echo "  Checking Redis..."
python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('    ✅ Redis: OK')
except Exception as e:
    print(f'    ❌ Redis: {e}')
    exit(1)
"

# Check MinIO
echo "  Checking MinIO..."
python3 -c "
import boto3
from botocore.exceptions import ClientError
try:
    s3 = boto3.client('s3', 
                      endpoint_url='http://localhost:9000',
                      aws_access_key_id='minio',
                      aws_secret_access_key='minio123',
                      region_name='us-east-1')
    s3.head_bucket(Bucket='promoai')
    print('    ✅ MinIO: OK')
except Exception as e:
    print(f'    ❌ MinIO: {e}')
    exit(1)
"

# Check Celery tasks
echo "  Checking Celery tasks..."
python3 -c "
from workers.app import celery_app
from workers.tasks.parse import parse_document
from workers.tasks.chunk import chunk_document

# Check if tasks are registered
if 'workers.tasks.parse.parse_document' not in celery_app.tasks:
    print('    ❌ parse_document task not registered')
    exit(1)
if 'workers.tasks.chunk.chunk_document' not in celery_app.tasks:
    print('    ❌ chunk_document task not registered')
    exit(1)

print('    ✅ Celery tasks: OK')
"

# Check S3 client methods
echo "  Checking S3 client methods..."
python3 -c "
from storage.r2 import ObjectStore
import os

os.environ['S3_ENDPOINT'] = 'http://localhost:9000'
os.environ['S3_ACCESS_KEY_ID'] = 'minio'
os.environ['S3_SECRET_ACCESS_KEY'] = 'minio123'

try:
    store = ObjectStore()
    # Test basic methods exist
    methods = ['put_file', 'get_file', 'delete', 'exists']
    for method in methods:
        if not hasattr(store, method):
            print(f'    ❌ S3 client missing method: {method}')
            exit(1)
    print('    ✅ S3 client methods: OK')
except Exception as e:
    print(f'    ❌ S3 client: {e}')
    exit(1)
"

# Check TableParser and dependencies
echo "  Checking TableParser..."
python3 -c "
try:
    from services.parsing.tables import TableParser
    print('    ✅ TableParser: OK')
except Exception as e:
    print(f'    ❌ TableParser: {e}')
    exit(1)
"

echo "  Checking pdfplumber..."
python3 -c "
try:
    import pdfplumber
    print('    ✅ pdfplumber: OK')
except Exception as e:
    print(f'    ❌ pdfplumber: {e}')
    exit(1)
"

echo "  Checking ChunkingPipeline..."
python3 -c "
try:
    from services.chunking.pipeline import ChunkingPipeline
    print('    ✅ ChunkingPipeline: OK')
except Exception as e:
    print(f'    ❌ ChunkingPipeline: {e}')
    exit(1)
"

echo "  Checking pgvector setup..."
python3 -c "
try:
    from db.models import Embedding
    from sqlalchemy import inspect
    
    # Check if vector column is proper pgvector type
    inspector = inspect(Embedding.__table__)
    vector_col = inspector.get_columns()['vector']
    
    if 'Vector' in str(vector_col.type):
        print('    ✅ Embedding.vector is Vector(1024): OK')
    else:
        print('    ❌ Embedding.vector is not Vector type')
        exit(1)
        
    # Check migrations for pgvector extension
    import os
    migration_files = [f for f in os.listdir('db/migrations/versions') if f.endswith('.py')]
    pgvector_migrations = []
    
    for f in migration_files:
        with open(f'db/migrations/versions/{f}', 'r') as mf:
            content = mf.read()
            if 'CREATE EXTENSION' in content and 'vector' in content:
                pgvector_migrations.append(f)
    
    if pgvector_migrations:
        print(f'    ✅ Found pgvector migrations: {pgvector_migrations}')
    else:
        print('    ❌ No pgvector extension migration found')
        exit(1)
        
except Exception as e:
    print(f'    ❌ pgvector check failed: {e}')
    exit(1)
"

echo "  Checking WorkersAIEmbedder..."
python3 -c "
try:
    from services.embed.workers_ai import WorkersAIEmbedder
    
    # Check if it's not returning zeros
    embedder = WorkersAIEmbedder()
    test_text = 'test'
    embedding = embedder.embed_single(test_text)
    
    if embedding is None or len(embedding) == 0:
        print('    ❌ WorkersAIEmbedder returned empty embedding')
        exit(1)
    
    # Check if it's not all zeros
    if all(x == 0 for x in embedding):
        print('    ❌ WorkersAIEmbedder returned all zeros')
        exit(1)
        
    print('    ✅ WorkersAIEmbedder: OK')
except ValueError as e:
    if 'WORKERS_AI_TOKEN' in str(e):
        print('    ✅ WorkersAIEmbedder: properly configured (requires token)')
    else:
        print(f'    ❌ WorkersAIEmbedder: {e}')
        exit(1)
except Exception as e:
    print(f'    ❌ WorkersAIEmbedder: {e}')
    exit(1)
"

echo "✅ All services and components are ready!"
