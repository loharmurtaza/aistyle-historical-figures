"""SQLAlchemy ORM models for chatbot sessions and message history."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False)        # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Populated only on assistant rows; NULL on user rows.
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    retrieval_ms = Column(Float, nullable=True)
    first_token_ms = Column(Float, nullable=True)
    total_ms = Column(Float, nullable=True)
    docs_retrieved = Column(Integer, nullable=True)
