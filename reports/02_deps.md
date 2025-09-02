# PASS 1 — DEPENDENCIES

## Current Dependencies Analysis

### Core Dependencies
| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `fastapi` | `0.115.0` | Web framework | ✅ Stable |
| `uvicorn[standard]` | `0.32.0` | ASGI server | ✅ Stable |
| `pydantic` | `2.8.0` | Data validation | ✅ Stable |
| `sqlalchemy` | `2.0.23` | ORM | ✅ Stable |
| `psycopg[binary]` | `3.1.13` | PostgreSQL driver | ✅ Stable |
| `pgvector` | `0.2.4` | Vector extension | ✅ Stable |
| `redis` | `5.0.1` | Redis client | ✅ Stable |
| `celery` | `5.3.4` | Task queue | ✅ Stable |

### ML/AI Dependencies - HIGH RISK
| Package | Version | Purpose | Risk Level | Issue |
|---------|---------|---------|------------|-------|
| `sentence-transformers` | `2.0.0` | Text embeddings | 🔴 HIGH | Version conflict with huggingface-hub |
| `transformers` | `4.21.3` | HuggingFace models | 🟡 MEDIUM | May conflict with sentence-transformers |
| `huggingface-hub` | `0.10.1` | Model hub | 🔴 HIGH | Incompatible with sentence-transformers 2.0.0 |
| `numpy` | `1.24.4` | Numerical computing | 🟡 MEDIUM | Version constraint conflicts |

### Document Processing Dependencies
| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `unstructured` | `0.18.3` | Document parsing | ✅ Stable |
| `camelot-py` | `1.0.9` | Table extraction | ✅ Stable |
| `pandas` | `2.2.2` | Data manipulation | ✅ Stable |
| `pdfplumber` | `0.11.7` | PDF parsing | ✅ Stable |
| `pymupdf4llm` | `0.0.1` | PDF processing | ✅ Stable |

## Version Conflicts Identified

### Critical Conflict: sentence-transformers ↔ huggingface-hub
```
sentence-transformers 2.0.0 requires huggingface-hub<0.8.0
huggingface-hub 0.10.1 is incompatible with sentence-transformers 2.0.0
```

**Root Cause**: Version mismatch between core ML packages
**Impact**: Import failures at startup, API container crashes
**Resolution**: Pin compatible versions or use lazy imports

### Transitive Dependencies Analysis
```
sentence-transformers 2.0.0
├── transformers>=4.6.0,<5.0.0
├── huggingface-hub<0.8.0
├── numpy>=1.17.0
└── torch>=1.6.0

huggingface-hub 0.10.1
├── numpy>=1.17.0
├── requests>=2.17.0
└── typing-extensions>=3.7.4
```

## Dependency Resolution Strategy

### Option 1: Downgrade sentence-transformers (RECOMMENDED)
```txt
sentence-transformers==2.0.2
huggingface-hub==0.8.1
transformers==4.21.3
numpy==1.24.4
```

**Pros**: Maintains current functionality, minimal changes
**Cons**: Older versions, potential security issues

### Option 2: Upgrade to latest compatible versions
```txt
sentence-transformers==2.2.2
huggingface-hub==0.19.4
transformers==4.35.0
numpy==1.24.4
```

**Pros**: Latest features, security updates
**Cons**: May introduce breaking changes

### Option 3: Remove ML dependencies (TEMPORARY)
```txt
# Comment out ML packages temporarily
# sentence-transformers==2.0.0
# transformers==4.21.3
# huggingface-hub==0.10.1
```

**Pros**: Immediate startup fix
**Cons**: Loses embedding functionality

## Constraints.txt Proposal

Create `constraints.txt` to lock transitive dependencies:

```txt
# Core constraints
numpy==1.24.4
pandas==2.2.2

# ML constraints
sentence-transformers==2.0.2
huggingface-hub==0.8.1
transformers==4.21.3
torch>=1.6.0,<2.0.0

# Document processing constraints
unstructured==0.18.3
camelot-py==1.0.9
pdfplumber==0.11.7
```

## Dockerfile Changes Required

### Current Issue
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

### Recommended Change
```dockerfile
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
```

## Immediate Action Items

### 1. Fix Version Conflicts (URGENT)
```bash
# Update requirements.txt
sed -i '' 's/sentence-transformers==2.0.0/sentence-transformers==2.0.2/' requirements.txt
sed -i '' 's/huggingface-hub==0.10.1/huggingface-hub==0.8.1/' requirements.txt
```

### 2. Create constraints.txt
```bash
pip install pip-tools
pip-compile requirements.txt --output-file constraints.txt
```

### 3. Update Dockerfiles
```dockerfile
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
```

## Verification Commands

### Test Dependency Resolution
```bash
# Test pip install locally
pip install -r requirements.txt

# Test with constraints
pip install -r requirements.txt -c constraints.txt
```

### Test Import Chain
```bash
# Test critical imports
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
python -c "from huggingface_hub import hf_hub_url; print('OK')"
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Version conflicts | HIGH | HIGH | Use constraints.txt |
| Breaking changes | MEDIUM | MEDIUM | Pin major versions |
| Security vulnerabilities | LOW | HIGH | Regular updates |
| Startup failures | HIGH | HIGH | Lazy imports |

## Next Steps

1. **Immediate**: Fix sentence-transformers version conflict
2. **Short-term**: Create constraints.txt for reproducible builds
3. **Medium-term**: Implement lazy imports for ML packages
4. **Long-term**: Establish dependency update pipeline
