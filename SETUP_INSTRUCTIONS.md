# Инструкции по установке инструментов разработки

## ✅ Уже установлено
- Python 3.9.6
- pip (обновлен до 25.2)
- Все Python пакеты для проекта:
  - FastAPI + Uvicorn
  - SQLAlchemy + psycopg
  - Redis
  - pre-commit, black, ruff, mypy
  - types-redis

## 🔄 Нужно установить

### 1. Docker Desktop
- Скачан файл: `~/Downloads/Docker.dmg`
- Откройте файл и перетащите Docker в Applications
- Запустите Docker Desktop
- Дождитесь, пока Docker Engine запустится

### 2. Homebrew (опционально)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 3. GitHub CLI (опционально)
```bash
brew install gh
```

## 🚀 Как запустить проект

### Без Docker (текущий способ)
```bash
# 1. Установить pre-commit хуки
pre-commit install

# 2. Запустить API
uvicorn api.main:app --reload --port 8000

# 3. Проверить работу
curl http://localhost:8000/healthz
```

### С Docker (после установки Docker Desktop)
```bash
# 1. Поднять базу данных и Redis
docker compose -f infra/docker-compose.yml up -d db redis

# 2. Запустить API
uvicorn api.main:app --reload --port 8000
```

## 📋 Проверка установки
```bash
# Проверить Python
python3 --version

# Проверить pip
pip3 --version

# Проверить Docker (после установки)
docker --version

# Проверить pre-commit
pre-commit --version
```

## 🎯 Что работает сейчас
- ✅ API запускается: `uvicorn api.main:app --reload --port 8000`
- ✅ /healthz endpoint работает: `curl http://localhost:8000/healthz`
- ✅ Все линтеры проходят: `pre-commit run -a`
- ✅ Код отправлен в репозиторий: `https://github.com/kiryakovTchp/rag`
