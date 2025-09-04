.PHONY: help start stop restart logs clean test-user build-frontend build-backend

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Показать справку по командам
	@echo "$(BLUE)🚀 PromoAI RAG - Команды управления проектом$(NC)"
	@echo ""
	@echo "$(GREEN)Основные команды:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Примеры:$(NC)"
	@echo "  make start          # Запустить весь проект"
	@echo "  make stop           # Остановить все сервисы"
	@echo "  make logs           # Показать логи"
	@echo "  make test-user      # Создать тестового пользователя"

start: ## Запустить весь проект
	@echo "$(BLUE)🚀 Запуск PromoAI RAG проекта...$(NC)"
	@chmod +x start.sh
	@./start.sh

stop: ## Остановить все сервисы
	@echo "$(YELLOW)🛑 Остановка всех сервисов...$(NC)"
	docker-compose down

restart: stop start ## Перезапустить проект

logs: ## Показать логи всех сервисов
	@echo "$(BLUE)📋 Логи всех сервисов:$(NC)"
	docker-compose logs -f

logs-api: ## Показать логи API
	@echo "$(BLUE)📋 Логи API:$(NC)"
	docker-compose logs -f api

logs-frontend: ## Показать логи фронтенда
	@echo "$(BLUE)📋 Логи фронтенда:$(NC)"
	docker-compose logs -f frontend

logs-worker: ## Показать логи воркеров
	@echo "$(BLUE)📋 Логи воркеров:$(NC)"
	docker-compose logs -f worker

clean: ## Очистить все контейнеры и volumes
	@echo "$(RED)🧹 Очистка всех контейнеров и volumes...$(NC)"
	docker-compose down -v
	docker system prune -f

test-user: ## Создать тестового пользователя
	@echo "$(BLUE)👤 Создание тестового пользователя...$(NC)"
	@echo "$(YELLOW)Убедитесь, что база данных запущена: make start$(NC)"
	@echo "$(YELLOW)Тестовые данные:$(NC)"
	@echo "$(GREEN)  Email: test@promoai.com$(NC)"
	@echo "$(GREEN)  Пароль: test123456$(NC)"
	@echo ""
	@echo "$(BLUE)Запуск скрипта создания пользователя...$(NC)"
	docker-compose exec api python scripts/create_test_user.py

build-frontend: ## Собрать фронтенд для продакшена
	@echo "$(BLUE)🔨 Сборка фронтенда для продакшена...$(NC)"
	cd web && npm run build

build-backend: ## Собрать бэкенд для продакшена
	@echo "$(BLUE)🔨 Сборка бэкенда для продакшена...$(NC)"
	docker-compose build api worker

status: ## Показать статус всех сервисов
	@echo "$(BLUE)🔍 Статус сервисов:$(NC)"
	docker-compose ps

health: ## Проверить здоровье сервисов
	@echo "$(BLUE)🏥 Проверка здоровья сервисов:$(NC)"
	@echo "$(BLUE)API:$(NC)"
	@curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "$(GREEN)✅ API работает$(NC)" || echo "$(RED)❌ API недоступен$(NC)"
	@echo "$(BLUE)Фронтенд:$(NC)"
	@curl -f http://localhost:3000 > /dev/null 2>&1 && echo "$(GREEN)✅ Фронтенд работает$(NC)" || echo "$(RED)❌ Фронтенд недоступен$(NC)"
	@echo "$(BLUE)Grafana:$(NC)"
	@curl -f http://localhost:3001 > /dev/null 2>&1 && echo "$(GREEN)✅ Grafana работает$(NC)" || echo "$(RED)❌ Grafana недоступен$(NC)"

db-shell: ## Подключиться к базе данных
	@echo "$(BLUE)🗄️ Подключение к базе данных...$(NC)"
	docker-compose exec db psql -U rag_user -d rag_db

redis-cli: ## Подключиться к Redis CLI
	@echo "$(BLUE)🔴 Подключение к Redis CLI...$(NC)"
	docker-compose exec redis redis-cli

frontend-shell: ## Подключиться к контейнеру фронтенда
	@echo "$(BLUE)📱 Подключение к контейнеру фронтенда...$(NC)"
	docker-compose exec frontend sh

api-shell: ## Подключиться к контейнеру API
	@echo "$(BLUE)🔧 Подключение к контейнеру API...$(NC)"
	docker-compose exec api bash

worker-shell: ## Подключиться к контейнеру воркера
	@echo "$(BLUE)⚙️ Подключение к контейнеру воркера...$(NC)"
	docker-compose exec worker bash

install-deps: ## Установить зависимости для разработки
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	@echo "$(BLUE)Python зависимости:$(NC)"
	pip install -r requirements.txt
	@echo "$(BLUE)Node.js зависимости:$(NC)"
	cd web && npm install

dev: ## Запустить в режиме разработки (без Docker)
	@echo "$(BLUE)🔧 Запуск в режиме разработки...$(NC)"
	@echo "$(YELLOW)Убедитесь, что PostgreSQL и Redis запущены$(NC)"
	@echo "$(BLUE)Запуск API...$(NC)"
	cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "$(BLUE)Запуск фронтенда...$(NC)"
	cd web && npm run dev &
	@echo "$(GREEN)✅ Сервисы запущены в фоне$(NC)"
	@echo "$(BLUE)API: http://localhost:8000$(NC)"
	@echo "$(BLUE)Фронтенд: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Для остановки: pkill -f uvicorn && pkill -f vite$(NC)"
