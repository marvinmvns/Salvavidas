#!/usr/bin/env python3
"""
Salvavidas - Real-time Voice Translation Application
Main entry point for the application
"""
import sys
import argparse
import asyncio
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def run_web_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the web server with FastAPI."""
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║              🚁 Salvavidas Voice Translation               ║
    ║                                                            ║
    ║  Real-time voice translation with speaker identification  ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝

    🌐 Server starting at: http://{host}:{port}
    📱 Open your browser and navigate to the URL above

    Press CTRL+C to stop the server
    """)

    uvicorn.run(
        "src.adapters.presenters.web_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


async def run_cli_mode():
    """Run CLI mode for testing."""
    from config.settings import get_settings
    from src.infrastructure.database import Database
    from src.infrastructure.service_factory import ServiceFactory
    from src.core.use_cases import ProcessVoiceTranslationUseCase
    from src.adapters.controllers import VoiceTranslationController
    from src.core.entities import AudioChunk
    from datetime import datetime
    import pyaudio

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║              🚁 Salvavidas Voice Translation               ║
    ║                      CLI Mode                              ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    # Initialize
    print("🔧 Initializing...")
    settings = get_settings()
    database = Database()
    await database.init_db()

    # Get configs from database
    configs = await database.get_all_configs()
    for key, value in configs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    print(f"📊 Processing Mode: {settings.processing_mode}")
    print(f"🌍 Target Language: {settings.target_language}")
    print(f"🔊 Speaker ID: {'Enabled' if settings.enable_speaker_id else 'Disabled'}")
    print(f"💡 Suggestions: {'Enabled' if settings.enable_suggestions else 'Disabled'}")
    print()

    # Create services
    use_intel_gpu = configs.get("use_intel_gpu", False)
    factory = ServiceFactory(settings, use_intel_gpu=use_intel_gpu)

    try:
        use_case = ProcessVoiceTranslationUseCase(
            stt_service=factory.create_stt_service(),
            speaker_id_service=factory.create_speaker_id_service(),
            translation_service=factory.create_translation_service(),
            llm_service=factory.create_llm_service(),
            target_language=settings.target_language,
            enable_speaker_id=settings.enable_speaker_id,
            enable_suggestions=settings.enable_suggestions,
        )

        controller = VoiceTranslationController(use_case, database)
        await controller.initialize()

        print("✅ Ready! Speak into your microphone...")
        print("Press CTRL+C to stop")
        print("-" * 60)

        # Audio capture
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=settings.channels,
            rate=settings.sample_rate,
            input=True,
            frames_per_buffer=settings.chunk_size
        )

        try:
            while True:
                # Read audio chunk
                data = stream.read(settings.chunk_size, exception_on_overflow=False)

                audio_chunk = AudioChunk(
                    data=data,
                    timestamp=datetime.now(),
                    sample_rate=settings.sample_rate,
                    channels=settings.channels,
                    duration_ms=len(data) / (settings.sample_rate * 2) * 1000
                )

                # Process if chunk is large enough
                if len(data) >= settings.chunk_size * 20:  # ~1 second
                    conversation_turn = await controller.process_audio(audio_chunk)

                    if conversation_turn.transcription.text:
                        print(f"\n👤 Speaker: {conversation_turn.speaker.speaker_id}")
                        print(f"🗣️  Original ({conversation_turn.translation.source_language}): {conversation_turn.transcription.text}")
                        print(f"🌐 Translated ({conversation_turn.translation.target_language}): {conversation_turn.translation.translated_text}")

                        if conversation_turn.suggestions:
                            print(f"💡 Suggestions:")
                            for i, sug in enumerate(conversation_turn.suggestions, 1):
                                print(f"   {i}. {sug.text}")
                        print("-" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Stopping...")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            await database.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await database.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Salvavidas - Real-time Voice Translation"
    )
    parser.add_argument(
        "mode",
        choices=["web", "cli"],
        default="web",
        nargs="?",
        help="Run mode: web (default) or cli"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for web server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for web server (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    if args.mode == "web":
        run_web_server(host=args.host, port=args.port, reload=args.reload)
    elif args.mode == "cli":
        asyncio.run(run_cli_mode())


if __name__ == "__main__":
    main()
