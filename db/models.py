from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    mime = Column(String(100), nullable=False)
    storage_uri = Column(String(500), nullable=False)
    status = Column(String(50), default="uploaded")  # uploaded, processing, done, error
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
