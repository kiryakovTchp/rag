"""Test authentication functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

from api.main import app
from db.models import User

client = TestClient(app)


class TestAuthentication:
    """Test authentication functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.secret = "test_secret_key"
        self.valid_payload = {
            "sub": "test_user_123",
            "tenant_id": "test_tenant",
            "email": "test@example.com",
            "role": "user",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

    def test_jwt_authentication_success(self):
        """Test successful JWT authentication."""
        with patch.dict("os.environ", {"NEXTAUTH_SECRET": self.secret}):
            token = jwt.encode(self.valid_payload, self.secret, algorithm="HS256")

            with patch("api.dependencies.auth.get_current_user") as mock_auth:
                mock_user = User(
                    id="test_user_123",
                    tenant_id="test_tenant",
                    email="test@example.com",
                    role="user",
                )
                mock_auth.return_value = mock_user

                response = client.get(
                    "/me", headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code == 200

    def test_jwt_authentication_invalid_token(self):
        """Test JWT authentication with invalid token."""
        with patch.dict("os.environ", {"NEXTAUTH_SECRET": self.secret}):
            response = client.get(
                "/me", headers={"Authorization": "Bearer invalid_token"}
            )
            assert response.status_code == 401

    def test_jwt_authentication_no_token(self):
        """Test JWT authentication without token."""
        response = client.get("/me")
        assert response.status_code == 401

    def test_api_key_authentication_success(self):
        """Test successful API key authentication."""
        with patch("api.dependencies.auth.get_current_user_api_key") as mock_auth:
            mock_user = User(
                id="api_123", tenant_id="test_tenant", email="", role="user"
            )
            mock_auth.return_value = mock_user

            response = client.get(
                "/me", headers={"Authorization": "Bearer pk_test_key"}
            )
            assert response.status_code == 200

    def test_api_key_header_authentication_success(self):
        """Test successful API key authentication via X-API-Key header."""
        with patch(
            "api.dependencies.auth.get_current_user_api_key_header"
        ) as mock_auth:
            mock_user = User(
                id="api_123", tenant_id="test_tenant", email="", role="user"
            )
            mock_auth.return_value = mock_user

            response = client.get("/me", headers={"X-API-Key": "pk_test_key"})
            assert response.status_code == 200

    def test_api_key_authentication_invalid_key(self):
        """Test API key authentication with invalid key."""
        with patch("api.dependencies.auth.get_current_user_api_key") as mock_auth:
            mock_auth.return_value = None

            response = client.get(
                "/me", headers={"Authorization": "Bearer pk_invalid_key"}
            )
            assert response.status_code == 401

    def test_authentication_priority(self):
        """Test authentication priority (API key over JWT)."""
        with patch(
            "api.dependencies.auth.get_current_user_api_key"
        ) as mock_api_key, patch(
            "api.dependencies.auth.get_current_user_api_key_header"
        ) as mock_api_header, patch(
            "api.dependencies.auth.get_current_user"
        ) as mock_jwt:
            # API key should be tried first
            mock_user = User(
                id="api_123", tenant_id="test_tenant", email="", role="user"
            )
            mock_api_key.return_value = mock_user
            mock_api_header.return_value = None

            token = jwt.encode(self.valid_payload, self.secret, algorithm="HS256")
            response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

            # Should use API key, not JWT
            mock_api_key.assert_called_once()
            mock_jwt.assert_not_called()


class TestAPIKeyManagement:
    """Test API key management endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.secret = "test_secret_key"
        self.valid_payload = {
            "sub": "test_user_123",
            "tenant_id": "test_tenant",
            "email": "test@example.com",
            "role": "user",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

    @patch("api.routers.auth.get_current_user")
    @patch("api.routers.auth.get_db")
    def test_create_api_key_success(self, mock_db, mock_auth):
        """Test successful API key creation."""
        # Mock user
        mock_user = User(
            id="test_user_123",
            tenant_id="test_tenant",
            email="test@example.com",
            role="user",
        )
        mock_auth.return_value = mock_user

        # Mock database
        mock_session = Mock()
        mock_db.return_value = mock_session

        token = jwt.encode(self.valid_payload, self.secret, algorithm="HS256")

        response = client.post(
            "/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "user"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert data["tenant_id"] == "test_tenant"
        assert data["role"] == "user"

    @patch("api.routers.auth.get_current_user")
    @patch("api.routers.auth.get_db")
    def test_list_api_keys_success(self, mock_db, mock_auth):
        """Test successful API key listing."""
        # Mock user
        mock_user = User(
            id="test_user_123",
            tenant_id="test_tenant",
            email="test@example.com",
            role="user",
        )
        mock_auth.return_value = mock_user

        # Mock database
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []
        mock_db.return_value = mock_session

        token = jwt.encode(self.valid_payload, self.secret, algorithm="HS256")

        response = client.get("/api-keys", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.auth.get_current_user")
    @patch("api.routers.auth.get_db")
    def test_revoke_api_key_success(self, mock_db, mock_auth):
        """Test successful API key revocation."""
        # Mock user
        mock_user = User(
            id="test_user_123",
            tenant_id="test_tenant",
            email="test@example.com",
            role="user",
        )
        mock_auth.return_value = mock_user

        # Mock database
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_api_key = Mock()
        mock_api_key.revoked_at = None

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_api_key
        mock_db.return_value = mock_session

        token = jwt.encode(self.valid_payload, self.secret, algorithm="HS256")

        response = client.delete(
            "/api-keys/123", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "API key revoked successfully"

    @patch("api.routers.auth.get_current_user")
    @patch("api.routers.auth.get_db")
    def test_revoke_api_key_not_found(self, mock_db, mock_auth):
        """Test API key revocation when key not found."""
        # Mock user
        mock_user = User(
            id="test_user_123",
            tenant_id="test_tenant",
            email="test@example.com",
            role="user",
        )
        mock_auth.return_value = mock_user

        # Mock database
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        mock_db.return_value = mock_session

        token = jwt.encode(self.valid_payload, self.secret, algorithm="HS256")

        response = client.delete(
            "/api-keys/999", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "API key not found"


class TestUserInfo:
    """Test user information endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.secret = "test_secret_key"
        self.valid_payload = {
            "sub": "test_user_123",
            "tenant_id": "test_tenant",
            "email": "test@example.com",
            "role": "user",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

    @patch("api.routers.auth.get_current_user")
    def test_get_current_user_info(self, mock_auth):
        """Test getting current user information."""
        # Mock user
        mock_user = User(
            id="test_user_123",
            tenant_id="test_tenant",
            email="test@example.com",
            role="user",
        )
        mock_auth.return_value = mock_user

        token = jwt.encode(self.valid_payload, self.secret, algorithm="HS256")

        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_user_123"
        assert data["email"] == "test@example.com"
        assert data["tenant_id"] == "test_tenant"
        assert data["role"] == "user"


if __name__ == "__main__":
    pytest.main([__file__])
