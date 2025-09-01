# PromoAI RAG - Интеллектуальная система поиска по документам

Полнофункциональная RAG (Retrieval-Augmented Generation) система с веб-интерфейсом, API и интеграцией с Google OAuth.

## 🚀 Быстрый старт

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/kiryakovTchp/rag.git
cd rag

# Настройте Google OAuth (см. docs/GOOGLE_OAUTH_SETUP.md)
cp env.example .env
# Отредактируйте .env файл

# Запустите весь проект
./start.sh

# Или используйте Makefile
make start
```

### Вариант 2: Ручной запуск

```bash
# Установите зависимости
make install-deps

# Запустите базу данных и Redis
docker-compose up -d postgres redis

# Запустите API
cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# В другом терминале запустите фронтенд
cd web && npm run dev
```

## 🏗️ Архитектура

### Backend
- **FastAPI** - веб-фреймворк
- **PostgreSQL + pgvector** - база данных с векторным поиском
- **Redis** - кэширование и очереди
- **Celery** - асинхронные задачи
- **OpenTelemetry** - наблюдаемость

### Frontend
- **React 18** - пользовательский интерфейс
- **TypeScript** - типобезопасность
- **Vite** - сборка и dev сервер
- **Tailwind CSS** - стилизация
- **React Router** - навигация

### Мониторинг
- **Prometheus** - метрики
- **Grafana** - дашборды
- **OpenTelemetry** - трассировка

## 🔐 Аутентификация

### Google OAuth
- Интеграция с Google для входа
- JWT токены для API
- Безопасные сессии

### Тестовый аккаунт
```bash
# Создать тестового пользователя
make test-user

# Данные для входа:
# Email: test@promoai.com
# Пароль: test123456
```

## 📱 Основные страницы

- **Landing** - маркетинговая страница
- **Login/Register** - аутентификация
- **Dashboard** - главная панель
- **Documents** - управление документами
- **Search** - AI поиск по документам
- **Settings** - настройки профиля

## 🛠️ Управление проектом

### Основные команды
```bash
make start          # Запустить весь проект
make stop           # Остановить все сервисы
make restart        # Перезапустить проект
make logs           # Показать логи
make status         # Статус сервисов
make health         # Проверить здоровье
```

### Разработка
```bash
make dev            # Режим разработки (без Docker)
make test-user      # Создать тестового пользователя
make install-deps   # Установить зависимости
```

### Администрирование
```bash
make db-shell       # Подключиться к базе данных
make redis-cli      # Подключиться к Redis
make api-shell      # Подключиться к API контейнеру
make frontend-shell # Подключиться к фронтенд контейнеру
```

## 🌐 Доступные сервисы

После запуска доступны:
- **Фронтенд**: http://localhost:3000
- **API**: http://localhost:8000
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **База данных**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Конфигурация

### Переменные окружения
Скопируйте `env.example` в `.env` и настройте:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=ваш-client-id
GOOGLE_CLIENT_SECRET=ваш-client-secret

# JWT
JWT_SECRET_KEY=ваш-секретный-ключ

# База данных
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_db

# Redis
REDIS_URL=redis://localhost:6379
```

### Google OAuth настройка
Подробная инструкция: [docs/GOOGLE_OAUTH_SETUP.md](docs/GOOGLE_OAUTH_SETUP.md)

## 📊 API Endpoints

### Аутентификация
- `POST /auth/login` - вход с email/password
- `POST /auth/register` - регистрация
- `POST /auth/google` - вход через Google
- `POST /auth/logout` - выход

### Документы
- `GET /documents` - список документов
- `POST /documents/upload` - загрузка документа
- `GET /documents/{id}` - получение документа
- `DELETE /documents/{id}` - удаление документа

### Поиск
- `POST /query` - AI поиск по документам
- `GET /ws/jobs` - WebSocket для отслеживания задач

### Пользователи
- `GET /user/profile` - профиль пользователя
- `PUT /user/profile` - обновление профиля
- `GET /user/keys` - API ключи
- `POST /user/keys` - создание API ключа

## 🧪 Тестирование

```bash
# Backend тесты
python -m pytest

# Frontend тесты
cd web && npm test

# E2E тесты
cd web && npm run test:e2e
```

## 📈 Мониторинг

### Prometheus метрики
- `query_latency_seconds` - задержка запросов
- `ingest_job_duration_seconds` - время обработки документов
- `tenant_queries_total` - количество запросов
- `redis_publish_failures_total` - ошибки Redis

### Grafana дашборды
- **Ingest** - загрузка и обработка документов
- **Query** - поиск и ответы
- **Realtime** - WebSocket соединения
- **Errors** - ошибки и исключения

## 🚀 Развертывание

### Production
```bash
# Сборка для продакшена
make build-frontend
make build-backend

# Запуск в production режиме
docker-compose -f docker-compose.prod.yml up -d
```

### Docker
```bash
# Сборка образов
docker-compose build

# Запуск
docker-compose up -d

# Остановка
docker-compose down
```

## 🤝 Разработка

### Структура проекта
```
rag/
├── api/                 # FastAPI backend
├── web/                 # React frontend
├── services/            # Бизнес-логика
├── workers/             # Celery workers
├── db/                  # База данных
├── infra/               # Docker конфигурация
├── docs/                # Документация
└── scripts/             # Скрипты
```

### Добавление новых функций
1. Создайте Issue с описанием
2. Создайте ветку: `git checkout -b feature/название-функции`
3. Реализуйте функциональность
4. Добавьте тесты
5. Создайте Pull Request

## 📚 Документация

- [Google OAuth Setup](docs/GOOGLE_OAUTH_SETUP.md)
- [Unification Report](docs/UNIFICATION_REPORT.md)
- [Engineering Log](docs/ENGINEERING_LOG.md)
- [ADR](docs/adr/)

## 🆘 Поддержка

### Решение проблем
```bash
# Проверить статус сервисов
make status

# Проверить здоровье
make health

# Показать логи
make logs

# Очистить и перезапустить
make clean && make start
```

### Частые проблемы
1. **Порт занят**: `docker-compose down` и перезапуск
2. **База не подключается**: проверьте `DATABASE_URL` в `.env`
3. **Google OAuth не работает**: проверьте настройки в Google Console

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## 👥 Команда

- **Ivan Kiryakov** - разработка и архитектура

---

**PromoAI RAG** - Интеллектуальный поиск по документам с AI 🚀
