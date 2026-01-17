"""Unit tests for core entities."""
import pytest
from datetime import datetime
from src.core.entities import (
    AudioChunk,
    Speaker,
    TranscriptionSegment,
    Translation,
    SuggestionResponse,
    ConversationTurn
)


class TestAudioChunk:
    """Test AudioChunk entity."""

    def test_create_audio_chunk(self):
        """Test creating an audio chunk."""
        chunk = AudioChunk(
            data=b"test_audio_data",
            timestamp=datetime.now(),
            sample_rate=16000,
            channels=1,
            duration_ms=1000.0
        )

        assert chunk.data == b"test_audio_data"
        assert chunk.sample_rate == 16000
        assert chunk.channels == 1
        assert chunk.duration_ms == 1000.0
        assert chunk.size_bytes == len(b"test_audio_data")


class TestSpeaker:
    """Test Speaker entity."""

    def test_create_speaker(self):
        """Test creating a speaker."""
        speaker = Speaker(
            speaker_id="speaker_1",
            name="John Doe",
            language="en",
            confidence=0.95
        )

        assert speaker.speaker_id == "speaker_1"
        assert speaker.name == "John Doe"
        assert speaker.language == "en"
        assert speaker.confidence == 0.95

    def test_speaker_equality(self):
        """Test speaker equality."""
        speaker1 = Speaker(speaker_id="speaker_1")
        speaker2 = Speaker(speaker_id="speaker_1", name="Different Name")
        speaker3 = Speaker(speaker_id="speaker_2")

        assert speaker1 == speaker2
        assert speaker1 != speaker3

    def test_speaker_hash(self):
        """Test speaker hashing."""
        speaker1 = Speaker(speaker_id="speaker_1")
        speaker2 = Speaker(speaker_id="speaker_1")

        assert hash(speaker1) == hash(speaker2)


class TestTranscriptionSegment:
    """Test TranscriptionSegment entity."""

    def test_create_transcription(self):
        """Test creating a transcription segment."""
        speaker = Speaker(speaker_id="speaker_1")
        transcription = TranscriptionSegment(
            text="Hello world",
            speaker=speaker,
            language="en",
            timestamp=datetime.now(),
            confidence=0.95,
            start_time=0.0,
            end_time=2.5
        )

        assert transcription.text == "Hello world"
        assert transcription.speaker == speaker
        assert transcription.language == "en"
        assert transcription.confidence == 0.95
        assert transcription.duration == 2.5


class TestTranslation:
    """Test Translation entity."""

    def test_create_translation(self):
        """Test creating a translation."""
        translation = Translation(
            original_text="Hello world",
            translated_text="Olá mundo",
            source_language="en",
            target_language="pt",
            timestamp=datetime.now(),
            confidence=0.98,
            service="test"
        )

        assert translation.original_text == "Hello world"
        assert translation.translated_text == "Olá mundo"
        assert translation.source_language == "en"
        assert translation.target_language == "pt"
        assert translation.confidence == 0.98
        assert translation.service == "test"


class TestConversationTurn:
    """Test ConversationTurn entity."""

    def test_create_conversation_turn(self):
        """Test creating a conversation turn."""
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
        suggestions = [
            SuggestionResponse(
                text="Hi there!",
                language="en",
                confidence=0.9,
                context="Hello"
            )
        ]

        turn = ConversationTurn(
            transcription=transcription,
            translation=translation,
            suggestions=suggestions
        )

        assert turn.transcription == transcription
        assert turn.translation == translation
        assert len(turn.suggestions) == 1
        assert turn.speaker == speaker
