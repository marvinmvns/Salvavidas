# Salvavidas Backend - Stable Build (Python 3.12)
# Optimized for maximum compatibility with Audio/AI libraries and Intel GPU

# --- Builder Stage ---
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
# We need these to compile any packages that don't have wheels
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    pkg-config \
    libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to ensure legacy vs new build behavior is handled correctly
RUN pip install --upgrade pip wheel setuptools

# Copy requirements
COPY requirements.txt .

# Install dependencies into a local directory
# process-dependency-links is not needed for modern pip, --prefer-binary helps speed
RUN pip install --user --no-cache-dir --prefer-binary -r requirements.txt

# --- Runtime Stage ---
FROM python:3.12-slim

WORKDIR /app

# Install runtime system dependencies
# ffmpeg: required for audio processing
# libsndfile1: required by soundfile/librosa
# curl: for healthcheck
# Intel Compute Runtime dependencies (optional but good for OpenVINO/Torch on Intel GPU)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder (this includes all installed libs)
COPY --from=builder /root/.local /root/.local

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

# Copy Project Configuration
COPY config/ ./config/

# Copy Application Code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY main.py ./main.py
COPY requirements.txt ./requirements.txt
COPY .env.example .env

# Copy Docker helper scripts
COPY docker/backend/download-models.py /app/download-models.py
COPY docker/backend/patch_speechbrain.py /app/patch_speechbrain.py
COPY docker/backend/entrypoint.sh /app/entrypoint.sh

# Permissions
RUN chmod +x /app/download-models.py /app/entrypoint.sh
RUN mkdir -p data/speakers data/analytics data/models

# Expose Port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=15s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start
ENTRYPOINT ["/app/entrypoint.sh"]
