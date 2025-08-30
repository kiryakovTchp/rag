init:
	pre-commit install

dev-up:
	docker compose -f infra/docker-compose.yml up -d db redis minio worker api

dev-down:
	docker compose -f infra/docker-compose.yml down -v

dev:
	docker compose -f infra/docker-compose.yml up -d db redis
	uvicorn api.main:app --reload --port 8000

lint:
	pre-commit run -a

test:
	python3 -m pytest

test-e2e:
	python3 -m pytest tests/test_ingest_pipeline.py tests/test_tables_pdf.py -v
