# Настройка Google OAuth для PromoAI RAG

## 🔑 Что нужно получить

Для работы Google OAuth вам понадобятся:
1. **Google Client ID** - идентификатор приложения
2. **Google Client Secret** - секретный ключ приложения

## 📋 Пошаговая инструкция

### 1. Создание проекта в Google Cloud Console

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google+ API и Google OAuth2 API

### 2. Настройка OAuth consent screen

1. В меню слева выберите "APIs & Services" → "OAuth consent screen"
2. Выберите "External" тип
3. Заполните обязательные поля:
   - App name: `PromoAI RAG`
   - User support email: ваш email
   - Developer contact information: ваш email
4. Добавьте scope: `email`, `profile`, `openid`
5. Добавьте тестовых пользователей (ваш email)

### 3. Создание OAuth 2.0 credentials

1. В меню слева выберите "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "OAuth 2.0 Client IDs"
3. Выберите "Web application"
4. Заполните поля:
   - Name: `PromoAI RAG Web Client`
   - Authorized JavaScript origins:
     - `http://localhost:3000`
     - `http://localhost:8000`
   - Authorized redirect URIs:
     - `http://localhost:3000/auth/google/callback`
     - `http://localhost:8000/auth/google/callback`
5. Нажмите "Create"

### 4. Получение credentials

После создания вы получите:
- **Client ID** (например: `123456789-abcdef.apps.googleusercontent.com`)
- **Client Secret** (например: `GOCSPX-abcdefghijklmnop`)

### 5. Настройка .env файла

Скопируйте `env.example` в `.env` и заполните:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=ваш-client-id
GOOGLE_CLIENT_SECRET=ваш-client-secret

# JWT
JWT_SECRET_KEY=ваш-супер-секретный-ключ

# Остальные переменные...
```

## 🚀 Тестирование

1. Запустите проект: `./start.sh`
2. Откройте http://localhost:3000
3. Попробуйте войти через Google

## 🔒 Безопасность

- **НИКОГДА** не коммитьте `.env` файл в Git
- Используйте сильный JWT_SECRET_KEY
- В продакшене используйте HTTPS
- Ограничьте redirect URIs только вашими доменами

## 🆘 Решение проблем

### Ошибка "redirect_uri_mismatch"
- Проверьте, что redirect URI в Google Console точно совпадает с вашим
- Убедитесь, что нет лишних слешей или пробелов

### Ошибка "invalid_client"
- Проверьте Client ID и Client Secret
- Убедитесь, что OAuth consent screen настроен правильно

### Ошибка "access_denied"
- Проверьте, что ваш email добавлен в тестовых пользователей
- Убедитесь, что приложение не в режиме "Testing"

## 📚 Полезные ссылки

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Playground](https://oauth2.googleapis.com/token)
