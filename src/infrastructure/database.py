"""Database connection and management."""
from typing import Optional, Any, Dict, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, delete
from .models import Base, ConfigModel, SpeakerModel, ConversationHistoryModel
from ..core.entities import Speaker
import json
import base64


class Database:
    """Database manager for SQLite."""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///salvavidas.db"):
        """Initialize database connection."""
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Insert default configurations
        await self.seed_default_configs()

    async def seed_default_configs(self):
        """Seed default configuration values."""
        defaults = [
            ("processing_mode", "local", "str", "general", "Processing mode: local, api_fast, api_premium"),
            ("target_language", "en", "str", "language", "Default target language"),
            ("enable_speaker_id", "true", "bool", "features", "Enable speaker identification"),
            ("enable_suggestions", "true", "bool", "features", "Enable response suggestions"),
            ("latency_priority", "realtime", "str", "performance", "Latency priority: realtime, balanced, quality"),
            ("sample_rate", "16000", "int", "audio", "Audio sample rate"),
            ("enable_streaming", "true", "bool", "features", "Enable audio streaming"),
            ("use_intel_gpu", "true", "bool", "performance", "Use Intel GPU acceleration for local models"),
        ]

        async with self.SessionLocal() as session:
            for key, value, value_type, category, description in defaults:
                # Check if exists
                result = await session.execute(
                    select(ConfigModel).where(ConfigModel.key == key)
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    config = ConfigModel(
                        key=key,
                        value=value,
                        value_type=value_type,
                        category=category,
                        description=description
                    )
                    session.add(config)

            await session.commit()

    async def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value."""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(ConfigModel).where(ConfigModel.key == key)
            )
            config = result.scalar_one_or_none()

            if not config:
                return None

            # Convert to appropriate type
            if config.value_type == "bool":
                return config.value.lower() == "true"
            elif config.value_type == "int":
                return int(config.value)
            elif config.value_type == "float":
                return float(config.value)
            else:
                return config.value

    async def set_config(self, key: str, value: Any, category: str = "general"):
        """Set configuration value."""
        value_type = type(value).__name__
        value_str = str(value).lower() if isinstance(value, bool) else str(value)

        async with self.SessionLocal() as session:
            result = await session.execute(
                select(ConfigModel).where(ConfigModel.key == key)
            )
            config = result.scalar_one_or_none()

            if config:
                config.value = value_str
                config.value_type = value_type
            else:
                config = ConfigModel(
                    key=key,
                    value=value_str,
                    value_type=value_type,
                    category=category
                )
                session.add(config)

            await session.commit()

    async def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations."""
        async with self.SessionLocal() as session:
            result = await session.execute(select(ConfigModel))
            configs = result.scalars().all()

            config_dict = {}
            for config in configs:
                if config.value_type == "bool":
                    config_dict[config.key] = config.value.lower() == "true"
                elif config.value_type == "int":
                    config_dict[config.key] = int(config.value)
                elif config.value_type == "float":
                    config_dict[config.key] = float(config.value)
                else:
                    config_dict[config.key] = config.value

            return config_dict

    async def save_speaker(self, speaker: Speaker) -> None:
        """Save speaker profile."""
        async with self.SessionLocal() as session:
            # Check if exists
            result = await session.execute(
                select(SpeakerModel).where(SpeakerModel.speaker_id == speaker.speaker_id)
            )
            existing = result.scalar_one_or_none()

            embedding_b64 = None
            if speaker.embedding:
                embedding_b64 = base64.b64encode(speaker.embedding).decode()

            if existing:
                existing.name = speaker.name
                existing.language = speaker.language
                existing.embedding = embedding_b64
                existing.confidence = speaker.confidence
            else:
                speaker_model = SpeakerModel(
                    speaker_id=speaker.speaker_id,
                    name=speaker.name,
                    language=speaker.language,
                    embedding=embedding_b64,
                    confidence=speaker.confidence
                )
                session.add(speaker_model)

            await session.commit()

    async def get_all_speakers(self) -> List[Speaker]:
        """Get all known speakers."""
        async with self.SessionLocal() as session:
            result = await session.execute(select(SpeakerModel))
            speaker_models = result.scalars().all()

            speakers = []
            for model in speaker_models:
                embedding = None
                if model.embedding:
                    embedding = base64.b64decode(model.embedding.encode())

                speakers.append(
                    Speaker(
                        speaker_id=model.speaker_id,
                        name=model.name,
                        language=model.language,
                        confidence=model.confidence,
                        embedding=embedding
                    )
                )

            return speakers

    async def close(self):
        """Close database connection."""
        await self.engine.dispose()
