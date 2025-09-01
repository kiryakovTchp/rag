#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск PromoAI RAG проекта...${NC}"

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен. Установите Docker Desktop${NC}"
    exit 1
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен${NC}"
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден. Создаю из примера...${NC}"
    cp env.example .env
    echo -e "${YELLOW}⚠️  Отредактируйте .env файл с вашими Google OAuth данными${NC}"
    echo -e "${YELLOW}⚠️  Нажмите Enter когда будете готовы продолжить...${NC}"
    read
fi

# Останавливаем существующие контейнеры
echo -e "${BLUE}🛑 Останавливаю существующие контейнеры...${NC}"
docker-compose down

# Собираем и запускаем сервисы
echo -e "${BLUE}🔨 Собираю и запускаю сервисы...${NC}"
docker-compose up --build -d

# Ждем запуска сервисов
echo -e "${BLUE}⏳ Жду запуска сервисов...${NC}"
sleep 30

# Проверяем статус сервисов
echo -e "${BLUE}🔍 Проверяю статус сервисов...${NC}"
docker-compose ps

# Проверяем доступность API
echo -e "${BLUE}🔍 Проверяю API...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API доступен на http://localhost:8000${NC}"
else
    echo -e "${RED}❌ API недоступен${NC}"
fi

# Проверяем доступность фронтенда
echo -e "${BLUE}🔍 Проверяю фронтенд...${NC}"
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Фронтенд доступен на http://localhost:3000${NC}"
else
    echo -e "${RED}❌ Фронтенд недоступен${NC}"
fi

# Проверяем доступность Grafana
echo -e "${BLUE}🔍 Проверяю Grafana...${NC}"
if curl -f http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Grafana доступен на http://localhost:3001 (admin/admin)${NC}"
else
    echo -e "${RED}❌ Grafana недоступен${NC}"
fi

echo -e "${GREEN}🎉 Проект запущен!${NC}"
echo -e "${BLUE}📱 Фронтенд: http://localhost:3000${NC}"
echo -e "${BLUE}🔧 API: http://localhost:8000${NC}"
echo -e "${BLUE}📊 Grafana: http://localhost:3001 (admin/admin)${NC}"
echo -e "${BLUE}📈 Prometheus: http://localhost:9090${NC}"
echo -e "${BLUE}🗄️  База данных: localhost:5432${NC}"
echo -e "${BLUE}🔴 Redis: localhost:6379${NC}"
echo -e ""
echo -e "${YELLOW}💡 Для остановки: docker-compose down${NC}"
echo -e "${YELLOW}💡 Для просмотра логов: docker-compose logs -f${NC}"
