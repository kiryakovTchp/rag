# PASS 2 — IMPORTS & LAZY LOADING

## Heavy Imports Analysis

### Critical Import Chain Causing Startup Failures

#### 1. API Startup Import Chain
```
api/main.py:11 → api/routers/query.py:11 → services/retrieve/hybrid.py:9 → 
services/embed/provider.py:8 → services/embed/bge_m3.py:6 → sentence_transformers
```

**File**: `api/main.py:11`
**Import**: `from api.routers.query import router as query_router`
**Impact**: Triggers entire ML dependency chain at startup

#### 2. Worker Startup Import Chain
```
workers/app.py:4 → workers/tracing.py:12 → opentelemetry.exporter.otlp.proto.grpc.trace_exporter
```

**File**: `workers/app.py:4`
**Import**: `from workers.tracing import setup_tracing, instrument_celery, instrument_redis, instrument_logging, TracedTask`
**Impact**: Triggers OpenTelemetry imports (currently disabled)

## Heavy Imports by Module

### API Service Imports
| File | Line | Import | Weight | Risk |
|------|------|--------|--------|------|
| `api/main.py` | 11 | `api.routers.query` | HIGH | 🔴 CRITICAL |
| `api/main.py` | 12 | `api.routers.ingest` | HIGH | 🔴 CRITICAL |
| `api/main.py` | 13 | `api.routers.answer` | HIGH | 🔴 CRITICAL |
| `api/main.py` | 14 | `api.websocket` | MEDIUM | 🟡 MEDIUM |
| `api/main.py` | 15 | `api.routers.auth` | LOW | 🟢 LOW |
| `api/main.py` | 16 | `api.routers.feedback` | LOW | 🟢 LOW |

### Services Layer Imports
| File | Line | Import | Weight | Risk |
|------|------|--------|--------|------|
| `services/retrieve/hybrid.py` | 9 | `services.embed.provider` | HIGH | 🔴 CRITICAL |
| `services/embed/provider.py` | 8 | `services.embed.bge_m3` | HIGH | 🔴 CRITICAL |
| `services/embed/bge_m3.py` | 6 | `sentence_transformers` | HIGH | 🔴 CRITICAL |
| `services/ingest/service.py` | 11 | `workers.tasks.parse` | MEDIUM | 🟡 MEDIUM |
| `workers/tasks/parse.py` | 13 | `workers.app` | LOW | 🟢 LOW |

### Worker Service Imports
| File | Line | Import | Weight | Risk |
|------|------|--------|--------|------|
| `workers/app.py` | 4 | `workers.tracing` | MEDIUM | 🟡 MEDIUM |
| `workers/tasks/parse.py` | 11 | `services.parsing.office` | MEDIUM | 🟡 MEDIUM |
| `workers/tasks/parse.py` | 12 | `services.parsing.pdf` | MEDIUM | 🟡 MEDIUM |
| `workers/tasks/parse.py` | 13 | `services.parsing.tables` | MEDIUM | 🟡 MEDIUM |

## Lazy Import Implementation

### 1. Critical Fix: services/embed/provider.py

**Current Code**:
```python
# Line 8 - Heavy import at module level
from services.embed.bge_m3 import BGEM3Embedder
```

**Proposed Fix**:
```python
class EmbeddingProvider:
    def __init__(self, provider: str = "workers_ai"):
        self.provider = provider
        self._local_embedder = None
    
    def _get_local_embedder(self):
        """Lazy load local embedder only when needed."""
        if self._local_embedder is None:
            try:
                from services.embed.bge_m3 import BGEM3Embedder
                self._local_embedder = BGEM3Embedder()
            except ImportError as e:
                raise ImportError(
                    "Local embeddings require sentence-transformers. "
                    "Set EMBED_PROVIDER=workers_ai or install dependencies."
                ) from e
        return self._local_embedder
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        if self.provider == "local":
            embedder = self._get_local_embedder()
            return embedder.embed_texts(texts)
        # ... rest of implementation
```

### 2. Critical Fix: services/retrieve/hybrid.py

**Current Code**:
```python
# Line 9 - Heavy import at module level
from services.embed.provider import EmbeddingProvider
```

**Proposed Fix**:
```python
class HybridRetriever:
    def __init__(self, embed_provider: str = "workers_ai"):
        self.embed_provider = embed_provider
        self._embedding_provider = None
    
    def _get_embedding_provider(self):
        """Lazy load embedding provider only when needed."""
        if self._embedding_provider is None:
            try:
                from services.embed.provider import EmbeddingProvider
                self._embedding_provider = EmbeddingProvider(self.embed_provider)
            except ImportError as e:
                raise ImportError(
                    "Embedding service unavailable. "
                    "Check EMBED_PROVIDER configuration."
                ) from e
        return self._embedding_provider
```

### 3. Critical Fix: api/routers/query.py

