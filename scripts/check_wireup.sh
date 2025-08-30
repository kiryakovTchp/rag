#!/bin/bash
set -e

echo "🔍 Checking service connectivity..."

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

echo "✅ All services and components are ready!"
