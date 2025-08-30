import os
import tempfile
import unittest
from io import BytesIO

from storage.r2 import ObjectStore


class TestObjectStore(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Use test bucket
        os.environ["S3_BUCKET"] = "test-bucket"
        self.storage = ObjectStore()
        self.test_key = "test/test_file.txt"
        self.test_content = b"Hello, World! This is a test file."

    def test_put_and_get_file(self):
        """Test file upload and download."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(self.test_content)
            temp_file_path = temp_file.name

        try:
            # Upload file
            s3_uri = self.storage.put_file(temp_file_path, self.test_key)
            self.assertTrue(s3_uri.startswith("s3://"))
            self.assertIn(self.test_key, s3_uri)

            # Check if file exists
            self.assertTrue(self.storage.exists(self.test_key))

            # Download file
            with tempfile.NamedTemporaryFile(delete=False) as download_file:
                self.storage.get_file(self.test_key, download_file.name)

                # Read downloaded content
                with open(download_file.name, "rb") as f:
                    downloaded_content = f.read()

                os.unlink(download_file.name)

            # Verify content
            self.assertEqual(downloaded_content, self.test_content)

        finally:
            # Clean up
            os.unlink(temp_file_path)
            self.storage.delete(self.test_key)

    def test_put_and_get_data(self):
        """Test data upload and download using file-like objects."""
        # Upload data
        data_stream = BytesIO(self.test_content)
        s3_uri = self.storage.put_data(data_stream, self.test_key)
        self.assertTrue(s3_uri.startswith("s3://"))

        # Download data
        downloaded_data = self.storage.get_data(self.test_key)
        self.assertEqual(downloaded_data, self.test_content)

        # Clean up
        self.storage.delete(self.test_key)

    def test_delete(self):
        """Test file deletion."""
        # Upload file first
        data_stream = BytesIO(self.test_content)
        self.storage.put_data(data_stream, self.test_key)

        # Verify file exists
        self.assertTrue(self.storage.exists(self.test_key))

        # Delete file
        result = self.storage.delete(self.test_key)
        self.assertTrue(result)

        # Verify file doesn't exist
        self.assertFalse(self.storage.exists(self.test_key))

    def test_exists(self):
        """Test file existence check."""
        # File shouldn't exist initially
        self.assertFalse(self.storage.exists("nonexistent_file.txt"))


if __name__ == "__main__":
    unittest.main()
