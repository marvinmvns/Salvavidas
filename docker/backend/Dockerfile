# Salvavidas Backend
# Multi-stage build for optimized Python FastAPI application

# Build stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY .env.example .env

# Copy model downloader and entrypoint
COPY docker/backend/download-models.py /app/download-models.py
COPY docker/backend/entrypoint.sh /app/entrypoint.sh

# Make scripts executable
RUN chmod +x /app/download-models.py /app/entrypoint.sh

# Create data directories
RUN mkdir -p data/speakers data/analytics data/models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
