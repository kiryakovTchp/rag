#!/bin/bash
set -euo pipefail

echo "🧪 Sprint-2 Acceptance Test"
echo "=========================="

# Check if services are running
echo "1. Checking services..."
if ! curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "❌ API not running. Start with: docker compose -f infra/docker-compose.yml up -d"
    exit 1
fi
echo "✅ API is running"

# Check pgvector setup
echo "2. Checking pgvector setup..."
if ! psql -U postgres -d postgres -tAc "\dx" | grep -qE '^\s*vector\s'; then
    echo "❌ pgvector extension missing"
    exit 1
fi
echo "✅ pgvector extension found"

if ! psql -U postgres -d postgres -tAc "\d+ embeddings" | grep -q "vector(1024)"; then
    echo "❌ embeddings.vector is not vector(1024)"
    exit 1
fi
echo "✅ embeddings.vector is vector(1024)"

if ! psql -U postgres -d postgres -tAc "\d+ embeddings" | grep -q "USING ivfflat"; then
    echo "❌ ivfflat index missing"
    exit 1
fi
echo "✅ ivfflat index found"

if ! psql -U postgres -d postgres -tAc "\d+ embeddings" | grep -q "vector_cosine_ops"; then
    echo "❌ ivfflat without vector_cosine_ops"
    exit 1
fi
echo "✅ ivfflat with vector_cosine_ops found"

# Check for SQLite traces
echo "3. Checking for SQLite traces..."
if git grep -nE 'sqlite|aiosqlite|:memory:|check_same_thread|StaticPool' -- api/ services/ workers/ db/ storage/ 2>/dev/null; then
    echo "❌ SQLite traces found in production code"
    exit 1
fi
echo "✅ No SQLite traces found"

# Test ingest pipeline
echo "4. Testing ingest pipeline..."
echo "   Uploading README.md..."

# Create a test README if it doesn't exist
if [ ! -f "test_readme.md" ]; then
    cat > test_readme.md << 'EOF'
# Test Document

This is a test document for Sprint-2 acceptance testing.

## Features

- Document processing
- Vector embeddings
- Semantic search
- Query API

## Architecture

The system uses PostgreSQL with pgvector for vector storage and BGE-M3 for embeddings.
EOF
fi

