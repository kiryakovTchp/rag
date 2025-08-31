from datetime import datetime
import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Import pgvector Vector type
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    mime = Column(String(100), nullable=False)
    storage_uri = Column(String(500), nullable=False)
    status = Column(String(50), default="uploaded")  # uploaded, processing, done, error
    created_at = Column(DateTime, default=func.now())

    # Relationships
    jobs = relationship("Job", back_populates="document")
    elements = relationship("Element", back_populates="document")
    chunks = relationship("Chunk", back_populates="document")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # parse, chunk
    status = Column(String(50), default="queued")  # queued, running, done, error
    progress = Column(Integer, default=0)  # 0-100
    error = Column(Text, nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="jobs")


class Element(Base):
    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    type = Column(String(50), nullable=False)  # text, title, list, table, code, image
    page = Column(Integer, nullable=True)
    bbox = Column(JSON, nullable=True)  # bounding box coordinates
    table_id = Column(String(100), nullable=True)  # for table elements
    text = Column(Text, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="elements")
    chunks = relationship("Chunk", back_populates="element")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    element_id = Column(Integer, ForeignKey("elements.id"), nullable=True)
    level = Column(String(50), nullable=False)  # section, passage, table
    header_path = Column(JSON, nullable=True)  # breadcrumbs path
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    page = Column(Integer, nullable=True)
    table_meta = Column(JSON, nullable=True)  # table metadata

    # Relationships
    document = relationship("Document", back_populates="chunks")
    element = relationship("Element", back_populates="chunks")



class Embedding(Base):
    __tablename__ = "embeddings"

    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True)
    vector = Column(Vector(1024), nullable=False, index=False)  # pgvector vector(1024)
    provider = Column(String(50), nullable=False)  # local, workers_ai
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    chunk = relationship("Chunk", backref="embedding")


class AnswerLog(Base):
    __tablename__ = "answer_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=True)
    query = Column(Text, nullable=False)
    provider = Column(String(50), nullable=False)  # gemini, openai, etc.
    model = Column(String(100), nullable=False)  # gemini-2.5-flash, etc.
    in_tokens = Column(Integer, nullable=True)
    out_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=False)
    cost_usd = Column(String(20), nullable=True)  # Decimal as string
    created_at = Column(DateTime, default=func.now())
