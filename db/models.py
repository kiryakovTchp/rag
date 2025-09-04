# Import pgvector Vector type
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

metadata = MetaData(schema="app")
Base = declarative_base(metadata=metadata)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=True, index=True)
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
    # Nullable by design: a job may not be tied to a specific document
    document_id = Column(Integer, ForeignKey("app.documents.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="jobs")


class Element(Base):
    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("app.documents.id"), nullable=False)
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
    tenant_id = Column(String(100), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("app.documents.id"), nullable=False)
    element_id = Column(Integer, ForeignKey("app.elements.id"), nullable=True)
    level = Column(String(50), nullable=False)  # section, passage, table
    header_path = Column(JSON, nullable=True)  # breadcrumbs path
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    page = Column(Integer, nullable=True)
    table_meta = Column(JSON, nullable=True)  # table metadata
    # ACL principals for multi-tenant and per-principal access control
    acl_principals = Column(ARRAY(Text), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    element = relationship("Element", back_populates="chunks")


# Index for searching by ACL principals
Index("ix_chunks_acl_principals", Chunk.acl_principals, postgresql_using="gin")


class Embedding(Base):
    __tablename__ = "embeddings"

    chunk_id = Column(
        Integer, ForeignKey("app.chunks.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id = Column(String(100), nullable=True, index=True)
    vector = Column(Vector(1024), nullable=False, index=False)  # pgvector vector(1024)
    provider = Column(String(50), nullable=False)  # local, workers_ai
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    chunk = relationship("Chunk", backref="embedding")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    tenant_id = Column(String(100), nullable=True, index=True)
    role = Column(String(50), default="user")
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


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


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False, server_default="user")
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash API key for storage."""
        import hashlib

        return hashlib.sha256(key.encode()).hexdigest()


class AnswerFeedback(Base):
    __tablename__ = "answer_feedback"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(String(100), nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    rating = Column(Enum("up", "down", name="feedback_rating"), nullable=False)  # type: ignore
    reason = Column(Text, nullable=True)  # type: ignore
    selected_citation_ids = Column(ARRAY(Integer), nullable=True)  # type: ignore
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("app.users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id = Column(String(100), nullable=True, index=True)
    provider = Column(String(50), nullable=False)  # google, notion, confluence
    account_id = Column(
        String(255), nullable=False, index=True
    )  # provider user id / resource id
    scopes = Column(ARRAY(String), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    user = relationship("User")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(
        Integer, ForeignKey("app.oauth_accounts.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id = Column(String(100), nullable=True, index=True)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    account = relationship("OAuthAccount")


# Indexes
Index(
    "ix_oauth_accounts_provider_account",
    OAuthAccount.provider,
    OAuthAccount.account_id,
    unique=True,
)
Index("ix_oauth_tokens_account_active", OAuthToken.account_id, OAuthToken.revoked_at)
