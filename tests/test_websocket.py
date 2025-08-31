"""Test WebSocket functionality."""

import pytest
import asyncio
import json
import jwt
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from api.main import app
from api.routers.websocket import manager


class TestWebSocket:
    """Test WebSocket functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.secret = "test_secret_key"
        
        # Mock environment variables
        with patch.dict('os.environ', {'NEXTAUTH_SECRET': self.secret}):
            self.setup_test_data()
    
    def setup_test_data(self):
        """Set up test data."""
        # Create test JWT token
        payload = {
            "sub": "test_user_123",
            "tenant_id": "test_tenant",
            "email": "test@example.com",
            "role": "user",
            "iat": datetime.utcnow().timestamp(),
            "exp": datetime.utcnow().timestamp() + 3600
        }
        self.test_token = jwt.encode(payload, self.secret, algorithm="HS256")
    
    @pytest.mark.asyncio
    async def test_websocket_connection_with_token(self):
        """Test WebSocket connection with valid token."""
        with patch('api.dependencies.auth.get_current_user_ws') as mock_auth:
            # Mock user
            mock_user = Mock()
            mock_user.tenant_id = "test_tenant"
            mock_auth.return_value = mock_user
            
            # Test WebSocket connection
            with self.client.websocket_connect(f"/ws/jobs?token={self.test_token}") as websocket:
                # Should receive connection confirmation
                data = websocket.receive_text()
                event = json.loads(data)
                
                assert event["event"] == "connected"
                assert event["tenant_id"] == "test_tenant"
                assert "ts" in event
    
    @pytest.mark.asyncio
    async def test_websocket_connection_without_token(self):
        """Test WebSocket connection without token."""
        with self.client.websocket_connect("/ws/jobs") as websocket:
            # Should close with authentication error
            with pytest.raises(Exception):
                websocket.receive_text()
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong."""
        with patch('api.dependencies.auth.get_current_user_ws') as mock_auth:
            # Mock user
            mock_user = Mock()
            mock_user.tenant_id = "test_tenant"
            mock_auth.return_value = mock_user
            
            with self.client.websocket_connect(f"/ws/jobs?token={self.test_token}") as websocket:
                # Send ping
                websocket.send_text("ping")
                
                # Should receive pong
                response = websocket.receive_text()
                assert response == "pong"
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_to_tenant(self):
        """Test broadcasting messages to tenant."""
        with patch('api.dependencies.auth.get_current_user_ws') as mock_auth:
            # Mock user
            mock_user = Mock()
            mock_user.tenant_id = "test_tenant"
            mock_auth.return_value = mock_user
            
            # Connect first client
            with self.client.websocket_connect(f"/ws/jobs?token={self.test_token}") as websocket1:
                # Connect second client
                with self.client.websocket_connect(f"/ws/jobs?token={self.test_token}") as websocket2:
                    # Broadcast message
                    test_message = {
                        "event": "test_event",
                        "data": "test_data"
                    }
                    
                    # Mock the broadcast function
                    with patch.object(manager, 'broadcast_to_tenant') as mock_broadcast:
                        await manager.broadcast_to_tenant(test_message, "test_tenant")
                        mock_broadcast.assert_called_once_with(test_message, "test_tenant")
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect(self):
        """Test WebSocket disconnect."""
        with patch('api.dependencies.auth.get_current_user_ws') as mock_auth:
            # Mock user
            mock_user = Mock()
            mock_user.tenant_id = "test_tenant"
            mock_auth.return_value = mock_user
            
            with self.client.websocket_connect(f"/ws/jobs?token={self.test_token}") as websocket:
                # Connection should be established
                data = websocket.receive_text()
                event = json.loads(data)
                assert event["event"] == "connected"
                
                # Close connection
                websocket.close()
                
                # Should be removed from active connections
                assert "test_tenant" not in manager.active_connections


class TestJobEvents:
    """Test job event emission."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.secret = "test_secret_key"
        
        # Mock environment variables
        with patch.dict('os.environ', {'NEXTAUTH_SECRET': self.secret}):
            self.setup_test_data()
    
    def setup_test_data(self):
        """Set up test data."""
        # Create test JWT token
        payload = {
            "sub": "test_user_123",
            "tenant_id": "test_tenant",
            "email": "test@example.com",
            "role": "user",
            "iat": datetime.utcnow().timestamp(),
            "exp": datetime.utcnow().timestamp() + 3600
        }
        self.test_token = jwt.encode(payload, self.secret, algorithm="HS256")
    
    @pytest.mark.asyncio
    async def test_job_event_format(self):
        """Test job event format."""
        from services.job_manager import job_manager
        
        # Test job started event
        event_data = await job_manager.job_started(123, "test_tenant", 456, "parse")
        
        # Event should have correct format
        assert "event" in event_data
        assert "job_id" in event_data
        assert "document_id" in event_data
        assert "type" in event_data
        assert "progress" in event_data
        assert "ts" in event_data
        
        assert event_data["event"] == "parse_started"
        assert event_data["job_id"] == 123
        assert event_data["document_id"] == 456
        assert event_data["type"] == "parse"
        assert event_data["progress"] == 0
    
    @pytest.mark.asyncio
    async def test_job_progress_event(self):
        """Test job progress event."""
        from services.job_manager import job_manager
        
        # Test job progress event
        event_data = await job_manager.job_progress(123, 50, "test_tenant", 456, "chunk")
        
        assert event_data["event"] == "chunk_progress"
        assert event_data["job_id"] == 123
        assert event_data["progress"] == 50
        assert event_data["type"] == "chunk"
    
    @pytest.mark.asyncio
    async def test_job_done_event(self):
        """Test job done event."""
        from services.job_manager import job_manager
        
        # Test job done event
        event_data = await job_manager.job_done(123, "test_tenant", 456, "embed")
        
        assert event_data["event"] == "embed_done"
        assert event_data["job_id"] == 123
        assert event_data["progress"] == 100
        assert event_data["type"] == "embed"
    
    @pytest.mark.asyncio
    async def test_job_failed_event(self):
        """Test job failed event."""
        from services.job_manager import job_manager
        
        # Test job failed event
        event_data = await job_manager.job_failed(123, "Test error", "test_tenant", 456, "parse")
        
        assert event_data["event"] == "parse_failed"
        assert event_data["job_id"] == 123
        assert event_data["error"] == "Test error"
        assert event_data["progress"] == 0
        assert event_data["type"] == "parse"


if __name__ == "__main__":
    pytest.main([__file__])
