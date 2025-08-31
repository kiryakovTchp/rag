#!/usr/bin/env python3
"""API Key Management Script."""

import argparse
import hashlib
import secrets
import sys
from datetime import datetime
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import APIKey


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"pk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def create_api_key(tenant_id: str, role: str = "user") -> str:
    """Create a new API key."""
    db = SessionLocal()
    try:
        # Generate API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Store in database
        db_key = APIKey(
            key_hash=key_hash,
            tenant_id=tenant_id,
            role=role
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        
        print(f"✅ API key created successfully!")
        print(f"   ID: {db_key.id}")
        print(f"   Tenant: {tenant_id}")
        print(f"   Role: {role}")
        print(f"   Created: {db_key.created_at}")
        print(f"   API Key: {api_key}")
        print("\n⚠️  IMPORTANT: Save this key now! It won't be shown again.")
        
        return api_key
        
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key."""
    db = SessionLocal()
    try:
        key_hash = hash_api_key(api_key)
        
        # Find and revoke the key
        db_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.revoked_at.is_(None)
        ).first()
        
        if not db_key:
            print(f"❌ API key not found or already revoked")
            return False
        
        db_key.revoked_at = datetime.utcnow()
        db.commit()
        
        print(f"✅ API key revoked successfully!")
        print(f"   ID: {db_key.id}")
        print(f"   Tenant: {db_key.tenant_id}")
        print(f"   Revoked: {db_key.revoked_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error revoking API key: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def list_api_keys(tenant_id: str = None) -> None:
    """List API keys."""
    db = SessionLocal()
    try:
        query = db.query(APIKey)
        if tenant_id:
            query = query.filter(APIKey.tenant_id == tenant_id)
        
        keys = query.order_by(APIKey.created_at.desc()).all()
        
        if not keys:
            print("No API keys found.")
            return
        
        print(f"Found {len(keys)} API key(s):")
        print("-" * 80)
        
        for key in keys:
            status = "ACTIVE" if key.revoked_at is None else "REVOKED"
            print(f"ID: {key.id}")
            print(f"Tenant: {key.tenant_id}")
            print(f"Role: {key.role}")
            print(f"Status: {status}")
            print(f"Created: {key.created_at}")
            if key.revoked_at:
                print(f"Revoked: {key.revoked_at}")
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error listing API keys: {e}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Manage API keys")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("tenant_id", help="Tenant ID")
    create_parser.add_argument("--role", default="user", help="Role (default: user)")
    
    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument("api_key", help="API key to revoke")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List API keys")
    list_parser.add_argument("--tenant", help="Filter by tenant ID")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_api_key(args.tenant_id, args.role)
    elif args.command == "revoke":
        revoke_api_key(args.api_key)
    elif args.command == "list":
        list_api_keys(args.tenant)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
