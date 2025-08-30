# Sprint 1 Acceptance Criteria

## Обзор
Sprint 1 реализует полный пайплайн загрузки и обработки документов: upload → parse → chunk с поддержкой таблиц и метаданных.

## Функциональные требования

### 1. Upload Pipeline
- ✅ POST `/ingest` принимает файлы (PDF, DOCX, XLSX, CSV, MD, HTML, TXT)
- ✅ Файлы сохраняются в S3-совместимое хранилище (MinIO/R2)
- ✅ Создается Document и Job записи в БД
- ✅ Возвращается job_id для отслеживания

### 2. Parse Pipeline
- ✅ PDF: PyMuPDF4LLM для текста, pdfplumber/camelot для таблиц
- ✅ Office: unstructured для DOCX/XLSX/CSV
- ✅ Создаются Element записи с типом, страницей, текстом
- ✅ Таблицы извлекаются в markdown формате

### 3. Chunk Pipeline
- ✅ Header-aware чанкинг (350-700 токенов, 15% overlap)
- ✅ Table-aware чанкинг (20-60 строк с повторением заголовка)
- ✅ Создаются Chunk записи с метаданными
- ✅ Token counting через tiktoken

### 4. Job Tracking
- ✅ GET `/ingest/{job_id}` возвращает статус и прогресс
- ✅ Асинхронная обработка через Celery
- ✅ Обработка ошибок и таймаутов

## Технические требования

### Архитектура
- ✅ FastAPI с роутерами
- ✅ Celery + Redis для очередей
- ✅ PostgreSQL с SQLAlchemy ORM
- ✅ S3-совместимое хранилище
- ✅ Docker Compose для локальной разработки

### Качество кода
- ✅ Pre-commit hooks (black, ruff, mypy)
- ✅ Conventional Commits
- ✅ Типизация (mypy)
- ✅ Линтинг (ruff)
- ✅ Тесты (pytest)

## Метрики производительности

### Latency (целевые значения)
- **simple.pdf** (1 страница, текст): < 5 секунд
- **table.pdf** (множественные таблицы): < 30 секунд
- **complex.pdf** (многостраничный): < 60 секунд

### Качество извлечения
- **Текст**: 95%+ точность извлечения
- **Таблицы**: 80%+ точность структуры
- **Заголовки**: Правильная иерархия header_path

### Надежность
- **Job completion**: 95%+ успешных завершений
- **Error handling**: Graceful degradation при ошибках парсинга
- **Timeout handling**: Максимум 90 секунд на job

## Acceptance тесты

### E2E тесты
1. **test_ingest_pipeline.py**: Полный цикл upload → parse → chunk
2. **test_tables_integration.py**: Обработка PDF с таблицами
3. **test_tables_pdf.py**: Unit тесты для TableParser

### Проверки
- ✅ elements > 0 после parse
- ✅ chunks > 0 после chunk
- ✅ token_count > 0 для всех chunks
- ✅ page указан для всех chunks
- ✅ header_path корректный (может быть пустым)
- ✅ table-chunks содержат повторение заголовка

## Ограничения Sprint 1

### Не реализовано
- ❌ Эмбеддинги и векторный поиск
- ❌ API `/query` для поиска
- ❌ Reranking результатов
- ❌ LLM генерация ответов

### Известные ограничения
- Локальная разработка требует Docker (PostgreSQL)
- Table parsing может быть неточным для сложных таблиц
- Нет оптимизации для больших файлов (>50MB)

## Следующие шаги
- Sprint 2: Эмбеддинги и векторный поиск
- Sprint 3: LLM интеграция и генерация ответов
