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
