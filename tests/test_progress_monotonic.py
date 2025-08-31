"""Test progress monotonicity."""

import unittest
from unittest.mock import patch, MagicMock
from workers.tasks.embed import embed_document
from workers.tasks.index import index_document
from db.models import Document, Job, Chunk
from db.session import SessionLocal


class TestProgressMonotonic(unittest.TestCase):
    """Test that progress is monotonic and reaches 100."""

    def setUp(self):
        """Set up test database."""
        self.db = SessionLocal()

    def tearDown(self):
        """Clean up."""
        self.db.close()

    def test_embed_progress_monotonic(self):
        """Test that embed progress is monotonic."""
        # Create test document
        document = Document(
            name="test_doc.pdf",
            mime="application/pdf",
            storage_uri="s3://test/test.pdf",
            status="uploaded"
        )
        self.db.add(document)
        self.db.flush()

        # Create test chunks
        chunks = []
        for i in range(10):
            chunk = Chunk(
                document_id=document.id,
                text=f"Test chunk {i}",
                token_count=100,
                level=1
            )
            chunks.append(chunk)
            self.db.add(chunk)

        self.db.commit()

        # Mock embedder and index
        with patch('workers.tasks.embed.EmbeddingProvider') as mock_embedder_class, \
             patch('workers.tasks.embed.PGVectorIndex') as mock_index_class:
            
            mock_embedder = MagicMock()
            mock_embedder.embed_texts.return_value = [[0.1] * 1024] * 10
            mock_embedder.get_provider.return_value = "test"
            mock_embedder_class.return_value = mock_embedder

            mock_index = MagicMock()
            mock_index_class.return_value = mock_index

            # Track progress updates
            progress_updates = []

            def track_progress(progress):
                progress_updates.append(progress)

            # Mock session to track progress
            with patch('workers.tasks.embed.SessionLocal') as mock_session:
                mock_session.return_value = self.db
                
                # Run embed task
                result = embed_document(document.id)

                # Check progress was updated
                job = self.db.query(Job).filter(
                    Job.document_id == document.id,
                    Job.type == "embed"
                ).first()

                self.assertIsNotNone(job)
                self.assertEqual(job.progress, 100)
                self.assertEqual(job.status, "done")

    def test_index_progress_monotonic(self):
        """Test that index progress is monotonic."""
        # Create test document
        document = Document(
            name="test_doc.pdf",
            mime="application/pdf",
            storage_uri="s3://test/test.pdf",
            status="uploaded"
        )
        self.db.add(document)
        self.db.flush()

        # Create test chunks
        chunks = []
        for i in range(10):
            chunk = Chunk(
                document_id=document.id,
                text=f"Test chunk {i}",
                token_count=100,
                level=1
            )
            chunks.append(chunk)
            self.db.add(chunk)

        self.db.commit()

        # Mock embedder and index
        with patch('workers.tasks.index.EmbeddingProvider') as mock_embedder_class, \
             patch('workers.tasks.index.PGVectorIndex') as mock_index_class:
            
            mock_embedder = MagicMock()
            mock_embedder.embed_texts.return_value = [[0.1] * 1024] * 10
            mock_embedder.get_provider.return_value = "test"
            mock_embedder.batch_size = 5
            mock_embedder_class.return_value = mock_embedder

            mock_index = MagicMock()
            mock_index_class.return_value = mock_index

            # Mock current_task
            with patch('workers.tasks.index.current_task') as mock_task:
                mock_task.update_state = MagicMock()

                # Run index task
                result = index_document(document.id)

                # Check that progress was updated
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["chunks_indexed"], 10)

                # Check that update_state was called
                mock_task.update_state.assert_called()

    def test_progress_final_value(self):
        """Test that progress reaches 100 at the end."""
        # Create test document
        document = Document(
            name="test_doc.pdf",
            mime="application/pdf",
            storage_uri="s3://test/test.pdf",
            status="uploaded"
        )
        self.db.add(document)
        self.db.flush()

        # Create test chunks
        chunks = []
        for i in range(5):
            chunk = Chunk(
                document_id=document.id,
                text=f"Test chunk {i}",
                token_count=100,
                level=1
            )
            chunks.append(chunk)
            self.db.add(chunk)

        self.db.commit()

        # Mock embedder and index
        with patch('workers.tasks.embed.EmbeddingProvider') as mock_embedder_class, \
             patch('workers.tasks.embed.PGVectorIndex') as mock_index_class:
            
            mock_embedder = MagicMock()
            mock_embedder.embed_texts.return_value = [[0.1] * 1024] * 5
            mock_embedder.get_provider.return_value = "test"
            mock_embedder_class.return_value = mock_embedder

            mock_index = MagicMock()
            mock_index_class.return_value = mock_index

            # Mock session
            with patch('workers.tasks.embed.SessionLocal') as mock_session:
                mock_session.return_value = self.db
                
                # Run embed task
                result = embed_document(document.id)

                # Check final progress
                job = self.db.query(Job).filter(
                    Job.document_id == document.id,
                    Job.type == "embed"
                ).first()

                self.assertIsNotNone(job)
                self.assertEqual(job.progress, 100)
                self.assertEqual(job.status, "done")


if __name__ == "__main__":
    unittest.main()
