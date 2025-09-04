# PromoAI RAG - Интеллектуальная система поиска по документам

Полнофункциональная RAG (Retrieval-Augmented Generation) система с веб-интерфейсом, API и интеграцией с Google OAuth.

## 🚀 Быстрый старт

### Prod (рекомендуется)

```bash
# Клонируйте репозиторий и подготовьте .env
git clone https://github.com/kiryakovTchp/rag.git
cd rag
cp env.example .env
# Заполните .env: JWT_SECRET_KEY, SESSION_SECRET и др.

# Запустите все сервисы (DB+Redis+API+Worker+Frontend+Prometheus+Grafana)
docker compose up -d

# Миграции применяются автоматически (alembic upgrade head)
curl -f http://localhost:8000/health
```

### Dev (быстрая разработка)

```bash
# 1) Создайте и заполните .env

# 2) Запуск dev окружения (API --reload, фронт через Vite)
docker compose -f docker-compose.dev.yml up

# API: http://localhost:8000, Frontend: http://localhost:3000
```

## 🏗️ Архитектура

### Backend
- **FastAPI** - веб-фреймворк
- **PostgreSQL + pgvector** - база данных с векторным поиском
- **Redis** - кэширование и очереди
- **Celery** - асинхронные задачи
- **OpenTelemetry** - наблюдаемость

### Frontend
- **React 18** - пользовательский интерфейс
- **TypeScript** - типобезопасность
- **Vite** - сборка и dev сервер
- **Tailwind CSS** - стилизация
- **React Router** - навигация

### Мониторинг
- **Prometheus** - метрики (экспортёры Redis/Postgres опционально)
- **Grafana** - дашборды
- **OpenTelemetry** - трассировка

## 🔐 Аутентификация

Аутентификация:
- Email/пароль: `POST /register`, `POST /login`, `GET /me`
- API ключи: `POST /api-keys`, `GET /api-keys`, `DELETE /api-keys/{id}`
- Google OAuth: `/auth/google` (start/callback), хранение state в сессии
- JWT: HS256 (`JWT_SECRET_KEY`) — секреты централизованы через `api/config.py`

### Тестовый аккаунт
```bash
# Создать тестового пользователя
make test-user

# Данные для входа:
# Email: test@promoai.com
# Пароль: test123456
```

## 📱 Основные страницы

- Landing, Login/Register, Dashboard, Documents, Search, Chat

## 🛠️ Управление проектом

### Основные команды
```bash
make start          # Запустить весь проект
make stop           # Остановить все сервисы
make restart        # Перезапустить проект
make logs           # Показать логи
make status         # Статус сервисов
make health         # Проверить здоровье
```

### Разработка
```bash
make dev            # Режим разработки (без Docker)
make test-user      # Создать тестового пользователя
make install-deps   # Установить зависимости
```

### Администрирование
```bash
make db-shell       # Подключиться к базе данных
make redis-cli      # Подключиться к Redis
make api-shell      # Подключиться к API контейнеру
make frontend-shell # Подключиться к фронтенд контейнеру
```

## 🌐 Доступные сервисы

После запуска доступны:
- **Фронтенд**: http://localhost:3000
- **API**: http://localhost:8000
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **База данных**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Конфигурация / ENV

Все переменные сведены в одном месте (`api/config.py`) и читаются через `get_settings()`. Шаблоны: `.env.example`, `env.example`.

Минимальный набор:
- Auth: `JWT_SECRET_KEY`, `SESSION_SECRET`, `REQUIRE_AUTH`
- Подключения: `DATABASE_URL`, `REDIS_URL`
- Хранилище: `S3_ENDPOINT`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` (локально MinIO)
- Инференс: `EMBED_PROVIDER` (local | workers_ai), `WORKERS_AI_TOKEN` (и/или `WORKERS_AI_*` для rerank)
- OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

### Google OAuth настройка
Подробная инструкция: [docs/GOOGLE_OAUTH_SETUP.md](docs/GOOGLE_OAUTH_SETUP.md)

## 📊 API (основные)

Аутентификация и ключи:
- `POST /register`, `POST /login`, `GET /me`
- `POST /api-keys`, `GET /api-keys`, `DELETE /api-keys/{id}`

Ингест:
- `POST /ingest` (multipart/form-data: file, tenant_id?, safe_mode?)
- `GET /ingest/{job_id}`
- `GET /ingest/document/{document_id}`

Поиск и ответы:
- `POST /query` (body: query, top_k, rerank, max_ctx)
- `POST /answer`, `POST /answer/stream`
- `GET /chunks/{id}` (получение текста фрагмента)

Feedback:
- `POST /feedback`, `GET /feedback/{answer_id}`, `GET /feedback?limit&offset`

Realtime:
- `GET /ws` (тест), `GET /ws/jobs` (события задач)

Сервисные:
- `GET /metrics`, `GET /health`, `GET /healthz`

## 🧪 Тестирование

```bash
# Backend тесты
python -m pytest

# Frontend тесты
cd web && npm test

# E2E тесты
cd web && npm run test:e2e
```

## 📈 Мониторинг

### Prometheus метрики
Экспорт метрик API доступен по `/metrics`. Экспортёры Redis/Postgres по умолчанию выключены — добавьте их в compose и включите джобы в `infra/prometheus.yml`.

## 🚀 Развертывание

### Production
Стандартный `docker compose up -d` (миграции Alembic применяются автоматически). Для dev используйте `docker-compose.dev.yml`.

## 🤝 Разработка

### Структура проекта
```
rag/
├── api/                 # FastAPI backend
├── web/                 # React frontend
├── services/            # Бизнес-логика
├── workers/             # Celery workers
├── db/                  # База данных
├── infra/               # Docker конфигурация
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── Dockerfile.frontend
│   ├── prometheus.yml
│   └── docker-compose.yml (внутренний)
├── docker-compose.dev.yml  # dev-окружение (Vite + reload)
├── docs/                # Документация
└── scripts/             # Скрипты
```

### Добавление новых функций
1. Создайте Issue с описанием
2. Создайте ветку: `git checkout -b feature/название-функции`
3. Реализуйте функциональность
4. Добавьте тесты
5. Создайте Pull Request

## 📚 Документация

- [Google OAuth Setup](docs/GOOGLE_OAUTH_SETUP.md)
- ENV/Secrets: см. `.env.example` / `env.example` и `api/config.py`
- [Unification Report](docs/UNIFICATION_REPORT.md)
- [Engineering Log](docs/ENGINEERING_LOG.md)
- [ADR](docs/adr/)

## 🆘 Поддержка

### Решение проблем
```bash
# Проверить статус сервисов
make status

# Проверить здоровье
make health

# Показать логи
make logs

# Очистить и перезапустить
make clean && make start
```

### Частые проблемы
1. **Порт занят**: `docker-compose down` и перезапуск
2. **База не подключается**: проверьте `DATABASE_URL` в `.env`
3. **Google OAuth не работает**: проверьте настройки в Google Console

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## 👥 Команда

- **Ivan Kiryakov** - разработка и архитектура

---

**PromoAI RAG** - Интеллектуальный поиск по документам с AI 🚀
