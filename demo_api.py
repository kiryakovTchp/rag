#!/usr/bin/env python3
"""
Демонстрация API PromoAI RAG
"""

import json
import time
from typing import Any, Dict, Optional

import requests  # type: ignore


def test_health() -> bool:
    """Тест health endpoint"""
    print("🔍 Тестируем health endpoint...")
    try:
        response = requests.get("http://localhost:8000/healthz")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_ingest() -> Optional[int]:
    """Тест ingest endpoint"""
    print("📤 Тестируем ingest endpoint...")
    try:
        # Создаем тестовый файл
        test_content = """# Test Document

This is a test document for the RAG system.

## Section 1
Some content here.

## Section 2
More content with **bold** and *italic* text.

| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |
"""

        files = {"file": ("test_document.txt", test_content, "text/plain")}
        data = {"tenant_id": "test", "safe_mode": "false"}

        response = requests.post("http://localhost:8000/ingest", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ingest successful: {result}")
            return result["job_id"]
        else:
            print(f"❌ Ingest failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ingest error: {e}")
        return None


def test_job_status(job_id: int) -> Optional[Dict[str, Any]]:
    """Тест job status endpoint"""
    print(f"📊 Тестируем job status для job_id={job_id}...")
    try:
        max_attempts = 30
        for _ in range(max_attempts):
            response = requests.get(f"http://localhost:8000/ingest/{job_id}")

            if response.status_code == 200:
                result = response.json()
                status = result["status"]
                progress = result["progress"]

                print(f"📈 Status: {status}, Progress: {progress}%")

                if status == "done":
                    print("✅ Job completed successfully!")
                    return result
                elif status == "error":
                    print(f"❌ Job failed: {result.get('error', 'Unknown error')}")
                    return result
                else:
                    time.sleep(2)
            else:
                print(f"❌ Job status failed: {response.status_code}")
                return None

        print("⏰ Job timeout")
        return None
    except Exception as e:
        print(f"❌ Job status error: {e}")
        return None


def main() -> None:
    """Основная функция демонстрации"""
    print("🚀 Демонстрация PromoAI RAG API")
    print("=" * 50)

    # Тест 1: Health check
    if not test_health():
        print("❌ Health check failed, exiting")
        return

    # Тест 2: Ingest
    job_id = test_ingest()
    if not job_id:
        print("❌ Ingest failed, exiting")
        return

    # Тест 3: Job status polling
    result = test_job_status(job_id)
    if result:
        print("🎉 Демонстрация завершена успешно!")
        print(f"📋 Результат: {json.dumps(result, indent=2)}")
    else:
        print("❌ Демонстрация завершена с ошибками")


if __name__ == "__main__":
    main()
