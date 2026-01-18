#!/usr/bin/env python3
"""
Salvavidas Model Downloader
Downloads all required AI models for local processing
Works both inside Docker and in local environment
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
import urllib.request

# Detect environment and set model directory
if os.path.exists("/.dockerenv") or os.path.exists("/app"):
    # Running inside Docker
    MODELS_DIR = Path("/app/data/models")
else:
    # Running locally
    MODELS_DIR = Path(__file__).parent.parent.parent / "data" / "models"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

def download_whisper_model(model_name="large-v3"):
    """Download Whisper model for STT."""
    print(f"📥 Downloading Whisper model: {model_name}...")

    from faster_whisper import WhisperModel

    model_path = MODELS_DIR / f"whisper-{model_name}"

    if model_path.exists():
        print(f"✅ Whisper {model_name} already exists, skipping...")
        return

    try:
        # Download and cache
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        print(f"✅ Whisper {model_name} downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download Whisper: {e}")
        sys.exit(1)


def download_translation_model():
    """Download translation model."""
    print("📥 Downloading Translation model...")

    model_name = "Helsinki-NLP/opus-mt-en-pt"
    model_path = MODELS_DIR / "translation"

    if model_path.exists():
        print("✅ Translation model already exists, skipping...")
        return

    try:
        snapshot_download(
            repo_id=model_name,
            cache_dir=str(MODELS_DIR / "translation"),
            local_dir=str(model_path)
        )
        print("✅ Translation model downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download Translation model: {e}")
        print("⚠️ Will use API-based translation instead")


def download_pyannote_model():
    """Download Pyannote speaker embedding model."""
    print("📥 Downloading Pyannote.audio embedding model...")

    model_name = "pyannote/embedding"
    model_path = MODELS_DIR / "pyannote"

    if model_path.exists():
        print("✅ Pyannote model already exists, skipping...")
        return

    try:
        # Check for HuggingFace token
        hf_token = os.getenv("HUGGINGFACE_TOKEN")

        snapshot_download(
            repo_id=model_name,
            cache_dir=str(MODELS_DIR / "pyannote"),
            local_dir=str(model_path),
            token=hf_token
        )
        print("✅ Pyannote model downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download Pyannote model: {e}")
        print("⚠️ Note: pyannote/embedding requires HuggingFace token")
        print("⚠️ Set HUGGINGFACE_TOKEN environment variable")
        print("⚠️ Will use fallback embedding method")


def download_llama_model():
    """Download Llama model for LLM."""
    print("📥 Downloading Llama model...")

    # Using a smaller GGUF model
    model_url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
    model_path = MODELS_DIR / "llama-7b-chat.gguf"

    if model_path.exists():
        print("✅ Llama model already exists, skipping...")
        return

    try:
        print("⚠️ Large file (~4GB), this may take a while...")
        urllib.request.urlretrieve(model_url, model_path)
        print("✅ Llama model downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download Llama model: {e}")
        print("⚠️ Will use API-based LLM instead")


def download_piper_voice():
    """Download Piper TTS voice."""
    print("📥 Downloading Piper voice...")

    voice_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    voice_config_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

    voice_dir = MODELS_DIR / "piper" / "en_US-lessac-medium"
    voice_dir.mkdir(parents=True, exist_ok=True)

    voice_path = voice_dir / "en_US-lessac-medium.onnx"
    config_path = voice_dir / "en_US-lessac-medium.onnx.json"

    if voice_path.exists() and config_path.exists():
        print("✅ Piper voice already exists, skipping...")
        return

    try:
        print("Downloading voice model...")
        urllib.request.urlretrieve(voice_url, voice_path)
        print("Downloading voice config...")
        urllib.request.urlretrieve(voice_config_url, config_path)
        print("✅ Piper voice downloaded successfully!")
    except Exception as e:
        print(f"❌ Failed to download Piper voice: {e}")
        print("⚠️ Will use API-based TTS instead")


def main():
    """Download all models."""
    print("=" * 60)
    print("🤖 Salvavidas Model Downloader")
    print("=" * 60)
    print()

    # Check if we should skip download
    if os.getenv("SKIP_MODEL_DOWNLOAD") == "true":
        print("⏭️ SKIP_MODEL_DOWNLOAD=true, skipping model download")
        return

    # Get processing mode
    processing_mode = os.getenv("PROCESSING_MODE", "local")

    if processing_mode != "local":
        print(f"⏭️ PROCESSING_MODE={processing_mode}, skipping local model download")
        return

    print(f"📦 Processing mode: {processing_mode}")
    print(f"📁 Models directory: {MODELS_DIR}")
    print()

    # Download models
    models_to_download = [
        ("Whisper v3-turbo (STT)", download_whisper_model, ["large-v3"]),
        ("Translation", download_translation_model, []),
        ("Pyannote (Speaker ID)", download_pyannote_model, []),
        ("Llama (LLM)", download_llama_model, []),
        ("Piper (TTS)", download_piper_voice, []),
    ]

    total = len(models_to_download)

    for idx, (name, func, args) in enumerate(models_to_download, 1):
        print(f"\n[{idx}/{total}] {name}")
        print("-" * 60)
        try:
            func(*args)
        except Exception as e:
            print(f"❌ Error: {e}")
            print("⚠️ Continuing with next model...")

    print()
    print("=" * 60)
    print("✅ Model download complete!")
    print("=" * 60)
    print()
    print("Models stored in:", MODELS_DIR)
    print()

    # Check disk usage
    try:
        import shutil
        total, used, free = shutil.disk_usage(MODELS_DIR)
        print(f"💾 Disk usage:")
        print(f"   Total: {total // (2**30)} GB")
        print(f"   Used:  {used // (2**30)} GB")
        print(f"   Free:  {free // (2**30)} GB")
    except:
        pass


if __name__ == "__main__":
    main()
