# PromoAI RAG System

Полноценная система RAG (Retrieval-Augmented Generation) для интеллектуального поиска и анализа документов с объединенным фронтендом и бэкендом.

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.9+
- Node.js 18+
- PostgreSQL 16+ с расширением pgvector
- Redis 7+
- Docker и Docker Compose

### Запуск всей системы

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd rag
```

2. **Запустите бэкенд и базы данных:**
```bash
# Запуск PostgreSQL, Redis и API
make up

# Или вручную:
docker-compose up -d postgres redis
cd api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. **Запустите Celery workers:**
```bash
cd workers && celery -A app worker --loglevel=info
```

4. **Запустите фронтенд:**
```bash
cd web
npm install
npm run dev
```

5. **Откройте в браузере:**
- Фронтенд: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🏗️ Архитектура

### Бэкенд (Python/FastAPI)

- **API**: FastAPI с аутентификацией JWT
- **База данных**: PostgreSQL + pgvector для векторного поиска
- **Очереди**: Celery + Redis для асинхронной обработки
- **Векторные эмбеддинги**: OpenAI/Anthropic API
- **WebSocket**: Real-time обновления статуса задач

### Фронтенд (React/TypeScript)

- **Фреймворк**: React 18 + TypeScript
- **Сборщик**: Vite
- **Стили**: Tailwind CSS с OKLCH цветовой палитрой
- **Роутинг**: React Router
- **Анимации**: Framer Motion
- **Состояние**: React Context + Hooks

### Компоненты системы

```
├── api/                 # FastAPI бэкенд
│   ├── routers/        # API роутеры
│   ├── models.py       # Pydantic модели
│   ├── websocket.py    # WebSocket обработчики
│   └── tracing.py      # OpenTelemetry + Prometheus
├── workers/            # Celery workers
│   ├── app.py         # Celery приложение
│   └── tracing.py     # Worker метрики
├── web/               # React фронтенд
│   ├── src/pages/     # Страницы приложения
│   ├── src/components/# UI компоненты
│   └── src/services/  # API клиенты
├── services/          # Бизнес-логика
├── infra/            # Docker конфигурации
└── docs/             # Документация
```

## 🔌 API Endpoints

### Аутентификация
- `POST /auth/login` - Вход в систему
- `POST /auth/register` - Регистрация
- `GET /auth/profile` - Профиль пользователя

### Документы
- `GET /documents` - Список документов
- `POST /ingest` - Загрузка документа
- `GET /documents/{id}` - Получение документа

### Поиск
- `POST /query` - AI поиск по документам
- `GET /ws/jobs` - WebSocket для статуса задач

### Администрирование
- `GET /usage` - Статистика использования
- `GET /keys` - API ключи
- `GET /metrics` - Prometheus метрики

## 🎨 Фронтенд страницы

### Публичные
- **Landing** (`/`) - Маркетинговый лендинг с описанием возможностей
- **Login** (`/login`) - Страница входа
- **Register** (`/register`) - Страница регистрации

### Защищенные (требуют авторизации)
- **Dashboard** (`/dashboard`) - Главная страница с обзором
- **Documents** (`/documents`) - Управление документами
- **Search** (`/search`) - AI поиск по документам

## 🚀 Возможности

### Для пользователей
- 📄 Загрузка документов (PDF, DOCX, XLSX, PPTX, TXT, HTML)
- 🔍 AI поиск с цитатами и источниками
- 📊 Отслеживание статуса обработки в реальном времени
- 👥 Командная работа с документами
- 🔐 Безопасная аутентификация и авторизация

### Для разработчиков
- 🏗️ Модульная архитектура с четким разделением ответственности
- 📱 Адаптивный UI с современным дизайном
- 🔌 REST API с OpenAPI документацией
- 📡 WebSocket для real-time обновлений
- 📊 OpenTelemetry + Prometheus для мониторинга

## 🧪 Тестирование

### Бэкенд тесты
```bash
# Запуск всех тестов
pytest

# Тесты с покрытием
pytest --cov=api --cov=services --cov=workers

# E2E тесты
pytest tests/test_integration.py
```

### Фронтенд тесты
```bash
cd web
npm test              # Unit тесты
npm run test:e2e      # E2E тесты
```

## 📊 Мониторинг

### Метрики
- Latency API запросов (P50, P95, P99)
- Количество запросов по тенантам
- Время обработки документов
- Статус Redis и WebSocket соединений

### Дашборды
- Grafana дашборды для API и workers
- Prometheus алерты для критических метрик
- Jaeger для трассировки запросов

## 🔧 Конфигурация

### Переменные окружения

#### Бэкенд (.env)
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/promoai
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

#### Фронтенд (web/.env.local)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_AUTH_ENABLED=true
VITE_TENANT_ID=dev-tenant
```

## 🚀 Развертывание

### Docker Compose
```bash
# Продакшн
docker-compose -f infra/docker-compose.yml up -d

# С observability stack
docker-compose -f infra/observability.yml up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

## 📚 Документация

- [API Reference](http://localhost:8000/docs) - Swagger UI
- [Architecture Decisions](docs/adr/) - ADR записи
- [Engineering Log](docs/ENGINEERING_LOG.md) - Лог разработки
- [Setup Instructions](SETUP_INSTRUCTIONS.md) - Детальные инструкции по установке

## 🤝 Вклад в проект

1. Создайте Issue с описанием проблемы/фичи
2. Форкните репозиторий
3. Создайте feature ветку: `git checkout -b feature/amazing-feature`
4. Внесите изменения и закоммитьте: `git commit -m 'feat: add amazing feature'`
5. Запушьте в форк: `git push origin feature/amazing-feature`
6. Создайте Pull Request

### Commit Convention
Используем [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - новые возможности
- `fix:` - исправления багов
- `docs:` - документация
- `style:` - форматирование кода
- `refactor:` - рефакторинг
- `test:` - тесты
- `chore:` - обновления зависимостей

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл для деталей.

## 🆘 Поддержка

- 📧 Email: support@promo.ai
- 💬 Discord: [PromoAI Community](https://discord.gg/promoai)
- 📖 Документация: [docs.promo.ai](https://docs.promo.ai)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/promoai/rag/issues)

---

**PromoAI RAG System** - Интеллектуальный поиск по документам с AI 🚀
