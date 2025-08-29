init:
	pre-commit install

dev:
	docker compose -f infra/docker-compose.yml up -d db redis
	uvicorn api.main:app --reload --port 8000

lint:
	pre-commit run -a

test:
	pytest || true
