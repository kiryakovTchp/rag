"""Test Gemini LLM provider."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from services.llm.gemini import GeminiProvider


class TestGeminiProvider(unittest.TestCase):
    """Test Gemini provider functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            with patch('services.llm.gemini.genai.Client') as mock_client:
                self.mock_client = Mock()
                mock_client.return_value = self.mock_client
                self.provider = GeminiProvider()
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as cm:
                GeminiProvider()
            self.assertIn("GEMINI_API_KEY", str(cm.exception))
    
    def test_prepare_messages_system_user(self):
        """Test message preparation with system and user messages."""
        messages = [
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "User question"}
        ]
        
        contents = self.provider._prepare_messages(messages)
        
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0].role, "user")
        self.assertIn("System instruction", contents[0].parts[0].text)
        self.assertIn("User question", contents[0].parts[0].text)
    
    def test_prepare_messages_user_assistant(self):
        """Test message preparation with user and assistant messages."""
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"}
        ]
        
        contents = self.provider._prepare_messages(messages)
        
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[0].role, "user")
        self.assertEqual(contents[1].role, "model")
        self.assertEqual(contents[2].role, "user")
    
    def test_generate_success(self):
        """Test successful generation."""
        # Mock response
        mock_response = Mock()
        mock_response.text = "Generated answer"
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        # Mock executor
        self.provider.executor.submit.return_value.result.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test query"}]
        answer, usage = self.provider.generate(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        self.assertEqual(answer, "Generated answer")
        self.assertEqual(usage["in_tokens"], 100)
        self.assertEqual(usage["out_tokens"], 50)
        self.assertEqual(usage["provider"], "gemini")
    
    def test_generate_without_usage_metadata(self):
        """Test generation without usage metadata."""
        # Mock response without usage metadata
        mock_response = Mock()
        mock_response.text = "Generated answer"
        del mock_response.usage_metadata
        
        self.provider.executor.submit.return_value.result.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test query"}]
        answer, usage = self.provider.generate(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        self.assertEqual(answer, "Generated answer")
        self.assertIsNone(usage["in_tokens"])
        self.assertIsNone(usage["out_tokens"])
    
    def test_generate_api_key_error(self):
        """Test generation with API key error."""
        self.provider.executor.submit.return_value.result.side_effect = Exception("Invalid API key")
        
        messages = [{"role": "user", "content": "Test query"}]
        
        with self.assertRaises(Exception) as cm:
            self.provider.generate(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        self.assertIn("LLM_UNAVAILABLE", str(cm.exception))
        self.assertIn("Invalid API key", str(cm.exception))
    
    def test_generate_403_error(self):
        """Test generation with 403 error."""
        self.provider.executor.submit.return_value.result.side_effect = Exception("403 Forbidden")
        
        messages = [{"role": "user", "content": "Test query"}]
        
        with self.assertRaises(Exception) as cm:
            self.provider.generate(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        self.assertIn("LLM_UNAVAILABLE", str(cm.exception))
        self.assertIn("Invalid API key", str(cm.exception))
    
    def test_generate_429_error(self):
        """Test generation with 429 error."""
        self.provider.executor.submit.return_value.result.side_effect = Exception("429 Rate limit")
        
        messages = [{"role": "user", "content": "Test query"}]
        
        with self.assertRaises(Exception) as cm:
            self.provider.generate(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        self.assertIn("LLM_UNAVAILABLE", str(cm.exception))
        self.assertIn("Rate limit exceeded", str(cm.exception))
    
    def test_generate_timeout_error(self):
        """Test generation with timeout error."""
        self.provider.executor.submit.return_value.result.side_effect = Exception("Request timeout")
        
        messages = [{"role": "user", "content": "Test query"}]
        
        with self.assertRaises(Exception) as cm:
            self.provider.generate(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        self.assertIn("LLM_UNAVAILABLE", str(cm.exception))
        self.assertIn("Request timeout", str(cm.exception))
    
    def test_stream_success(self):
        """Test successful streaming."""
        # Mock stream chunks
        mock_chunk1 = Mock()
        mock_chunk1.text = "Hello"
        mock_chunk2 = Mock()
        mock_chunk2.text = " world"
        
        self.provider.executor.submit.return_value.result.return_value = [mock_chunk1, mock_chunk2]
        
        messages = [{"role": "user", "content": "Test query"}]
        stream = self.provider.stream(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        chunks = list(stream)
        self.assertEqual(chunks, ["Hello", " world"])
    
    def test_stream_timeout(self):
        """Test streaming with timeout."""
        self.provider.executor.submit.return_value.result.side_effect = Exception("Stream timeout")
        
        messages = [{"role": "user", "content": "Test query"}]
        
        with self.assertRaises(Exception) as cm:
            list(self.provider.stream(messages, "gemini-2.5-flash", 100, 0.2, 30))
        
        self.assertIn("LLM_UNAVAILABLE", str(cm.exception))
        self.assertIn("Stream timeout", str(cm.exception))
    
    def test_stream_empty_chunks(self):
        """Test streaming with empty chunks."""
        mock_chunk1 = Mock()
        mock_chunk1.text = ""
        mock_chunk2 = Mock()
        mock_chunk2.text = "Hello"
        
        self.provider.executor.submit.return_value.result.return_value = [mock_chunk1, mock_chunk2]
        
        messages = [{"role": "user", "content": "Test query"}]
        stream = self.provider.stream(messages, "gemini-2.5-flash", 100, 0.2, 30)
        
        chunks = list(stream)
        self.assertEqual(chunks, ["Hello"])  # Empty chunks should be filtered


if __name__ == "__main__":
    unittest.main()
