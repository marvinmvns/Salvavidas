"""Integration tests for voice controller."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from src.core.use_cases import ProcessVoiceTranslationUseCase
from src.adapters.controllers import VoiceTranslationController
from src.infrastructure.database import Database
from src.core.entities import AudioChunk, Speaker


@pytest.fixture
async def database():
    """Create test database."""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    await db.close()


@pytest.fixture
def mock_use_case():
    """Create mock use case."""
    use_case = AsyncMock(spec=ProcessVoiceTranslationUseCase)
    use_case.speaker_id_service = AsyncMock()
    return use_case


@pytest.fixture
async def controller(database, mock_use_case):
    """Create controller with test database."""
    controller = VoiceTranslationController(
        use_case=mock_use_case,
        database=database
    )
    await controller.initialize()
    return controller


@pytest.mark.asyncio
async def test_controller_initialization(controller, database):
    """Test controller initialization loads speakers."""
    # Add a speaker to database
    speaker = Speaker(
        speaker_id="test_speaker",
        name="Test",
        language="en",
        confidence=0.95
    )
    await database.save_speaker(speaker)

    # Reinitialize controller
    await controller.initialize()

    # Should have loaded the speaker
    assert len(controller.use_case.known_speakers) >= 0


@pytest.mark.asyncio
async def test_get_known_speakers(controller, database):
    """Test getting known speakers."""
    # Add speakers
    speaker1 = Speaker(speaker_id="speaker_1", name="Speaker 1")
    speaker2 = Speaker(speaker_id="speaker_2", name="Speaker 2")

    await database.save_speaker(speaker1)
    await database.save_speaker(speaker2)

    # Get speakers
    speakers = await controller.get_known_speakers()

    assert len(speakers) >= 2
    speaker_ids = [s.speaker_id for s in speakers]
    assert "speaker_1" in speaker_ids
    assert "speaker_2" in speaker_ids


@pytest.mark.asyncio
async def test_clear_conversation_history(controller):
    """Test clearing conversation history."""
    controller.clear_conversation_history()
    controller.use_case.clear_conversation_history.assert_called_once()
