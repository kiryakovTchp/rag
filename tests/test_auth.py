"""Test authentication functionality."""

import unittest
import jwt
import hashlib
from unittest.mock import Mock, patch
from fastapi import HTTPException
from datetime import datetime

from api.auth import validate_jwt_token, validate_api_key, require_auth
from db.models import APIKey


class TestAuth(unittest.TestCase):
    """Test authentication functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
    
    @patch.dict('os.environ', {'NEXTAUTH_SECRET': 'test_secret'})
    def test_validate_jwt_token_valid(self):
        """Test valid JWT token validation."""
        # Create a valid JWT token
        payload = {
            "tenant_id": "test_tenant",
            "user_id": "test_user",
            "role": "user"
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        result = validate_jwt_token(token)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["tenant_id"], "test_tenant")
        self.assertEqual(result["user_id"], "test_user")
        self.assertEqual(result["role"], "user")
    
    @patch.dict('os.environ', {'NEXTAUTH_SECRET': 'test_secret'})
    def test_validate_jwt_token_invalid(self):
        """Test invalid JWT token validation."""
        # Invalid token
        result = validate_jwt_token("invalid_token")
        self.assertIsNone(result)
        
        # Token with wrong secret
        payload = {"tenant_id": "test_tenant"}
        token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        result = validate_jwt_token(token)
        self.assertIsNone(result)
    
    @patch.dict('os.environ', {})
    def test_validate_jwt_token_no_secret(self):
        """Test JWT validation without secret."""
        result = validate_jwt_token("any_token")
        self.assertIsNone(result)
    
    def test_validate_api_key_valid(self):
        """Test valid API key validation."""
        # Create mock API key
        api_key = "pk_test_key_123"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        mock_db_key = Mock()
        mock_db_key.tenant_id = "test_tenant"
        mock_db_key.role = "user"
        mock_db_key.id = 1
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_db_key
        
        result = validate_api_key(api_key, self.mock_db)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["tenant_id"], "test_tenant")
        self.assertEqual(result["user_id"], "api_key_1")
        self.assertEqual(result["role"], "user")
    
    def test_validate_api_key_invalid(self):
        """Test invalid API key validation."""
        # Non-existent key
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = validate_api_key("invalid_key", self.mock_db)
        self.assertIsNone(result)
    
    def test_validate_api_key_revoked(self):
        """Test revoked API key validation."""
        # Create mock revoked API key
        api_key = "pk_test_key_123"
        
        mock_db_key = Mock()
        mock_db_key.revoked_at = datetime.utcnow()  # Revoked
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_db_key
        
        result = validate_api_key(api_key, self.mock_db)
        self.assertIsNone(result)
    
    @patch.dict('os.environ', {'REQUIRE_AUTH': 'true'})
    def test_require_auth_true(self):
        """Test require_auth when enabled."""
        self.assertTrue(require_auth())
    
    @patch.dict('os.environ', {'REQUIRE_AUTH': 'false'})
    def test_require_auth_false(self):
        """Test require_auth when disabled."""
        self.assertFalse(require_auth())
    
    @patch.dict('os.environ', {})
    def test_require_auth_default(self):
        """Test require_auth default value."""
        self.assertFalse(require_auth())


if __name__ == "__main__":
    unittest.main()
