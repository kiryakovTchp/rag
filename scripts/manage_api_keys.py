#!/usr/bin/env python3
"""Management script for API keys."""

import argparse
import hashlib
import os
import secrets
import sys
from datetime import datetime, timezone
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after adding to path
from api.dependencies.auth import get_current_user_api_key_header  # noqa: E402
from db.models import APIKey  # noqa: E402
from db.session import SessionLocal  # noqa: E402


def create_api_key(tenant_id: str, role: str = "user") -> Optional[str]:
    """Create a new API key."""

    # Generate API key
    api_key = f"pk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    db = SessionLocal()
    try:
        # Create API key record
        db_api_key = APIKey(key_hash=key_hash, tenant_id=tenant_id, role=role)

        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)

        print("✅ API key created successfully!")
        print(f"ID: {db_api_key.id}")
        print(f"Tenant: {tenant_id}")
        print(f"Role: {role}")
        print(f"Created: {db_api_key.created_at}")
        print("\n🔑 API Key (save this - it won't be shown again):")
        print(f"{api_key}")

        return api_key

    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def list_api_keys(tenant_id: Optional[str] = None):
    """List API keys."""
    db = SessionLocal()
    try:
        query = db.query(APIKey)
        if tenant_id:
            query = query.filter(APIKey.tenant_id == tenant_id)

        api_keys = query.all()

        if not api_keys:
            print("No API keys found.")
            return

        print(f"Found {len(api_keys)} API key(s):")
        print("-" * 80)

        for key in api_keys:
            status = (
                "ACTIVE" if key.revoked_at is None else f"REVOKED ({key.revoked_at})"
            )
            print(f"ID: {key.id}")
            print(f"Tenant: {key.tenant_id}")
            print(f"Role: {key.role}")
            print(f"Created: {key.created_at}")
            print(f"Status: {status}")
            print("-" * 80)

    except Exception as e:
        print(f"❌ Error listing API keys: {e}")
    finally:
        db.close()


def revoke_api_key(key_id: int):
    """Revoke an API key."""
    db = SessionLocal()
    try:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

        if not api_key:
            print(f"❌ API key with ID {key_id} not found.")
            return

        if api_key.revoked_at:
            print(f"❌ API key {key_id} is already revoked.")
            return

        api_key.revoked_at = datetime.now(timezone.utc)
        db.commit()

        print(f"✅ API key {key_id} revoked successfully.")

    except Exception as e:
        print(f"❌ Error revoking API key: {e}")
        db.rollback()
    finally:
        db.close()


def test_api_key(api_key: str):
    """Test an API key."""

    # Mock request
    class MockRequest:
        def __init__(self, headers):
            self.headers = headers

    request = MockRequest({"X-API-Key": api_key})

    # Test the key
    user = get_current_user_api_key_header(request)

    if user:
        print("✅ API key is valid!")
        print(f"User ID: {user.id}")
        print(f"Tenant: {user.tenant_id}")
        print(f"Role: {user.role}")
    else:
        print("❌ API key is invalid or revoked.")


def main():
    parser = argparse.ArgumentParser(description="Manage API keys")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("tenant_id", help="Tenant ID")
    create_parser.add_argument("--role", default="user", help="Role (default: user)")

    # List command
    list_parser = subparsers.add_parser("list", help="List API keys")
    list_parser.add_argument("--tenant-id", help="Filter by tenant ID")

    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument("key_id", type=int, help="API key ID")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test an API key")
    test_parser.add_argument("api_key", help="API key to test")

    args = parser.parse_args()

    if args.command == "create":
        create_api_key(args.tenant_id, args.role)
    elif args.command == "list":
        list_api_keys(args.tenant_id)
    elif args.command == "revoke":
        revoke_api_key(args.key_id)
    elif args.command == "test":
        test_api_key(args.api_key)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
