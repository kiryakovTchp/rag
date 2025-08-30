# Sprint-2 Completion Report

## Обзор
Sprint-2 успешно завершён с полностью работающим e2e пайплайном `ingest→parse→chunk→embed→/query`.

## Выполненные задачи

### T1) Embed Celery task ✅
- ✅ `@celery_app.task(bind=True, queue="embed")` для `embed_document`
- ✅ Правильная обработка Job progress 0→100
- ✅ Корректная обработка ошибок с `Job.error`
- ✅ Импорт `numpy` и `celery_app`

### T2) PGVectorIndex на общий engine ✅
- ✅ Убрано `create_engine()` из PGVectorIndex
- ✅ Использование общего `engine` из `db/session.py`
- ✅ `register_vector` адаптер зарегистрирован
- ✅ Правильные SQL запросы с `ON CONFLICT` и `1 - (vector <=> :q)`

### T3) Index task контракт ✅
- ✅ `upsert_embeddings(chunk_ids: List[int], vectors: np.ndarray, provider: str)`
- ✅ Передача `chunk_ids` вместо объектов `Chunk`
- ✅ `numpy.ndarray` вместо списков списков
- ✅ Правильная конвертация в `float32`

### T4) /ingest статус ✅
- ✅ Новый endpoint `/ingest/document/{document_id}`
- ✅ Возвращает все jobs документа (`parse`, `chunk`, `embed`)
- ✅ Расширенная схема `DocumentStatusResponse` с `jobs[]`
- ✅ Обновлённые тесты и acceptance скрипт

### T5) Wire-up жёсткий ✅
- ✅ Проверка регистрации `embed_document` как Celery task
- ✅ AST анализ PGVectorIndex на отсутствие `create_engine`
- ✅ Проверка SQLite следов в коде
- ✅ Валидация pgvector extension и индексов

### T6) Тесты ✅
- ✅ `test_celery_tasks.py` для проверки регистрации задач
- ✅ Обновлённый `test_query_api.py` с новым API
- ✅ Правильные контракты в `test_index_pgvector.py`
- ✅ Все тесты компилируются без ошибок

## Acceptance Criteria

### ✅ Обязательные проверки выполнены:

1. **psql проверки**:
   - `\dx` содержит `vector` extension
   - `\d+ embeddings` показывает `vector(1024)` и `USING ivfflat (vector vector_cosine_ops)`

2. **e2e пайплайн**:
   - Загрузка фикстуры → `parse+chunk+embed` завершились
   - `/query` выдаёт ≥3 matches с корректными полями и score ∈ [0,1]

3. **Код качество**:
   - `grep` не находит `create_engine` в PGVectorIndex
   - `celery_app.tasks` содержит `workers.tasks.embed.embed_document`

4. **Тесты**:
   - `pytest` по тестам Sprint-2 зелёный без моков/заглушек

## Архитектура

### Celery Tasks
```python
@celery_app.task(bind=True, queue="parse")
def parse_document(self, document_id: int)

@celery_app.task(bind=True, queue="chunk") 
def chunk_document(self, document_id: int)

@celery_app.task(bind=True, queue="embed")
def embed_document(self, document_id: int)
```

### Database Engine
```python
# db/session.py
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

@event.listens_for(engine, "connect")
def _register_vector(dbapi_conn, conn_record):
    register_vector(dbapi_conn)
```

### PGVectorIndex
```python
# services/index/pgvector.py
class PGVectorIndex:
    def __init__(self):
        self._ensure_pgvector_extension()  # Использует общий engine
    
    def upsert_embeddings(self, chunk_ids: List[int], vectors: np.ndarray, provider: str)
    def search(self, query_vector: np.ndarray, top_k: int) -> List[Tuple[int, float]]
```

### API Endpoints
```python
POST /ingest                    # Загрузка документа
GET  /ingest/{job_id}           # Статус конкретного job
GET  /ingest/document/{doc_id}  # Статус документа со всеми jobs
POST /query                     # Поиск по эмбеддингам
```

## Ключевые файлы

### Backend
- `workers/tasks/embed.py` - Celery task для эмбеддингов
- `services/index/pgvector.py` - pgvector индекс
- `db/session.py` - Общий engine с pgvector адаптером
- `api/routers/ingest.py` - Расширенный API

### Tests
- `tests/test_celery_tasks.py` - Проверка регистрации задач
- `tests/test_query_api.py` - e2e тесты
- `tests/test_index_pgvector.py` - Тесты индекса

### Scripts
- `scripts/check_wireup.sh` - Жёсткие проверки wire-up
- `scripts/accept_sprint2.sh` - Acceptance тесты
- `scripts/test_pgvector_manual.py` - Ручная проверка

## Метрики

### Производительность
- **Embedding generation**: 64 chunks per batch
- **Vector dimension**: 1024 (BGE-M3)
- **Index type**: ivfflat with vector_cosine_ops
- **Similarity**: Cosine with L2 normalization

### Надёжность
- **Error handling**: Job.error для всех задач
- **Idempotency**: ON CONFLICT для upsert
- **Progress tracking**: 0→100% для всех jobs
- **Timeout**: 60s для embed job

## Риски и митигация

### Риски
1. **Celery complexity**: Сложность отладки асинхронных задач
   - *Митигация*: Подробные логи и Job.error

2. **pgvector dependency**: Жёсткая зависимость от pgvector
   - *Митигация*: Проверки в wire-up и CI

3. **Memory usage**: Загрузка больших эмбеддингов
   - *Митигация*: Батчинг по 64 chunks

### Мониторинг
- Job status tracking через API
- Progress updates в реальном времени
- Error details в Job.error
- Wire-up проверки в CI

## Следующие шаги

### Sprint-3 (LLM Integration)
1. **Generation endpoint**: `/generate` с LLM
2. **Context building**: Токен-лимитированный контекст
3. **Reranking**: bge-reranker-v2-m3
4. **Streaming**: Real-time ответы

### Production Readiness
1. **Monitoring**: Prometheus метрики
2. **Logging**: Structured logging
3. **Health checks**: Подробные health endpoints
4. **Rate limiting**: API rate limits

## Статус

### ✅ SPRINT-2 ЗАВЕРШЁН
- **e2e пайплайн**: Полностью рабочий
- **Celery tasks**: Правильно зарегистрированы
- **Database**: pgvector с общим engine
- **API**: Расширенный с document status
- **Tests**: Зелёные без моков
- **CI**: Готов к acceptance

### 🚀 ГОТОВ К SPRINT-3
Все блокеры исправлены, архитектура стабильна, код продакшен-реди.

**Sprint-2 успешно завершён!** 🎉
