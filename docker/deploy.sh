#!/bin/bash

# Salvavidas Docker Deploy Script
# Manages Docker containers for the project

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Functions
show_usage() {
    echo "Salvavidas Docker Deploy Script"
    echo ""
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  status      - Show status of all services"
    echo "  logs        - Show logs (use -f to follow)"
    echo "  shell       - Open bash shell in backend container"
    echo "  clean       - Stop and remove all containers, networks, volumes"
    echo "  update      - Pull latest code and rebuild"
    echo "  health      - Check health of all services"
    echo ""
}

start_services() {
    echo -e "${BLUE}🚀 Starting Salvavidas services...${NC}"

    if [ ! -f .env ]; then
        echo -e "${RED}❌ .env file not found!${NC}"
        echo "Run: cp .env.example .env"
        exit 1
    fi

    docker-compose up -d

    echo ""
    echo -e "${GREEN}✅ Services started!${NC}"
    echo ""
    echo "Access the application at:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Frontend: http://localhost (if nginx enabled)"
    echo "  - API Docs: http://localhost:8000/docs"
    echo ""
    echo "Check status: ./deploy.sh status"
    echo "View logs: ./deploy.sh logs"
}

stop_services() {
    echo -e "${YELLOW}⏸ Stopping Salvavidas services...${NC}"
    docker-compose stop
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart_services() {
    echo -e "${YELLOW}🔄 Restarting Salvavidas services...${NC}"
    docker-compose restart
    echo -e "${GREEN}✅ Services restarted${NC}"
}

show_status() {
    echo -e "${BLUE}📊 Salvavidas Services Status${NC}"
    echo ""
    docker-compose ps
}

show_logs() {
    if [ "$2" == "-f" ]; then
        docker-compose logs -f
    else
        docker-compose logs --tail=100
    fi
}

open_shell() {
    echo -e "${BLUE}🐚 Opening shell in backend container...${NC}"
    docker-compose exec backend bash
}

clean_all() {
    echo -e "${RED}⚠️ WARNING: This will remove all containers, networks, and volumes!${NC}"
    read -p "Are you sure? (yes/no): " -r
    echo

    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Cleaning up..."
        docker-compose down -v --remove-orphans
        echo -e "${GREEN}✅ Cleanup complete${NC}"
    else
        echo "Cancelled"
    fi
}

update_project() {
    echo -e "${BLUE}🔄 Updating Salvavidas...${NC}"

    # Pull latest code
    cd ..
    echo "Pulling latest code..."
    git pull

    # Rebuild containers
    cd docker
    echo "Rebuilding containers..."
    ./build.sh fast

    # Restart services
    echo "Restarting services..."
    docker-compose up -d

    echo -e "${GREEN}✅ Update complete!${NC}"
}

check_health() {
    echo -e "${BLUE}🏥 Checking health of services...${NC}"
    echo ""

    # Check backend
    if docker-compose ps | grep -q "backend.*Up"; then
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend: Healthy${NC}"
        else
            echo -e "${RED}✗ Backend: Unhealthy${NC}"
        fi
    else
        echo -e "${RED}✗ Backend: Not running${NC}"
    fi

    # Check nginx (if enabled)
    if docker-compose ps | grep -q "nginx.*Up"; then
        if curl -s -f http://localhost/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Nginx: Healthy${NC}"
        else
            echo -e "${YELLOW}⚠ Nginx: Running but health check failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Nginx: Not enabled${NC}"
    fi

    echo ""
}

# Main
COMMAND=${1:-help}

case $COMMAND in
    start)
        start_services
        ;;

    stop)
        stop_services
        ;;

    restart)
        restart_services
        ;;

    status)
        show_status
        ;;

    logs)
        show_logs "$@"
        ;;

    shell)
        open_shell
        ;;

    clean)
        clean_all
        ;;

    update)
        update_project
        ;;

    health)
        check_health
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
