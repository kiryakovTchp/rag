#!/usr/bin/env python3
"""Test script for auth endpoints."""


import requests

BASE_URL = "http://localhost:8000"


def test_register():
    """Test user registration."""
    print("Testing user registration...")

    data = {"email": "test@example.com", "password": "testpassword123"}

    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json=data,
            headers={"Content-Type": "application/json"},
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 201:
            print("✅ Registration successful!")
            return response.json()
        else:
            print("❌ Registration failed!")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_login():
    """Test user login."""
    print("\nTesting user login...")

    data = {"email": "test@example.com", "password": "testpassword123"}

    try:
        response = requests.post(
            f"{BASE_URL}/login", json=data, headers={"Content-Type": "application/json"}
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ Login successful!")
            return response.json()
        else:
            print("❌ Login failed!")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_me(token):
    """Test getting user info."""
    print("\nTesting /me endpoint...")

    try:
        response = requests.get(
            f"{BASE_URL}/me", headers={"Authorization": f"Bearer {token}"}
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ /me successful!")
            return response.json()
        else:
            print("❌ /me failed!")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("🧪 Testing Auth Endpoints\n")

    # Test registration
    user = test_register()

    if user:
        # Test login
        login_result = test_login()

        if login_result and "access_token" in login_result:
            token = login_result["access_token"]
            print(f"\n🔑 Got token: {token[:20]}...")

            # Test /me endpoint
            test_me(token)
        else:
            print("❌ No token received from login")
    else:
        print("❌ Registration failed, skipping login test")

    print("\n🏁 Testing complete!")
