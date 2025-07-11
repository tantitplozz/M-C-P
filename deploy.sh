#!/bin/bash

# GOD-TIER AUTOBUY STACK - Production Deployment Script
# This script deploys the entire stack to production environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="god-tier-autobuy-stack"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed!"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed!"
    fi

    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]] && ! groups | grep -q docker; then
        error "Please run as root or add user to docker group!"
    fi

    success "All prerequisites met!"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."

    directories=(
        "data"
        "logs"
        "config"
        "backup"
        "data/screenshots"
        "data/results"
        "data/reports"
        "data/vector_store"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log "Created directory: $dir"
    done

    success "Directories created successfully!"
}

# Initialize environment
init_environment() {
    log "Initializing environment..."

    # Copy .env.example to .env if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example "$ENV_FILE"
            warning "Created .env from .env.example - Please update with your values!"
        else
            error ".env.example not found!"
        fi
    fi

    # Generate encryption key if not set
    if ! grep -q "ENCRYPTION_KEY=" "$ENV_FILE" || grep -q "your_32_character_encryption_key_here" "$ENV_FILE"; then
        ENCRYPTION_KEY=$(openssl rand -base64 32)
        sed -i "s/your_32_character_encryption_key_here/$ENCRYPTION_KEY/" "$ENV_FILE"
        log "Generated encryption key"
    fi

    # Generate JWT secret if not set
    if ! grep -q "JWT_SECRET=" "$ENV_FILE" || grep -q "your_jwt_secret_key_here" "$ENV_FILE"; then
        JWT_SECRET=$(openssl rand -base64 32)
        sed -i "s/your_jwt_secret_key_here/$JWT_SECRET/" "$ENV_FILE"
        log "Generated JWT secret"
    fi

    success "Environment initialized!"
}

# Pull latest images
pull_images() {
    log "Pulling latest Docker images..."

    docker-compose -f "$COMPOSE_FILE" pull

    success "Images pulled successfully!"
}

# Build custom images
build_images() {
    log "Building custom Docker images..."

    docker-compose -f "$COMPOSE_FILE" build --no-cache

    success "Images built successfully!"
}

# Start services
start_services() {
    log "Starting GOD-TIER AUTOBUY STACK services..."

    # Start in detached mode
    docker-compose -f "$COMPOSE_FILE" up -d

    success "Services started successfully!"
}

# Health check
health_check() {
    log "Performing health checks..."

    # Wait for services to be ready
    sleep 30

    # Check main application
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        success "Main application is healthy!"
    else
        error "Main application health check failed!"
    fi

    # Check Redis
    if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
        success "Redis is healthy!"
    else
        error "Redis health check failed!"
    fi

    # Check Prometheus
    if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
        success "Prometheus is healthy!"
    else
        warning "Prometheus health check failed (non-critical)"
    fi

    # Check Grafana
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        success "Grafana is healthy!"
    else
        warning "Grafana health check failed (non-critical)"
    fi

    success "Health checks completed!"
}

# Show status
show_status() {
    log "Current stack status:"

    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    log "Service URLs:"
    echo "🚀 Main Application: http://localhost:8080"
    echo "📊 Grafana Dashboard: http://localhost:3000 (admin/godtier2024)"
    echo "🔍 Prometheus: http://localhost:9090"
    echo "🖥️  VNC Viewer: vnc://localhost:5900"
    echo "📈 Metrics: http://localhost:8000"
    echo ""

    success "Stack deployed successfully!"
}

# Backup function
backup_data() {
    log "Creating backup..."

    BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Backup data directory
    if [[ -d "data" ]]; then
        cp -r data "$BACKUP_DIR/"
        log "Data backed up to $BACKUP_DIR/"
    fi

    # Backup configuration
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$BACKUP_DIR/"
        log "Configuration backed up to $BACKUP_DIR/"
    fi

    success "Backup created at $BACKUP_DIR"
}

# Restore function
restore_data() {
    if [[ -z "$1" ]]; then
        error "Please specify backup directory: ./deploy.sh restore <backup_directory>"
    fi

    BACKUP_DIR="$1"

    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Backup directory $BACKUP_DIR does not exist!"
    fi

    log "Restoring from backup: $BACKUP_DIR"

    # Stop services
    docker-compose -f "$COMPOSE_FILE" down

    # Restore data
    if [[ -d "$BACKUP_DIR/data" ]]; then
        rm -rf data
        cp -r "$BACKUP_DIR/data" ./
        log "Data restored from backup"
    fi

    # Restore configuration
    if [[ -f "$BACKUP_DIR/.env" ]]; then
        cp "$BACKUP_DIR/.env" ./
        log "Configuration restored from backup"
    fi

    success "Restore completed!"
}

# Update function
update_stack() {
    log "Updating GOD-TIER AUTOBUY STACK..."

    # Create backup before update
    backup_data

    # Pull latest code (if git repository)
    if [[ -d ".git" ]]; then
        git pull origin main
        log "Code updated from git"
    fi

    # Pull latest images
    pull_images

    # Rebuild images
    build_images

    # Restart services
    docker-compose -f "$COMPOSE_FILE" up -d

    # Health check
    health_check

    success "Stack updated successfully!"
}

# Stop services
stop_services() {
    log "Stopping GOD-TIER AUTOBUY STACK services..."

    docker-compose -f "$COMPOSE_FILE" down

    success "Services stopped successfully!"
}

# Remove everything
remove_stack() {
    log "Removing GOD-TIER AUTOBUY STACK..."

    # Confirm removal
    read -p "Are you sure you want to remove the entire stack? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Removal cancelled."
        exit 0
    fi

    # Create backup before removal
    backup_data

    # Stop and remove containers, networks, volumes
    docker-compose -f "$COMPOSE_FILE" down -v --rmi all

    # Remove dangling images
    docker system prune -f

    success "Stack removed successfully!"
}

# Show logs
show_logs() {
    if [[ -z "$1" ]]; then
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        docker-compose -f "$COMPOSE_FILE" logs -f "$1"
    fi
}

# Main execution
main() {
    case "$1" in
        "start"|"deploy")
            check_prerequisites
            create_directories
            init_environment
            pull_images
            build_images
            start_services
            health_check
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 5
            start_services
            health_check
            show_status
            ;;
        "update")
            update_stack
            ;;
        "backup")
            backup_data
            ;;
        "restore")
            restore_data "$2"
            ;;
        "remove")
            remove_stack
            ;;
        "logs")
            show_logs "$2"
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        *)
            echo "GOD-TIER AUTOBUY STACK - Deployment Script"
            echo ""
            echo "Usage: $0 {start|stop|restart|update|backup|restore|remove|logs|status|health}"
            echo ""
            echo "Commands:"
            echo "  start/deploy  - Deploy the entire stack"
            echo "  stop          - Stop all services"
            echo "  restart       - Restart all services"
            echo "  update        - Update stack to latest version"
            echo "  backup        - Create backup of data and configuration"
            echo "  restore <dir> - Restore from backup directory"
            echo "  remove        - Remove entire stack (with backup)"
            echo "  logs [service]- Show logs (all services or specific service)"
            echo "  status        - Show current status"
            echo "  health        - Run health checks"
            echo ""
            echo "Examples:"
            echo "  $0 start                    # Deploy the stack"
            echo "  $0 logs autobuy-stack      # Show main app logs"
            echo "  $0 restore backup/20240101_120000  # Restore from backup"
            echo ""
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
