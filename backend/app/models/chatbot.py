from __future__ import annotations
import uuid
from typing import List, Optional, Any
from sqlalchemy import String, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.db import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

class ChatbotDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chatbot_documents"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    chunks: Mapped[List[ChatbotDocumentChunk]] = relationship(
        "ChatbotDocumentChunk", back_populates="document", cascade="all, delete"
    )


class ChatbotDocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chatbot_document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chatbot_documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 384-dimensional vector embedding for Sentence Transformers (all-MiniLM-L6-v2)
    embedding: Mapped[List[float]] = mapped_column(Vector(384), nullable=False)

    # Relationships
    document: Mapped[ChatbotDocument] = relationship("ChatbotDocument", back_populates="chunks")


class ChatSession(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[List[ChatMessage]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete"
    )


class ChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)  # List of matching document source names
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    session: Mapped[ChatSession] = relationship("ChatSession", back_populates="messages")