**Current Code**:
```python
# Line 11 - Heavy import at module level
from services.retrieve.hybrid import HybridRetriever
```

**Proposed Fix**:
```python
@router.post("/query")
async def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Query documents with lazy loading of heavy dependencies."""
    try:
        from services.retrieve.hybrid import HybridRetriever
        retriever = HybridRetriever(
            embed_provider=os.getenv("EMBED_PROVIDER", "workers_ai")
        )
        # ... rest of implementation
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Retrieval service temporarily unavailable"
        )
```

## Environment Variable Guards

### Add EMBED_PROVIDER Configuration

**File**: `env.example`
```bash
# Embedding Provider Selection
EMBED_PROVIDER=workers_ai  # workers_ai | local
EMBED_PROVIDER_FALLBACK=true  # Allow fallback to workers_ai if local fails
```

**File**: `docker-compose.yml`
```yaml
api:
  environment:
    - EMBED_PROVIDER=${EMBED_PROVIDER:-workers_ai}
    - EMBED_PROVIDER_FALLBACK=${EMBED_PROVIDER_FALLBACK:-true}
```

## Minimal Diffs for PASS 2

### Diff 1: services/embed/provider.py
```diff
 class EmbeddingProvider:
     def __init__(self, provider: str = "workers_ai"):
         self.provider = provider
+        self._local_embedder = None
     
+    def _get_local_embedder(self):
+        """Lazy load local embedder only when needed."""
+        if self._local_embedder is None:
+            try:
+                from services.embed.bge_m3 import BGEM3Embedder
+                self._local_embedder = BGEM3Embedder()
+            except ImportError as e:
+                raise ImportError(
+                    "Local embeddings require sentence-transformers. "
+                    "Set EMBED_PROVIDER=workers_ai or install dependencies."
+                ) from e
+        return self._local_embedder
     
     def embed_texts(self, texts: List[str]) -> np.ndarray:
         if self.provider == "local":
-            embedder = BGEM3Embedder()
+            embedder = self._get_local_embedder()
             return embedder.embed_texts(texts)
```

### Diff 2: services/retrieve/hybrid.py
```diff
 class HybridRetriever:
     def __init__(self, embed_provider: str = "workers_ai"):
         self.embed_provider = embed_provider
+        self._embedding_provider = None
     
+    def _get_embedding_provider(self):
+        """Lazy load embedding provider only when needed."""
+        if self._embedding_provider is None:
+            try:
+                from services.embed.provider import EmbeddingProvider
+                self._embedding_provider = EmbeddingProvider(self.embed_provider)
+            except ImportError as e:
+                raise ImportError(
+                    "Embedding service unavailable. "
+                    "Check EMBED_PROVIDER configuration."
+                ) from e
+        return self._embedding_provider
     
     def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
         # ... existing code ...
         if self.embed_provider == "local":
-            embeddings = self.embedding_provider.embed_texts([query])
+            embeddings = self._get_embedding_provider().embed_texts([query])
```

### Diff 3: api/routers/query.py
```diff
 @router.post("/query")
 async def query_documents(
     request: QueryRequest,
     db: Session = Depends(get_db)
 ):
     """Query documents with lazy loading of heavy dependencies."""
+    try:
+        from services.retrieve.hybrid import HybridRetriever
+        retriever = HybridRetriever(
+            embed_provider=os.getenv("EMBED_PROVIDER", "workers_ai")
+        )
+    except ImportError as e:
+        raise HTTPException(
+            status_code=503,
+            detail="Retrieval service temporarily unavailable"
+        )
     
-    retriever = HybridRetriever()
     # ... rest of implementation
```

## Verification Commands

### Test Lazy Imports
```bash
# Test API startup without ML dependencies
EMBED_PROVIDER=workers_ai python -c "
from api.main import app
print('API imports successfully')
"

# Test local embedder import (should fail gracefully)
EMBED_PROVIDER=local python -c "
from services.embed.provider import EmbeddingProvider
try:
    provider = EmbeddingProvider('local')
    print('Local embedder loaded')
except ImportError as e:
    print(f'Graceful failure: {e}')
"
```

## Impact Assessment

### Benefits
- ✅ **Immediate startup fix** - API starts without ML imports
- ✅ **Configurable behavior** - Choose embedding provider at runtime
- ✅ **Graceful degradation** - Service works with available providers
- ✅ **Maintains functionality** - No loss of features

### Risks
- 🟡 **Runtime failures** - Imports may fail when actually needed
- 🟡 **Error handling** - Need proper error messages for users
- 🟡 **Testing complexity** - Need to test both provider paths

## Next Steps

1. **Immediate**: Apply lazy import diffs to critical files
2. **Test**: Verify API starts with EMBED_PROVIDER=workers_ai
3. **Validate**: Test local embeddings when EMBED_PROVIDER=local
4. **Document**: Update setup instructions with EMBED_PROVIDER configuration
