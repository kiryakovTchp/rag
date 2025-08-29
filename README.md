# PromoAI RAG (Sprint 1 - Ingest Pipeline)

Каркас mini-SaaS с рабочим пайплайном ingest → parsing → chunking.

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
# Установить pre-commit хуки
pre-commit install

# Установить Python зависимости
python3 -m pip install -r requirements.txt
```

### 2. Запуск инфраструктуры
```bash
# Поднять базу данных, Redis и MinIO
docker compose -f infra/docker-compose.yml up -d db redis minio

# Или запустить API локально (без Docker)
uvicorn api.main:app --reload --port 8000
```

### 3. Проверка работы
```bash
# Health check
curl http://localhost:8000/healthz

# Загрузка документа
curl -X POST http://localhost:8000/ingest \
  -F "file=@example.pdf" \
  -F "tenant_id=test" \
  -F "safe_mode=false"

# Проверка статуса job
curl http://localhost:8000/ingest/{job_id}
```

## 📋 Возможности Sprint 1

- ✅ **Загрузка документов**: PDF, DOCX, MD, HTML, XLSX, CSV
- ✅ **S3/MinIO хранение**: Загрузка файлов в S3-совместимое хранилище
- ✅ **Парсинг**: PyMuPDF4LLM для PDF, unstructured для Office
- ✅ **Чанкинг**: Header-aware + token-aware (350-700 токенов, 15% overlap)
- ✅ **Таблицы**: Извлечение и группировка по 20-60 строк с повтором шапки
- ✅ **Асинхронная обработка**: Celery + Redis очереди
- ✅ **Отслеживание прогресса**: Polling статуса job (0-100%)

## 🏗️ Архитектура

```
POST /ingest → S3 Upload → Document + Job → Celery Parse → Elements → Celery Chunk → Chunks
```

### Компоненты:
- **FastAPI**: REST API с валидацией типов файлов
- **Celery**: Асинхронная обработка parse/chunk задач
- **PostgreSQL**: Хранение документов, джобов, элементов, чанков
- **Redis**: Очереди Celery и кэширование
- **MinIO**: S3-совместимое хранилище файлов

## 📁 Структура проекта

```
api/                    # FastAPI приложение
├── routers/           # API эндпоинты
├── schemas/           # Pydantic модели
└── deps.py           # Зависимости

services/              # Бизнес-логика
├── ingest/           # Загрузка документов
├── parsing/          # Парсинг (PDF, Office)
└── chunking/         # Чанкинг (headers, tokens, tables)

workers/               # Celery задачи
├── tasks/            # parse, chunk задачи
└── app.py           # Celery конфигурация

db/                    # База данных
├── models.py         # SQLAlchemy модели
├── session.py        # Подключение к БД
└── migrations/       # Alembic миграции

storage/               # S3/MinIO клиент
└── r2.py            # ObjectStore класс
```

## 🔧 Конфигурация

Скопируйте `env.example` в `.env` и настройте переменные:

```bash
# База данных
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/postgres

# Redis
REDIS_URL=redis://localhost:6379

# S3/MinIO
S3_ENDPOINT=http://minio:9000
S3_BUCKET=promoai
S3_ACCESS_KEY_ID=minio
S3_SECRET_ACCESS_KEY=minio123
```

## 🧪 Тестирование

```bash
# Запуск линтеров
pre-commit run -a

# Запуск тестов
pytest

# Проверка типов
mypy .
```

## 📊 API Endpoints

### POST /ingest
Загрузка документа:
```json
{
  "job_id": 1,
  "status": "queued",
  "message": "Document uploaded successfully"
}
```

### GET /ingest/{job_id}
Статус обработки:
```json
{
  "job_id": 1,
  "type": "parse",
  "status": "running",
  "progress": 50,
  "document_id": 1,
  "created_at": "2025-01-27T10:00:00",
  "updated_at": "2025-01-27T10:05:00"
}
```

## 🚧 Следующие спринты

- **Sprint 2**: Эмбеддинги и векторный поиск
- **Sprint 3**: LLM интеграция и ответы
- **Sprint 4**: WebSocket для real-time статусов
