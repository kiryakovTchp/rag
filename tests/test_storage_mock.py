import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import Mock, patch

from storage.r2 import ObjectStore


class TestObjectStoreMock(unittest.TestCase):
    def setUp(self):
        """Set up test environment with mocked S3."""
        # Use test bucket
        os.environ["S3_BUCKET"] = "test-bucket"
        os.environ["S3_ENDPOINT"] = "http://localhost:9000"

        # Mock boto3 client
        self.mock_s3_client = Mock()
        self.mock_s3_client.head_bucket.return_value = {}
        self.mock_s3_client.upload_file.return_value = None
        self.mock_s3_client.upload_fileobj.return_value = None
        self.mock_s3_client.download_file.return_value = None
        self.mock_s3_client.get_object.return_value = {"Body": BytesIO(b"test content")}
        self.mock_s3_client.delete_object.return_value = {}
        self.mock_s3_client.head_object.return_value = {}

        with patch("boto3.client", return_value=self.mock_s3_client):
            self.storage = ObjectStore()

    def test_put_and_get_file(self):
        """Test file upload and download with mocks."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Hello, World! This is a test file.")
            temp_file_path = temp_file.name

        try:
            # Upload file
            s3_uri = self.storage.put_file(temp_file_path, "test/test_file.txt")
            self.assertTrue(s3_uri.startswith("s3://"))
            self.assertIn("test/test_file.txt", s3_uri)

            # Verify upload was called
            self.mock_s3_client.upload_file.assert_called_once()

            # Check if file exists
            self.assertTrue(self.storage.exists("test/test_file.txt"))

            # Download file
            with tempfile.NamedTemporaryFile(delete=False) as download_file:
                self.storage.get_file("test/test_file.txt", download_file.name)

                # Verify download was called
                self.mock_s3_client.download_file.assert_called_once()

                os.unlink(download_file.name)

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_put_and_get_data(self):
        """Test data upload and download using file-like objects."""
        # Upload data
        data_stream = BytesIO(b"test content")
        s3_uri = self.storage.put_data(data_stream, "test/test_data.txt")
        self.assertTrue(s3_uri.startswith("s3://"))

        # Verify upload was called
        self.mock_s3_client.upload_fileobj.assert_called_once()

        # Download data
        downloaded_data = self.storage.get_data("test/test_data.txt")
        self.assertEqual(downloaded_data, b"test content")

        # Verify get_object was called
        self.mock_s3_client.get_object.assert_called_once()

    def test_delete(self):
        """Test file deletion."""
        # Delete file
        result = self.storage.delete("test/test_file.txt")
        self.assertTrue(result)

        # Verify delete was called
        self.mock_s3_client.delete_object.assert_called_once()

    def test_exists(self):
        """Test file existence check."""
        # File should exist (mocked)
        self.assertTrue(self.storage.exists("test/test_file.txt"))

        # Verify head_object was called
        self.mock_s3_client.head_object.assert_called_once()


if __name__ == "__main__":
    unittest.main()
