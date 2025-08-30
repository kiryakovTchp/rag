#!/bin/bash
set -euo pipefail

echo "Running S2 acceptance test..."

# Upload document
echo "Uploading document..."
curl -sf -X POST http://localhost:8000/ingest \
  -F "file=@tests/fixtures/simple.pdf" -F "tenant_id=test" -F "safe_mode=false" | tee .job.json

JOB=$(python3 - <<'PY'
import json; print(json.load(open(".job.json"))["job_id"])
PY
)

echo "Job ID: $JOB"

# Wait for processing
echo "Waiting for processing..."
for i in {1..90}; do
  curl -sf http://localhost:8000/ingest/$JOB | tee .st.json
  if grep -q '"status": *"done"' .st.json; then
    echo "Processing completed in $i seconds"
    break
  fi
  sleep 1
done

# Check embeddings
echo "Checking embeddings..."
python3 - <<'PY'
from db.session import SessionLocal
from db.models import Document, Chunk
from services.embed.provider import EmbeddingProvider
from services.index.pgvector import PGVectorIndex

db = SessionLocal()
doc = db.query(Document).order_by(Document.id.desc()).first()
print(f"Document ID: {doc.id}")

chs = db.query(Chunk).filter(Chunk.document_id == doc.id).all()
print(f"Chunks: {len(chs)}")

emb = EmbeddingProvider()
idx = PGVectorIndex()
vec = emb.embed_texts(["test query"])[0]
hits = idx.search(vec, top_k=3)
print(f"Search hits: {len(hits)}")
PY

# Test query API
echo "Testing query API..."
curl -sf -H "Content-Type: application/json" \
  -d '{"query":"test query","top_k":10,"rerank":false,"max_ctx":1800}' \
  http://localhost:8000/query | tee .query.json

MATCHES=$(jq '.matches | length' .query.json)
echo "Matches found: $MATCHES"

if [[ $MATCHES -gt 0 ]]; then
    echo "✅ ACCEPTED S2-4/5"
    exit 0
else
    echo "❌ FAILED S2-4/5: No matches found"
    exit 1
fi
