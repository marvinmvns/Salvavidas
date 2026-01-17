"""Unit tests for database."""
import pytest
from src.infrastructure.database import Database
from src.core.entities import Speaker


@pytest.fixture
async def database():
    """Create test database."""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_config_operations(database):
    """Test configuration operations."""
    # Set config
    await database.set_config("test_key", "test_value")

    # Get config
    value = await database.get_config("test_key")
    assert value == "test_value"

    # Update config
    await database.set_config("test_key", "new_value")
    value = await database.get_config("test_key")
    assert value == "new_value"


@pytest.mark.asyncio
async def test_config_types(database):
    """Test configuration type handling."""
    # String
    await database.set_config("str_key", "value")
    assert await database.get_config("str_key") == "value"

    # Integer
    await database.set_config("int_key", 42)
    assert await database.get_config("int_key") == 42

    # Boolean
    await database.set_config("bool_key", True)
    assert await database.get_config("bool_key") is True

    # Float
    await database.set_config("float_key", 3.14)
    assert await database.get_config("float_key") == 3.14


@pytest.mark.asyncio
async def test_get_all_configs(database):
    """Test getting all configurations."""
    await database.set_config("key1", "value1")
    await database.set_config("key2", 123)
    await database.set_config("key3", True)

    configs = await database.get_all_configs()

    assert "key1" in configs
    assert "key2" in configs
    assert "key3" in configs
    assert configs["key1"] == "value1"
    assert configs["key2"] == 123
    assert configs["key3"] is True


@pytest.mark.asyncio
async def test_speaker_operations(database):
    """Test speaker operations."""
    # Create speaker
    speaker = Speaker(
        speaker_id="test_speaker",
        name="Test Speaker",
        language="en",
        confidence=0.95,
        embedding=b"test_embedding_data"
    )

    # Save speaker
    await database.save_speaker(speaker)

    # Get all speakers
    speakers = await database.get_all_speakers()
    assert len(speakers) == 1
    assert speakers[0].speaker_id == "test_speaker"
    assert speakers[0].name == "Test Speaker"
    assert speakers[0].language == "en"
    assert speakers[0].confidence == 0.95

    # Update speaker
    speaker.name = "Updated Name"
    speaker.confidence = 0.99
    await database.save_speaker(speaker)

    speakers = await database.get_all_speakers()
    assert len(speakers) == 1  # Should still be 1 (update, not insert)
    assert speakers[0].name == "Updated Name"
    assert speakers[0].confidence == 0.99


@pytest.mark.asyncio
async def test_default_configs_seeded(database):
    """Test that default configurations are seeded."""
    configs = await database.get_all_configs()

    # Check some default configs exist
    assert "processing_mode" in configs
    assert "target_language" in configs
    assert "enable_speaker_id" in configs
    assert "enable_suggestions" in configs
