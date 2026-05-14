#!/bin/bash
# F1 Strategy Platform v4.0 - Production Deployment Script
# Usage: ./deploy.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Setup environment
setup_env() {
    echo ""
    echo "Setting up environment..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status "Created .env from .env.example"
            print_warning "Please edit .env with your production values!"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_status ".env file exists"
    fi
}

# Deploy stack
deploy() {
    echo ""
    echo "🚀 Deploying F1 Strategy Platform v4.0..."
    echo "=============================================="
    
    check_prerequisites
    setup_env
    
    echo ""
    echo "Building and starting services..."
    docker-compose -f $COMPOSE_FILE up -d --build
    
    echo ""
    echo "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    echo ""
    echo "Checking service health..."
    
    if curl -s http://localhost/health > /dev/null; then
        print_status "NGINX is healthy"
    else
        print_warning "NGINX health check pending (may need more time)"
    fi
    
    if curl -s http://localhost/api/health > /dev/null; then
        print_status "Backend API is healthy"
    else
        print_warning "Backend health check pending (may need more time)"
    fi
    
    echo ""
    echo "=============================================="
    print_status "Deployment complete!"
    echo ""
    echo "Access your application:"
    echo "  • Main App:      http://localhost"
    echo "  • API Docs:      http://localhost/api/docs"
    echo "  • Grafana:       http://localhost:3001"
    echo "  • Prometheus:    http://localhost:9090"
    echo ""
    echo "Default credentials:"
    echo "  • Admin:         admin / admin123"
    echo "  • Grafana:       admin / (from .env)"
    echo ""
    print_warning "Change default passwords immediately!"
    echo ""
    echo "View logs: docker-compose logs -f"
    echo "Stop:      docker-compose down"
}

# Stop services
stop() {
    echo "Stopping F1 Strategy Platform..."
    docker-compose -f $COMPOSE_FILE down
    print_status "Services stopped"
}

# Restart services
restart() {
    echo "Restarting F1 Strategy Platform..."
    docker-compose -f $COMPOSE_FILE restart
    print_status "Services restarted"
}

# View logs
logs() {
    docker-compose -f $COMPOSE_FILE logs -f
}

# Update images
update() {
    echo "Updating to latest images..."
    docker-compose -f $COMPOSE_FILE pull
    docker-compose -f $COMPOSE_FILE up -d
    print_status "Update complete"
}

# Backup database
backup() {
    echo "Creating database backup..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T postgres pg_dump -U f1user f1strategy > "$BACKUP_FILE"
    print_status "Backup created: $BACKUP_FILE"
}

# Reset everything (WARNING: destroys data)
reset() {
    echo "WARNING: This will destroy all data!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        docker-compose -f $COMPOSE_FILE down -v
        sudo rm -rf postgres_data redis_data
        print_status "All data destroyed. Run './deploy.sh deploy' to start fresh."
    else
        echo "Reset cancelled."
    fi
}

# Show status
status() {
    echo "Service Status:"
    echo "==============="
    docker-compose -f $COMPOSE_FILE ps
    
    echo ""
    echo "Resource Usage:"
    echo "=============="
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Run load test
test() {
    if ! command -v locust &> /dev/null; then
        echo "Installing Locust..."
        pip install locust
    fi
    
    echo "Starting load test..."
    echo "Open http://localhost:8089 for Locust web interface"
    cd tests
    locust -f locustfile.py --host=http://localhost
}

# Show help
help() {
    cat << EOF
F1 Strategy Platform v4.0 - Deployment Script

Usage: ./deploy.sh [command]

Commands:
  deploy    - Deploy the full stack (build + start)
  stop      - Stop all services
  restart   - Restart all services
  logs      - View service logs
  update    - Update to latest images
  backup    - Backup database
  reset     - Reset everything (DESTROYS DATA!)
  status    - Show service status and resource usage
  test      - Run load tests with Locust
  help      - Show this help message

Examples:
  ./deploy.sh deploy    # First time deployment
  ./deploy.sh logs      # View logs
  ./deploy.sh backup    # Create database backup

Quick Start:
  1. Run: ./deploy.sh deploy
  2. Access: http://localhost
  3. Login: admin/admin123 (change immediately!)

For production:
  1. Edit .env with your production values
  2. Set up SSL certificates in nginx/ssl/
  3. Uncomment HTTPS section in nginx/nginx.conf
  4. Run: ./deploy.sh deploy

Documentation: INFRASTRUCTURE_v4.0.md
EOF
}

# Main
main() {
    case "${1:-help}" in
        deploy)
            deploy
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs
            ;;
        update)
            update
            ;;
        backup)
            backup
            ;;
        reset)
            reset
            ;;
        status)
            status
            ;;
        test)
            test
            ;;
        help|--help|-h)
            help
            ;;
        *)
            print_error "Unknown command: $1"
            help
            exit 1
            ;;
    esac
}

main "$@"
