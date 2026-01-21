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

    from faster_whisper import WhisperModel, download_model

    model_dir = MODELS_DIR / f"whisper-{model_name}"

    if model_dir.exists() and any(model_dir.iterdir()):
        print(f"✅ Whisper {model_name} already exists in {model_dir}, skipping...")
        return

    try:
        # Download to persistent directory
        print(f"📥 Downloading to {model_dir}...")
        path = download_model(model_name, output_dir=str(model_dir))
        print(f"✅ Whisper {model_name} downloaded successfully to {path}!")
        
        # Verify load
        WhisperModel(path, device="cpu", compute_type="int8")
        print("✅ Whisper model loaded/verified.")
    except Exception as e:
        print(f"❌ Failed to download Whisper: {e}")
        sys.exit(1)


def download_translation_model():
    """Download translation model (M2M100)."""
    print("📥 Downloading Translation model (Facebook M2M100)...")

    model_id = "facebook/m2m100_418M"
    base_url = f"https://huggingface.co/{model_id}/resolve/main"
    
    # Files required for M2M100
    files = [
        "config.json",
        "pytorch_model.bin",
        "vocab.json",
        "sentencepiece.bpe.model",
        "tokenizer_config.json",
        "generation_config.json"
    ]

    model_dir = MODELS_DIR / "translation" / "m2m100_418M"
    model_dir.mkdir(parents=True, exist_ok=True)

    for filename in files:
        file_path = model_dir / filename
        if file_path.exists():
            # Check for corruption (e.g. invalid auth response usually < 10KB, model is > 1GB)
            size = file_path.stat().st_size
            if filename.endswith(".bin") and size < 1024 * 1024 * 1000: # 1GB
                 print(f"⚠️ {filename} exists but looks corrupted ({size} bytes). Deleting to re-download...")
                 file_path.unlink()
            else:
                 print(f"✅ {filename} already exists, skipping...")
                 continue
            
        url = f"{base_url}/{filename}"
        print(f"📥 Downloading {filename}...")
        try:
            # properly handle large files
            urllib.request.urlretrieve(url, file_path)
            print(f"✅ {filename} downloaded successfully!")
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
            print("⚠️ Translation may not work without this file")

def download_speechbrain_model():
    """Download SpeechBrain Speaker ID model manually."""
    print("📥 Downloading SpeechBrain Speaker ID model...")
    
    model_name = "speechbrain/spkrec-ecapa-voxceleb"
    output_dir = MODELS_DIR / "speechbrain"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_url = "https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb/resolve/main"
    files = [
        "hyperparams.yaml",
        "embedding_model.ckpt",
        "mean_var_norm_emb.ckpt",
        "classifier.ckpt",
        "label_encoder.txt"
    ]
    
    print(f"📥 Downloading SpeechBrain model to {output_dir}...")
    
    for filename in files:
        url = f"{base_url}/{filename}"
        dest_path = output_dir / filename
        
        if dest_path.exists():
             print(f"✅ {filename} already exists, skipping...")
             continue
             
        print(f"   - Fetching {filename}...")
        try:
            urllib.request.urlretrieve(url, dest_path)
            print(f"✅ {filename} downloaded successfully!")
        except Exception as e:
            print(f"   ❌ Failed to download {filename}: {e}")
            # Non-critical files might fail, but hyperparams and embedding_model are strict
            if filename in ["hyperparams.yaml", "embedding_model.ckpt"]:
                raise

def download_pyannote_model():
    """
    Pyannote is gated, so we can't easily download it via script without token.
    We rely on the app to download it at runtime if token is provided,
    or use the fallback.
    """
    print("\n[3/5] Pyannote (Speaker ID)")
    print("-" * 60)
    print("📥 Downloading Pyannote.audio embedding model...")
    # We skip actual download here as it requires auth. 
    # The container will try to download on start if token env var is set.
    print("✅ Pyannote model download skipped (requires auth/runtime init), skipping...")


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
        ("SpeechBrain (Speaker ID)", download_speechbrain_model, []),
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
