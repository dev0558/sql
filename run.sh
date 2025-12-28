#!/bin/bash

# The Great Escape - CTF Challenge Runner
# NexusHR Enterprise HR Management System

set -e

COMPOSE_PROJECT_NAME="nexushr"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "================================================"
    echo "     The Great Escape - CTF Challenge"
    echo "     NexusHR Enterprise System"
    echo "================================================"
    echo -e "${NC}"
}

print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

get_compose_cmd() {
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

start_challenge() {
    print_banner
    check_docker

    COMPOSE_CMD=$(get_compose_cmd)

    print_status "Building and starting NexusHR challenge..."
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD up -d --build

    echo ""
    print_status "Waiting for services to be ready..."
    sleep 5

    # Check if services are running
    if $COMPOSE_CMD ps | grep -q "Up"; then
        echo ""
        print_status "Challenge is running!"
        echo ""
        echo -e "  ${GREEN}URL:${NC} http://localhost:5000"
        echo -e "  ${GREEN}Flag Format:${NC} Exploit3rs{...}"
        echo ""
        print_warning "Use './run.sh logs' to view application logs"
        print_warning "Use './run.sh stop' to stop the challenge"
    else
        print_error "Failed to start challenge. Check logs with './run.sh logs'"
        exit 1
    fi
}

stop_challenge() {
    print_banner
    check_docker

    COMPOSE_CMD=$(get_compose_cmd)

    print_status "Stopping NexusHR challenge..."
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD down -v

    print_status "Challenge stopped and volumes removed."
}

restart_challenge() {
    stop_challenge
    echo ""
    start_challenge
}

show_status() {
    print_banner
    check_docker

    COMPOSE_CMD=$(get_compose_cmd)

    print_status "Challenge Status:"
    echo ""
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD ps
}

show_logs() {
    check_docker

    COMPOSE_CMD=$(get_compose_cmd)

    cd "$SCRIPT_DIR"
    $COMPOSE_CMD logs -f
}

show_help() {
    print_banner
    echo "Usage: $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Build and start the challenge"
    echo "  stop     - Stop the challenge and remove volumes"
    echo "  restart  - Restart the challenge (stop + start)"
    echo "  status   - Show the status of challenge containers"
    echo "  logs     - Follow the container logs"
    echo "  help     - Show this help message"
    echo ""
}

# Main command handler
case "${1:-}" in
    start)
        start_challenge
        ;;
    stop)
        stop_challenge
        ;;
    restart)
        restart_challenge
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
