# Sprint-3 Preparation Guide

## Обзор
Подготовка к Sprint-3 (LLM слой) для добавления генерации ответов поверх retrieve.

## Провайдеры генерации

### Выбор провайдера
Выбираем один на старт и делаем конфиг под него:

1. **OpenRouter** (универсальный прокси провайдер)
   - Поддерживает OpenAI, Anthropic, Google, Meta и др.
   - Единый API для всех моделей
   - Хорошая документация

2. **AI Studio** (Gemini)
   - Google Gemini Pro/Ultra
   - Стабильный API
   - Хорошая производительность

3. **Workers AI** (через edge)
   - Уже настроен для эмбеддингов
   - Низкая латентность
   - Интеграция с Cloudflare

4. **Локально: Ollama**
   - Полный контроль
   - Бесплатно
   - Требует ресурсов

### Рекомендация
**OpenRouter** - универсальность и простота интеграции.

## Секреты и ENV

### .env.example
```bash
# LLM Provider
LLM_PROVIDER=openrouter|aistudio|workers_ai|ollama
LLM_MODEL=gpt-4o-mini                    # конкретная модель
LLM_TIMEOUT=30                           # сек
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.2

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...

# AI Studio (Gemini)
AISTUDIO_API_KEY=...

# Workers AI
WORKERS_AI_URL=https://...
WORKERS_AI_TOKEN=...
WORKERS_AI_MODEL=...

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Cache
ANSWER_CACHE_TTL=300                     # 5 минут
```

### CI Secrets
```bash
# GitHub Secrets
OPENROUTER_API_KEY=sk-or-v1-...
AISTUDIO_API_KEY=...
WORKERS_AI_TOKEN=...
```

## Тестовый набор для e2e ответов

### tests/fixtures/s3_golden.jsonl
```json
{"q": "Как устроен ingest?", "must_have": ["ingest", "Celery"], "min_citations": 2}
{"q": "Что такое pgvector?", "must_have": ["vector", "PostgreSQL"], "min_citations": 1}
{"q": "Как работает chunking?", "must_have": ["chunk", "text"], "min_citations": 2}
{"q": "Какие провайдеры эмбеддингов поддерживаются?", "must_have": ["BGE", "Workers"], "min_citations": 1}
{"q": "Как настроить векторный поиск?", "must_have": ["ivfflat", "probes"], "min_citations": 1}
{"q": "Что такое RAG?", "must_have": ["retrieval", "generation"], "min_citations": 1}
{"q": "Как работает парсинг документов?", "must_have": ["parse", "PDF"], "min_citations": 2}
{"q": "Какие форматы файлов поддерживаются?", "must_have": ["PDF", "DOCX"], "min_citations": 2}
{"q": "Как мониторить прогресс обработки?", "must_have": ["progress", "status"], "min_citations": 1}
{"q": "Что такое reranking?", "must_have": ["rerank", "quality"], "min_citations": 1}
```

## Фронтовая подготовка

### CORS для SSE
Если планируешь `/answer/stream`, разблокируй CORS в FastAPI:

```python
# api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # твой домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Проверка SSE
Убедись, что прокси пропускает SSE (не буферизует):
```bash
# nginx config
proxy_buffering off;
proxy_cache off;
```

## Бюджеты и лимиты

### Токены
```bash
MAX_CTX_TOKENS=1800-2500                # Контекст для LLM
LLM_MAX_TOKENS=1024                     # Максимум генерации
TOP_K_CLAMP=50                          # Ограничение retrieve
```

### Rate Limiting
```python
# api/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/answer")
@limiter.limit("10/minute")  # 10 запросов в минуту
async def answer(request: Request):
    pass
```

## Архитектура Sprint-3

### Компоненты
```
services/llm/
├── base.py          # LLMProvider interface
├── openrouter.py    # OpenRouter implementation
├── aistudio.py      # AI Studio implementation
├── workers_ai.py    # Workers AI implementation
└── ollama.py        # Ollama implementation

services/prompt/
└── answer.py        # Prompt builder

services/answer/
├── orchestrator.py  # Main orchestrator
├── logging.py       # Cost tracking
├── guard.py         # Input validation
└── cache.py         # Answer caching

api/routers/
└── answer.py        # /answer endpoints
```

### Пайплайн
```
Query → Retrieve → Context Builder → Prompt → LLM → Response + Citations
```

### API Endpoints
```python
POST /answer
{
  "query": "Как работает RAG?",
  "top_k": 10,
  "rerank": false,
  "max_ctx": 2000,
  "model": "gpt-4o-mini",
  "temperature": 0.2,
  "stream": false
}

# Response
{
  "answer": "RAG (Retrieval-Augmented Generation)...",
  "citations": [
    {"doc_id": 1, "chunk_id": 5, "page": 2, "score": 0.85}
  ],
  "usage": {
    "in_tokens": 150,
    "out_tokens": 200,
    "latency_ms": 1200,
    "provider": "openrouter",
    "model": "gpt-4o-mini",
    "cost_usd": 0.002
  }
}
```

## Следующие шаги

1. **Выбрать провайдера** и настроить ENV
2. **Создать golden set** тестов
3. **Настроить CORS** для фронтенда
4. **Добавить rate limiting**
5. **Начать Sprint-3** с LLM провайдеров

## Риски и митигация

### Риски
- **API costs**: Rate limiting и мониторинг
- **Latency**: Кэширование ответов
- **Quality**: Golden set тесты
- **Reliability**: Fallback провайдеры

### Митигация
- **Cost tracking**: Подробное логирование
- **Caching**: TTL-based кэш
- **Testing**: Автоматические e2e тесты
- **Monitoring**: Health checks и метрики
