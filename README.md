# PromoAI RAG (bootstrap)
Каркас mini-SaaS. Запуск:
1) `pre-commit install`
2) `docker compose -f infra/docker-compose.yml up -d db redis`
3) `uvicorn api.main:app --reload --port 8000`
GET http://localhost:8000/healthz → {"status":"ok"}
