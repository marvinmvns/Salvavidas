"""SQLAlchemy models for database tables."""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ConfigModel(Base):
    """Configuration model."""
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False, default="str")
    category = Column(String(50), nullable=False, default="general")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SpeakerModel(Base):
    """Speaker profile model."""
    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    speaker_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)  # Can be None until user names the speaker
    language = Column(String(10), nullable=True)
    embedding = Column(Text, nullable=True)  # Base64 encoded embedding
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationHistoryModel(Base):
    """Conversation history model."""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    speaker_id = Column(String(100), nullable=True)
    speaker_name = Column(String(200), nullable=True)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), nullable=True)
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
