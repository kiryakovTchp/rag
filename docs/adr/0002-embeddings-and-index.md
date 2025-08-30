# ADR 0002: Embeddings and Index Architecture

## Статус
Accepted

## Дата
2025-08-31

## Контекст
Sprint 2 требует реализации эмбеддингов, индексации и поиска для RAG системы. Нужно выбрать архитектуру для генерации эмбеддингов, их хранения и поиска.

## Решение

### Embeddings Architecture
- **Модель**: BAAI/bge-m3 (1024-dimensional)
- **Провайдеры**: 
  - `local`: sentence-transformers (основной)
  - `workers_ai`: Cloudflare Workers AI (опциональный)
- **Нормализация**: L2-normalization для косинусного сходства
- **Батчинг**: 64 текста за раз для эффективности

### Index Architecture
- **Backend**: PostgreSQL + pgvector (основной)
- **Интерфейс**: Адаптер для Cloudflare Vectorize (будущее)
- **Индекс**: IVFFlat с косинусным сходством
- **Upsert**: Идемпотентная вставка/обновление

### Retrieval Architecture
- **Dense Search**: Топ-k по косинусному сходству
- **Reranking**: bge-reranker-v2-m3 через Workers AI (опционально)
- **Context Building**: Токен-лимитированный контекст (max 6 чанков)

### API Design
- **Endpoint**: `POST /query`
- **Response**: `matches` с чанками и метаданными
- **Usage**: Токен-счетчики для мониторинга

## Альтернативы

### Embeddings Models
- **OpenAI Ada**: Дорого, зависимость от API
- **all-MiniLM**: Меньше размерность, хуже качество
- **E5**: Хорошо, но bge-m3 лучше для многоязычности

### Index Backends
- **Pinecone**: Дорого, vendor lock-in
- **Weaviate**: Сложнее, избыточно для MVP
- **Qdrant**: Хорошо, но pgvector бесплатно

### Reranking
- **Cohere Rerank**: Дорого, API зависимость
- **BGE Rerank**: Локально, но медленно
- **Workers AI**: Быстро, дешево, но ограничения

## Последствия

### Положительные
- ✅ BGE-M3: высокое качество, многоязычность
- ✅ pgvector: бесплатно, стабильно, SQL
- ✅ Гибридный подход: локальная разработка + облачный продакшен
- ✅ Опциональный reranking: улучшение качества при доступности

### Отрицательные
- ❌ BGE-M3: 1024D (больше памяти)
- ❌ Workers AI: зависимость от Cloudflare
- ❌ Сложность: больше компонентов для отладки

### Риски
- **Митигация**: Fallback на local embedder
- **Митигация**: Graceful degradation без reranking
- **Митигация**: Мониторинг качества через тесты

## Технические детали

### Embeddings Pipeline
```python
# Генерация
embedder = EmbeddingProvider()  # local/workers_ai
vectors = embedder.embed_texts(texts)  # (n, 1024) np.array

# Индексация
index = PGVectorIndex()
index.upsert_embeddings(chunks, vectors, provider)

# Поиск
results = index.search(query_vector, top_k=100)
```

### Retrieval Pipeline
```python
# Dense search
retriever = HybridRetriever()
matches = retriever.retrieve(query, top_k=100, use_rerank=True)

# Context building
context = context_builder.build(matches, max_tokens=1800)
```

### Performance Targets
- **Embedding**: < 100ms на батч (64 текста)
- **Search**: < 50ms для top-100
- **Reranking**: < 200ms для top-20
- **End-to-end**: < 500ms для /query

## Следующие шаги
1. Мониторинг производительности
2. A/B тестирование reranking
3. Миграция на Cloudflare Vectorize
4. Оптимизация индексов
