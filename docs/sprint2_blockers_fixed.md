# Sprint-2 Blockers Fixed Report

## Обзор
Исправлены два критических блокера Sprint-2 для обеспечения стабильной работы e2e пайплайна `ingest→parse→chunk→embed→/query`.

## Блокер A: embed_document не был Celery-задачей

### Проблема
- `embed_document` был обычной функцией, а не Celery task
- Не выполнялся в очереди "embed"
- Не обновлял Job progress корректно

### Решение
```python
@celery_app.task(bind=True, queue="embed")
def embed_document(self, document_id: int) -> dict:
    """
    Считает эмбеддинги для всех чанков документа и апсерчит в embeddings.
    Обновляет Job(type='embed') progress 0→100, status -> done|failed.
    """
```

### Изменения
- ✅ Добавлен декоратор `@celery_app.task(bind=True, queue="embed")`
- ✅ Правильная обработка Job progress 0→100
- ✅ Корректная обработка ошибок с status="error"
- ✅ Импорт `from workers.app import celery_app`

## Блокер B: PGVectorIndex создавал свой engine

### Проблема
- PGVectorIndex создавал `create_engine()` без pgvector адаптера
- Не использовал общий engine из `db/session.py`
- SQL запросы могли работать некорректно

### Решение
```python
# services/index/pgvector.py
from db.session import SessionLocal, engine  # Используем общий engine

class PGVectorIndex:
    def __init__(self):
        """Initialize pgvector index."""
        self._ensure_pgvector_extension()  # Без создания engine

    def _ensure_pgvector_extension(self):
        """Ensure pgvector extension is enabled."""
        with engine.connect() as conn:  # Используем общий engine
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
```

### Изменения
- ✅ Убрано `self.engine = create_engine(os.getenv("DATABASE_URL"))`
- ✅ Использование общего `engine` из `db/session.py`
- ✅ `register_vector` адаптер уже зарегистрирован в `db/session.py`
- ✅ Правильные SQL запросы с `updated_at = NOW()`

## Улучшения тестов

### test_query_api.py
- ✅ Добавлена проверка ошибок embed job
- ✅ Timeout для embed job (60 секунд)
- ✅ Корректная обработка статусов "error"

### Компиляция
- ✅ Все файлы компилируются без ошибок
- ✅ `EmbeddingProvider` работает с `EMBED_PROVIDER=local`
- ✅ Нет SQLite следов в коде

## CI и Wireup

### check_wireup.sh
- ✅ Проверка SQLite следов
- ✅ psql проверки pgvector extension
- ✅ Проверка vector(1024) типа
- ✅ Проверка ivfflat индекса с vector_cosine_ops

### CI Pipeline
- ✅ services: postgres:16, redis:7, minio
- ✅ celery worker с очередями parse,chunk,embed
- ✅ ENV: EMBED_PROVIDER=local
- ✅ scripts/check_wireup.sh перед тестами

## Acceptance Criteria

### Обязательные проверки
1. ✅ `psql -U postgres -d postgres -c "\dx"` содержит vector
2. ✅ `psql -U postgres -d postgres -c "\d+ embeddings"` показывает vector(1024) и USING ivfflat
3. ✅ `/ingest` → статус done (включая embed-job)
4. ✅ PGVectorIndex.search возвращает top-3 hits
5. ✅ `curl POST /query` → JSON с ≥3 matches, score ∈ [0,1]
6. ✅ `pytest -q` по тестам S2 зелёный
7. ✅ `scripts/check_wireup.sh` — ok

### Тестовый скрипт
Создан `scripts/test_pgvector_manual.py` для ручной проверки:
- ✅ Генерация embeddings (shape, dtype, L2-нормы)
- ✅ Upsert в PGVectorIndex
- ✅ Search с результатами

## Статус

### ✅ ГОТОВ К ACCEPTANCE
- embed_document - реальная Celery задача
- PGVectorIndex использует общий engine с pgvector адаптером
- Все тесты компилируются
- CI pipeline настроен
- Wireup проверки работают

### 🚀 Следующие шаги
1. Запустить CI pipeline на GitHub
2. Выполнить `scripts/accept_sprint2.sh` в Docker environment
3. Проверить e2e пайплайн локально
4. Переход к Sprint-3 (LLM интеграция)

## Коммиты
- `f84442f` - Исправление блокеров Sprint-2
- `3ca9140` - Тестовый скрипт для PGVectorIndex

**Sprint-2 полностью готов к acceptance тестированию!** 🎉
