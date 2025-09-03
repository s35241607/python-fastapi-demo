#!/bin/bash

# Docker development helper script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to setup development environment
setup_dev() {
    print_status "Setting up development environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please review and update the .env file with your settings."
    fi
    
    # Create logs directory
    mkdir -p backend/logs
    
    # Build and start services
    print_status "Building and starting development services..."
    docker-compose up --build -d
    
    print_status "Development environment is ready!"
    print_status "Backend API: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "pgAdmin: http://localhost:5050 (admin@example.com / admin)"
}

# Function to stop services
stop_services() {
    print_status "Stopping all services..."
    docker-compose down
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
}

# Function to show logs
show_logs() {
    if [ -z "$1" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$1"
    fi
}

# Function to run tests
run_tests() {
    print_status "Running tests in Docker container..."
    docker-compose exec backend pytest
}

# Main script logic
case "$1" in
    "setup"|"start")
        check_docker
        setup_dev
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        check_docker
        stop_services
        setup_dev
        ;;
    "logs")
        show_logs "$2"
        ;;
    "test")
        run_tests
        ;;
    "clean")
        cleanup
        ;;
    "status")
        docker-compose ps
        ;;
    *)
        echo "Usage: $0 {setup|start|stop|restart|logs|test|clean|status}"
        echo ""
        echo "Commands:"
        echo "  setup/start  - Build and start development environment"
        echo "  stop         - Stop all services"
        echo "  restart      - Restart all services"
        echo "  logs [service] - Show logs (optionally for specific service)"
        echo "  test         - Run tests"
        echo "  clean        - Clean up Docker resources"
        echo "  status       - Show service status"
        exit 1
        ;;
esac