#!/bin/bash
set -e

echo "========================================="
echo "🚁 Salvavidas Backend Starting..."
echo "========================================="
echo ""

# Check if models should be downloaded
if [ "$PROCESSING_MODE" = "local" ] && [ "$SKIP_MODEL_DOWNLOAD" != "true" ]; then
    echo "🔍 Checking for required models..."
    python3 /app/download-models.py

    if [ $? -ne 0 ]; then
        echo "⚠️ Model download failed, but continuing..."
        echo "⚠️ Some features may not work until models are downloaded"
    fi
    echo ""
fi

# Print configuration
echo "📋 Configuration:"
echo "   Processing Mode: ${PROCESSING_MODE:-local}"
echo "   Target Language: ${TARGET_LANGUAGE:-en}"
echo "   Speaker ID: ${ENABLE_SPEAKER_ID:-true}"
echo "   Suggestions: ${ENABLE_SUGGESTIONS:-true}"
echo "   Workers: ${WORKERS:-4}"
echo ""

# Start application
echo "🚀 Starting Uvicorn server..."
echo "========================================="
echo ""

exec uvicorn src.adapters.presenters.web_api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WORKERS:-4}" \
    --log-level "${LOG_LEVEL:-info}"
