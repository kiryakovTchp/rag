# PASS 0 — REPO INVENTORY

## Repository Structure

### Core Services
- **API**: FastAPI/Uvicorn service (`api/`)
- **Worker**: Celery worker service (`workers/`)
- **Frontend**: React/Vite application (`web/`)
- **Database**: PostgreSQL with pgvector (`db/`)
- **Cache**: Redis (`redis/`)
- **Storage**: S3-compatible storage (`storage/`)

### Infrastructure
- **Docker**: Multi-service compose setup
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions workflows

## Module Inventory

### Python Modules
| Module | Purpose | Entry Point | Dependencies |
|--------|---------|-------------|--------------|
| `api/` | FastAPI web service | `api/main.py` | FastAPI, Uvicorn, SQLAlchemy |
| `workers/` | Celery background tasks | `workers/app.py` | Celery, Redis |
| `services/` | Business logic services | Various | ML libraries, DB, Storage |
| `db/` | Database models & migrations | `db/models.py` | SQLAlchemy, pgvector |
| `storage/` | S3 storage abstraction | `storage/r2.py` | boto3 |

### Binary Entry Points
| Binary | Service | Command | Port |
|--------|---------|---------|------|
| `uvicorn` | API | `uvicorn api.main:app --host 0.0.0.0 --port 8000` | 8000 |
| `celery` | Worker | `celery -A workers.app worker --loglevel=info` | N/A |
| `node` | Frontend | `npm run dev -- --host 0.0.0.0` | 3000 |

### Docker Services
| Service | Image | Ports | Health Check |
|---------|-------|-------|--------------|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | `pg_isready` |
| `redis` | `redis:7-alpine` | 6379 | `redis-cli ping` |
| `api` | Custom build | 8000 | `curl /health` |
| `worker` | Custom build | N/A | N/A |
| `frontend` | Custom build | 3000 | N/A |
| `prometheus` | `prom/prometheus:latest` | 9090 | N/A |
| `grafana` | `grafana/grafana:latest` | 3001 | N/A |

## Environment Variables

### Required Variables
| Variable | Default | Purpose | Used By |
|----------|---------|---------|---------|
| `DATABASE_URL` | `postgresql://rag_user:rag_password@localhost:5432/rag_db` | PostgreSQL connection | API, Worker |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection | API, Worker |
| `JWT_SECRET_KEY` | `your-super-secret-jwt-key-change-in-production` | JWT signing | API |
| `GOOGLE_CLIENT_ID` | `your-google-client-id` | OAuth authentication | API, Frontend |
| `GOOGLE_CLIENT_SECRET` | `your-google-client-secret` | OAuth authentication | API |

### Optional Variables
| Variable | Default | Purpose | Used By |
|----------|---------|---------|---------|
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8000` | CORS policy | API |
| `VITE_API_BASE_URL` | `http://localhost:8000` | API endpoint | Frontend |
| `VITE_WS_URL` | `ws://localhost:8000` | WebSocket endpoint | Frontend |
| `VITE_AUTH_ENABLED` | `true` | Authentication toggle | Frontend |
| `ADMIN_API_ENABLED` | `false` | Admin API toggle | API |
| `ADMIN_API_TOKEN` | N/A | Admin authentication | API |

### Missing Critical Variables
| Variable | Purpose | Impact |
|----------|---------|--------|
| `EMBED_PROVIDER` | Embedding service selection | Determines ML imports |
| `S3_ENDPOINT` | Storage endpoint | File uploads fail |
| `S3_ACCESS_KEY_ID` | Storage credentials | File uploads fail |
| `S3_SECRET_ACCESS_KEY` | Storage credentials | File uploads fail |
| `S3_BUCKET` | Storage bucket | File uploads fail |

## Scripts Inventory

### Shell Scripts
| Script | Purpose | Dependencies |
|--------|---------|--------------|
| `start.sh` | Project startup | Docker, docker-compose |
| `scripts/check_wireup.sh` | Service connectivity test | curl, redis-cli |
| `scripts/ws_smoke.py` | WebSocket smoke test | Python, websockets |

### Python Scripts
| Script | Purpose | Dependencies |
|--------|---------|--------------|
| `scripts/create_test_user.py` | Test user creation | SQLAlchemy, DB |
| `scripts/manage_api_keys.py` | API key management | SQLAlchemy, DB |

## Health Checks

### Service Health Checks
| Service | Endpoint | Method | Expected Response |
|---------|----------|--------|-------------------|
| API | `/health` | GET | `{"status": "healthy"}` |
| Database | `pg_isready` | CLI | `accepting connections` |
| Redis | `redis-cli ping` | CLI | `PONG` |

### Missing Health Checks
- Worker service health check
- Frontend service health check
- Storage service connectivity check

## Port Mapping

| Port | Service | Purpose | External Access |
|------|---------|---------|-----------------|
| 3000 | Frontend | React dev server | Yes |
| 3001 | Grafana | Monitoring dashboard | Yes |
| 5432 | PostgreSQL | Database | Yes (should be internal) |
| 6379 | Redis | Cache/Queue | Yes (should be internal) |
| 8000 | API | FastAPI service | Yes |
| 9090 | Prometheus | Metrics collection | Yes |

## Volume Mounts

| Service | Volume | Purpose | Persistence |
|---------|--------|---------|-------------|
| API | `./api:/app/api` | Code hot-reload | No |
| API | `./services:/app/services` | Code hot-reload | No |
| API | `./db:/app/db` | Code hot-reload | No |
| Worker | `./services:/app/services` | Code hot-reload | No |
| Worker | `./workers:/app/workers` | Code hot-reload | No |
| Frontend | `./web:/app` | Code hot-reload | No |
| Frontend | `/app/node_modules` | Dependencies | No |

## Critical Issues Identified

1. **Missing EMBED_PROVIDER configuration** - Causes ML imports at startup
2. **Missing storage configuration** - File uploads will fail
3. **Exposed database ports** - Security risk
4. **No worker health checks** - Service monitoring incomplete
5. **Code hot-reload volumes** - Production deployment issue
