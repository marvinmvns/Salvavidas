"""Unit tests for use cases."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from src.core.use_cases import ProcessVoiceTranslationUseCase
from src.core.entities import (
    AudioChunk,
    Speaker,
    TranscriptionSegment,
    Translation,
    SuggestionResponse
)


@pytest.fixture
def mock_services():
    """Create mock services."""
    stt_service = AsyncMock()
    speaker_id_service = AsyncMock()
    translation_service = AsyncMock()
    llm_service = AsyncMock()

    return {
        "stt": stt_service,
        "speaker_id": speaker_id_service,
        "translation": translation_service,
        "llm": llm_service
    }


@pytest.fixture
def use_case(mock_services):
    """Create use case with mocked services."""
    return ProcessVoiceTranslationUseCase(
        stt_service=mock_services["stt"],
        speaker_id_service=mock_services["speaker_id"],
        translation_service=mock_services["translation"],
        llm_service=mock_services["llm"],
        target_language="pt",
        enable_speaker_id=True,
        enable_suggestions=True
    )


@pytest.mark.asyncio
async def test_execute_processes_audio_chunk(use_case, mock_services):
    """Test that execute processes an audio chunk correctly."""
    # Setup
    audio_chunk = AudioChunk(
        data=b"test_audio",
        timestamp=datetime.now(),
        sample_rate=16000,
        channels=1,
        duration_ms=1000.0
    )

    speaker = Speaker(speaker_id="speaker_1", confidence=0.9)
    transcription = TranscriptionSegment(
        text="Hello world",
        speaker=speaker,
        language="en",
        timestamp=datetime.now(),
        confidence=0.95,
        start_time=0.0,
        end_time=1.0
    )
    translation = Translation(
        original_text="Hello world",
        translated_text="Olá mundo",
        source_language="en",
        target_language="pt",
        timestamp=datetime.now()
    )
    suggestions = [
        SuggestionResponse(
            text="Oi!",
            language="en",
            confidence=0.9,
            context="Hello world"
        )
    ]

    # Mock responses
    mock_services["speaker_id"].identify_speaker.return_value = speaker
    mock_services["stt"].transcribe.return_value = transcription
    mock_services["llm"].detect_language.return_value = "en"
    mock_services["translation"].translate.return_value = translation
    mock_services["llm"].generate_suggestions.return_value = suggestions

    # Execute
    result = await use_case.execute(audio_chunk)

    # Assert
    assert result.transcription.text == "Hello world"
    assert result.translation.translated_text == "Olá mundo"
    assert len(result.suggestions) == 1
    assert result.speaker.speaker_id == "speaker_1"

    # Verify service calls
    mock_services["speaker_id"].identify_speaker.assert_called_once()
    mock_services["stt"].transcribe.assert_called_once()
    mock_services["translation"].translate.assert_called_once()
    mock_services["llm"].generate_suggestions.assert_called_once()


@pytest.mark.asyncio
async def test_execute_without_suggestions(mock_services):
    """Test execute without suggestions enabled."""
    use_case = ProcessVoiceTranslationUseCase(
        stt_service=mock_services["stt"],
        speaker_id_service=mock_services["speaker_id"],
        translation_service=mock_services["translation"],
        llm_service=mock_services["llm"],
        target_language="pt",
        enable_speaker_id=True,
        enable_suggestions=False  # Disabled
    )

    audio_chunk = AudioChunk(
        data=b"test_audio",
        timestamp=datetime.now(),
        sample_rate=16000,
        channels=1,
        duration_ms=1000.0
    )

    speaker = Speaker(speaker_id="speaker_1")
    transcription = TranscriptionSegment(
        text="Hello",
        speaker=speaker,
        language="en",
        timestamp=datetime.now(),
        confidence=0.95,
        start_time=0.0,
        end_time=1.0
    )
    translation = Translation(
        original_text="Hello",
        translated_text="Olá",
        source_language="en",
        target_language="pt",
        timestamp=datetime.now()
    )

    mock_services["speaker_id"].identify_speaker.return_value = speaker
    mock_services["stt"].transcribe.return_value = transcription
    mock_services["llm"].detect_language.return_value = "en"
    mock_services["translation"].translate.return_value = translation

    result = await use_case.execute(audio_chunk)

    assert len(result.suggestions) == 0
    mock_services["llm"].generate_suggestions.assert_not_called()


@pytest.mark.asyncio
async def test_clear_conversation_history(use_case):
    """Test clearing conversation history."""
    use_case.conversation_history = ["msg1", "msg2", "msg3"]

    use_case.clear_conversation_history()

    assert len(use_case.conversation_history) == 0
