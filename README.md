# PromoAI RAG

Каркас mini-SaaS для RAG (Retrieval-Augmented Generation) системы.

## Быстрый старт

### 1. Настройка окружения

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Установить pre-commit hooks
pre-commit install
```

### 2. Запуск полного стека

```bash
# Запустить все сервисы (db, redis, minio, worker, api)
docker compose -f infra/docker-compose.yml up -d db redis minio worker api

# Или через Makefile
make dev-up
```

### 3. Инициализация базы данных

```bash
# Применить миграции
alembic upgrade head
```

### 4. Проверка работоспособности

```bash
# Проверка здоровья API
curl http://localhost:8000/healthz

# Загрузка PDF документа
curl -F file=@tests/fixtures/simple.pdf http://localhost:8000/ingest

# Проверка статуса job (замените {job_id} на полученный ID)
curl http://localhost:8000/ingest/{job_id}

# Поиск по документам
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ваш поисковый запрос",
    "top_k": 10,
    "rerank": false,
    "max_ctx": 1800
  }'

# Пример ответа:
# {
#   "matches": [
#     {
#       "doc_id": 1,
#       "chunk_id": 5,
#       "page": 2,
#       "score": 0.85,
#       "snippet": "Найденный текст...",
#       "breadcrumbs": ["Глава 1", "Раздел 2"]
#     }
#   ],
#   "usage": {
#     "in_tokens": 5,
#     "out_tokens": 150
#   }
# }
```

### 5. Остановка сервисов

```bash
# Остановить все сервисы
make dev-down
```

## Архитектура

### Компоненты

- **API**: FastAPI с эндпоинтами для загрузки и поиска
- **Worker**: Celery для асинхронной обработки документов
- **Storage**: S3-совместимое хранилище (MinIO локально, R2 в продакшене)
- **Database**: PostgreSQL с pgvector для векторного поиска
- **Cache**: Redis для очередей и кэширования

### Пайплайн обработки

1. **Upload**: Файл загружается в S3
2. **Parse**: Документ разбивается на элементы (текст, заголовки, таблицы)
3. **Chunk**: Элементы разбиваются на чанки с метаданными
4. **Index**: Чанки индексируются для поиска
5. **Query**: Векторный поиск с опциональным reranking

### Query API

- **POST `/query`**: Поиск по документам
- **Embeddings**: BGE-M3 (1024-dimensional)
- **Index**: PostgreSQL + pgvector
- **Reranking**: Опционально через Workers AI

#### Переменные окружения

```bash
# Embeddings
EMBED_PROVIDER=local                    # local или workers_ai
EMBED_BATCH_SIZE=64                     # Размер батча

# Workers AI (опционально)
WORKERS_AI_TOKEN=your_token_here        # API токен
WORKERS_AI_URL=https://api.cloudflare.com/client/v4/ai/run/@cf/baai/bge-m3
MODEL_ID=@cf/baai/bge-m3

# Vector Search
TOP_K=100                               # Количество результатов поиска
RERANK_ENABLED=false                    # Включить reranking
MAX_CTX_TOKENS=1800                     # Максимальный размер контекста

# pgvector Tuning
IVFFLAT_LISTS=100                       # Количество списков в ivfflat индексе
IVFFLAT_PROBES=10                       # Количество проб для поиска (10-20)

# Admin API (опционально)
ADMIN_API_ENABLED=false                 # Включить админ API
ADMIN_API_TOKEN=your_admin_token        # Токен для админ API
```

#### Примеры использования

```bash
# Поиск с настройками
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "как работает система",
    "top_k": 20,
    "rerank": false,
    "max_ctx": 1800
  }'

# Оптимизация поиска (для больших индексов)
# Увеличить ivfflat.probes для лучшего качества:
# SET ivfflat.probes = 20;
```

## How to check status

### Document Status

Для получения статуса документа со всеми jobs:

```bash
# Получить статус документа
curl http://localhost:8000/ingest/document/{document_id}

# Пример ответа:
{
  "document_id": 1,
  "status": "done",
  "jobs": [
    {
      "id": 1,
      "type": "parse",
      "status": "done",
      "progress": 100,
      "document_id": 1,
      "created_at": "2024-01-01T10:00:00",
      "updated_at": "2024-01-01T10:01:00"
    },
    {
      "id": 2,
      "type": "chunk",
      "status": "done", 
      "progress": 100,
      "document_id": 1,
      "created_at": "2024-01-01T10:01:00",
      "updated_at": "2024-01-01T10:02:00"
    },
    {
      "id": 3,
      "type": "embed",
      "status": "done",
      "progress": 100,
      "document_id": 1,
      "created_at": "2024-01-01T10:02:00",
      "updated_at": "2024-01-01T10:03:00"
    }
  ]
}
```

### Job Status

Для получения статуса конкретного job:

```bash
curl http://localhost:8000/ingest/{job_id}
```

## How to tune vector search

### pgvector Parameters

- **IVFFLAT_LISTS**: Количество списков в ivfflat индексе (по умолчанию 100)
  - Больше списков = лучше качество, медленнее поиск
  - Меньше списков = быстрее поиск, хуже качество

- **IVFFLAT_PROBES**: Количество проб для поиска (по умолчанию 10)
  - Больше проб = лучше качество, медленнее поиск
  - Рекомендуется 10-20 для большинства случаев
  - Для больших индексов можно увеличить до 50-100

### Tuning Guidelines

```bash
# Для высокого качества (медленнее)
IVFFLAT_PROBES=20

# Для высокой скорости (хуже качество)
IVFFLAT_PROBES=5

# Для больших индексов (>1M векторов)
IVFFLAT_LISTS=1000
IVFFLAT_PROBES=50
```
```

## Разработка

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск конкретного теста
pytest tests/test_ingest_pipeline.py

# Проверка качества кода
pre-commit run -a
```

### Миграции БД

```bash
# Создать миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head
```

## Конфигурация

### Переменные окружения

Скопируйте `.env.example` в `.env` и настройте:
             
             

```bash
# База данных
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/postgres

# Redis
REDIS_URL=redis://localhost:6379/0

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_REGION=us-east-1
S3_BUCKET=promoai
S3_ACCESS_KEY_ID=minio
S3_SECRET_ACCESS_KEY=minio123

# JWT
JWT_SECRET=your-secret-key
```

## Sprint 1: Ingest Pipeline

Реализован полный пайплайн загрузки документов:

- ✅ POST `/ingest` - загрузка файлов
- ✅ GET `/ingest/{job_id}` - статус обработки
- ✅ Парсинг PDF (PyMuPDF4LLM) и Office (unstructured)
- ✅ Извлечение таблиц (pdfplumber/camelot)
- ✅ Чанкинг с метаданными (header-aware, token-aware)
- ✅ Асинхронная обработка через Celery
- ✅ S3-совместимое хранилище

### Поддерживаемые форматы

- **PDF**: application/pdf
- **Word**: application/vnd.openxmlformats-officedocument.wordprocessingml.document
- **Excel**: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- **CSV**: text/csv
- **Markdown**: text/markdown
- **HTML**: text/html
- **Plain Text**: text/plain

## Лицензия

MIT
