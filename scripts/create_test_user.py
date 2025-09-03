#!/usr/bin/env python3
"""
Скрипт для создания тестового пользователя в базе данных
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent.parent))

# Загружаем переменные окружения
from dotenv import load_dotenv

load_dotenv()

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import User

# Создаем прямое подключение к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хеширует пароль"""
    return pwd_context.hash(password)


async def create_test_user() -> None:
    """Создает тестового пользователя"""

    # Данные тестового пользователя
    test_user_data: dict[str, Any] = {
        "email": "test@promoai.com",
        "password": "test123456",
        "tenant_id": "test_tenant",
        "role": "user",
    }

    try:
        # Получаем сессию базы данных
        db = SessionLocal()

        # Проверяем, существует ли уже пользователь
        existing_user = (
            db.query(User).filter(User.email == test_user_data["email"]).first()
        )

        if existing_user:
            print(f"✅ Пользователь {test_user_data['email']} уже существует")
            return

        # Создаем нового пользователя
        hashed_password = hash_password(str(test_user_data["password"]))

        new_user = User(
            email=str(test_user_data["email"]),
            hashed_password=hashed_password,
            tenant_id=str(test_user_data["tenant_id"]),
            role=str(test_user_data["role"]),
        )

        db.add(new_user)
        db.commit()

        print("✅ Тестовый пользователь создан успешно!")
        print(f"📧 Email: {test_user_data['email']}")
        print(f"🔑 Пароль: {test_user_data['password']}")
        print(f"🏢 Tenant ID: {test_user_data['tenant_id']}")
        print(f"👤 Роль: {test_user_data['role']}")

    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {e}")
        if "db" in locals():
            db.rollback()
    finally:
        if "db" in locals():
            db.close()


if __name__ == "__main__":
    print("🚀 Создание тестового пользователя...")
    asyncio.run(create_test_user())