# Upload document
INGEST_RESPONSE=$(curl -s -F "file=@test_readme.md" -F "tenant_id=test" -F "safe_mode=false" http://localhost:8000/ingest)
JOB_ID=$(echo $INGEST_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

echo "   Job ID: $JOB_ID"

# Wait for processing
echo "   Waiting for processing..."
for i in {1..60}; do
    STATUS_RESPONSE=$(curl -s http://localhost:8000/ingest/$JOB_ID)
    STATUS=$(echo $STATUS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    
    if [ "$STATUS" = "done" ]; then
        echo "   ✅ Processing completed"
        break
    elif [ "$STATUS" = "error" ]; then
        ERROR=$(echo $STATUS_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'Unknown error'))")
        echo "   ❌ Processing failed: $ERROR"
        exit 1
    fi
    
    if [ $i -eq 60 ]; then
        echo "   ❌ Processing timeout"
        exit 1
    fi
    
    sleep 1
done

# Check for embed job
    # Wait for embed job to complete using document status
    echo "5. Checking embed job..."
    DOCUMENT_ID=$(curl -s http://localhost:8000/ingest/$JOB_ID | python3 -c "
    import sys, json
    data = json.load(sys.stdin)
    print(data.get('document_id', ''))
    ")

    if [ -z "$DOCUMENT_ID" ]; then
        echo "   ❌ No document_id found"
        exit 1
    fi

    EMBED_JOBS=$(curl -s http://localhost:8000/ingest/document/$DOCUMENT_ID | python3 -c "
    import sys, json
    data = json.load(sys.stdin)
    jobs = data.get('jobs', [])
    embed_jobs = [j for j in jobs if j.get('type') == 'embed']
    print(len(embed_jobs))
    ")

    if [ "$EMBED_JOBS" -gt 0 ]; then
        echo "   ✅ Embed job created"
    else
        echo "   ❌ No embed job found"
        exit 1
    fi

    # Wait for embed job to complete
    echo "   Waiting for embed job to complete..."
    for i in {1..60}; do
        STATUS_RESPONSE=$(curl -s http://localhost:8000/ingest/document/$DOCUMENT_ID)
        EMBED_STATUS=$(echo $STATUS_RESPONSE | python3 -c "
    import sys, json
    data = json.load(sys.stdin)
    jobs = data.get('jobs', [])
    embed_jobs = [j for j in jobs if j.get('type') == 'embed']
    if embed_jobs:
        print(embed_jobs[0].get('status', 'unknown'))
    else:
        print('not_found')
    ")

        if [ "$EMBED_STATUS" = "done" ]; then
            echo "   ✅ Embed job completed"
            break
        elif [ "$EMBED_STATUS" = "error" ]; then
            echo "   ❌ Embed job failed"
            exit 1
        fi

        if [ $i -eq 60 ]; then
            echo "   ❌ Embed job timeout"
            exit 1
        fi

        sleep 1
    done

# Test PGVectorIndex directly
echo "6. Testing PGVectorIndex directly..."
python3 -c "
import os
import numpy as np
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex

# Set environment
os.environ['DATABASE_URL'] = 'postgresql+psycopg://postgres:postgres@localhost:5432/postgres'
os.environ['EMBED_PROVIDER'] = 'local'

# Test embedding and search
embedder = EmbeddingProvider()
index = PGVectorIndex()

# Test query
query_text = 'test document'
query_embedding = embedder.embed_single(query_text)

# Search
results = index.search(query_embedding, top_k=5)

if len(results) > 0:
    print(f'✅ PGVectorIndex.search returned {len(results)} results')
    chunk_id, score = results[0]
    print(f'   Top result: chunk_id={chunk_id}, score={score:.3f}')
else:
    print('❌ PGVectorIndex.search returned no results')
    exit(1)
"

# Test query API
echo "7. Testing query API..."
QUERY_RESPONSE=$(curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test document",
    "top_k": 5,
    "rerank": false,
    "max_ctx": 1000
  }')

echo "   Query response received"

# Check response structure
MATCHES_COUNT=$(echo $QUERY_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
matches = data.get('matches', [])
print(len(matches))
")

if [ "$MATCHES_COUNT" -ge 3 ]; then
    echo "   ✅ Found $MATCHES_COUNT matches (>= 3 required)"
else
    echo "   ❌ Only $MATCHES_COUNT matches found (need >= 3)"
    exit 1
fi

# Check match structure
FIRST_MATCH=$(echo $QUERY_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
matches = data.get('matches', [])
if matches:
    match = matches[0]
    print(f\"doc_id:{match.get('doc_id')}, chunk_id:{match.get('chunk_id')}, score:{match.get('score')}\")
else:
    print('no_matches')
")

if [ "$FIRST_MATCH" != "no_matches" ]; then
    echo "   ✅ Match structure: $FIRST_MATCH"
else
    echo "   ❌ No matches in response"
    exit 1
fi

# Check score range
SCORE=$(echo $FIRST_MATCH | cut -d',' -f3 | cut -d':' -f2)
if (( $(echo "$SCORE >= 0.0 && $SCORE <= 1.0" | bc -l) )); then
    echo "   ✅ Score $SCORE is in valid range [0, 1]"
else
    echo "   ❌ Score $SCORE is outside valid range [0, 1]"
    exit 1
fi

# Check all required fields
REQUIRED_FIELDS=$(echo $QUERY_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
matches = data.get('matches', [])
if matches:
    match = matches[0]
    required = ['doc_id', 'chunk_id', 'page', 'score', 'snippet', 'breadcrumbs']
    missing = [field for field in required if field not in match]
    if missing:
        print(f'Missing fields: {missing}')
    else:
        print('all_fields_present')
else:
    print('no_matches')
")

if [ "$REQUIRED_FIELDS" = "all_fields_present" ]; then
    echo "   ✅ All required fields present"
else
    echo "   ❌ Missing fields: $REQUIRED_FIELDS"
    exit 1
fi

# Check usage
USAGE=$(echo $QUERY_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
usage = data.get('usage', {})
print(f\"in_tokens:{usage.get('in_tokens', 0)}, out_tokens:{usage.get('out_tokens', 0)}\")
")

echo "   ✅ Usage: $USAGE"

echo ""
echo "🎉 Sprint-2 Acceptance Test PASSED!"
echo "==================================="
echo ""
echo "Summary:"
echo "- ✅ pgvector extension and vector(1024) type"
echo "- ✅ ivfflat index with vector_cosine_ops"
echo "- ✅ No SQLite traces in code"
echo "- ✅ Ingest pipeline working"
echo "- ✅ Embed job created and completed"
echo "- ✅ PGVectorIndex.search returning results"
echo "- ✅ Query API returning valid matches"
echo "- ✅ Score range [0, 1] correct"
echo "- ✅ All required fields present"
echo ""
echo "Sprint-2 is ready for production! 🚀"
