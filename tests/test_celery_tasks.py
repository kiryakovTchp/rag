"""Test Celery task registration."""

import unittest
from workers.app import celery_app


class TestCeleryTasks(unittest.TestCase):
    """Test that Celery tasks are properly registered."""

    def test_embed_document_task_registered(self):
        """Test that embed_document task is registered."""
        from workers.tasks.embed import embed_document
        
        # Check if task is registered
        task_name = embed_document.name
        self.assertIn(task_name, celery_app.tasks)
        
        # Check task properties
        task = celery_app.tasks[task_name]
        self.assertEqual(task.name, task_name)
        self.assertEqual(task.queue, "embed")

    def test_parse_document_task_registered(self):
        """Test that parse_document task is registered."""
        from workers.tasks.parse import parse_document
        
        task_name = parse_document.name
        self.assertIn(task_name, celery_app.tasks)
        
        task = celery_app.tasks[task_name]
        self.assertEqual(task.name, task_name)
        self.assertEqual(task.queue, "parse")

    def test_chunk_document_task_registered(self):
        """Test that chunk_document task is registered."""
        from workers.tasks.chunk import chunk_document
        
        task_name = chunk_document.name
        self.assertIn(task_name, celery_app.tasks)
        
        task = celery_app.tasks[task_name]
        self.assertEqual(task.name, task_name)
        self.assertEqual(task.queue, "chunk")

    def test_all_required_tasks_registered(self):
        """Test that all required tasks are registered."""
        required_tasks = [
            "workers.tasks.parse.parse_document",
            "workers.tasks.chunk.chunk_document", 
            "workers.tasks.embed.embed_document"
        ]
        
        for task_name in required_tasks:
            self.assertIn(task_name, celery_app.tasks, f"Task {task_name} not registered")


if __name__ == "__main__":
    unittest.main()
