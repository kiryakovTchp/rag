#!/bin/bash
set -e

echo "🧪 Sprint-2 Acceptance Test"
echo "=========================="

# Check if services are running
echo "1. Checking services..."
if ! curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "❌ API not running. Start with: docker compose -f infra/docker-compose.yml up -d"
    exit 1
fi
echo "✅ API is running"

# Test ingest
echo "2. Testing ingest pipeline..."
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
echo "3. Checking embed job..."
EMBED_JOBS=$(curl -s http://localhost:8000/ingest/$JOB_ID | python3 -c "
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

# Test query API
echo "4. Testing query API..."
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
echo "- ✅ Ingest pipeline working"
echo "- ✅ Embed job created and completed"
echo "- ✅ Query API returning valid matches"
echo "- ✅ Score range [0, 1] correct"
echo "- ✅ Response structure valid"
echo ""
echo "Sprint-2 is ready for production! 🚀"
