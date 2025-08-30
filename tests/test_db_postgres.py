"""Test PostgreSQL database connectivity and pgvector extension."""

import os
import unittest

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class TestPostgreSQL(unittest.TestCase):
    """Test PostgreSQL database functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.database_url = os.getenv("DATABASE_URL")
        self.assertIsNotNone(self.database_url, "DATABASE_URL not set")
        self.assertTrue(self.database_url.startswith("postgresql+psycopg"), "Not PostgreSQL")
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def test_database_connection(self):
        """Test database connection."""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            self.assertIn("PostgreSQL", version)
            print(f"Connected to: {version}")
    
    def test_pgvector_extension(self):
        """Test pgvector extension is available."""
        with self.engine.connect() as conn:
            # Check if vector extension is available
            result = conn.execute(text("""
                SELECT extname FROM pg_available_extensions 
                WHERE extname = 'vector'
            """))
            extension = result.fetchone()
            self.assertIsNotNone(extension, "pgvector extension not available")
            
            # Check if vector extension is installed
            result = conn.execute(text("""
                SELECT extname FROM pg_extension 
                WHERE extname = 'vector'
            """))
            installed = result.fetchone()
            self.assertIsNotNone(installed, "pgvector extension not installed")
            
            print("✅ pgvector extension is available and installed")
    
    def test_vector_operations(self):
        """Test basic vector operations."""
        with self.engine.connect() as conn:
            # Test vector type creation
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_vectors (
                    id SERIAL PRIMARY KEY,
                    vector vector(3)
                )
            """))
            
            # Test vector insertion
            conn.execute(text("""
                INSERT INTO test_vectors (vector) VALUES ('[1,2,3]'::vector)
            """))
            
            # Test vector query
            result = conn.execute(text("""
                SELECT vector FROM test_vectors WHERE id = 1
            """))
            vector = result.scalar()
            self.assertIsNotNone(vector)
            
            # Cleanup
            conn.execute(text("DROP TABLE test_vectors"))
            conn.commit()
            
            print("✅ Vector operations work correctly")
