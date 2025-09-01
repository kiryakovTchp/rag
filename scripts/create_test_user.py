#!/usr/bin/env python3
"""
Скрипт для создания тестового пользователя в базе данных
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent.parent))

from passlib.context import CryptContext

from db.models import User
from db.session import get_db

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
        "full_name": "Тестовый Пользователь",
        "is_active": True,
        "is_superuser": False,
    }

    try:
        # Получаем сессию базы данных
        db = next(get_db())  # type: ignore

        # Проверяем, существует ли уже пользователь
        existing_user = db.query(User).filter(User.email == test_user_data["email"]).first()

        if existing_user:
            print(f"✅ Пользователь {test_user_data['email']} уже существует")
            return

        # Создаем нового пользователя
        hashed_password = hash_password(str(test_user_data["password"]))

        new_user = User(
            email=str(test_user_data["email"]),
            hashed_password=hashed_password,
            full_name=str(test_user_data["full_name"]),
            is_active=bool(test_user_data["is_active"]),
            is_superuser=bool(test_user_data["is_superuser"]),
        )

        db.add(new_user)
        db.commit()

        print("✅ Тестовый пользователь создан успешно!")
        print(f"📧 Email: {test_user_data['email']}")
        print(f"🔑 Пароль: {test_user_data['password']}")
        print(f"👤 Имя: {test_user_data['full_name']}")

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
