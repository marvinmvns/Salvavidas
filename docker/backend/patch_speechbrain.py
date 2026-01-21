
import os
import glob
import sys
from pathlib import Path

def patch_speechbrain():
    """
    Patches speechbrain to work with torchaudio 2.x
    Replaces the deprecated list_audio_backends check with a dummy or modern equivalent.
    """
    print("🔧 Patching SpeechBrain for Torchaudio 2.x compatibility...")
    
    # Locate speechbrain installation
    site_packages = glob.glob("/root/.local/lib/python3.*/site-packages")[0]
    target_file = Path(site_packages) / "speechbrain/utils/torch_audio_backend.py"
    
    if not target_file.exists():
        print(f"⚠️ SpeechBrain backend file not found at {target_file}")
        return

    with open(target_file, 'r') as f:
        content = f.read()

    # The failing line is: available_backends = torchaudio.list_audio_backends()
    # We will replace the check_torchaudio_backend function content or the specific call.
    
    if "torchaudio.list_audio_backends()" in content:
        # Replace with a dummy list that includes standard backends or a safe fallback
        # In newer torchaudio, backends are different, but for speechbrain < 1.0 mostly 'sox' or 'soundfile' matter.
        new_content = content.replace(
            "available_backends = torchaudio.list_audio_backends()",
            "available_backends = ['soundfile', 'sox_io'] # Patched by Salvavidas"
        )
        
        with open(target_file, 'w') as f:
            f.write(new_content)
            
        print("✅ SpeechBrain patched successfully!")
    else:
        print("ℹ️ SpeechBrain already patched or code not found.")

if __name__ == "__main__":
    try:
        patch_speechbrain()
    except Exception as e:
        print(f"❌ Failed to patch SpeechBrain: {e}")
