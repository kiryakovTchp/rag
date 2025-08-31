"""Test feedback functionality."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from api.main import app
from db.models import User, AnswerFeedback

client = TestClient(app)


class TestFeedbackAPI:
    """Test feedback API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user = User(
            id="test_user_123",
            tenant_id="test_tenant",
            email="test@example.com",
            role="user"
        )
    
    @patch('api.routers.feedback.get_current_user')
    @patch('api.routers.feedback.get_db')
    def test_create_feedback_success(self, mock_db, mock_auth):
        """Test successful feedback creation."""
        # Mock user
        mock_auth.return_value = self.mock_user
        
        # Mock database
        mock_session = Mock()
        mock_db.return_value = mock_session
        
        # Mock feedback object
        mock_feedback = Mock()
        mock_feedback.id = 1
        mock_feedback.answer_id = "answer_123"
        mock_feedback.tenant_id = "test_tenant"
        mock_feedback.user_id = "test_user_123"
        mock_feedback.rating = "up"
        mock_feedback.reason = None
        mock_feedback.selected_citation_ids = None
        mock_feedback.created_at = "2024-01-01T00:00:00Z"
        
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        response = client.post(
            "/feedback",
            headers={"Authorization": "Bearer test_token"},
            json={
                "answer_id": "answer_123",
                "rating": "up",
                "reason": None,
                "selected_citation_ids": None
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer_id"] == "answer_123"
        assert data["rating"] == "up"
        assert data["tenant_id"] == "test_tenant"
        assert data["user_id"] == "test_user_123"
    
    @patch('api.routers.feedback.get_current_user')
    @patch('api.routers.feedback.get_db')
    def test_create_feedback_with_reason(self, mock_db, mock_auth):
        """Test feedback creation with reason."""
        # Mock user
        mock_auth.return_value = self.mock_user
        
        # Mock database
        mock_session = Mock()
        mock_db.return_value = mock_session
        
        # Mock feedback object
        mock_feedback = Mock()
        mock_feedback.id = 1
        mock_feedback.answer_id = "answer_123"
        mock_feedback.tenant_id = "test_tenant"
        mock_feedback.user_id = "test_user_123"
        mock_feedback.rating = "down"
        mock_feedback.reason = "Incorrect information"
        mock_feedback.selected_citation_ids = [1, 2]
        mock_feedback.created_at = "2024-01-01T00:00:00Z"
        
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        response = client.post(
            "/feedback",
            headers={"Authorization": "Bearer test_token"},
            json={
                "answer_id": "answer_123",
                "rating": "down",
                "reason": "Incorrect information",
                "selected_citation_ids": [1, 2]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == "down"
        assert data["reason"] == "Incorrect information"
        assert data["selected_citation_ids"] == [1, 2]
    
    @patch('api.routers.feedback.get_current_user')
    @patch('api.routers.feedback.get_db')
    def test_create_feedback_api_key_user(self, mock_db, mock_auth):
        """Test feedback creation with API key user (no user_id)."""
        # Mock API key user
        api_user = User(
            id="api_123",
            tenant_id="test_tenant",
            email="",
            role="user"
        )
        mock_auth.return_value = api_user
        
        # Mock database
        mock_session = Mock()
        mock_db.return_value = mock_session
        
        # Mock feedback object
        mock_feedback = Mock()
        mock_feedback.id = 1
        mock_feedback.answer_id = "answer_123"
        mock_feedback.tenant_id = "test_tenant"
        mock_feedback.user_id = None  # API key users don't have user_id
        mock_feedback.rating = "up"
        mock_feedback.reason = None
        mock_feedback.selected_citation_ids = None
        mock_feedback.created_at = "2024-01-01T00:00:00Z"
        
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        response = client.post(
            "/feedback",
            headers={"Authorization": "Bearer test_token"},
            json={
                "answer_id": "answer_123",
                "rating": "up"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None
    
    @patch('api.routers.feedback.get_current_user')
    @patch('api.routers.feedback.get_db')
    def test_get_feedback_for_answer(self, mock_db, mock_auth):
        """Test getting feedback for a specific answer."""
        # Mock user
        mock_auth.return_value = self.mock_user
        
        # Mock database
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_db.return_value = mock_session
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        
        # Mock feedback objects
        mock_feedback1 = Mock()
        mock_feedback1.id = 1
        mock_feedback1.answer_id = "answer_123"
        mock_feedback1.tenant_id = "test_tenant"
        mock_feedback1.user_id = "test_user_123"
        mock_feedback1.rating = "up"
        mock_feedback1.reason = None
        mock_feedback1.selected_citation_ids = None
        mock_feedback1.created_at = "2024-01-01T00:00:00Z"
        
        mock_feedback2 = Mock()
        mock_feedback2.id = 2
        mock_feedback2.answer_id = "answer_123"
        mock_feedback2.tenant_id = "test_tenant"
        mock_feedback2.user_id = "test_user_456"
        mock_feedback2.rating = "down"
        mock_feedback2.reason = "Wrong answer"
        mock_feedback2.selected_citation_ids = [1]
        mock_feedback2.created_at = "2024-01-02T00:00:00Z"
        
        mock_filter.all.return_value = [mock_feedback1, mock_feedback2]
        
        response = client.get(
            "/feedback/answer_123",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["rating"] == "up"
        assert data[1]["rating"] == "down"
        assert data[1]["reason"] == "Wrong answer"
    
    @patch('api.routers.feedback.get_current_user')
    @patch('api.routers.feedback.get_db')
    def test_get_feedback_summary(self, mock_db, mock_auth):
        """Test getting feedback summary."""
        # Mock user
        mock_auth.return_value = self.mock_user
        
        # Mock database
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        mock_db.return_value = mock_session
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        
        # Mock feedback objects
        mock_feedback = Mock()
        mock_feedback.id = 1
        mock_feedback.answer_id = "answer_123"
        mock_feedback.tenant_id = "test_tenant"
        mock_feedback.user_id = "test_user_123"
        mock_feedback.rating = "up"
        mock_feedback.reason = None
        mock_feedback.selected_citation_ids = None
        mock_feedback.created_at = "2024-01-01T00:00:00Z"
        
        mock_limit.all.return_value = [mock_feedback]
        
        response = client.get(
            "/feedback?limit=10&offset=0",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["answer_id"] == "answer_123"
    
    @patch('api.routers.feedback.get_current_user')
    def test_get_feedback_unauthorized(self, mock_auth):
        """Test getting feedback without authentication."""
        mock_auth.side_effect = Exception("Unauthorized")
        
        response = client.get("/feedback/answer_123")
        assert response.status_code == 401
    
    def test_create_feedback_invalid_rating(self):
        """Test feedback creation with invalid rating."""
        response = client.post(
            "/feedback",
            headers={"Authorization": "Bearer test_token"},
            json={
                "answer_id": "answer_123",
                "rating": "invalid_rating"
            }
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_create_feedback_missing_answer_id(self):
        """Test feedback creation without answer_id."""
        response = client.post(
            "/feedback",
            headers={"Authorization": "Bearer test_token"},
            json={
                "rating": "up"
            }
        )
        
        # Should fail validation
        assert response.status_code == 422


class TestFeedbackValidation:
    """Test feedback validation."""
    
    def test_feedback_create_schema(self):
        """Test FeedbackCreate schema validation."""
        from api.schemas.feedback import FeedbackCreate
        
        # Valid feedback
        valid_feedback = FeedbackCreate(
            answer_id="answer_123",
            rating="up",
            reason="Great answer!",
            selected_citation_ids=[1, 2, 3]
        )
        assert valid_feedback.answer_id == "answer_123"
        assert valid_feedback.rating == "up"
        assert valid_feedback.reason == "Great answer!"
        assert valid_feedback.selected_citation_ids == [1, 2, 3]
        
        # Valid feedback without optional fields
        minimal_feedback = FeedbackCreate(
            answer_id="answer_456",
            rating="down"
        )
        assert minimal_feedback.answer_id == "answer_456"
        assert minimal_feedback.rating == "down"
        assert minimal_feedback.reason is None
        assert minimal_feedback.selected_citation_ids is None
    
    def test_feedback_response_schema(self):
        """Test FeedbackResponse schema validation."""
        from api.schemas.feedback import FeedbackResponse
        from datetime import datetime
        
        feedback_response = FeedbackResponse(
            id=1,
            answer_id="answer_123",
            tenant_id="test_tenant",
            user_id="test_user_123",
            rating="up",
            reason="Great answer!",
            selected_citation_ids=[1, 2],
            created_at=datetime.utcnow()
        )
        
        assert feedback_response.id == 1
        assert feedback_response.answer_id == "answer_123"
        assert feedback_response.tenant_id == "test_tenant"
        assert feedback_response.user_id == "test_user_123"
        assert feedback_response.rating == "up"
        assert feedback_response.reason == "Great answer!"
        assert feedback_response.selected_citation_ids == [1, 2]


if __name__ == "__main__":
    pytest.main([__file__])
