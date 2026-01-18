#!/bin/bash

# Salvavidas Docker Build Script
# Builds all Docker images for the project

set -e

echo "🐳 Salvavidas Docker Build Script"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file. Please edit it with your configuration.${NC}"
fi

# Build mode
BUILD_MODE=${1:-local}

echo ""
echo -e "${YELLOW}Build Mode: $BUILD_MODE${NC}"
echo ""

case $BUILD_MODE in
    local)
        echo "Building for local development..."
        docker-compose build --no-cache
        ;;

    production)
        echo "Building for production..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
        ;;

    fast)
        echo "Building (using cache)..."
        docker-compose build
        ;;

    *)
        echo -e "${RED}❌ Unknown build mode: $BUILD_MODE${NC}"
        echo "Usage: ./build.sh [local|production|fast]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your configuration"
echo "  2. Run: ./deploy.sh start"
echo ""
