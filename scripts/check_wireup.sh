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

echo "✅ All services are ready!"
