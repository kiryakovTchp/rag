"""Test WebSocket functionality."""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from websockets import connect
import websockets

from api.main import app
from api.websocket import manager, emit_job_event
from services.job_manager import job_manager


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    return {
        "tenant_id": "test_tenant",
        "user_id": "test_user",
        "role": "user"
    }


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection and message handling."""
    # Mock authentication
    with patch('api.auth.get_current_user_ws') as mock_auth:
        mock_auth.return_value = {
            "tenant_id": "test_tenant",
            "user_id": "test_user",
            "role": "user"
        }
        
        # Test connection
        async with connect("ws://localhost:8000/ws/jobs?token=test_token") as websocket:
            # Send a message to keep connection alive
            await websocket.send("ping")
            
            # Connection should be established
            assert websocket.open


@pytest.mark.asyncio
async def test_job_events():
    """Test job event emission."""
    # Create a test job
    job_id = job_manager.create_job(1, "parse", "test_tenant")
    
    # Test job started event
    await job_manager.job_started(job_id)
    
    # Test job progress event
    await job_manager.job_progress(job_id, 50)
    
    # Test job done event
    await job_manager.job_done(job_id)
    
    # Verify job state
    job = job_manager.jobs[job_id]
    assert job["status"] == "done"
    assert job["progress"] == 100


@pytest.mark.asyncio
async def test_emit_job_event():
    """Test emit_job_event function."""
    # Mock manager
    with patch.object(manager, 'send_personal_message') as mock_send:
        event_data = {
            "event": "parse_started",
            "job_id": 1,
            "document_id": 1,
            "type": "parse",
            "progress": 0
        }
        
        await emit_job_event("test_tenant", event_data)
        
        # Verify event was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        message = call_args[0][0]  # First argument is the message
        
        # Verify message format
        assert message["event"] == "parse_started"
        assert message["job_id"] == 1
        assert message["document_id"] == 1
        assert message["type"] == "parse"
        assert message["progress"] == 0
        assert "ts" in message  # Timestamp should be present


@pytest.mark.asyncio
async def test_websocket_unauthorized():
    """Test WebSocket connection without authentication."""
    with patch('api.auth.get_current_user_ws') as mock_auth:
        mock_auth.return_value = None
        
        # Should close with unauthorized code
        with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
            async with connect("ws://localhost:8000/ws/jobs") as websocket:
                pass
        
        assert exc_info.value.code == 4001


@pytest.mark.asyncio
async def test_websocket_no_tenant():
    """Test WebSocket connection without tenant ID."""
    with patch('api.auth.get_current_user_ws') as mock_auth:
        mock_auth.return_value = {"user_id": "test_user"}  # No tenant_id
        
        # Should close with no tenant code
        with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
            async with connect("ws://localhost:8000/ws/jobs") as websocket:
                pass
        
        assert exc_info.value.code == 4002


def test_job_manager_create_job():
    """Test job creation."""
    job_id = job_manager.create_job(1, "parse", "test_tenant")
    
    assert job_id in job_manager.jobs
    job = job_manager.jobs[job_id]
    
    assert job["document_id"] == 1
    assert job["type"] == "parse"
    assert job["tenant_id"] == "test_tenant"
    assert job["status"] == "created"
    assert job["progress"] == 0


@pytest.mark.asyncio
async def test_job_manager_events():
    """Test job manager event methods."""
    job_id = job_manager.create_job(1, "chunk", "test_tenant")
    
    # Test all event types
    await job_manager.job_started(job_id)
    assert job_manager.jobs[job_id]["status"] == "started"
    
    await job_manager.job_progress(job_id, 50)
    assert job_manager.jobs[job_id]["progress"] == 50
    
    await job_manager.job_done(job_id)
    assert job_manager.jobs[job_id]["status"] == "done"
    assert job_manager.jobs[job_id]["progress"] == 100
    
    # Test failed event
    job_id2 = job_manager.create_job(2, "embed", "test_tenant")
    await job_manager.job_failed(job_id2, "Test error")
    assert job_manager.jobs[job_id2]["status"] == "failed"
    assert job_manager.jobs[job_id2]["error"] == "Test error"


if __name__ == "__main__":
    pytest.main([__file__])
