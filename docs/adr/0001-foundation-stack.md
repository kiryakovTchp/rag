# 0001: Foundation stack на Cloudflare + external Ollama
Дата: 2025-08-30
Статус: accepted

## Контекст
Нужен дешевый масштабируемый каркас RAG mini-SaaS.

## Решение

### Архитектура (Sprint 1 реализовано)
- **Backend**: FastAPI + Celery + Redis для асинхронной обработки
- **Database**: PostgreSQL + pgvector для векторного поиска
- **Storage**: S3-совместимое хранилище (MinIO локально, R2 в продакшене)
- **Parsing**: PyMuPDF4LLM для PDF, unstructured для Office документов
- **Chunking**: header-aware → token-aware (350-700 токенов, 15% overlap) → semantic
- **Tables**: pdfplumber/camelot для извлечения таблиц, группы 20-60 строк с повтором заголовков

### Планируемая архитектура (Sprint 2+)
- **Edge**: Cloudflare Pages + Workers (гейт/аутентификация/лимиты)
- **Vector Search**: Cloudflare Vectorize или pgvector
- **Embeddings**: BAAI/bge-m3 (локально) + Workers AI (опционально)
- **Reranking**: bge-reranker-v2-m3 через Workers AI
- **LLM**: внешняя Ollama (7-14B, Q6/Q8, 4-8k) за Cloudflare Tunnel

## Альтернативы
- Full self-host: дороже и сложнее в масштабировании
- Монолит без очередей: хуже по DX и масштабируемости
- Только Cloudflare: ограничения по размеру файлов и времени выполнения

## Последствия
+ Дешево на старте, легко масштабировать edge
+ Гибридный подход: локальная разработка + облачный продакшен
- Нужен внешний GPU для LLM
- Сложность в отладке распределенной системы
