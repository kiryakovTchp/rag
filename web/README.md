# PromoAI Frontend

Объединенный фронтенд для PromoAI, включающий лендинг и SPA приложение с интеграцией реального бэкенда.

## 🚀 Быстрый старт

### Предварительные требования

- Node.js 18+ 
- npm или yarn

### Установка зависимостей

```bash
npm install
```

### Настройка окружения

Скопируйте `.env.example` в `.env.local` и настройте переменные:

```bash
cp env.example .env.local
```

Основные переменные:
- `VITE_API_BASE_URL` - URL вашего FastAPI бэкенда
- `VITE_WS_URL` - URL WebSocket для real-time обновлений
- `VITE_AUTH_ENABLED` - включить/выключить авторизацию
- `VITE_TENANT_ID` - ID тенанта для разработки

### Запуск в режиме разработки

```bash
npm run dev
```

Приложение будет доступно по адресу: http://localhost:3000

### Сборка для продакшена

```bash
npm run build
```

Собранные файлы будут в папке `dist/`

### Предварительный просмотр сборки

```bash
npm run preview
```

## 🏗️ Архитектура

### Структура проекта

```
src/
├── components/          # UI компоненты
│   └── ui/            # Базовые компоненты (Button, Input, Card, etc.)
├── pages/              # Страницы приложения
│   ├── Landing.tsx    # Маркетинговый лендинг
│   ├── Login.tsx      # Страница входа
│   ├── Register.tsx   # Страница регистрации
│   └── Dashboard.tsx  # Главная страница приложения
├── contexts/           # React контексты
│   └── AuthContext.tsx # Контекст аутентификации
├── services/           # API сервисы
│   └── api.ts         # Основной API клиент
├── hooks/              # Кастомные хуки
│   └── useJobsWebSocket.ts # WebSocket хук для jobs
├── types/              # TypeScript типы
│   └── index.ts       # Основные типы приложения
└── utils/              # Утилиты
```

### Технологии

- **React 18** - основной фреймворк
- **TypeScript** - типизация
- **Vite** - сборщик и dev сервер
- **React Router** - маршрутизация
- **Tailwind CSS** - стилизация
- **Framer Motion** - анимации
- **Lucide React** - иконки

## 🔌 Интеграция с бэкендом

### API Endpoints

Приложение интегрируется со следующими эндпоинтами:

- **Auth**: `/auth/login`, `/auth/register`, `/auth/profile`
- **Documents**: `/documents`, `/ingest`
- **Jobs**: `/jobs`
- **Search**: `/query`
- **WebSocket**: `/ws/jobs`

### WebSocket

Real-time обновления jobs через WebSocket с автоматическим реконнектом и обработкой ошибок:

- Код 4000: Redis недоступен
- Код 4001: Неавторизован
- Код 4002: Нет tenant_id

## 🎨 UI Компоненты

### Базовые компоненты

Все компоненты поддерживают:
- Различные варианты (`variant`)
- Размеры (`size`)
- Состояния (`disabled`, `loading`)
- Кастомные классы (`className`)

### Цветовая схема

Используется OKLCH палитра с CSS переменными:
- `primary` - основные цвета
- `secondary` - вторичные цвета  
- `muted` - приглушенные цвета
- `success`, `warning`, `error` - статусные цвета

## 🧪 Тестирование

### Запуск тестов

```bash
npm test
```

### E2E тесты

```bash
npm run test:e2e
```

## 📱 Адаптивность

Приложение полностью адаптивно и оптимизировано для:
- Мобильных устройств
- Планшетов
- Десктопов

Используется mobile-first подход с Tailwind CSS breakpoints.

## 🚀 Развертывание

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### CI/CD

Пример GitHub Actions workflow:

```yaml
name: Deploy Frontend
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - run: npm run test
```

## 🔧 Разработка

### Добавление новых страниц

1. Создайте компонент в `src/pages/`
2. Добавьте роут в `src/App.tsx`
3. Обновите навигацию в `src/components/AppShell.tsx`

### Добавление новых API методов

1. Добавьте метод в `src/services/api.ts`
2. Создайте соответствующие типы в `src/types/index.ts`
3. Используйте в компонентах

### Стилизация

Используйте Tailwind CSS классы. Для сложных стилей создавайте компоненты в `src/components/ui/`.

## 📚 Документация

- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Router](https://reactrouter.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [Vite](https://vitejs.dev/guide/)

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature ветку
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License
