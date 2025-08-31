"""Test feedback functionality."""

import unittest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from datetime import datetime

from api.schemas.feedback import FeedbackRequest, FeedbackResponse, FeedbackStats
from db.models import AnswerFeedback


class TestFeedbackSchemas(unittest.TestCase):
    """Test feedback schemas."""
    
    def test_feedback_request_valid(self):
        """Test valid feedback request."""
        request = FeedbackRequest(
            answer_id="test_answer_123",
            rating="up",
            reason="Great answer!",
            selected_citation_ids=[1, 2, 3]
        )
        
        self.assertEqual(request.answer_id, "test_answer_123")
        self.assertEqual(request.rating, "up")
        self.assertEqual(request.reason, "Great answer!")
        self.assertEqual(request.selected_citation_ids, [1, 2, 3])
    
    def test_feedback_request_minimal(self):
        """Test minimal feedback request."""
        request = FeedbackRequest(
            answer_id="test_answer_123",
            rating="down"
        )
        
        self.assertEqual(request.answer_id, "test_answer_123")
        self.assertEqual(request.rating, "down")
        self.assertIsNone(request.reason)
        self.assertIsNone(request.selected_citation_ids)
    
    def test_feedback_response(self):
        """Test feedback response."""
        response = FeedbackResponse(
            id=1,
            answer_id="test_answer_123",
            rating="up",
            reason="Great answer!",
            selected_citation_ids=[1, 2, 3],
            created_at=datetime.utcnow()
        )
        
        self.assertEqual(response.id, 1)
        self.assertEqual(response.answer_id, "test_answer_123")
        self.assertEqual(response.rating, "up")
        self.assertEqual(response.reason, "Great answer!")
        self.assertEqual(response.selected_citation_ids, [1, 2, 3])
    
    def test_feedback_stats(self):
        """Test feedback statistics."""
        stats = FeedbackStats(
            total_feedback=100,
            positive_feedback=80,
            negative_feedback=20,
            positive_rate=0.8
        )
        
        self.assertEqual(stats.total_feedback, 100)
        self.assertEqual(stats.positive_feedback, 80)
        self.assertEqual(stats.negative_feedback, 20)
        self.assertEqual(stats.positive_rate, 0.8)


class TestFeedbackAPI(unittest.TestCase):
    """Test feedback API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_user = {
            "tenant_id": "test_tenant",
            "user_id": "test_user",
            "role": "user"
        }
    
    def test_submit_feedback_valid(self):
        """Test valid feedback submission."""
        from api.routers.feedback import submit_feedback
        
        request = FeedbackRequest(
            answer_id="test_answer_123",
            rating="up",
            reason="Great answer!",
            selected_citation_ids=[1, 2, 3]
        )
        
        # Mock database operations
        mock_feedback = Mock()
        mock_feedback.id = 1
        mock_feedback.answer_id = "test_answer_123"
        mock_feedback.rating = "up"
        mock_feedback.reason = "Great answer!"
        mock_feedback.selected_citation_ids = [1, 2, 3]
        mock_feedback.created_at = datetime.utcnow()
        
        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        self.mock_db.refresh.return_value = None
        
        # Test submission
        with patch('api.routers.feedback.AnswerFeedback') as mock_feedback_class:
            mock_feedback_class.return_value = mock_feedback
            
            result = submit_feedback(request, self.mock_db, self.mock_user)
            
            # Verify feedback was created
            mock_feedback_class.assert_called_once_with(
                answer_id="test_answer_123",
                tenant_id="test_tenant",
                user_id="test_user",
                rating="up",
                reason="Great answer!",
                selected_citation_ids=[1, 2, 3]
            )
            
            # Verify database operations
            self.mock_db.add.assert_called_once_with(mock_feedback)
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once_with(mock_feedback)
    
    def test_submit_feedback_invalid_rating(self):
        """Test feedback submission with invalid rating."""
        from api.routers.feedback import submit_feedback
        
        request = FeedbackRequest(
            answer_id="test_answer_123",
            rating="invalid",
            reason="Test"
        )
        
        # Should raise HTTPException
        with self.assertRaises(HTTPException) as context:
            submit_feedback(request, self.mock_db, self.mock_user)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Rating must be 'up' or 'down'", context.exception.detail)
    
    def test_get_feedback_for_answer(self):
        """Test getting feedback for an answer."""
        from api.routers.feedback import get_feedback_for_answer
        
        # Mock feedback records
        mock_feedback1 = Mock()
        mock_feedback1.id = 1
        mock_feedback1.answer_id = "test_answer_123"
        mock_feedback1.rating = "up"
        mock_feedback1.reason = "Great!"
        mock_feedback1.selected_citation_ids = [1, 2]
        mock_feedback1.created_at = datetime.utcnow()
        
        mock_feedback2 = Mock()
        mock_feedback2.id = 2
        mock_feedback2.answer_id = "test_answer_123"
        mock_feedback2.rating = "down"
        mock_feedback2.reason = "Not helpful"
        mock_feedback2.selected_citation_ids = None
        mock_feedback2.created_at = datetime.utcnow()
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_feedback1, mock_feedback2]
        self.mock_db.query.return_value = mock_query
        
        # Test retrieval
        result = get_feedback_for_answer("test_answer_123", self.mock_db, self.mock_user)
        
        # Verify query was made correctly
        self.mock_db.query.assert_called_once()
        mock_query.filter.assert_called_once()
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].rating, "up")
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[1].rating, "down")
    
    def test_get_feedback_stats(self):
        """Test getting feedback statistics."""
        from api.routers.feedback import get_feedback_stats
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 100
        
        # Mock positive feedback query
        mock_positive_query = Mock()
        mock_positive_query.filter.return_value.count.return_value = 80
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_positive_query
        
        # Test statistics
        result = get_feedback_stats(self.mock_db, self.mock_user)
        
        # Verify result
        self.assertEqual(result.total_feedback, 100)
        self.assertEqual(result.positive_feedback, 80)
        self.assertEqual(result.negative_feedback, 20)
        self.assertEqual(result.positive_rate, 0.8)


if __name__ == "__main__":
    unittest.main()
