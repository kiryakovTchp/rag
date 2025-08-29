# 0001: Foundation stack на Cloudflare + external Ollama
Дата: 2025-08-30
Статус: accepted
## Контекст
Нужен дешевый масштабируемый каркас RAG mini-SaaS.
## Решение
- Edge: Cloudflare Pages + Workers (гейт/аутентификация/лимиты), R2, Vectorize, Workers AI (эмбеддинги bge-m3, реранкер bge-reranker-v2-m3).
- LLM: внешняя Ollama (7–14B, Q6/Q8, 4–8k) за Cloudflare Tunnel; Workers проксирует OpenAI-совместимо.
- Backend: FastAPI + Celery + Redis; Postgres (+pgvector).
- Парсинг/чанк: PyMuPDF4LLM, Unstructured; header→token(350–700, 15% overlap)→semantic; таблицы группами строк.
## Альтернативы
Full self-host или монолит без очередей — хуже по DX/масштабируемости.
## Последствия
+ Дешево на старте, легко масштабировать edge. − Нужен внешний GPU для LLM.
